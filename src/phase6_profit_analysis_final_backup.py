"""
Phase 6 - Net Profit & Transaction Cost Analysis

Research-only simulation.

This module takes Phase 5 execution results and estimates:

    Gross Profit
    Trading Fees
    Slippage Buffer
    Total Estimated Costs
    Net Profit
    Net ROI

No real orders are placed.
"""

import pandas as pd


INPUT_FILE = "arbitrage_execution_analysis.csv"
OUTPUT_FILE = "arbitrage_net_profit_analysis.csv"


# ============================================================
# RESEARCH COST ASSUMPTIONS
# ============================================================

# These are configurable research assumptions.
# They are NOT presented as the exchange's official fee schedule.

FEE_RATE = 0.01

SLIPPAGE_BUFFER_RATE = 0.002


# ============================================================
# TRANSACTION COST MODEL
# ============================================================

def calculate_transaction_costs(
    total_cost,
    fee_rate=FEE_RATE,
    slippage_buffer_rate=SLIPPAGE_BUFFER_RATE,
):
    """
    Estimate transaction-related costs.

    fee:
        Percentage of execution cost.

    slippage buffer:
        Additional conservative percentage applied
        to execution cost.

    Returns estimated costs only.
    """

    estimated_fee = (
        total_cost
        * fee_rate
    )

    slippage_buffer = (
        total_cost
        * slippage_buffer_rate
    )

    total_estimated_costs = (
        estimated_fee
        + slippage_buffer
    )

    return {
        "estimated_fee": estimated_fee,
        "slippage_buffer": slippage_buffer,
        "total_estimated_costs": total_estimated_costs,
    }


# ============================================================
# PROFIT MODEL
# ============================================================

def calculate_net_profit(
    total_cost,
    gross_profit,
):
    """
    Calculate net profit after estimated costs.
    """

    costs = calculate_transaction_costs(
        total_cost=total_cost,
    )

    net_profit = (
        gross_profit
        - costs["total_estimated_costs"]
    )

    if total_cost > 0:

        net_roi_pct = (
            net_profit
            / total_cost
        ) * 100

    else:

        net_roi_pct = None

    return {
        "estimated_fee": costs[
            "estimated_fee"
        ],

        "slippage_buffer": costs[
            "slippage_buffer"
        ],

        "total_estimated_costs": costs[
            "total_estimated_costs"
        ],

        "net_profit": net_profit,

        "net_roi_pct": net_roi_pct,
    }


# ============================================================
# MAIN
# ============================================================

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
    # Keep only executable scenarios
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
    # Calculate costs
    # --------------------------------------------------------

    calculations = executable.apply(
        lambda row: calculate_net_profit(
            total_cost=row["total_cost"],
            gross_profit=row["gross_profit"],
        ),
        axis=1,
    )

    calculations_df = pd.DataFrame(
        calculations.tolist()
    )

    executable = pd.concat(
        [
            executable.reset_index(drop=True),
            calculations_df,
        ],
        axis=1,
    )

    # --------------------------------------------------------
    # Profit classifications
    # --------------------------------------------------------

    executable[
        "profitable_before_costs"
    ] = (
        executable[
            "gross_profit"
        ] > 0
    )

    executable[
        "profitable_after_costs"
    ] = (
        executable[
            "net_profit"
        ] > 0
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

    gross_profitable = int(
        executable[
            "profitable_before_costs"
        ].sum()
    )

    net_profitable = int(
        executable[
            "profitable_after_costs"
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
        f"{FEE_RATE * 100:.3f}%"
    )

    print(
        f"Slippage buffer assumption: "
        f"{SLIPPAGE_BUFFER_RATE * 100:.3f}%"
    )

    # --------------------------------------------------------
    # TOP SCENARIOS
    # --------------------------------------------------------

    print(
        "\nTOP 10 SCENARIOS BY NET PROFIT"
    )

    print("-" * 70)

    columns = [
        "question",
        "quantity",
        "total_cost",
        "gross_profit",
        "estimated_fee",
        "slippage_buffer",
        "total_estimated_costs",
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


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
