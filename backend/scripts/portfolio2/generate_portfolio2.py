import sys
from pathlib import Path
from typing import Dict, List
import argparse

import pandas as pd

# ============================
# Strategy configuration
# ============================
# This strategy triggers trades when ANY of RSI-6, RSI-12, or RSI-24 signals.

ASSET_SECTORS: Dict[str, str] = {
    "MRKV": "Electric Power",
    "KRSB": "Electric Power",
    "T": "Finance",
}

# RSI thresholds (use 20/80 instead of default 30/70)
RSI_OVERSOLD: float = 30.0
RSI_OVERBOUGHT: float = 70.0

# Each asset has its own starting capital; total portfolio = len(ASSET_SECTORS) * INITIAL_CAPITAL_PER_ASSET
INITIAL_CAPITAL_PER_ASSET: float = 1_000_000.0
BUY_PCT: float = 0.2   # default buy percent of remaining cash for the symbol
SELL_PCT: float = 0.01  # default sell percent of current position


# Paths (this file lives in backend/scripts/portfolio2, so use backend root)
ROOT_DIR = Path(__file__).resolve().parents[2]
# Ensure project root is on sys.path for module imports
root_str = str(ROOT_DIR)
if root_str not in sys.path:
    sys.path.insert(0, root_str)
DATA_DIR = ROOT_DIR / "data" / "csv_backup"
PRICE_CSV = DATA_DIR / "price_data.csv"
TI_CSV = DATA_DIR / "technical_indicators.csv"
OUTPUT_CSV = DATA_DIR / "portfolio2" / "portfolio2.csv"


def load_joined_price_and_signals() -> pd.DataFrame:
    """Load price data and RSI-6/12/24 values (and signals if available), merged on (symbol, date)."""
    # Read prices
    price_usecols = ["symbol", "date", "close_price"]
    try:
        price_df = pd.read_csv(PRICE_CSV, usecols=price_usecols)
    except ValueError:
        price_df = pd.read_csv(PRICE_CSV)
    # Read indicators
    ti_usecols = [
        "symbol",
        "date",
        "rsi_6",
        "rsi_6_signal",
        "rsi_12",
        "rsi_12_signal",
        "rsi_24",
        "rsi_24_signal",
    ]
    try:
        ti_df = pd.read_csv(TI_CSV, usecols=ti_usecols)
    except ValueError:
        ti_df = pd.read_csv(TI_CSV)

    # Normalize types
    price_df["date"] = pd.to_datetime(price_df["date"], errors="coerce")
    ti_df["date"] = pd.to_datetime(ti_df["date"], errors="coerce")

    # Merge inner to ensure we have prices where we have signals
    merged = pd.merge(
        price_df,
        ti_df,
        how="inner",
        on=["symbol", "date"],
        validate="m:1",
    )
    return merged


def rsi_to_signal(rsi_value: float) -> str:
    try:
        v = float(rsi_value)
    except Exception:
        return "hold"
    if pd.isna(v):
        return "hold"
    if v <= RSI_OVERSOLD:
        return "buy"
    if v >= RSI_OVERBOUGHT:
        return "sell"
    return "hold"


def combine_signals(row: pd.Series) -> str:
    """Return combined trade signal when ANY RSI-6/12/24 indicates action using 20/80 thresholds.

    Priority on conflict:
    - If any is 'sell' -> 'sell'
    - Else if any is 'buy' -> 'buy'
    - Else -> 'hold'
    """
    s6 = rsi_to_signal(row.get("rsi_6"))
    s12 = rsi_to_signal(row.get("rsi_12"))
    s24 = rsi_to_signal(row.get("rsi_24"))
    if "sell" in (s6, s12, s24):
        return "sell"
    if "buy" in (s6, s12, s24):
        return "buy"
    return "hold"


