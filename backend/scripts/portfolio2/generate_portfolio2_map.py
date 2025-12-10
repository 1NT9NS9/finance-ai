import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

# Use non-interactive backend for servers/CI
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ============================
# Transaction costs
# ============================
# Commission applied to both buy and sell notional (fraction). Example: 0.0001 = 0.01%
COMMISSION_RATE: float = 0.0001


# Paths and IO setup
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data" / "csv_backup"
CHARTS_DIR = ROOT_DIR / "charts" / "portfolio2"
INPUT_PORTFOLIO_CSV = DATA_DIR / "portfolio2" / "portfolio2.csv"
OUTPUT_MAP_CSV = DATA_DIR / "portfolio2" / "portfolio2_map.csv"
OUTPUT_SUMMARY_CSV = DATA_DIR / "portfolio2" / "portfolio2_summary.csv"
OUTPUT_RATE_PLOT_CSV = DATA_DIR / "portfolio2" / "portfolio2_map_rate_plot.csv"
# Last trades per asset (one row per symbol)
OUTPUT_LAST_WEEK_CSV = DATA_DIR / "portfolio2" / "portfolio2_map_last.csv"


def compute_trade_map_and_summary(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    required_cols = [
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
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in portfolio2.csv: {missing}")

    # Normalize types
    work = df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work = work.dropna(subset=["date"])  # filter bad dates
    # Ensure numeric
    for c in ["price", "shares", "notional", "position_shares_after", "position_value_after", "cash_after", "total_equity_after"]:
        work[c] = pd.to_numeric(work[c], errors="coerce")
    work = work.dropna(subset=["price", "shares"]).sort_values(["symbol", "date"]).reset_index(drop=True)

    symbols: List[str] = sorted(work["symbol"].unique().tolist())

    map_rows: List[Dict] = []
    summary_rows: List[Dict] = []

    for symbol in symbols:
        sdf = work[work["symbol"] == symbol].copy()
        sdf = sdf.sort_values("date").reset_index(drop=True)
        sector = sdf["sector"].iloc[0] if "sector" in sdf.columns and not sdf["sector"].isna().all() else ""

        avg_cost_per_share: float = 0.0
        position_shares: float = 0.0
        realized_pnl_total: float = 0.0

        total_buy_notional: float = 0.0
        total_sell_proceeds: float = 0.0
        total_buys: int = 0
        total_sells: int = 0

        for _, r in sdf.iterrows():
            date = r["date"]
            action = str(r["action"]).lower()
            price = float(r["price"])
            sh = float(r["shares"])  # shares bought or sold in this trade

            realized_pnl = 0.0
            if action == "buy":
                trade_cost = sh * price
                commission = trade_cost * COMMISSION_RATE
                effective_cost = trade_cost + commission
                # Update average cost (weighted) including commission on buys
                total_cost_before = avg_cost_per_share * position_shares
                total_cost_after = total_cost_before + effective_cost
                position_shares += sh
                avg_cost_per_share = total_cost_after / position_shares if position_shares > 0 else 0.0

                total_buy_notional += trade_cost
                total_buys += 1

            elif action == "sell":
                shares_to_sell = min(sh, position_shares) if position_shares > 0 else 0.0
                if shares_to_sell > 0:
                    proceeds_gross = shares_to_sell * price
                    commission = proceeds_gross * COMMISSION_RATE
                    proceeds_net = proceeds_gross - commission
                    cost_basis = shares_to_sell * avg_cost_per_share
                    realized_pnl = proceeds_net - cost_basis
                    realized_pnl_total += realized_pnl
                    position_shares -= shares_to_sell
                    # avg_cost_per_share remains unchanged for remaining shares
                    total_sell_proceeds += proceeds_gross
                    total_sells += 1
                else:
                    # No shares to sell; realized PnL remains 0
                    realized_pnl = 0.0
            else:
                # Non-trade row; skip mapping
                pass

            equity_after = float(r.get("total_equity_after", r.get("cash_after", 0.0)))

            map_rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "sector": sector,
                    "action": action,
                    "price": price,
                    # Write integer number of shares in the CSV output
                    "shares": int(round(sh)),
                    "notional": float(r["notional"]),
                    "realized_pnl": realized_pnl,
                    "cumulative_realized_pnl": realized_pnl_total,
                    "avg_cost_per_share": avg_cost_per_share,
                    "position_shares_after": float(r["position_shares_after"]),
                    "position_value_after": float(r["position_value_after"]),
                    "cash_after": float(r["cash_after"]),
                    "equity_after": equity_after,
                }
            )

        # At end of symbol's activity, compute unrealized PnL using last trade price
        last_trade_price = float(sdf["price"].iloc[-1]) if not sdf.empty else 0.0
        unrealized_pnl = position_shares * (last_trade_price - avg_cost_per_share)
        total_pnl = realized_pnl_total + unrealized_pnl

        # Ending free capital + position at current price
        ending_cash = float(sdf["cash_after"].iloc[-1]) if not sdf.empty else 0.0
        ending_cash_plus_position_value = ending_cash + position_shares * last_trade_price

        summary_rows.append(
            {
                "symbol": symbol,
                "sector": sector,
                "total_buys": total_buys,
                "total_sells": total_sells,
                "ending_cash_plus_position_value": ending_cash_plus_position_value,
                "total_buy_notional": total_buy_notional,
                "total_sell_proceeds": total_sell_proceeds,
                "realized_pnl": realized_pnl_total,
                "unrealized_pnl": unrealized_pnl,
                "total_pnl": total_pnl,
                "ending_shares": position_shares,
                "ending_avg_cost": avg_cost_per_share,
                "last_price": last_trade_price,
            }
        )

    map_df = pd.DataFrame(map_rows).sort_values(["symbol", "date"]).reset_index(drop=True)
    # Round selected numeric columns to two decimals for output
    round_cols = [
        "notional",
        "realized_pnl",
        "cumulative_realized_pnl",
        "avg_cost_per_share",
        "position_value_after",
        "cash_after",
        "equity_after",
    ]
    for col in round_cols:
        if col in map_df.columns:
            map_df[col] = map_df[col].round(2)
    # position_shares_after as whole numbers
    if "position_shares_after" in map_df.columns:
        map_df["position_shares_after"] = map_df["position_shares_after"].round().astype(int)
    summary_df = pd.DataFrame(summary_rows).sort_values(["symbol"]).reset_index(drop=True)
    # Round summary numeric columns to two decimals for output
    summary_round_cols = [
        "ending_cash_plus_position_value",
        "total_buy_notional",
        "total_sell_proceeds",
        "realized_pnl",
        "unrealized_pnl",
        "total_pnl",
        "ending_shares",
        "ending_avg_cost",
    ]
    for col in summary_round_cols:
        if col in summary_df.columns:
            summary_df[col] = summary_df[col].round(2)
    return map_df, summary_df


