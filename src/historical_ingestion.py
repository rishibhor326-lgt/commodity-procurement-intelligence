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
    "User-Agent": "Mozilla/5.0",
}


def fetch_historical_data(year, month, state_id, commodity_id, max_retries=1):
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

            response.raise_for_status()
            payload = response.json()

            if not payload.get("success"):
                raise RuntimeError(
                    payload.get("message", "Historical API request failed.")
                )

            return payload

        except (requests.RequestException, ValueError, RuntimeError) as error:
            if attempt == max_retries:
                raise RuntimeError(
                    f"Failed to fetch {year}-{month:02d}"
                ) from error

            wait_seconds = 2 ** attempt
            print(f"Retrying in {wait_seconds} seconds...")
            time.sleep(wait_seconds)


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
    archive_dates = pd.to_datetime(archive.get("arrival_date"), errors="coerce")
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

    fresh = pd.DataFrame(fresh_rows)
    df = pd.concat([archive, fresh], ignore_index=True)

    df["arrival_date"] = pd.to_datetime(
        df["arrival_date"],
        format="%d/%m/%Y",
        errors="coerce",
    )

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
