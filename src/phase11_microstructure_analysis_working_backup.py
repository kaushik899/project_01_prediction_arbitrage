"""
PHASE 11 - MARKET MICROSTRUCTURE ANALYSIS

Analyzes historical prediction-market order-book data:

- Bid/ask spreads
- Relative spreads
- YES/NO market consistency
- Combined execution cost
- Gross arbitrage edge
- Price stability
- Market-level liquidity proxies
- Observation quality
"""

from pathlib import Path

import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = Path("data/historical_market_snapshots.csv")

OUTPUT_DATA = Path(
    "data/phase11_microstructure_analysis.csv"
)

OUTPUT_SUMMARY = Path(
    "dashboard/phase11_summary.csv"
)

OUTPUT_MARKET_STATS = Path(
    "dashboard/phase11_market_stats.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    return df


# ============================================================
# PREPARE COMPLETE OBSERVATIONS
# ============================================================

def prepare_data(df):

    complete = df[
        df["complete_orderbook"] == True
    ].copy()

    if complete.empty:
        raise ValueError(
            "No complete orderbook observations found."
        )

    numeric_columns = [
        "yes_bid",
        "yes_ask",
        "no_bid",
        "no_ask",
        "combined_yes_no_ask",
        "gross_edge",
    ]

    for column in numeric_columns:
        complete[column] = pd.to_numeric(
            complete[column],
            errors="coerce",
        )

    complete = complete.dropna(
        subset=numeric_columns
    ).copy()

    return complete


# ============================================================
# CALCULATE MICROSTRUCTURE METRICS
# ============================================================

def calculate_metrics(df):

    result = df.copy()

    # --------------------------------------------------------
    # YES SPREAD
    # --------------------------------------------------------

    result["yes_spread"] = (
        result["yes_ask"]
        - result["yes_bid"]
    )

    # --------------------------------------------------------
    # NO SPREAD
    # --------------------------------------------------------

    result["no_spread"] = (
        result["no_ask"]
        - result["no_bid"]
    )

    # --------------------------------------------------------
    # RELATIVE SPREADS
    # --------------------------------------------------------

    result["yes_mid"] = (
        result["yes_bid"]
        + result["yes_ask"]
    ) / 2

    result["no_mid"] = (
        result["no_bid"]
        + result["no_ask"]
    ) / 2

    result["yes_relative_spread"] = (
        result["yes_spread"]
        / result["yes_mid"]
    )

    result["no_relative_spread"] = (
        result["no_spread"]
        / result["no_mid"]
    )

    # --------------------------------------------------------
    # COMBINED SPREAD
    # --------------------------------------------------------

    result["combined_spread"] = (
        result["yes_spread"]
        + result["no_spread"]
    )

    # --------------------------------------------------------
    # EXECUTION COST
    # --------------------------------------------------------

    result["execution_cost"] = (
        result["combined_yes_no_ask"]
        - 1.0
    )

    # --------------------------------------------------------
    # IMPLIED COST IN BASIS POINTS
    # --------------------------------------------------------

    result["execution_cost_bps"] = (
        result["execution_cost"] * 10000
    )

    # --------------------------------------------------------
    # GROSS EDGE IN BASIS POINTS
    # --------------------------------------------------------

    result["gross_edge_bps"] = (
        result["gross_edge"] * 10000
    )

    # --------------------------------------------------------
    # MIDPOINT CONSISTENCY
    # --------------------------------------------------------

    result["midpoint_sum"] = (
        result["yes_mid"]
        + result["no_mid"]
    )

    result["midpoint_deviation"] = (
        result["midpoint_sum"]
        - 1.0
    )

    # --------------------------------------------------------
    # PRICE COMPLEMENT CONSISTENCY
    # --------------------------------------------------------

    result["price_complement_error"] = (
        result["yes_ask"]
        + result["no_bid"]
        - 1.0
    )

    # --------------------------------------------------------
    # EXECUTION STATUS
    # --------------------------------------------------------

    result["arbitrage_available"] = (
        result["gross_edge"] > 0
    )

    return result


# ============================================================
# MARKET-LEVEL ANALYSIS
# ============================================================

def create_market_statistics(df):

    grouped = (
        df.groupby("question")
        .agg(
            observations=("question", "size"),

            average_yes_bid=("yes_bid", "mean"),
            average_yes_ask=("yes_ask", "mean"),
            average_no_bid=("no_bid", "mean"),
            average_no_ask=("no_ask", "mean"),

            average_yes_spread=("yes_spread", "mean"),
            average_no_spread=("no_spread", "mean"),

            average_combined_spread=(
                "combined_spread",
                "mean",
            ),

            average_execution_cost_bps=(
                "execution_cost_bps",
                "mean",
            ),

            average_gross_edge_bps=(
                "gross_edge_bps",
                "mean",
            ),

            minimum_gross_edge_bps=(
                "gross_edge_bps",
                "min",
            ),

            maximum_gross_edge_bps=(
                "gross_edge_bps",
                "max",
            ),

            yes_price_volatility=(
                "yes_ask",
                "std",
            ),

            no_price_volatility=(
                "no_ask",
                "std",
            ),

            edge_volatility=(
                "gross_edge",
                "std",
            ),

            positive_edge_observations=(
                "arbitrage_available",
                "sum",
            ),
        )
        .reset_index()
    )

    grouped["gross_arbitrage_rate"] = (
        grouped["positive_edge_observations"]
        / grouped["observations"]
    )

    grouped["research_rank"] = (
        grouped["average_gross_edge_bps"]
        .rank(
            ascending=False,
            method="first",
        )
        .astype(int)
    )

    grouped = grouped.sort_values(
        "research_rank"
    )

    return grouped


# ============================================================
# SUMMARY
# ============================================================

def create_summary(df):

    summary = pd.DataFrame(
        {
            "metric": [
                "Total complete observations",
                "Unique markets",
                "Unique timestamps",
                "Average YES spread",
                "Average NO spread",
                "Average combined spread",
                "Average execution cost (bps)",
                "Average gross edge (bps)",
                "Median gross edge (bps)",
                "Minimum gross edge (bps)",
                "Maximum gross edge (bps)",
                "Gross edge standard deviation (bps)",
                "Positive-edge observations",
                "Gross arbitrage rate",
            ],
            "value": [
                len(df),
                df["question"].nunique(),
                df["timestamp"].nunique(),

                df["yes_spread"].mean(),
                df["no_spread"].mean(),
                df["combined_spread"].mean(),

                df["execution_cost_bps"].mean(),

                df["gross_edge_bps"].mean(),
                df["gross_edge_bps"].median(),
                df["gross_edge_bps"].min(),
                df["gross_edge_bps"].max(),
                df["gross_edge_bps"].std(),

                df["arbitrage_available"].sum(),

                df["arbitrage_available"].mean(),
            ],
        }
    )

    return summary


# ============================================================
# PRINT REPORT
# ============================================================

def print_report(
    df,
    market_stats,
    summary,
):

    print()
    print("=" * 70)
    print("PHASE 11 - MARKET MICROSTRUCTURE ANALYSIS")
    print("=" * 70)

    print()
    print("DATA QUALITY")
    print("-" * 70)

    print(
        f"Complete observations: {len(df)}"
    )

    print(
        f"Unique markets: {df['question'].nunique()}"
    )

    print(
        f"Unique timestamps: {df['timestamp'].nunique()}"
    )

    print()
    print("SPREAD ANALYSIS")
    print("-" * 70)

    print(
        f"Average YES spread: "
        f"{df['yes_spread'].mean():.6f}"
    )

    print(
        f"Average NO spread: "
        f"{df['no_spread'].mean():.6f}"
    )

    print(
        f"Average combined spread: "
        f"{df['combined_spread'].mean():.6f}"
    )

    print()
    print("EXECUTION COST")
    print("-" * 70)

    print(
        f"Average execution cost: "
        f"{df['execution_cost_bps'].mean():.2f} bps"
    )

    print(
        f"Minimum execution cost: "
        f"{df['execution_cost_bps'].min():.2f} bps"
    )

    print(
        f"Maximum execution cost: "
        f"{df['execution_cost_bps'].max():.2f} bps"
    )

    print()
    print("ARBITRAGE SIGNAL")
    print("-" * 70)

    print(
        f"Average gross edge: "
        f"{df['gross_edge_bps'].mean():.2f} bps"
    )

    print(
        f"Minimum gross edge: "
        f"{df['gross_edge_bps'].min():.2f} bps"
    )

    print(
        f"Maximum gross edge: "
        f"{df['gross_edge_bps'].max():.2f} bps"
    )

    print(
        f"Positive-edge observations: "
        f"{int(df['arbitrage_available'].sum())}"
    )

    print(
        f"Gross arbitrage rate: "
        f"{df['arbitrage_available'].mean():.4%}"
    )

    print()
    print("TOP MARKETS BY MICROSTRUCTURE SIGNAL")
    print("-" * 70)

    display_columns = [
        "question",
        "observations",
        "average_yes_spread",
        "average_no_spread",
        "average_execution_cost_bps",
        "average_gross_edge_bps",
        "positive_edge_observations",
        "gross_arbitrage_rate",
        "research_rank",
    ]

    print(
        market_stats[
            display_columns
        ]
        .head(20)
        .to_string(index=False)
    )


# ============================================================
# MAIN
# ============================================================

def main():

    df = load_data()

    complete = prepare_data(df)

    analyzed = calculate_metrics(
        complete
    )

    market_stats = create_market_statistics(
        analyzed
    )

    summary = create_summary(
        analyzed
    )

    OUTPUT_DATA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_SUMMARY.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_MARKET_STATS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    analyzed.to_csv(
        OUTPUT_DATA,
        index=False,
    )

    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
    )

    market_stats.to_csv(
        OUTPUT_MARKET_STATS,
        index=False,
    )

    print_report(
        analyzed,
        market_stats,
        summary,
    )

    print()
    print("=" * 70)
    print("PHASE 11 COMPLETE")
    print("=" * 70)

    print()
    print("Saved:")
    print(f"  {OUTPUT_DATA}")
    print(f"  {OUTPUT_SUMMARY}")
    print(f"  {OUTPUT_MARKET_STATS}")


if __name__ == "__main__":
    main()