def compute_daily_average_capital(map_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a daily time series under the assumption that each symbol starts with
    its own independent initial capital (1,000,000). Trades for each symbol are
    applied to that symbol's cash/shares only. Daily capital per symbol is:
    cash_t + shares_t * price_t (price_t is last known trade price, ffilled).
    The output contains equal-weight average across symbols and the total sum.
    """
    INITIAL_PER_SYMBOL_CAPITAL: float = 1_000_000.0

    work = map_df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work = work.dropna(subset=["date"]).sort_values(["symbol", "date"]).reset_index(drop=True)
    work["day"] = work["date"].dt.normalize()

    if work.empty:
        return pd.DataFrame(columns=["date", "avg_symbol_capital", "total_capital"])  # nothing to compute

    symbols: List[str] = sorted(work["symbol"].unique().tolist())
    start_day = work["day"].min()
    end_day = work["day"].max()
    full_days = pd.date_range(start=start_day, end=end_day, freq="D")

    # Prepare per-symbol daily last trade price
    price_last_per_day = (
        work.groupby(["symbol", "day"], as_index=False)
        .agg(last_price=("price", "last"))
    )

    # Map of symbol -> Series of daily price (ffilled)
    symbol_to_price_series: Dict[str, pd.Series] = {}
    for symbol in symbols:
        s = price_last_per_day[price_last_per_day["symbol"] == symbol]
        if s.empty:
            # No trades at all (unlikely) -> keep all NaN prices
            price_series = pd.Series(index=full_days, dtype=float)
        else:
            p = s.set_index("day")["last_price"].sort_index()
            price_series = p.reindex(full_days).ffill()
        symbol_to_price_series[symbol] = price_series

    # Build per-symbol daily capital via simulating cash/shares with commissions
    capitals = []  # list of DataFrames per symbol with one column named by symbol
    for symbol in symbols:
        sdf = work[work["symbol"] == symbol].copy()
        sdf = sdf.sort_values("day")

        # Trades grouped per day to process in order (keep intraday order by original index)
        trades_by_day = {d: g.sort_index() for d, g in sdf.groupby("day")}
        daily_prices = symbol_to_price_series[symbol]

        cash = INITIAL_PER_SYMBOL_CAPITAL
        shares = 0.0
        series_vals: List[float] = []
        for day in full_days:
            # Apply all trades for this day
            day_trades = trades_by_day.get(day)
            if day_trades is not None and not day_trades.empty:
                for _, r in day_trades.iterrows():
                    action = str(r["action"]).lower()
                    trade_price = float(r["price"])
                    trade_shares = float(r["shares"])  # already quantity traded
                    if action == "buy":
                        trade_cost = trade_shares * trade_price
                        commission = trade_cost * COMMISSION_RATE
                        cash -= (trade_cost + commission)
                        shares += trade_shares
                    elif action == "sell":
                        shares_to_sell = min(trade_shares, shares) if shares > 0 else 0.0
                        if shares_to_sell > 0:
                            proceeds_gross = shares_to_sell * trade_price
                            commission = proceeds_gross * COMMISSION_RATE
                            proceeds_net = proceeds_gross - commission
                            cash += proceeds_net
                            shares -= shares_to_sell
                    # ignore any other actions

            price_t = daily_prices.loc[day] if day in daily_prices.index else float("nan")
            position_value = (shares * price_t) if pd.notna(price_t) else 0.0
            capital = cash + position_value
            series_vals.append(capital)

        capitals.append(pd.Series(series_vals, index=full_days, name=symbol))

    # Combine per-symbol capitals
    capitals_df = pd.concat(capitals, axis=1)
    avg_capital = capitals_df.mean(axis=1, skipna=True)
    total_capital = capitals_df.sum(axis=1, skipna=True)

    out = pd.DataFrame({
        "date": full_days,
        "avg_symbol_capital": avg_capital.values,
        "total_capital": total_capital.values,
    })

    # Normalize average to start from zero regardless of number of symbols
    if not out.empty:
        out["avg_symbol_capital"] = out["avg_symbol_capital"] - float(out["avg_symbol_capital"].iloc[0])

    out["avg_symbol_capital"] = out["avg_symbol_capital"].round(2)
    out["total_capital"] = out["total_capital"].round(2)
    return out


def compute_weekly_returns_per_symbol(map_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute weekly percent returns per symbol from the trade map dataframe.
    Weeks are aligned to Monday (W-MON), using last known price in the week.
    Returns percentage values, not decimals.
    """
    if map_df is None or map_df.empty:
        return pd.DataFrame(columns=["week", "symbol", "weekly_return_pct"])

    df = map_df.copy()
    required_cols = ["date", "symbol", "price"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in map_df: {missing}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values(["symbol", "date"]).reset_index(drop=True)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])  # ensure valid prices

    rows: List[Dict] = []
    for symbol, sdf in df.groupby("symbol", sort=True):
        sdf = sdf.sort_values("date").copy()
        s = sdf.set_index("date")["price"].asfreq("D").ffill()
        weekly_prices = s.resample("W-MON").last().dropna()
        weekly_returns = weekly_prices.pct_change().fillna(0.0) * 100.0
        for idx, val in weekly_returns.items():
            rows.append({
                "week": idx,
                "symbol": symbol,
                "weekly_return_pct": float(val),
            })

    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(columns=["week", "symbol", "weekly_return_pct"])
    out = out.sort_values(["week", "symbol"]).reset_index(drop=True)
    return out


