from pathlib import Path
import time

import pandas as pd
import requests


URL = "https://api.agmarknet.gov.in/v1/prices-and-arrivals/date-wise/specific-commodity"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://agmarknet.gov.in",
    "Referer": "https://agmarknet.gov.in/",
    "User-Agent": "Mozilla/5.0",
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
                timeout=(10, 60),
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
    months = [
        (2026, 2),
        (2026, 3),
        (2026, 4),
        (2026, 5),
        (2026, 6),
        (2026, 7),
    ]

    all_rows = []

    for year, month in months:
        payload = fetch_historical_data(
            year=year,
            month=month,
            state_id=20,
            commodity_id=23,
        )

        rows = flatten_records(
            payload,
            state_name="Maharashtra",
            commodity_name="Onion",
        )

        all_rows.extend(rows)

        print(
            f"{year}-{month:02d}: "
            f"{len(rows)} rows | "
            f"Total collected: {len(all_rows)}"
        )

    df = pd.DataFrame(all_rows)

    df["arrival_date"] = pd.to_datetime(
        df["arrival_date"],
        format="%d/%m/%Y",
        errors="coerce",
    )

    df = df.sort_values(
        ["arrival_date", "market", "variety"]
    ).reset_index(drop=True)

    output_dir = Path("data/historical")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = (
        output_dir /
        "maharashtra_onion_2026_02_to_07.csv"
    )

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
