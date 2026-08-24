import os
import time
from pathlib import Path

import pandas as pd
import requests


RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

HEADERS = {
    "User-Agent": "curl/8.7.1",
    "Accept": "application/json",
    "Connection": "close",
}


def load_api_key():
    api_key = os.getenv("DATA_GOV_API_KEY")

    if not api_key:
        raise ValueError(
            "DATA_GOV_API_KEY is not set. "
            "Load it from the .env file before running the script."
        )

    return api_key


def fetch_page(api_key, limit, offset, max_retries=3):
    params = {
        "api-key": api_key,
        "format": "json",
        "limit": limit,
        "offset": offset,
    }

    for attempt in range(1, max_retries + 1):
        try:
            print(
                f"Fetching offset={offset}, "
                f"attempt {attempt}/{max_retries}..."
            )

            response = requests.get(
                BASE_URL,
                params=params,
                headers=HEADERS,
                timeout=(5, 30),
            )

            response.raise_for_status()

            data = response.json()

            if data.get("status") != "ok":
                raise RuntimeError("API returned an unexpected response.")

            return data

        except (requests.RequestException, ValueError) as error:
            print(f"Attempt failed: {type(error).__name__}")

            if attempt == max_retries:
                raise RuntimeError(
                    f"API request failed at offset {offset}."
                ) from error

            wait_seconds = 2 ** attempt
            print(f"Waiting {wait_seconds} seconds before retry...")
            time.sleep(wait_seconds)


def fetch_mandi_data(batch_size=100, max_records=500):
    api_key = load_api_key()

    all_records = []
    offset = 0
    total_available = None

    while len(all_records) < max_records:
        remaining = max_records - len(all_records)
        current_limit = min(batch_size, remaining)

        data = fetch_page(
            api_key=api_key,
            limit=current_limit,
            offset=offset,
        )

        records = data.get("records", [])

        if total_available is None:
            total_available = data.get("total")
            print(f"Total records currently available: {total_available}")

        if not records:
            break

        all_records.extend(records)

        print(f"Records collected so far: {len(all_records)}")

        offset += len(records)

        if len(records) < current_limit:
            break

    return all_records, total_available


def save_raw_data(records):
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "mandi_prices_raw.csv"

    df = pd.DataFrame(records)
    df.to_csv(output_file, index=False)

    return output_file, len(df)


def main():
    records, total_available = fetch_mandi_data(
        batch_size=100,
        max_records=500,
    )

    output_file, row_count = save_raw_data(records)

    print("\nIngestion complete.")
    print(f"Total records available: {total_available}")
    print(f"Records fetched: {row_count}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()