def plot_cumulative_returns_per_symbol(weekly_df: pd.DataFrame) -> None:
    """
    Plot cumulative returns per symbol from weekly return percentages and
    save to charts/portfolio2_cumulative_returns_symbols.png
    """
    if weekly_df is None or weekly_df.empty:
        return
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(14, 7))
    for symbol, sdf in weekly_df.groupby("symbol"):
        sdf = sdf.sort_values("week")
        cum = ((1.0 + sdf["weekly_return_pct"].values / 100.0).cumprod() - 1.0) * 100.0
        ax.plot(sdf["week"], cum, label=symbol)
    ax.axhline(0.0, color="gray", linewidth=1, alpha=0.6)
    ax.set_title("Total Return from Start (%) by Symbol (Portfolio 2)")
    ax.set_xlabel("Week")
    ax.set_ylabel("Cumulative Return (%)")
    ax.legend(ncol=2)
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    out_path = CHARTS_DIR / "portfolio2_cumulative_returns_symbols.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_per_symbol(map_df: pd.DataFrame) -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    for symbol, sdf in map_df.groupby("symbol"):
        sdf = sdf.sort_values("date")

        # Only generate the equity (capital) chart. Do not create price-with-trades charts.
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        ax2.plot(sdf["date"], sdf["equity_after"], label=f"{symbol} equity", color="tab:purple")
        ax2.set_title(f"{symbol} Capital Over Time (Portfolio 2)")
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Capital")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        fig2.autofmt_xdate()
        fig2.tight_layout()
        out_path_equity = CHARTS_DIR / f"{symbol}_portfolio2_equity.png"
        fig2.savefig(out_path_equity, dpi=150)
        plt.close(fig2)


