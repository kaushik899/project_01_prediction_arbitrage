"""
PHASE 15 - HISTORICAL ARBITRAGE BACKTEST

Purpose:
    Evaluate historical YES/NO arbitrage opportunities using
    the existing complete-orderbook observations.

The backtest:
    1. Loads historical snapshots.
    2. Keeps only complete order books.
    3. Calculates gross edge.
    4. Applies configurable fee and slippage assumptions.
    5. Calculates net edge.
    6. Counts theoretical opportunities.
    7. Produces market-level statistics.
    8. Produces time-series statistics.
    9. Saves CSV outputs and charts.

Important:
    This is a signal backtest, not proof of executable historical
    trades. The dataset contains snapshots rather than full historical
    trade executions.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "data/historical_market_snapshots.csv"

OUTPUT_FILE = "data/phase15_backtest.csv"
SUMMARY_FILE = "dashboard/phase15_summary.csv"
MARKET_FILE = "dashboard/phase15_market_stats.csv"
TIMESERIES_FILE = "data/phase15_time_series.csv"

EDGE_DISTRIBUTION = "dashboard/phase15_edge_distribution.png"
NET_EDGE_DISTRIBUTION = "dashboard/phase15_net_edge_distribution.png"
OPPORTUNITY_COUNTS = "dashboard/phase15_opportunity_counts.png"
MARKET_SIGNAL_HISTORY = "dashboard/phase15_market_signal_history.png"

# Same assumptions used by Phase 14
FEE_RATE = 0.0010
SLIPPAGE_RATE = 0.0010

# Minimum net edge required to classify an opportunity
MIN_NET_EDGE = 0.0020


# ============================================================
# HELPERS
# ============================================================

def ensure_directories():
    os.makedirs("data", exist_ok=True)
    os.makedirs("dashboard", exist_ok=True)


def load_data():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Historical dataset not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "timestamp",
        "question",
        "yes_ask",
        "no_ask",
        "combined_yes_no_ask",
        "gross_edge",
        "complete_orderbook",
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    return df


# ============================================================
# MAIN BACKTEST
# ============================================================

def main():

    print("=" * 70)
    print("PHASE 15 - HISTORICAL ARBITRAGE BACKTEST")
    print("=" * 70)

    ensure_directories()

    df = load_data()

    print()
    print("RAW DATA")
    print("-" * 70)

    print(f"Total observations: {len(df)}")
    print(
        f"Complete observations: "
        f"{df['complete_orderbook'].eq(True).sum()}"
    )
    print(
        f"Incomplete observations: "
        f"{df['complete_orderbook'].eq(False).sum()}"
    )
    print(f"Unique markets: {df['question'].nunique()}")
    print(f"Unique timestamps: {df['timestamp'].nunique()}")

    # --------------------------------------------------------
    # COMPLETE OBSERVATIONS ONLY
    # --------------------------------------------------------

    complete = df[
        df["complete_orderbook"].eq(True)
    ].copy()

    if complete.empty:
        raise ValueError(
            "No complete observations available for backtesting."
        )

    # --------------------------------------------------------
    # NORMALIZE NUMERIC COLUMNS
    # --------------------------------------------------------

    numeric_columns = [
        "yes_ask",
        "no_ask",
        "combined_yes_no_ask",
        "gross_edge",
    ]

    for column in numeric_columns:
        complete[column] = pd.to_numeric(
            complete[column],
            errors="coerce"
        )

    complete = complete.dropna(
        subset=numeric_columns
    ).copy()

    # --------------------------------------------------------
    # RECOMPUTE SIGNAL
    # --------------------------------------------------------

    complete["calculated_combined_ask"] = (
        complete["yes_ask"] +
        complete["no_ask"]
    )

    complete["calculated_gross_edge"] = (
        1.0 -
        complete["calculated_combined_ask"]
    )

    # Use the calculated value for the backtest
    complete["gross_edge"] = (
        complete["calculated_gross_edge"]
    )

    # --------------------------------------------------------
    # COST MODEL
    # --------------------------------------------------------

    complete["fee_cost"] = FEE_RATE

    complete["slippage_cost"] = SLIPPAGE_RATE

    complete["total_cost"] = (
        complete["fee_cost"] +
        complete["slippage_cost"]
    )

    complete["net_edge"] = (
        complete["gross_edge"] -
        complete["total_cost"]
    )

    # --------------------------------------------------------
    # SIGNAL FLAGS
    # --------------------------------------------------------

    complete["positive_gross_edge"] = (
        complete["gross_edge"] > 0
    )

    complete["positive_net_edge"] = (
        complete["net_edge"] > 0
    )

    complete["qualified_opportunity"] = (
        complete["net_edge"] >= MIN_NET_EDGE
    )

    # --------------------------------------------------------
    # SAVE OBSERVATION-LEVEL BACKTEST
    # --------------------------------------------------------

    complete.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # SUMMARY STATISTICS
    # ========================================================

    total = len(complete)

    positive_gross = int(
        complete["positive_gross_edge"].sum()
    )

    positive_net = int(
        complete["positive_net_edge"].sum()
    )

    qualified = int(
        complete["qualified_opportunity"].sum()
    )

    summary = pd.DataFrame([
        ["raw_observations", len(df)],
        ["complete_observations", total],
        ["incomplete_observations", len(df) - total],
        ["unique_markets_total", df["question"].nunique()],
        ["unique_markets_backtested", complete["question"].nunique()],
        ["unique_timestamps_total", df["timestamp"].nunique()],
        ["average_gross_edge", complete["gross_edge"].mean()],
        ["median_gross_edge", complete["gross_edge"].median()],
        ["minimum_gross_edge", complete["gross_edge"].min()],
        ["maximum_gross_edge", complete["gross_edge"].max()],
        ["std_gross_edge", complete["gross_edge"].std()],
        ["positive_gross_observations", positive_gross],
        ["positive_gross_rate", positive_gross / total],
        ["average_net_edge", complete["net_edge"].mean()],
        ["median_net_edge", complete["net_edge"].median()],
        ["minimum_net_edge", complete["net_edge"].min()],
        ["maximum_net_edge", complete["net_edge"].max()],
        ["positive_net_observations", positive_net],
        ["positive_net_rate", positive_net / total],
        ["qualified_opportunities", qualified],
        ["qualified_opportunity_rate", qualified / total],
        ["fee_rate", FEE_RATE],
        ["slippage_rate", SLIPPAGE_RATE],
        ["total_cost_rate", FEE_RATE + SLIPPAGE_RATE],
        ["minimum_required_net_edge", MIN_NET_EDGE],
    ], columns=["metric", "value"])

    summary.to_csv(
        SUMMARY_FILE,
        index=False
    )

    # ========================================================
    # MARKET-LEVEL ANALYSIS
    # ========================================================

    market_stats = (
        complete
        .groupby("question")
        .agg(
            observations=("question", "size"),
            average_gross_edge=("gross_edge", "mean"),
            minimum_gross_edge=("gross_edge", "min"),
            maximum_gross_edge=("gross_edge", "max"),
            average_net_edge=("net_edge", "mean"),
            minimum_net_edge=("net_edge", "min"),
            maximum_net_edge=("net_edge", "max"),
            positive_gross_observations=(
                "positive_gross_edge",
                "sum"
            ),
            positive_net_observations=(
                "positive_net_edge",
                "sum"
            ),
            qualified_opportunities=(
                "qualified_opportunity",
                "sum"
            ),
        )
        .reset_index()
    )

    market_stats["gross_signal_rate"] = (
        market_stats["positive_gross_observations"] /
        market_stats["observations"]
    )

    market_stats["net_signal_rate"] = (
        market_stats["positive_net_observations"] /
        market_stats["observations"]
    )

    market_stats["qualified_rate"] = (
        market_stats["qualified_opportunities"] /
        market_stats["observations"]
    )

    market_stats = market_stats.sort_values(
        "maximum_net_edge",
        ascending=False
    )

    market_stats.to_csv(
        MARKET_FILE,
        index=False
    )

    # ========================================================
    # TIME-SERIES ANALYSIS
    # ========================================================

    complete["timestamp"] = pd.to_datetime(
        complete["timestamp"],
        errors="coerce"
    )

    complete["timestamp"] = complete["timestamp"].dt.floor("min")

    timeseries = (
        complete
        .groupby("timestamp")
        .agg(
            observations=("question", "size"),
            average_gross_edge=("gross_edge", "mean"),
            maximum_gross_edge=("gross_edge", "max"),
            average_net_edge=("net_edge", "mean"),
            maximum_net_edge=("net_edge", "max"),
            positive_gross_observations=(
                "positive_gross_edge",
                "sum"
            ),
            positive_net_observations=(
                "positive_net_edge",
                "sum"
            ),
            qualified_opportunities=(
                "qualified_opportunity",
                "sum"
            ),
        )
        .reset_index()
    )

    timeseries.to_csv(
        TIMESERIES_FILE,
        index=False
    )

    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print()
    print("=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)

    print()
    print(f"Complete observations: {total}")
    print(f"Markets backtested: {complete['question'].nunique()}")
    print()

    print(f"Average gross edge: {complete['gross_edge'].mean():.6f}")
    print(f"Median gross edge:  {complete['gross_edge'].median():.6f}")
    print(f"Minimum gross edge: {complete['gross_edge'].min():.6f}")
    print(f"Maximum gross edge: {complete['gross_edge'].max():.6f}")

    print()

    print(f"Fee assumption:       {FEE_RATE:.4%}")
    print(f"Slippage assumption:  {SLIPPAGE_RATE:.4%}")
    print(f"Total cost assumption:{FEE_RATE + SLIPPAGE_RATE:.4%}")

    print()

    print(f"Average net edge: {complete['net_edge'].mean():.6f}")
    print(f"Maximum net edge: {complete['net_edge'].max():.6f}")

    print()

    print(f"Positive gross observations: {positive_gross}")
    print(f"Positive gross rate: {positive_gross / total:.4%}")

    print(f"Positive net observations: {positive_net}")
    print(f"Positive net rate: {positive_net / total:.4%}")

    print(f"Qualified opportunities: {qualified}")
    print(f"Qualified opportunity rate: {qualified / total:.4%}")

    # ========================================================
    # TOP MARKETS
    # ========================================================

    print()
    print("=" * 70)
    print("TOP MARKETS BY MAXIMUM NET EDGE")
    print("=" * 70)

    columns = [
        "question",
        "observations",
        "average_gross_edge",
        "maximum_gross_edge",
        "average_net_edge",
        "maximum_net_edge",
        "qualified_opportunities",
    ]

    print(
        market_stats[columns]
        .head(15)
        .to_string(index=False)
    )

    # ========================================================
    # CHART 1 - GROSS EDGE DISTRIBUTION
    # ========================================================

    plt.figure(figsize=(10, 6))

    plt.hist(
        complete["gross_edge"],
        bins=20
    )

    plt.axvline(
        0,
        linestyle="--",
        linewidth=1
    )

    plt.title(
        "Historical Gross Arbitrage Edge Distribution"
    )

    plt.xlabel("Gross Edge")
    plt.ylabel("Observations")

    plt.tight_layout()

    plt.savefig(
        EDGE_DISTRIBUTION,
        dpi=150
    )

    plt.close()

    # ========================================================
    # CHART 2 - NET EDGE DISTRIBUTION
    # ========================================================

    plt.figure(figsize=(10, 6))

    plt.hist(
        complete["net_edge"],
        bins=20
    )

    plt.axvline(
        0,
        linestyle="--",
        linewidth=1
    )

    plt.axvline(
        MIN_NET_EDGE,
        linestyle=":",
        linewidth=1
    )

    plt.title(
        "Historical Net Arbitrage Edge Distribution"
    )

    plt.xlabel("Net Edge")
    plt.ylabel("Observations")

    plt.tight_layout()

    plt.savefig(
        NET_EDGE_DISTRIBUTION,
        dpi=150
    )

    plt.close()

    # ========================================================
    # CHART 3 - OPPORTUNITY COUNTS
    # ========================================================

    labels = [
        "Positive Gross",
        "Positive Net",
        "Qualified"
    ]

    values = [
        positive_gross,
        positive_net,
        qualified
    ]

    plt.figure(figsize=(9, 6))

    plt.bar(
        labels,
        values
    )

    plt.title(
        "Historical Arbitrage Signal Counts"
    )

    plt.ylabel("Observations")

    plt.tight_layout()

    plt.savefig(
        OPPORTUNITY_COUNTS,
        dpi=150
    )

    plt.close()

    # ========================================================
    # CHART 4 - MARKET SIGNAL HISTORY
    # ========================================================

    plt.figure(figsize=(12, 6))

    plt.plot(
        timeseries["timestamp"],
        timeseries["maximum_net_edge"],
        marker="o"
    )

    plt.axhline(
        0,
        linestyle="--",
        linewidth=1
    )

    plt.axhline(
        MIN_NET_EDGE,
        linestyle=":",
        linewidth=1
    )

    plt.title(
        "Maximum Historical Net Edge Over Time"
    )

    plt.xlabel("Timestamp")
    plt.ylabel("Maximum Net Edge")

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig(
        MARKET_SIGNAL_HISTORY,
        dpi=150
    )

    plt.close()

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print()
    print("=" * 70)
    print("PHASE 15 COMPLETE")
    print("=" * 70)

    print()
    print("Saved:")
    print(f"  {OUTPUT_FILE}")
    print(f"  {SUMMARY_FILE}")
    print(f"  {MARKET_FILE}")
    print(f"  {TIMESERIES_FILE}")

    print()
    print("Dashboard:")
    print(f"  {EDGE_DISTRIBUTION}")
    print(f"  {NET_EDGE_DISTRIBUTION}")
    print(f"  {OPPORTUNITY_COUNTS}")
    print(f"  {MARKET_SIGNAL_HISTORY}")

    print()

    if qualified == 0:
        print(
            "RESULT: No historical observations met the "
            "configured net-edge threshold."
        )
    else:
        print(
            f"RESULT: {qualified} historical observations "
            "met the configured net-edge threshold."
        )


if __name__ == "__main__":
    main()
