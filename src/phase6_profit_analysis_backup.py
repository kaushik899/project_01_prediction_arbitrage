"""
Phase 6 - Net Profit & Transaction Cost Analysis

Takes the execution results from Phase 5 and calculates:

    Gross Profit
    Estimated Trading Fees
    Net Profit
    Net ROI

This is a research/simulation engine.
It DOES NOT place real orders.
"""

import pandas as pd


INPUT_FILE = "arbitrage_execution_analysis.csv"
OUTPUT_FILE = "arbitrage_net_profit_analysis.csv"


# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

# Conservative research assumption.
# We are NOT claiming this is the exact current fee schedule.
# It is simply a configurable transaction-cost assumption.

FEE_RATE = 0.01


# ------------------------------------------------------------
# NET PROFIT CALCULATION
# ------------------------------------------------------------

def calculate_net_profit(
    total_cost,
    gross_profit,
    fee_rate=FEE_RATE,
):
    """
    Calculate estimated fees and net profit.

    Fee is modeled as a percentage of execution cost.

    This is a simplified research model.
    """

    estimated_fees = total_cost * fee_rate

    net_profit = (
        gross_profit
        - estimated_fees
    )

    if total_cost > 0:
        net_roi = (
            net_profit
            / total_cost
        ) * 100
    else:
        net_roi = None

    return {
        "estimated_fees": estimated_fees,
        "net_profit": net_profit,
        "net_roi_pct": net_roi,
    }


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():

    print("=" * 70)
    print("PHASE 6 - NET PROFIT ANALYSIS")
    print("=" * 70)

    print(
        f"\nLoading:\n{INPUT_FILE}"
    )

    df = pd.read_csv(
        INPUT_FILE
    )

    print(
        f"Rows loaded: {len(df)}"
    )

    # --------------------------------------------------------
    # Only fully executable scenarios
    # --------------------------------------------------------

    executable = df[
        df["status"] == "fully_filled"
    ].copy()

    print(
        f"Fully executable scenarios: "
        f"{len(executable)}"
    )

    if executable.empty:

        print(
            "\nNo fully executable scenarios."
        )

        return

    # --------------------------------------------------------
    # Calculate transaction costs
    # --------------------------------------------------------

    calculations = executable.apply(
        lambda row: calculate_net_profit(
            total_cost=row["total_cost"],
            gross_profit=row["gross_profit"],
        ),
        axis=1,
    )

    calculation_df = pd.DataFrame(
        calculations.tolist()
    )

    executable = pd.concat(
        [
            executable.reset_index(drop=True),
            calculation_df,
        ],
        axis=1,
    )

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    executable["profitable_after_fees"] = (
        executable["net_profit"] > 0
    )

    executable["profitable_before_fees"] = (
        executable["gross_profit"] > 0
    )

    # --------------------------------------------------------
    # Sort by net profit
    # --------------------------------------------------------

    executable = executable.sort_values(
        by="net_profit",
        ascending=False,
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    executable.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    gross_profitable = (
        executable[
            "profitable_before_fees"
        ].sum()
    )

    net_profitable = (
        executable[
            "profitable_after_fees"
        ].sum()
    )

    print("\n" + "=" * 70)
    print("PHASE 6 SUMMARY")
    print("=" * 70)

    print(
        f"Executable scenarios: "
        f"{len(executable)}"
    )

    print(
        f"Gross profitable scenarios: "
        f"{gross_profitable}"
    )

    print(
        f"Net profitable scenarios: "
        f"{net_profitable}"
    )

    print(
        f"\nFee assumption: "
        f"{FEE_RATE * 100:.2f}%"
    )

    # --------------------------------------------------------
    # Show top scenarios
    # --------------------------------------------------------

    print("\nTOP 10 SCENARIOS BY NET PROFIT")
    print("-" * 70)

    columns = [
        "question",
        "quantity",
        "total_cost",
        "gross_profit",
        "estimated_fees",
        "net_profit",
        "net_roi_pct",
    ]

    print(
        executable[
            columns
        ]
        .head(10)
        .to_string(index=False)
    )

    print(
        f"\nSaved results to:\n"
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