def build_last_trades_per_asset(map_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a CSV view with the last transaction for each asset (one row per symbol).

    Output columns:
      - date
      - symbol
      - action
      - price
      - shares
      - notional
      - realized_pnl
    """
    work = map_df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work = work.dropna(subset=["date"]).sort_values(["symbol", "date"]).reset_index(drop=True)

    if work.empty:
        return pd.DataFrame(columns=[
            "date", "symbol", "action", "price", "shares", "notional", "realized_pnl"
        ])

    # Get last row per symbol by date
    idx = work.groupby("symbol")["date"].idxmax()
    last = work.loc[idx].copy()

    # Ensure required fields are properly typed
    for c in ["price", "shares", "notional", "realized_pnl"]:
        if c in last.columns:
            last[c] = pd.to_numeric(last[c], errors="coerce")

    last = last.dropna(subset=["price", "shares"]).copy()

    out = last[["date", "symbol", "action", "price", "shares", "notional", "realized_pnl"]].copy()
    out["date"] = out["date"].dt.date.astype(str)

    # Round numerics to two decimals where applicable
    for col in ["price", "notional", "realized_pnl"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(2)

    # Order by symbol for readability
    out = out.sort_values(["symbol"]).reset_index(drop=True)
    return out


def main() -> int:
    if not INPUT_PORTFOLIO_CSV.exists():
        print(f"Input file not found: {INPUT_PORTFOLIO_CSV}")
        return 1

    df = pd.read_csv(INPUT_PORTFOLIO_CSV)
    # Filter by symbol then by date (done inside compute function)
    map_df, summary_df = compute_trade_map_and_summary(df)

    # Save CSV outputs
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    map_df.to_csv(OUTPUT_MAP_CSV, index=False)
    summary_df.to_csv(OUTPUT_SUMMARY_CSV, index=False)

    # Generate plots (only equity; price-with-trades charts are intentionally not created)
    plot_per_symbol(map_df)

    print(f"Saved trade map to: {OUTPUT_MAP_CSV}")
    print(f"Saved summary to: {OUTPUT_SUMMARY_CSV}")
    # Save daily average capital time series for plotting
    daily_avg_cap_df = compute_daily_average_capital(map_df)
    daily_avg_cap_df.to_csv(OUTPUT_RATE_PLOT_CSV, index=False)
    print(f"Saved daily average and total capital to: {OUTPUT_RATE_PLOT_CSV}")

    # Compute weekly returns per symbol from map_df and plot cumulative chart
    weekly_returns_df = compute_weekly_returns_per_symbol(map_df)
    plot_cumulative_returns_per_symbol(weekly_returns_df)

    # Save last transaction per asset
    last_trades_df = build_last_trades_per_asset(map_df)
    last_trades_df.to_csv(OUTPUT_LAST_WEEK_CSV, index=False)
    print(f"Saved last trades per asset to: {OUTPUT_LAST_WEEK_CSV}")
    print(f"Charts saved to: {CHARTS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())