def main() -> int:
    # CLI overrides for buy/sell percentages
    parser = argparse.ArgumentParser(description="Generate portfolio2.csv using RSI-6/12/24 any-signal strategy (20/80 thresholds)")
    parser.add_argument("--buy-pct", type=float, default=BUY_PCT, help="Buy percentage of remaining cash per trade (0-1)")
    parser.add_argument("--sell-pct", type=float, default=SELL_PCT, help="Sell percentage of current position per trade (0-1)")
    args = parser.parse_args()

    buy_pct = max(0.0, min(1.0, args.buy_pct))
    sell_pct = max(0.0, min(1.0, args.sell_pct))

    # Validate inputs
    if not PRICE_CSV.exists():
        print(f"price_data.csv not found at: {PRICE_CSV}")
        return 1
    if not TI_CSV.exists():
        print(f"technical_indicators.csv not found at: {TI_CSV}")
        return 1

    symbols = list(ASSET_SECTORS.keys())

    merged = load_joined_price_and_signals()
    missing_cols = {"symbol", "date", "close_price", "rsi_6", "rsi_12", "rsi_24"} - set(merged.columns)
    if missing_cols:
        print(f"Missing required columns after merge: {missing_cols}")
        return 1

    # Filter to target symbols and clean
    df = merged[merged["symbol"].isin(symbols)].copy()
    if df.empty:
        # Write empty portfolio file with headers
        cols = [
            "date",
            "symbol",
            "sector",
            "action",
            "price",
            "shares",
            "notional",
            "position_shares_after",
            "position_value_after",
            "cash_after",
            "total_equity_after",
            "rsi_6",
            "rsi_6_signal",
            "rsi_12",
            "rsi_12_signal",
            "rsi_24",
            "rsi_24_signal",
        ]
        pd.DataFrame(columns=cols).to_csv(OUTPUT_CSV, index=False)
        print("No rows found for target symbols in merged data. Created portfolio2.csv with headers only.")
        return 0

    df = df.dropna(subset=["date", "close_price"]).sort_values(["date", "symbol"])  # across symbols by date

    # Portfolio state (per-asset capital)
    cash_per_symbol: Dict[str, float] = {sym: INITIAL_CAPITAL_PER_ASSET for sym in symbols}
    position_shares: Dict[str, float] = {sym: 0.0 for sym in symbols}

    trade_rows: List[Dict] = []

    # Seed initial positions: invest half of initial capital into each asset at its first available price
    first_rows = (
        df.sort_values(["symbol", "date"]).groupby("symbol", as_index=False).first()
    )
    for _, fr in first_rows.iterrows():
        symbol = fr["symbol"]
        if symbol not in ASSET_SECTORS:
            continue
        first_price = float(fr["close_price"])
        invest_amount = 0.5 * INITIAL_CAPITAL_PER_ASSET
        initial_shares = invest_amount / first_price if first_price > 0 else 0.0
        position_shares[symbol] = initial_shares
        cash_per_symbol[symbol] = INITIAL_CAPITAL_PER_ASSET - invest_amount

        position_value = position_shares[symbol] * first_price
        total_equity_after = cash_per_symbol[symbol] + position_value

        trade_rows.append({
            "date": pd.to_datetime(fr["date"]).date(),
            "symbol": symbol,
            "sector": ASSET_SECTORS.get(symbol, ""),
            "action": "init",
            "price": first_price,
            "shares": initial_shares,
            "notional": invest_amount,
            "position_shares_after": position_shares[symbol],
            "position_value_after": position_value,
            "cash_after": cash_per_symbol[symbol],
            "total_equity_after": total_equity_after,
            "rsi_6": fr.get("rsi_6"),
            "rsi_6_signal": rsi_to_signal(fr.get("rsi_6")),
            "rsi_12": fr.get("rsi_12"),
            "rsi_12_signal": rsi_to_signal(fr.get("rsi_12")),
            "rsi_24": fr.get("rsi_24"),
            "rsi_24_signal": rsi_to_signal(fr.get("rsi_24")),
        })

    # Iterate rows and act on combined signals
    for _, row in df.iterrows():
        symbol = row["symbol"]
        if symbol not in ASSET_SECTORS:
            continue
        price = float(row["close_price"])
        date = pd.to_datetime(row["date"]).date()

        combined = combine_signals(row)

        if combined == "buy":
            # Buy fraction of remaining cash for this symbol (no leverage)
            target_amount = buy_pct * cash_per_symbol[symbol]
            amount = min(target_amount, cash_per_symbol[symbol])
            if amount > 0:
                shares = amount / price
                position_shares[symbol] += shares
                cash_per_symbol[symbol] -= amount

                position_value = position_shares[symbol] * price
                total_equity_after = cash_per_symbol[symbol] + position_value

                trade_rows.append({
                    "date": date,
                    "symbol": symbol,
                    "sector": ASSET_SECTORS.get(symbol, ""),
                    "action": "buy",
                    "price": price,
                    "shares": shares,
                    "notional": amount,
                    "position_shares_after": position_shares[symbol],
                    "position_value_after": position_value,
                    "cash_after": cash_per_symbol[symbol],
                    "total_equity_after": total_equity_after,
                    "rsi_6": row.get("rsi_6"),
                    "rsi_6_signal": rsi_to_signal(row.get("rsi_6")),
                    "rsi_12": row.get("rsi_12"),
                    "rsi_12_signal": rsi_to_signal(row.get("rsi_12")),
                    "rsi_24": row.get("rsi_24"),
                    "rsi_24_signal": rsi_to_signal(row.get("rsi_24")),
                })

        elif combined == "sell":
            # Sell fraction of current position
            shares_to_sell = sell_pct * position_shares[symbol]
            if shares_to_sell > 0:
                proceeds = shares_to_sell * price
                position_shares[symbol] -= shares_to_sell
                cash_per_symbol[symbol] += proceeds

                position_value = position_shares[symbol] * price
                total_equity_after = cash_per_symbol[symbol] + position_value

                trade_rows.append({
                    "date": date,
                    "symbol": symbol,
                    "sector": ASSET_SECTORS.get(symbol, ""),
                    "action": "sell",
                    "price": price,
                    "shares": shares_to_sell,
                    "notional": proceeds,
                    "position_shares_after": position_shares[symbol],
                    "position_value_after": position_value,
                    "cash_after": cash_per_symbol[symbol],
                    "total_equity_after": total_equity_after,
                    "rsi_6": row.get("rsi_6"),
                    "rsi_6_signal": rsi_to_signal(row.get("rsi_6")),
                    "rsi_12": row.get("rsi_12"),
                    "rsi_12_signal": rsi_to_signal(row.get("rsi_12")),
                    "rsi_24": row.get("rsi_24"),
                    "rsi_24_signal": rsi_to_signal(row.get("rsi_24")),
                })

    trades_df = pd.DataFrame(trade_rows)
    if not trades_df.empty:
        # Ensure column order (superset accepted by downstream)
        ordered_cols = [
            "date",
            "symbol",
            "sector",
            "action",
            "price",
            "shares",
            "notional",
            "position_shares_after",
            "position_value_after",
            "cash_after",
            "total_equity_after",
            "rsi_6",
            "rsi_6_signal",
            "rsi_12",
            "rsi_12_signal",
            "rsi_24",
            "rsi_24_signal",
        ]
        trades_df = trades_df[[c for c in ordered_cols if c in trades_df.columns]]

        # For non-init trades, convert shares to integers; keep 'init' fractional shares as-is
        if "shares" in trades_df.columns:
            non_init_mask = trades_df.get("action").ne("init") if "action" in trades_df.columns else True
            trades_df.loc[non_init_mask, "shares"] = trades_df.loc[non_init_mask, "shares"].round().astype(int)
        # Round selected numeric fields to two decimals
        round_cols = [
            "notional",
            "position_shares_after",
            "position_value_after",
            "cash_after",
            "total_equity_after",
            "rsi_6",
            "rsi_12",
            "rsi_24",
        ]
        for col in round_cols:
            if col in trades_df.columns:
                trades_df[col] = trades_df[col].round(2)

    # Write output
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    trades_df.to_csv(OUTPUT_CSV, index=False)

    # Print brief summary
    print(f"Saved trade history to: {OUTPUT_CSV}")
    if trades_df.empty:
        print("No trades generated (no confirmed RSI-12/24 buy/sell signals or missing symbol data).")
    else:
        by_symbol = trades_df.groupby("symbol")["action"].value_counts().unstack(fill_value=0)
        print(by_symbol)

    return 0


if __name__ == "__main__":
    sys.exit(main())



