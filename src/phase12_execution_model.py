"""
PHASE 12 - EXECUTION & SLIPPAGE MODEL

Converts theoretical arbitrage opportunities into
realistic executable scenarios.

Models:

- Gross arbitrage edge
- Execution costs
- Slippage
- Net executable edge
- Net profit
- Net ROI
- Trade feasibility
"""

from pathlib import Path

import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = Path(
    "data/phase11_microstructure_analysis.csv"
)

OUTPUT_FILE = Path(
    "data/phase12_execution_analysis.csv"
)

SUMMARY_FILE = Path(
    "dashboard/phase12_summary.csv"
)

SCENARIOS_FILE = Path(
    "dashboard/phase12_slippage_scenarios.csv"
)

TRADE_SIZE = 1000.0

SLIPPAGE_SCENARIOS = [
    0.0000,
    0.0005,
    0.0010,
    0.0020,
    0.0050,
]


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
# PREPARE DATA
# ============================================================

def prepare_data(df):

    numeric_columns = [
        "yes_ask",
        "no_ask",
        "combined_yes_no_ask",
        "gross_edge",
        "yes_spread",
        "no_spread",
        "execution_cost",
        "execution_cost_bps",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    df = df.dropna(
        subset=[
            "yes_ask",
            "no_ask",
            "combined_yes_no_ask",
            "gross_edge",
        ]
    ).copy()

    return df


# ============================================================
# EXECUTION MODEL
# ============================================================

def calculate_execution_metrics(
    df,
    slippage,
):

    result = df.copy()

    # --------------------------------------------------------
    # SLIPPAGE
    # --------------------------------------------------------

    result["slippage"] = slippage

    result["slippage_cost"] = (
        slippage * 2
    )

    # Two legs:
    #
    # YES purchase
    # NO purchase
    #
    # Therefore total slippage cost is
    # approximately 2 × assumed per-leg slippage.

    # --------------------------------------------------------
    # THEORETICAL COST
    # --------------------------------------------------------

    result["theoretical_entry_cost"] = (
        result["combined_yes_no_ask"]
    )

    # --------------------------------------------------------
    # EXECUTABLE ENTRY COST
    # --------------------------------------------------------

    result["executable_entry_cost"] = (
        result["theoretical_entry_cost"]
        + result["slippage_cost"]
    )

    # --------------------------------------------------------
    # NET EDGE
    # --------------------------------------------------------

    result["net_edge"] = (
        1.0
        - result["executable_entry_cost"]
    )

    # --------------------------------------------------------
    # NET EDGE IN BASIS POINTS
    # --------------------------------------------------------

    result["net_edge_bps"] = (
        result["net_edge"] * 10000
    )

    # --------------------------------------------------------
    # GROSS PROFIT
    # --------------------------------------------------------

    result["gross_profit"] = (
        result["gross_edge"]
        * TRADE_SIZE
    )

    # --------------------------------------------------------
    # SLIPPAGE COST
    # --------------------------------------------------------

    result["slippage_dollar_cost"] = (
        result["slippage_cost"]
        * TRADE_SIZE
    )

    # --------------------------------------------------------
    # NET PROFIT
    # --------------------------------------------------------

    result["net_profit"] = (
        result["net_edge"]
        * TRADE_SIZE
    )

    # --------------------------------------------------------
    # NET ROI
    # --------------------------------------------------------

    result["net_roi"] = (
        result["net_edge"]
        / result["executable_entry_cost"]
    )

    # --------------------------------------------------------
    # EXECUTION FEASIBILITY
    # --------------------------------------------------------

    result["executable"] = (
        result["net_edge"] > 0
    )

    return result


# ============================================================
# SCENARIO ANALYSIS
# ============================================================

def create_scenario_analysis(df):

    rows = []

    for slippage in SLIPPAGE_SCENARIOS:

        scenario = calculate_execution_metrics(
            df,
            slippage,
        )

        rows.append(
            {
                "slippage_per_leg": slippage,

                "slippage_bps_per_leg":
                    slippage * 10000,

                "observations":
                    len(scenario),

                "average_gross_edge_bps":
                    scenario["gross_edge"]
                    .mean()
                    * 10000,

                "average_net_edge_bps":
                    scenario["net_edge_bps"]
                    .mean(),

                "minimum_net_edge_bps":
                    scenario["net_edge_bps"]
                    .min(),

                "maximum_net_edge_bps":
                    scenario["net_edge_bps"]
                    .max(),

                "executable_observations":
                    int(
                        scenario["executable"]
                        .sum()
                    ),

                "executable_rate":
                    scenario["executable"]
                    .mean(),

                "average_net_profit":
                    scenario["net_profit"]
                    .mean(),

                "maximum_net_profit":
                    scenario["net_profit"]
                    .max(),

                "average_net_roi":
                    scenario["net_roi"]
                    .mean(),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# MAIN SUMMARY
# ============================================================

def create_summary(
    df,
    scenario_df,
):

    zero_slippage = calculate_execution_metrics(
        df,
        0.0,
    )

    summary = pd.DataFrame(
        {
            "metric": [
                "Trade size",
                "Complete observations",
                "Unique markets",
                "Unique timestamps",
                "Gross profitable observations",
                "Gross arbitrage rate",
                "Average gross edge (bps)",
                "Average theoretical entry cost",
                "Average YES spread",
                "Average NO spread",
                "Zero-slippage executable observations",
                "Zero-slippage executable rate",
                "Maximum gross profit",
                "Maximum zero-slippage net profit",
            ],
            "value": [
                TRADE_SIZE,

                len(df),

                df["question"].nunique(),

                df["timestamp"].nunique(),

                int(
                    (df["gross_edge"] > 0)
                    .sum()
                ),

                (
                    df["gross_edge"] > 0
                ).mean(),

                df["gross_edge"]
                .mean()
                * 10000,

                df["combined_yes_no_ask"]
                .mean(),

                df["yes_spread"]
                .mean(),

                df["no_spread"]
                .mean(),

                int(
                    zero_slippage[
                        "executable"
                    ].sum()
                ),

                zero_slippage[
                    "executable"
                ].mean(),

                (
                    df["gross_edge"]
                    * TRADE_SIZE
                ).max(),

                zero_slippage[
                    "net_profit"
                ].max(),
            ],
        }
    )

    return summary


# ============================================================
# PRINT REPORT
# ============================================================

def print_report(
    df,
    scenario_df,
    summary,
):

    print()
    print("=" * 70)
    print(
        "PHASE 12 - EXECUTION & SLIPPAGE MODEL"
    )
    print("=" * 70)

    print()
    print("DATA")
    print("-" * 70)

    print(
        f"Complete observations: {len(df)}"
    )

    print(
        f"Unique markets: "
        f"{df['question'].nunique()}"
    )

    print(
        f"Trade size: ${TRADE_SIZE:,.2f}"
    )

    print()
    print("GROSS EDGE")
    print("-" * 70)

    print(
        f"Average gross edge: "
        f"{df['gross_edge'].mean() * 10000:.2f} bps"
    )

    print(
        f"Maximum gross edge: "
        f"{df['gross_edge'].max() * 10000:.2f} bps"
    )

    print(
        "Gross profitable observations: "
        f"{int((df['gross_edge'] > 0).sum())}"
    )

    print()
    print("SLIPPAGE SCENARIOS")
    print("-" * 70)

    display_columns = [
        "slippage_bps_per_leg",
        "average_gross_edge_bps",
        "average_net_edge_bps",
        "minimum_net_edge_bps",
        "maximum_net_edge_bps",
        "executable_observations",
        "executable_rate",
        "average_net_profit",
        "maximum_net_profit",
    ]

    print(
        scenario_df[
            display_columns
        ].to_string(index=False)
    )

    print()
    print("INTERPRETATION")
    print("-" * 70)

    if (
        scenario_df[
            "executable_observations"
        ].max()
        == 0
    ):

        print(
            "No historical observation remained "
            "executable under the tested scenarios."
        )

    else:

        print(
            "Some historical observations remained "
            "executable under at least one scenario."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    df = load_data()

    df = prepare_data(df)

    scenario_df = create_scenario_analysis(
        df
    )

    summary = create_summary(
        df,
        scenario_df,
    )

    zero_slippage = calculate_execution_metrics(
        df,
        0.0,
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    SUMMARY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    SCENARIOS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    zero_slippage.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    summary.to_csv(
        SUMMARY_FILE,
        index=False,
    )

    scenario_df.to_csv(
        SCENARIOS_FILE,
        index=False,
    )

    print_report(
        df,
        scenario_df,
        summary,
    )

    print()
    print("=" * 70)
    print("PHASE 12 COMPLETE")
    print("=" * 70)

    print()
    print("Saved:")

    print(
        f"  {OUTPUT_FILE}"
    )

    print(
        f"  {SUMMARY_FILE}"
    )

    print(
        f"  {SCENARIOS_FILE}"
    )


if __name__ == "__main__":
    main()
