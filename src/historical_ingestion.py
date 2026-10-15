from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from datetime import datetime
import requests

from project_config import COMMODITY, COMMODITY_ID, HISTORICAL_FILE


URL = "https://api.agmarknet.gov.in/v1/prices-and-arrivals/date-wise/specific-commodity"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://agmarknet.gov.in",
    "Referer": "https://agmarknet.gov.in/",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
}


def fetch_historical_data(year, month, state_id, commodity_id, max_retries=3):
    params = {
        "year": year,
        "month": month,
        "stateId": state_id,
        "commodityId": commodity_id,
        "includeExcel": "false",
    }

    for attempt in range(1, max_retries + 1):
        try:
            print(
                f"Fetching {year}-{month:02d} "
                f"(attempt {attempt}/{max_retries})..."
            )

            response = requests.get(
                URL,
                params=params,
                headers=HEADERS,
                timeout=(5, 20),
            )

            if not response.ok:
                body_preview = response.text[:400].replace("\\n", " ")
                raise requests.HTTPError(
                    f"HTTP {response.status_code} for {response.url}; response: {body_preview}",
                    response=response,
                )
            payload = response.json()

            if not payload.get("success"):
                raise RuntimeError(
                    payload.get("message", "Historical API request failed.")
                )

            return payload

        except (requests.RequestException, ValueError, RuntimeError) as error:
            error_text = str(error)
            # AGMARKNET now explicitly requires a CAPTCHA token for this endpoint.
            # Retrying the same anonymous request cannot resolve that server-side requirement.
            if "TOKEN_OR_CAPTCHA_REQUIRED" in error_text or (
                isinstance(error, requests.HTTPError)
                and getattr(error.response, "status_code", None) == 400
                and "captcha" in error_text.lower()
            ):
                raise RuntimeError(
                    "AGMARKNET's monthly endpoint requires a CAPTCHA token "
                    "(TOKEN_OR_CAPTCHA_REQUIRED). Automated refresh is blocked for "
                    "this endpoint; no retries were attempted. Existing saved data "
                    "has been preserved. Switch to a supported data source or an "
                    "official API that permits authenticated programmatic access."
                ) from error

            if attempt == max_retries:
                raise RuntimeError(
                    f"Failed to fetch {year}-{month:02d}: {type(error).__name__}: {error}"
                ) from error

            wait_seconds = 2 ** attempt
            print(f"Request failed ({type(error).__name__}: {error}). Retrying in {wait_seconds} seconds...")
            time.sleep(wait_seconds)


