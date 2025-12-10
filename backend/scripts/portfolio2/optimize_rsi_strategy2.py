import sys
from pathlib import Path
from typing import Iterable, Tuple, Dict
import subprocess
import itertools

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data" / "csv_backup"
PORTFOLIO2_DIR = DATA_DIR / "portfolio2"
PORTFOLIO_CSV = PORTFOLIO2_DIR / "portfolio2.csv"
SUMMARY_CSV = PORTFOLIO2_DIR / "portfolio2_summary.csv"


def run_strategy(buy_pct: float, sell_pct: float) -> Tuple[bool, Dict[str, float]]:
    """Run the pipeline generate_portfolio2.py -> generate_portfolio2_map.py and return per-symbol equity.

    Returns (ok, results) where results maps symbol->ending_equity.
    """
    # Run generator
    cmd_gen = [
        sys.executable,
        str(ROOT_DIR / "scripts" / "portfolio2" / "generate_portfolio2.py"),
        "--buy-pct", f"{buy_pct}",
        "--sell-pct", f"{sell_pct}",
    ]
    try:
        subprocess.run(cmd_gen, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Failed to run generate_portfolio2.py ({buy_pct}, {sell_pct}): {e}")
        return False, {}

    # Run mapping/summary
    cmd_map = [
        sys.executable,
        str(ROOT_DIR / "scripts" / "portfolio2" / "generate_portfolio2_map.py"),
    ]
    try:
        subprocess.run(cmd_map, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Failed to run generate_portfolio2_map.py ({buy_pct}, {sell_pct}): {e}")
        return False, {}

    if not SUMMARY_CSV.exists():
        print("Summary CSV not found after run")
        return False, {}

    # Read summary; compute ending equity per symbol = initial per-asset capital (1e6) + total_pnl.
    try:
        summary = pd.read_csv(SUMMARY_CSV)
    except Exception as e:
        print(f"Error reading summary: {e}")
        return False, {}

    results: Dict[str, float] = {}
    for _, row in summary.iterrows():
        symbol = row.get("symbol")
        total_pnl = float(row.get("total_pnl", 0.0) or 0.0)
        ending_equity = 1_000_000.0 + total_pnl
        results[str(symbol)] = ending_equity

    return True, results


def gridspace(start: float, stop: float, num: int) -> Iterable[float]:
    if num <= 1:
        yield start
        return
    step = (stop - start) / (num - 1)
    for i in range(num):
        yield round(start + i * step, 4)


def main() -> int:
    # Define search spaces (inclusive)
    buy_candidates = list(gridspace(0.05, 1.0, 5))
    sell_candidates = list(gridspace(0.01, 1.0, 5))

    best_per_symbol: Dict[str, Tuple[float, float, float]] = {}  # symbol -> (best_equity, buy_pct, sell_pct)

    total_runs = len(buy_candidates) * len(sell_candidates)
    run_idx = 0

    for b, s in itertools.product(buy_candidates, sell_candidates):
        run_idx += 1
        print(f"[{run_idx}/{total_runs}] Testing buy={b:.2%}, sell={s:.2%}")
        ok, results = run_strategy(b, s)
        if not ok:
            continue

        # Track best per symbol
        for symbol, equity in results.items():
            if symbol not in best_per_symbol or equity > best_per_symbol[symbol][0]:
                best_per_symbol[symbol] = (equity, b, s)

    # Prepare and save report
    rows = []
    for symbol, (equity, b, s) in sorted(best_per_symbol.items()):
        rows.append({
            "symbol": symbol,
            "best_buy_pct": b,
            "best_sell_pct": s,
            "ending_equity": round(equity, 2),
        })

    result_df = pd.DataFrame(rows)
    out_csv = PORTFOLIO2_DIR / "portfolio2_optimization_results.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(out_csv, index=False)
    print(f"Saved optimization results to: {out_csv}")

    if not result_df.empty:
        print(result_df)

    return 0


if __name__ == "__main__":
    sys.exit(main())



