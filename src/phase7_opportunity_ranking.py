"""
Phase 7 - Opportunity Ranking & Research Analytics

Research-only analytics layer.

This module reads Phase 6 net-profit results and produces
a ranked research dataset.

It does NOT place orders.

Ranking is based on observed execution economics:
    - net profit
    - net ROI
    - gross profit
    - execution size
    - liquidity/fill status

The purpose is to identify the strongest and weakest
execution scenarios in the research dataset.
"""

import pandas as pd


# ============================================================
# FILES
# ============================================================

INPUT_FILE = "arbitrage_net_profit_analysis.csv"

OUTPUT_FILE = "arbitrage_opportunity_ranking.csv"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    df = pd.read_csv(
        INPUT_FILE
    )

    return df


# ============================================================
# DATA QUALITY CHECK
# ============================================================

def validate_columns(df):

    required_columns = [
        "question",
        "yes_token",
        "no_token",
        "quantity",
        "total_cost",
        "gross_profit",
        "gross_profit_pct",
        "estimated_fee",
        "slippage_buffer",
        "total_estimated_costs",
        "net_profit",
        "net_roi_pct",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing)
        )


# ============================================================
# RANKING
# ============================================================

def create_ranking(df):

    ranked = df.copy()

    # --------------------------------------------------------
    # Absolute economics
    # --------------------------------------------------------

    ranked["profit_per_dollar"] = (
        ranked["net_profit"]
        / ranked["total_cost"]
    )

    # --------------------------------------------------------
    # Distance from break-even
    #
    # Positive = above break-even
    # Negative = below break-even
    # --------------------------------------------------------

    ranked["break_even_gap"] = (
        ranked["net_roi_pct"]
    )

    # --------------------------------------------------------
    # Rank by net profit
    # --------------------------------------------------------

    ranked["net_profit_rank"] = (
        ranked["net_profit"]
        .rank(
            method="min",
            ascending=False,
        )
        .astype(int)
    )

    # --------------------------------------------------------
    # Rank by ROI
    # --------------------------------------------------------

    ranked["net_roi_rank"] = (
        ranked["net_roi_pct"]
        .rank(
            method="min",
            ascending=False,
        )
        .astype(int)
    )

    # --------------------------------------------------------
    # Combined research rank
    #
    # Lower rank number = stronger observed result.
    # This is NOT an investment recommendation.
    # --------------------------------------------------------

    ranked["research_rank"] = (
        (
            ranked["net_profit_rank"]
            + ranked["net_roi_rank"]
        )
        / 2
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    ranked = ranked.sort_values(
        by=[
            "research_rank",
            "net_profit",
        ],
        ascending=[
            True,
            False,
        ],
    )

    return ranked


# ============================================================
# SUMMARY
# ============================================================

def print_summary(df):

    print("\n" + "=" * 70)
    print("PHASE 7 SUMMARY")
    print("=" * 70)

    print(
        f"\nScenarios analyzed: {len(df)}"
    )

    positive_gross = int(
        (
            df["gross_profit"] > 0
        ).sum()
    )

    positive_net = int(
        (
            df["net_profit"] > 0
        ).sum()
    )

    print(
        f"Gross profitable scenarios: "
        f"{positive_gross}"
    )

    print(
        f"Net profitable scenarios: "
        f"{positive_net}"
    )

    print(
        f"\nBest observed net P/L: "
        f"${df['net_profit'].max():.6f}"
    )

    print(
        f"Worst observed net P/L: "
        f"${df['net_profit'].min():.6f}"
    )

    print(
        f"Best observed net ROI: "
        f"{df['net_roi_pct'].max():.6f}%"
    )

    print(
        f"Worst observed net ROI: "
        f"{df['net_roi_pct'].min():.6f}%"
    )

    print(
        f"\nAverage net P/L: "
        f"${df['net_profit'].mean():.6f}"
    )

    print(
        f"Average net ROI: "
        f"{df['net_roi_pct'].mean():.6f}%"
    )


# ============================================================
# TOP SCENARIOS
# ============================================================

def print_top_scenarios(df):

    print(
        "\n" + "=" * 70
    )

    print(
        "TOP 15 OBSERVED SCENARIOS"
    )

    print(
        "=" * 70
    )

    columns = [
        "question",
        "quantity",
        "total_cost",
        "gross_profit",
        "total_estimated_costs",
        "net_profit",
        "net_roi_pct",
        "research_rank",
    ]

    print(
        df[
            columns
        ]
        .head(15)
        .to_string(
            index=False
        )
    )


# ============================================================
# BOTTOM SCENARIOS
# ============================================================

def print_bottom_scenarios(df):

    print(
        "\n" + "=" * 70
    )

    print(
        "BOTTOM 10 OBSERVED SCENARIOS"
    )

    print(
        "=" * 70
    )

    columns = [
        "question",
        "quantity",
        "total_cost",
        "gross_profit",
        "total_estimated_costs",
        "net_profit",
        "net_roi_pct",
    ]

    print(
        df.sort_values(
            "net_profit",
            ascending=True,
        )[
            columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "PHASE 7 - OPPORTUNITY RANKING"
    )
    print("=" * 70)

    print(
        f"\nLoading:\n{INPUT_FILE}"
    )

    df = load_data()

    print(
        f"Rows loaded: {len(df)}"
    )

    validate_columns(df)

    # --------------------------------------------------------
    # Rank
    # --------------------------------------------------------

    ranked = create_ranking(
        df
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print_summary(
        ranked
    )

    # --------------------------------------------------------
    # Top scenarios
    # --------------------------------------------------------

    print_top_scenarios(
        ranked
    )

    # --------------------------------------------------------
    # Bottom scenarios
    # --------------------------------------------------------

    print_bottom_scenarios(
        ranked
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    ranked.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "\nSaved ranked research dataset to:"
    )

    print(
        OUTPUT_FILE
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