def fetch_latest_fallback(state_name, commodity_name):
    """
    Fetch recent AGMARKNET-derived records from a documented community API
    when the official monthly endpoint requires CAPTCHA. These are labelled
    by their source arrival_date; this endpoint is a recent-record fallback,
    not a replacement for the historical archive.
    """
    fallback_url = "https://mandi-api.onrender.com/v1/prices"
    response = requests.get(
        fallback_url,
        params={"state": state_name, "commodity": commodity_name},
        headers={"Accept": "application/json"},
        timeout=(8, 45),
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise RuntimeError("Fallback mandi API returned an unexpected response.")
    source_rows = payload.get("data")
    if not isinstance(source_rows, list):
        raise RuntimeError("Fallback mandi API response is missing its data list.")

    rows = []
    for item in source_rows:
        if not isinstance(item, dict):
            continue
        if str(item.get("state", "")).strip().casefold() != state_name.casefold():
            continue
        if str(item.get("commodity", "")).strip().casefold() != commodity_name.casefold():
            continue
        rows.append({
            "state": item.get("state", state_name),
            "district": item.get("district"),
            "market": item.get("market"),
            "commodity": item.get("commodity", commodity_name),
            "arrival_date": item.get("arrival_date"),
            "variety": item.get("variety"),
            "grade": item.get("grade"),
            "arrivals_mt": item.get("arrivals_mt"),
            "min_price": item.get("min_price"),
            "max_price": item.get("max_price"),
            "modal_price": item.get("modal_price"),
        })
    return rows


def flatten_records(payload, state_name, commodity_name):
    rows = []

    for market in payload.get("markets", []):
        market_name = market.get("marketName")

        for date_entry in market.get("dates", []):
            arrival_date = date_entry.get("arrivalDate")

            for item in date_entry.get("data", []):
                rows.append(
                    {
                        "state": state_name,
                        "market": market_name,
                        "commodity": commodity_name,
                        "arrival_date": arrival_date,
                        "variety": item.get("variety"),
                        "arrivals_mt": item.get("arrivals"),
                        "min_price": item.get("minimumPrice"),
                        "max_price": item.get("maximumPrice"),
                        "modal_price": item.get("modalPrice"),
                    }
                )

    return rows


def main():
    today = datetime.now()

    archive_file = Path(
        f"data/historical/maharashtra_{COMMODITY.lower()}_2026_02_to_07.csv"
    )
    archive = pd.read_csv(archive_file) if archive_file.exists() else pd.DataFrame()
    # Archive CSVs use ISO dates (YYYY-MM-DD); API responses may use DD/MM/YYYY.
    # Parse flexibly so the archive's real latest date is detected correctly.
    if not archive.empty:
        archive_raw_dates = archive["arrival_date"].astype(str).str.strip()
        archive_iso_mask = archive_raw_dates.str.match(r"^\d{4}-\d{2}-\d{2}")
        archive_dates = pd.Series(pd.NaT, index=archive.index, dtype="datetime64[ns]")
        archive_dates.loc[archive_iso_mask] = pd.to_datetime(archive_raw_dates.loc[archive_iso_mask], format="%Y-%m-%d", errors="coerce")
        archive_dates.loc[~archive_iso_mask] = pd.to_datetime(archive_raw_dates.loc[~archive_iso_mask], dayfirst=True, errors="coerce")
    else:
        archive_dates = pd.Series(dtype="datetime64[ns]")
    last_archive_date = archive_dates.max() if not archive.empty else pd.Timestamp(2026, 1, 31)

    first_month = (last_archive_date + pd.offsets.MonthBegin(1)).normalize()
    current_month = pd.Timestamp(today.year, today.month, 1)
    months = []
    cursor = first_month
    while cursor <= current_month:
        months.append((cursor.year, cursor.month))
        cursor += pd.offsets.MonthBegin(1)

    fresh_rows = []
    with ThreadPoolExecutor(max_workers=min(4, max(1, len(months)))) as executor:
        futures = {
            executor.submit(
                fetch_historical_data,
                year,
                month,
                20,
                COMMODITY_ID,
            ): (year, month)
            for year, month in months
        }
        for future in as_completed(futures):
            year, month = futures[future]
            try:
                payload = future.result()
            except RuntimeError as error:
                print(f"{year}-{month:02d}: unavailable ({error})")
                continue
            rows = flatten_records(payload, "Maharashtra", COMMODITY)
            fresh_rows.extend(rows)
            print(f"{year}-{month:02d}: {len(rows)} rows")

    # The official monthly endpoint may require CAPTCHA. Fall back to a
    # separate AGMARKNET-derived API for recent dated records, preserving the archive.
    if not fresh_rows:
        print("Official monthly endpoint returned no rows; trying recent-record fallback...")
        try:
            fresh_rows = fetch_latest_fallback("Maharashtra", COMMODITY)
            print(f"Fallback source returned {len(fresh_rows)} matching rows.")
        except (requests.RequestException, ValueError, RuntimeError) as error:
            raise RuntimeError(
                "Official AGMARKNET monthly refresh was blocked and the recent-record "
                f"fallback failed ({type(error).__name__}: {error}). Existing data was preserved."
            ) from error

    # Do not report a successful refresh unless a source returned observations.
    if not fresh_rows:
        raise RuntimeError(
            "Both the official monthly endpoint and recent-record fallback returned "
            "zero usable rows. The existing latest-data file was not overwritten."
        )

    fresh = pd.DataFrame(fresh_rows)
    df = pd.concat([archive, fresh], ignore_index=True)

    # Parse ISO dates strictly; parse slash-formatted API dates as day-first.
    raw_dates = df["arrival_date"].astype(str).str.strip()
    iso_mask = raw_dates.str.match(r"^\d{4}-\d{2}-\d{2}")
    parsed_dates = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    parsed_dates.loc[iso_mask] = pd.to_datetime(raw_dates.loc[iso_mask], format="%Y-%m-%d", errors="coerce")
    parsed_dates.loc[~iso_mask] = pd.to_datetime(raw_dates.loc[~iso_mask], dayfirst=True, errors="coerce")
    df["arrival_date"] = parsed_dates.dt.normalize()

    # Never persist future-dated rows as actual market observations.
    today_date = pd.Timestamp(datetime.now().date())
    future_count = int((df["arrival_date"] > today_date).sum())
    if future_count:
        print(f"Discarding {future_count} future-dated rows beyond {today_date.date()}.")
    df = df[df["arrival_date"].notna() & (df["arrival_date"] <= today_date)].copy()

    df = df.sort_values(
        ["arrival_date", "market", "variety"]
    ).drop_duplicates(
        subset=["market", "commodity", "arrival_date", "variety"],
        keep="last",
    ).reset_index(drop=True)

    output_dir = Path("data/historical")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = Path(HISTORICAL_FILE)

    df.to_csv(output_file, index=False)

    print("\nHistorical ingestion complete.")
    print("Rows:", len(df))
    print("Markets:", df["market"].nunique())
    print("Dates:", df["arrival_date"].nunique())
    print("Varieties:", df["variety"].nunique())
    print(
        "Date range:",
        df["arrival_date"].min().date(),
        "to",
        df["arrival_date"].max().date(),
    )
    print("Saved to:", output_file)


if __name__ == "__main__":
    main()
