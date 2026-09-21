"""
PHASE 13 - STATISTICAL VALIDATION

Purpose:
- Validate historical arbitrage observations
- Measure edge/spread stability
- Analyze distributions
- Separate complete from incomplete observations
- Produce research-quality statistical summaries
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


INPUT_FILE = "data/historical_market_snapshots.csv"

OUTPUT_DATA = "data/phase13_statistical_validation.csv"
OUTPUT_SUMMARY = "dashboard/phase13_summary.csv"

EDGE_PLOT = "dashboard/phase13_edge_distribution.png"
SPREAD_PLOT = "dashboard/phase13_spread_analysis.png"
STABILITY_PLOT = "dashboard/phase13_edge_stability.png"


# ============================================================
# SETUP
# ============================================================

os.makedirs("data", exist_ok=True)
os.makedirs("dashboard", exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

complete = df[df["complete_orderbook"] == True].copy()

if complete.empty:
    raise ValueError("No complete observations available.")


# ============================================================
# DERIVED VARIABLES
# ============================================================

complete["yes_spread"] = (
    complete["yes_ask"] - complete["yes_bid"]
)

complete["no_spread"] = (
    complete["no_ask"] - complete["no_bid"]
)

complete["average_spread"] = (
    complete["yes_spread"] + complete["no_spread"]
) / 2

complete["edge_bps"] = (
    complete["gross_edge"] * 10000
)

complete["combined_ask_bps_from_par"] = (
    (complete["combined_yes_no_ask"] - 1) * 10000
)


# ============================================================
# BASIC STATISTICS
# ============================================================

edges = complete["gross_edge"].dropna()

summary = {
    "total_raw_observations": len(df),
    "complete_observations": len(complete),
    "incomplete_observations": len(df) - len(complete),
    "unique_markets_total": df["question"].nunique(),
    "unique_markets_complete": complete["question"].nunique(),
    "unique_timestamps_total": df["timestamp"].nunique(),

    "average_gross_edge": edges.mean(),
    "median_gross_edge": edges.median(),
    "std_gross_edge": edges.std(),
    "min_gross_edge": edges.min(),
    "max_gross_edge": edges.max(),

    "positive_edge_observations": int((edges > 0).sum()),
    "zero_edge_observations": int((edges == 0).sum()),
    "negative_edge_observations": int((edges < 0).sum()),

    "positive_edge_rate": (edges > 0).mean(),

    "average_yes_spread": complete["yes_spread"].mean(),
    "average_no_spread": complete["no_spread"].mean(),
    "average_combined_ask": complete["combined_yes_no_ask"].mean(),

    "median_combined_ask": complete["combined_yes_no_ask"].median(),
    "minimum_combined_ask": complete["combined_yes_no_ask"].min(),
    "maximum_combined_ask": complete["combined_yes_no_ask"].max(),

    "average_edge_bps": complete["edge_bps"].mean(),
    "minimum_edge_bps": complete["edge_bps"].min(),
    "maximum_edge_bps": complete["edge_bps"].max(),
}


# ============================================================
# QUANTILES
# ============================================================

for q in [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]:
    summary[f"gross_edge_quantile_{q}"] = edges.quantile(q)


# ============================================================
# MARKET-LEVEL STATISTICS
# ============================================================

market_stats = (
    complete
    .groupby("question")
    .agg(
        observations=("gross_edge", "count"),
        average_edge=("gross_edge", "mean"),
        median_edge=("gross_edge", "median"),
        std_edge=("gross_edge", "std"),
        minimum_edge=("gross_edge", "min"),
        maximum_edge=("gross_edge", "max"),
        positive_edges=("gross_edge", lambda x: (x > 0).sum()),
        average_combined_ask=("combined_yes_no_ask", "mean"),
        minimum_combined_ask=("combined_yes_no_ask", "min"),
        average_yes_spread=("yes_spread", "mean"),
        average_no_spread=("no_spread", "mean"),
    )
    .reset_index()
)

market_stats["positive_edge_rate"] = (
    market_stats["positive_edges"]
    / market_stats["observations"]
)

market_stats = market_stats.sort_values(
    ["average_edge", "observations"],
    ascending=[False, False],
)


# ============================================================
# TIME-LEVEL STATISTICS
# ============================================================

time_stats = (
    complete
    .groupby("timestamp")
    .agg(
        observations=("gross_edge", "count"),
        average_edge=("gross_edge", "mean"),
        median_edge=("gross_edge", "median"),
        minimum_edge=("gross_edge", "min"),
        maximum_edge=("gross_edge", "max"),
        positive_edges=("gross_edge", lambda x: (x > 0).sum()),
        average_combined_ask=("combined_yes_no_ask", "mean"),
    )
    .reset_index()
)

time_stats["positive_edge_rate"] = (
    time_stats["positive_edges"]
    / time_stats["observations"]
)

time_stats = time_stats.sort_values("timestamp")


# ============================================================
# SAVE MAIN DATASET
# ============================================================

complete.to_csv(
    OUTPUT_DATA,
    index=False
)


# ============================================================
# SAVE SUMMARY
# ============================================================

summary_df = pd.DataFrame(
    list(summary.items()),
    columns=["metric", "value"]
)

summary_df.to_csv(
    OUTPUT_SUMMARY,
    index=False
)


# ============================================================
# EDGE DISTRIBUTION
# ============================================================

plt.figure(figsize=(10, 6))

plt.hist(
    complete["edge_bps"],
    bins=20
)

plt.axvline(
    0,
    linestyle="--",
    linewidth=2
)

plt.title(
    "Phase 13 - Gross Arbitrage Edge Distribution"
)

plt.xlabel(
    "Gross Edge (basis points)"
)

plt.ylabel(
    "Frequency"
)

plt.tight_layout()

plt.savefig(
    EDGE_PLOT,
    dpi=150
)

plt.close()


# ============================================================
# SPREAD ANALYSIS
# ============================================================

plt.figure(figsize=(10, 6))

plt.plot(
    complete["timestamp"],
    complete["yes_spread"],
    marker="o",
    label="YES spread"
)

plt.plot(
    complete["timestamp"],
    complete["no_spread"],
    marker="o",
    label="NO spread"
)

plt.title(
    "Phase 13 - YES/NO Bid-Ask Spreads"
)

plt.xlabel(
    "Timestamp"
)

plt.ylabel(
    "Bid-Ask Spread"
)

plt.xticks(rotation=45)

plt.legend()

plt.tight_layout()

plt.savefig(
    SPREAD_PLOT,
    dpi=150
)

plt.close()


# ============================================================
# EDGE STABILITY
# ============================================================

plt.figure(figsize=(10, 6))

plt.plot(
    time_stats["timestamp"],
    time_stats["average_edge"] * 10000,
    marker="o"
)

plt.axhline(
    0,
    linestyle="--",
    linewidth=2
)

plt.title(
    "Phase 13 - Historical Gross Edge Stability"
)

plt.xlabel(
    "Timestamp"
)

plt.ylabel(
    "Average Gross Edge (basis points)"
)

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig(
    STABILITY_PLOT,
    dpi=150
)

plt.close()


# ============================================================
# REPORT
# ============================================================

print()
print("=" * 70)
print("PHASE 13 - STATISTICAL VALIDATION")
print("=" * 70)

print()
print("DATASET")
print("-" * 70)

print(f"Total raw observations:        {len(df)}")
print(f"Complete observations:         {len(complete)}")
print(f"Incomplete observations:       {len(df) - len(complete)}")
print(f"Unique markets:                {df['question'].nunique()}")
print(f"Complete markets:              {complete['question'].nunique()}")
print(f"Unique timestamps:             {df['timestamp'].nunique()}")

print()
print("GROSS EDGE STATISTICS")
print("-" * 70)

print(f"Average gross edge:            {edges.mean():.6f}")
print(f"Median gross edge:             {edges.median():.6f}")
print(f"Std deviation:                 {edges.std():.6f}")
print(f"Minimum gross edge:            {edges.min():.6f}")
print(f"Maximum gross edge:            {edges.max():.6f}")

print()
print(f"Average edge (bps):            {complete['edge_bps'].mean():.2f}")
print(f"Minimum edge (bps):            {complete['edge_bps'].min():.2f}")
print(f"Maximum edge (bps):            {complete['edge_bps'].max():.2f}")

print()
print(f"Positive-edge observations:    {(edges > 0).sum()}")
print(f"Negative-edge observations:    {(edges < 0).sum()}")
print(f"Positive-edge rate:            {(edges > 0).mean():.4%}")

print()
print("SPREAD STATISTICS")
print("-" * 70)

print(f"Average YES spread:             {complete['yes_spread'].mean():.6f}")
print(f"Average NO spread:              {complete['no_spread'].mean():.6f}")
print(f"Average combined ask:           {complete['combined_yes_no_ask'].mean():.6f}")

print()
print("OUTPUT FILES")
print("-" * 70)

print(f"Saved: {OUTPUT_DATA}")
print(f"Saved: {OUTPUT_SUMMARY}")
print(f"Saved: {EDGE_PLOT}")
print(f"Saved: {SPREAD_PLOT}")
print(f"Saved: {STABILITY_PLOT}")

print()
print("=" * 70)
print("PHASE 13 COMPLETE")
print("=" * 70)
