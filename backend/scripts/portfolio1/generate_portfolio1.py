import sys
from pathlib import Path
from typing import Dict, List
import argparse

import pandas as pd

# ============================
# Strategy configuration
# ============================
RSI_PERIOD_INPUT: int = 6

ASSET_SECTORS: Dict[str, str] = {
    "SBER": "Finance",
    "RTGZ": "Rosneft Oil Company",
    "OZON": "Information technology",
}

# Each asset has its own starting capital; total portfolio = len(ASSET_SECTORS) * INITIAL_CAPITAL_PER_ASSET
INITIAL_CAPITAL_PER_ASSET: float = 1_000_000.0
BUY_PCT: float = 0.2   # default buy percent of remaining cash for the symbol
SELL_PCT: float = 0.01  # default sell percent of current position


# Paths
# This file lives in backend/scripts/portfolio1, so ROOT_DIR should be the backend directory
ROOT_DIR = Path(__file__).resolve().parents[2]
# Ensure project root is on sys.path for module imports (e.g., indicators)
root_str = str(ROOT_DIR)
if root_str not in sys.path:
    sys.path.insert(0, root_str)
DATA_DIR = ROOT_DIR / "data" / "csv_backup"
PRICE_CSV = DATA_DIR / "price_data.csv"
OUTPUT_CSV = DATA_DIR / "portfolio1" / "portfolio1.csv"


def compute_rsi_signals_for_symbol(symbol_df: pd.DataFrame, rsi_period: int) -> pd.DataFrame:
    """Append RSI and RSI signal columns for a single symbol dataframe."""
    from indicators.technical_indicators import TechnicalIndicators

    ti = TechnicalIndicators()
    closes: List[float] = symbol_df["close_price"].astype(float).tolist()
    rsi_values = ti.calculate_rsi(closes, period=rsi_period)
    signals = ti.get_rsi_signals(rsi_values)

    out = symbol_df.copy()
    out["rsi"] = rsi_values
    out["rsi_signal"] = signals
    return out


def main() -> int:
    # CLI overrides for buy/sell percentages and RSI period
    parser = argparse.ArgumentParser(description="Generate portfolio1.csv using RSI strategy")
    parser.add_argument("--buy-pct", type=float, default=BUY_PCT, help="Buy percentage of remaining cash per trade (0-1)")
    parser.add_argument("--sell-pct", type=float, default=SELL_PCT, help="Sell percentage of current position per trade (0-1)")
    parser.add_argument("--rsi-period", type=int, default=RSI_PERIOD_INPUT, help="RSI period to use")
    args = parser.parse_args()

    buy_pct = max(0.0, min(1.0, args.buy_pct))
    sell_pct = max(0.0, min(1.0, args.sell_pct))
    rsi_period = args.rsi_period
    if not PRICE_CSV.exists():
        print(f"price_data.csv not found at: {PRICE_CSV}")
        return 1

    symbols = list(ASSET_SECTORS.keys())

    # Read minimal columns
    usecols = [
        "symbol",
        "date",
        "close_price",
    ]
    try:
        df = pd.read_csv(PRICE_CSV, usecols=usecols)
    except ValueError:
        df = pd.read_csv(PRICE_CSV)

    missing_cols = {"symbol", "date", "close_price"} - set(df.columns)
    if missing_cols:
        print(f"Missing required columns in price_data.csv: {missing_cols}")
        return 1

    # Filter to target symbols and clean
    df = df[df["symbol"].isin(symbols)].copy()
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
            "rsi",
            "rsi_signal",
        ]
        pd.DataFrame(columns=cols).to_csv(OUTPUT_CSV, index=False)
        print("No rows found for SBER/PLZL/OZON in price_data.csv. Created portfolio1.csv with headers only.")
        return 0

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "close_price"]).sort_values(["symbol", "date"])  # by symbol then date

    # Compute RSI and signals per symbol
    enriched_frames: List[pd.DataFrame] = []
    for sym in symbols:
        sdf = df[df["symbol"] == sym]
        if sdf.empty:
            continue
        enriched_frames.append(compute_rsi_signals_for_symbol(sdf, rsi_period))

    if not enriched_frames:
        pd.DataFrame(columns=[
            "date","symbol","sector","action","price","shares","notional",
            "position_shares_after","position_value_after","cash_after","total_equity_after","rsi","rsi_signal"
        ]).to_csv(OUTPUT_CSV, index=False)
        print("No data points with valid prices for target symbols. Created portfolio1.csv with headers only.")
        return 0

    all_data = pd.concat(enriched_frames, ignore_index=True)

    # Build event stream across all symbols by date
    all_data = all_data.sort_values(["date", "symbol"])  # stable order

    # Portfolio state (per-asset capital)
    cash_per_symbol: Dict[str, float] = {sym: INITIAL_CAPITAL_PER_ASSET for sym in symbols}
    position_shares: Dict[str, float] = {sym: 0.0 for sym in symbols}

    trade_rows: List[Dict] = []

    # Iterate rows and act on RSI signals
    for _, row in all_data.iterrows():
        symbol = row["symbol"]
        price = float(row["close_price"])
        rsi = row.get("rsi")
        signal = row.get("rsi_signal")
        date = row["date"].date()

        # Current cash and position value for this symbol
        position_value_before = position_shares[symbol] * price

        if signal == "buy":
            # Buy 5% of remaining cash for this symbol (no leverage)
            target_amount = buy_pct * cash_per_symbol[symbol]
            amount = min(target_amount, cash_per_symbol[symbol])
            if amount > 0:
                shares = amount / price
                position_shares[symbol] += shares
                cash_per_symbol[symbol] -= amount

                # Recompute equity components
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
                    "rsi": rsi,
                    "rsi_signal": signal,
                })

        elif signal == "sell":
            # Sell 50% of current position
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
                    "rsi": rsi,
                    "rsi_signal": signal,
                })

    trades_df = pd.DataFrame(trade_rows)
    if not trades_df.empty:
        # Ensure column order
        trades_df = trades_df[[
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
            "rsi",
            "rsi_signal",
        ]]

    # Round output columns per requirements before writing
    if not trades_df.empty:
        # Shares as whole numbers
        if "shares" in trades_df.columns:
            trades_df["shares"] = trades_df["shares"].round().astype(int)
        # Round selected numeric fields to two decimals
        round_cols = [
            "notional",
            "position_shares_after",
            "position_value_after",
            "cash_after",
            "total_equity_after",
            "rsi",
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
        print("No trades generated (no RSI buy/sell signals or missing symbol data).")
    else:
        by_symbol = trades_df.groupby("symbol")["action"].value_counts().unstack(fill_value=0)
        print(by_symbol)

    return 0


if __name__ == "__main__":
    sys.exit(main())


