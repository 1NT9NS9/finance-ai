import sys
from pathlib import Path
from typing import List

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "csv_backup"
PRICE_CSV = DATA_DIR / "price_data.csv"
OUTPUT_CSV = DATA_DIR / "index.csv"

TARGET_SYMBOLS: List[str] = ["XAUT-USD", "IMOEX"]


def build_index_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Filter and project price data to index.csv structure.

    Output columns: symbol, name, currency, date, close price
    Only for symbols in TARGET_SYMBOLS.
    """
    df_copy = df.copy()
    # Filter for target symbols
    df_copy = df_copy[df_copy["symbol"].isin(TARGET_SYMBOLS)]

    if df_copy.empty:
        return pd.DataFrame(columns=[
            "symbol",
            "name",
            "currency",
            "date",
            "close price",
        ])

    # Ensure proper ordering by symbol then date
    # Keep date as string in CSV output but sort using datetime for correctness
    df_copy["_date_dt"] = pd.to_datetime(df_copy["date"], errors="coerce")
    df_copy = df_copy.dropna(subset=["_date_dt"]).sort_values(["symbol", "_date_dt"]).drop(columns=["_date_dt"])  # noqa: E501

    # Select and rename columns to required headers
    df_out = df_copy[["symbol", "name", "currency", "date", "close_price"]].rename(columns={
        "close_price": "close price",
    })

    # Reset index for clean CSV output
    return df_out.reset_index(drop=True)


def main() -> int:
    if not PRICE_CSV.exists():
        print(f"Price data not found: {PRICE_CSV}")
        return 1

    # Read minimal necessary columns for performance
    usecols = [
        "symbol",
        "name",
        "currency",
        "date",
        "close_price",
    ]
    try:
        df = pd.read_csv(PRICE_CSV, usecols=usecols)
    except ValueError:
        # Fallback if some columns missing
        df = pd.read_csv(PRICE_CSV)

    required_cols = {"symbol", "name", "currency", "date", "close_price"}
    if not required_cols.issubset(df.columns):
        print("CSV must contain columns: symbol, name, currency, date, close_price")
        return 1

    index_df = build_index_dataframe(df)

    # Ensure output directory exists
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    index_df.to_csv(OUTPUT_CSV, index=False)

    if index_df.empty:
        print("No data for requested symbols (XAUT-USD, IMOEX). index.csv written with headers only.")
        return 0

    # Print a brief confirmation with counts
    counts = index_df["symbol"].value_counts().to_dict()
    print("Saved index.csv with rows per symbol:")
    for sym in TARGET_SYMBOLS:
        print(f"  {sym}: {counts.get(sym, 0)}")
    print(f"Saved results to: {OUTPUT_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


