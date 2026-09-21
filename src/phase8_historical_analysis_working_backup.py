"""
PHASE 8B - HISTORICAL MARKET ANALYSIS

Reads:
    data/historical_market_snapshots.csv

Produces:
    data/historical_market_analysis.csv
"""

import os
import pandas as pd


INPUT_FILE = "data/historical_market_snapshots.csv"
OUTPUT_FILE = "data/historical_market_analysis.csv"


def main():

    print("=" * 70)
    print("PHASE 8B - HISTORICAL MARKET ANALYSIS")
    print("=" * 70)

    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: {INPUT_FILE} does not exist.")
        return

    df = pd.read_csv(INPUT_FILE)

    print()
    print(f"Rows loaded: {len(df)}")
    print(f"Unique markets: {df['question'].nunique()}")

    # ------------------------------------------------------------
    # BASIC DATA CLEANING
    # ------------------------------------------------------------

    numeric_columns = [
        "yes_bid",
        "yes_ask",
        "no_bid",
        "no_ask",
        "combined_yes_no_ask",
        "gross_edge",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    # ------------------------------------------------------------
    # BASIC STATISTICS
    # ------------------------------------------------------------

    complete = df[df["complete_orderbook"] == True].copy()

    print()
    print("=" * 70)
    print("DATA QUALITY")
    print("=" * 70)

    print(f"Total observations: {len(df)}")
    print(f"Complete order books: {len(complete)}")
    print(f"Incomplete order books: {len(df) - len(complete)}")

    # ------------------------------------------------------------
    # APPARENT GROSS ARBITRAGE
    # ------------------------------------------------------------

    df["apparent_gross_arbitrage"] = (
        df["combined_yes_no_ask"] < 1.0
    )

    gross_opportunities = df[
        df["apparent_gross_arbitrage"] == True
    ].copy()

    print()
    print("=" * 70)
    print("GROSS ARBITRAGE ANALYSIS")
    print("=" * 70)

    print(
        f"Observations with YES + NO ask < $1: "
        f"{len(gross_opportunities)}"
    )

    if len(gross_opportunities) > 0:

        print()
        print("Potential observations:")

        display_columns = [
            "timestamp",
            "question",
            "yes_ask",
            "no_ask",
            "combined_yes_no_ask",
            "gross_edge",
        ]

        print(
            gross_opportunities[
                display_columns
            ]
            .sort_values("gross_edge", ascending=False)
            .head(20)
            .to_string(index=False)
        )

    # ------------------------------------------------------------
    # SUMMARY STATISTICS
    # ------------------------------------------------------------

    print()
    print("=" * 70)
    print("PRICE STATISTICS")
    print("=" * 70)

    if len(complete) > 0:

        print(
            f"Average YES ask: "
            f"{complete['yes_ask'].mean():.6f}"
        )

        print(
            f"Average NO ask: "
            f"{complete['no_ask'].mean():.6f}"
        )

        print(
            f"Average combined ask: "
            f"{complete['combined_yes_no_ask'].mean():.6f}"
        )

        print(
            f"Minimum combined ask: "
            f"{complete['combined_yes_no_ask'].min():.6f}"
        )

        print(
            f"Maximum combined ask: "
            f"{complete['combined_yes_no_ask'].max():.6f}"
        )

        print(
            f"Average gross edge: "
            f"{complete['gross_edge'].mean():.6f}"
        )

        print(
            f"Maximum gross edge: "
            f"{complete['gross_edge'].max():.6f}"
        )

    # ------------------------------------------------------------
    # MARKET-LEVEL SUMMARY
    # ------------------------------------------------------------

    market_summary = (
        df.groupby("question")
        .agg(
            observations=("question", "count"),
            average_yes_ask=("yes_ask", "mean"),
            average_no_ask=("no_ask", "mean"),
            average_combined_ask=(
                "combined_yes_no_ask",
                "mean",
            ),
            minimum_combined_ask=(
                "combined_yes_no_ask",
                "min",
            ),
            maximum_gross_edge=(
                "gross_edge",
                "max",
            ),
            gross_arbitrage_observations=(
                "apparent_gross_arbitrage",
                "sum",
            ),
        )
        .reset_index()
    )

    # ------------------------------------------------------------
    # RANK MARKETS
    # ------------------------------------------------------------

    market_summary = market_summary.sort_values(
        [
            "gross_arbitrage_observations",
            "maximum_gross_edge",
        ],
        ascending=False,
    )

    market_summary["research_rank"] = (
        range(1, len(market_summary) + 1)
    )

    # ------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------

    os.makedirs("data", exist_ok=True)

    market_summary.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("=" * 70)
    print("TOP MARKETS BY RESEARCH SIGNAL")
    print("=" * 70)

    print(
        market_summary.head(10).to_string(
            index=False
        )
    )

    print()
    print("=" * 70)
    print("PHASE 8B COMPLETE")
    print("=" * 70)

    print()
    print(f"Saved analysis to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
