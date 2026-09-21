import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


INPUT_FILE = "data/historical_market_snapshots.csv"
OUTPUT_FILE = "data/phase10_historical_analysis.csv"
SUMMARY_FILE = "dashboard/phase10_summary.csv"


def main():
    print("=" * 70)
    print("PHASE 10B - HISTORICAL STATISTICAL ANALYSIS")
    print("=" * 70)

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)

    print(f"Rows loaded: {len(df)}")

    # ------------------------------------------------------------
    # DATA CLEANING
    # ------------------------------------------------------------

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    numeric_columns = [
        "yes_bid",
        "yes_ask",
        "no_bid",
        "no_ask",
        "combined_yes_no_ask",
        "gross_edge",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    complete = df[df["complete_orderbook"] == True].copy()

    print(f"Complete observations: {len(complete)}")
    print(f"Unique markets: {df['question'].nunique()}")
    print(f"Markets with complete observations: {complete['question'].nunique()}")

    if complete.empty:
        print("No complete observations available.")
        return

    # ------------------------------------------------------------
    # BASIC STATISTICS
    # ------------------------------------------------------------

    gross_edge = complete["gross_edge"].dropna()

    summary = {
        "total_observations": len(df),
        "complete_observations": len(complete),
        "incomplete_observations": len(df) - len(complete),
        "unique_markets": df["question"].nunique(),
        "markets_with_complete_data": complete["question"].nunique(),
        "unique_timestamps": df["timestamp"].nunique(),
        "average_gross_edge": gross_edge.mean(),
        "median_gross_edge": gross_edge.median(),
        "minimum_gross_edge": gross_edge.min(),
        "maximum_gross_edge": gross_edge.max(),
        "gross_edge_std": gross_edge.std(),
        "positive_edge_observations": int((gross_edge > 0).sum()),
        "zero_edge_observations": int((gross_edge == 0).sum()),
        "negative_edge_observations": int((gross_edge < 0).sum()),
    }

    summary["positive_edge_rate_pct"] = (
        summary["positive_edge_observations"]
        / len(gross_edge)
        * 100
    )

    summary["gross_arbitrage_rate_pct"] = (
        (gross_edge > 0).mean() * 100
    )

    # ------------------------------------------------------------
    # MARKET OBSERVATION COUNTS
    # ------------------------------------------------------------

    market_counts = (
        complete.groupby("question")
        .size()
        .reset_index(name="complete_observations")
        .sort_values(
            "complete_observations",
            ascending=False
        )
    )

    # ------------------------------------------------------------
    # MARKET-LEVEL STATISTICS
    # ------------------------------------------------------------

    market_stats = (
        complete.groupby("question")
        .agg(
            observations=("gross_edge", "count"),
            average_combined_ask=("combined_yes_no_ask", "mean"),
            median_combined_ask=("combined_yes_no_ask", "median"),
            minimum_combined_ask=("combined_yes_no_ask", "min"),
            maximum_combined_ask=("combined_yes_no_ask", "max"),
            average_gross_edge=("gross_edge", "mean"),
            minimum_gross_edge=("gross_edge", "min"),
            maximum_gross_edge=("gross_edge", "max"),
            positive_edge_observations=(
                "gross_edge",
                lambda x: int((x > 0).sum())
            ),
        )
        .reset_index()
    )

    market_stats["gross_arbitrage_rate"] = (
        market_stats["positive_edge_observations"]
        / market_stats["observations"]
    )

    market_stats = market_stats.sort_values(
        [
            "positive_edge_observations",
            "maximum_gross_edge",
            "observations",
        ],
        ascending=[False, False, False],
    )

    market_stats["research_rank"] = range(
        1,
        len(market_stats) + 1
    )

    # ------------------------------------------------------------
    # TIME-SERIES STATISTICS
    # ------------------------------------------------------------

    time_stats = (
        complete.groupby("timestamp")
        .agg(
            observations=("gross_edge", "count"),
            average_gross_edge=("gross_edge", "mean"),
            minimum_gross_edge=("gross_edge", "min"),
            maximum_gross_edge=("gross_edge", "max"),
            average_combined_ask=(
                "combined_yes_no_ask",
                "mean"
            ),
            positive_edge_observations=(
                "gross_edge",
                lambda x: int((x > 0).sum())
            ),
        )
        .reset_index()
        .sort_values("timestamp")
    )

    time_stats["gross_arbitrage_rate"] = (
        time_stats["positive_edge_observations"]
        / time_stats["observations"]
    )

    # ------------------------------------------------------------
    # SAVE MARKET ANALYSIS
    # ------------------------------------------------------------

    os.makedirs("data", exist_ok=True)
    os.makedirs("dashboard", exist_ok=True)

    market_stats.to_csv(
        OUTPUT_FILE,
        index=False
    )

    summary_df = pd.DataFrame(
        [summary]
    )

    summary_df.to_csv(
        SUMMARY_FILE,
        index=False
    )

    # ------------------------------------------------------------
    # PRINT RESULTS
    # ------------------------------------------------------------

    print()
    print("=" * 70)
    print("PHASE 10B SUMMARY")
    print("=" * 70)

    print(f"Total observations:       {summary['total_observations']}")
    print(f"Complete observations:    {summary['complete_observations']}")
    print(f"Incomplete observations:  {summary['incomplete_observations']}")
    print(f"Unique markets:            {summary['unique_markets']}")
    print(
        f"Markets with complete data: "
        f"{summary['markets_with_complete_data']}"
    )
    print(f"Unique timestamps:         {summary['unique_timestamps']}")

    print()
    print("GROSS EDGE STATISTICS")
    print("-" * 70)

    print(
        f"Average gross edge:       "
        f"{summary['average_gross_edge']:.6f}"
    )

    print(
        f"Median gross edge:        "
        f"{summary['median_gross_edge']:.6f}"
    )

    print(
        f"Minimum gross edge:       "
        f"{summary['minimum_gross_edge']:.6f}"
    )

    print(
        f"Maximum gross edge:       "
        f"{summary['maximum_gross_edge']:.6f}"
    )

    print(
        f"Gross edge std dev:       "
        f"{summary['gross_edge_std']:.6f}"
    )

    print(
        f"Positive-edge observations: "
        f"{summary['positive_edge_observations']}"
    )

    print(
        f"Positive-edge rate:       "
        f"{summary['positive_edge_rate_pct']:.4f}%"
    )

    print(
        f"Gross arbitrage rate:     "
        f"{summary['gross_arbitrage_rate_pct']:.4f}%"
    )

    print()
    print("=" * 70)
    print("MARKETS WITH MOST COMPLETE OBSERVATIONS")
    print("=" * 70)

    print(
        market_counts.head(10).to_string(
            index=False
        )
    )

    print()
    print("=" * 70)
    print("TOP MARKETS BY HISTORICAL SIGNAL")
    print("=" * 70)

    columns_to_show = [
        "question",
        "observations",
        "average_combined_ask",
        "minimum_combined_ask",
        "average_gross_edge",
        "minimum_gross_edge",
        "maximum_gross_edge",
        "positive_edge_observations",
        "gross_arbitrage_rate",
        "research_rank",
    ]

    print(
        market_stats[columns_to_show]
        .head(10)
        .to_string(index=False)
    )

    # ------------------------------------------------------------
    # VISUALIZATION 1: GROSS EDGE OVER TIME
    # ------------------------------------------------------------

    plt.figure(figsize=(12, 6))

    plt.plot(
        time_stats["timestamp"],
        time_stats["average_gross_edge"],
        marker="o",
    )

    plt.axhline(
        0,
        linestyle="--",
    )

    plt.title("Average Gross Arbitrage Edge Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Average Gross Edge")

    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(
        "dashboard/phase10_gross_edge_over_time.png",
        dpi=150,
    )

    plt.close()

    # ------------------------------------------------------------
    # VISUALIZATION 2: EDGE DISTRIBUTION
    # ------------------------------------------------------------

    plt.figure(figsize=(10, 6))

    plt.hist(
        gross_edge,
        bins=min(20, max(5, len(gross_edge) // 2)),
    )

    plt.axvline(
        0,
        linestyle="--",
    )

    plt.title("Historical Gross Edge Distribution")
    plt.xlabel("Gross Edge")
    plt.ylabel("Frequency")

    plt.tight_layout()

    plt.savefig(
        "dashboard/phase10_edge_distribution.png",
        dpi=150,
    )

    plt.close()

    # ------------------------------------------------------------
    # VISUALIZATION 3: COMBINED ASK
    # ------------------------------------------------------------

    plt.figure(figsize=(10, 6))

    plt.hist(
        complete["combined_yes_no_ask"],
        bins=min(20, max(5, len(complete) // 2)),
    )

    plt.axvline(
        1.0,
        linestyle="--",
    )

    plt.title("YES + NO Combined Ask Distribution")
    plt.xlabel("Combined Ask")
    plt.ylabel("Frequency")

    plt.tight_layout()

    plt.savefig(
        "dashboard/phase10_combined_ask_distribution.png",
        dpi=150,
    )

    plt.close()

    # ------------------------------------------------------------
    # VISUALIZATION 4: OBSERVATIONS PER MARKET
    # ------------------------------------------------------------

    plt.figure(figsize=(12, 6))

    counts = market_counts[
        "complete_observations"
    ]

    plt.hist(
        counts,
        bins=range(
            int(counts.min()),
            int(counts.max()) + 2
        ),
    )

    plt.title("Complete Observations per Market")
    plt.xlabel("Complete Observations")
    plt.ylabel("Number of Markets")

    plt.tight_layout()

    plt.savefig(
        "dashboard/phase10_market_observation_distribution.png",
        dpi=150,
    )

    plt.close()

    # ------------------------------------------------------------
    # SAVE TIME-SERIES TABLE
    # ------------------------------------------------------------

    time_stats.to_csv(
        "data/phase10_time_series.csv",
        index=False,
    )

    print()
    print("=" * 70)
    print("PHASE 10B COMPLETE")
    print("=" * 70)

    print()
    print("Saved:")
    print(f"  {OUTPUT_FILE}")
    print(f"  {SUMMARY_FILE}")
    print("  data/phase10_time_series.csv")

    print()
    print("Dashboard:")
    print("  dashboard/phase10_gross_edge_over_time.png")
    print("  dashboard/phase10_edge_distribution.png")
    print("  dashboard/phase10_combined_ask_distribution.png")
    print("  dashboard/phase10_market_observation_distribution.png")


if __name__ == "__main__":
    main()
