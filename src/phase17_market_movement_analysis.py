"""
PHASE 17 - MARKET MOVEMENT & SIGNAL ANALYSIS

Analyzes the historical observations collected by Phase 16.

Goals:
1. Measure YES/NO price movements.
2. Measure gross-edge movements.
3. Measure changes between consecutive observations.
4. Identify temporary price dislocations.
5. Measure whether market movement creates potentially interesting
   short-term signals, without assuming that those signals are profitable.

This phase does NOT execute trades.
"""

import os
import pandas as pd
import numpy as np


INPUT_FILE = "data/phase16_live_monitor.csv"

OUTPUT_FILE = "data/phase17_market_movement_analysis.csv"
SUMMARY_FILE = "dashboard/phase17_summary.csv"
MARKET_STATS_FILE = "dashboard/phase17_market_stats.csv"

MIN_OBSERVATIONS = 2


def safe_mkdir(path):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def main():

    print("=" * 70)
    print("PHASE 17 - MARKET MOVEMENT & SIGNAL ANALYSIS")
    print("=" * 70)

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print()
    print("RAW DATA")
    print("-" * 70)

    print(f"Total observations: {len(df)}")

    if "status" in df.columns:
        usable = df[df["status"] != "ERROR"].copy()
    else:
        usable = df.copy()

    print(f"Usable observations: {len(usable)}")

    if "question" in usable.columns:
        print(
            f"Unique markets: {usable['question'].nunique()}"
        )

    usable["timestamp"] = pd.to_datetime(
        usable["timestamp"],
        errors="coerce",
        utc=True
    )

    numeric_columns = [
        "yes_bid",
        "yes_ask",
        "no_bid",
        "no_ask",
        "combined_yes_no_ask",
        "gross_edge",
        "net_edge",
    ]

    for col in numeric_columns:
        if col in usable.columns:
            usable[col] = pd.to_numeric(
                usable[col],
                errors="coerce"
            )

    usable = usable.dropna(
        subset=[
            "timestamp",
            "question",
            "yes_ask",
            "no_ask",
            "gross_edge"
        ]
    )

    usable = usable.sort_values(
        ["question", "timestamp"]
    ).reset_index(drop=True)

    # ------------------------------------------------------------
    # CONSECUTIVE MARKET MOVEMENTS
    # ------------------------------------------------------------

    usable["previous_timestamp"] = (
        usable.groupby("question")["timestamp"].shift(1)
    )

    usable["previous_yes_ask"] = (
        usable.groupby("question")["yes_ask"].shift(1)
    )

    usable["previous_no_ask"] = (
        usable.groupby("question")["no_ask"].shift(1)
    )

    usable["previous_gross_edge"] = (
        usable.groupby("question")["gross_edge"].shift(1)
    )

    usable["time_delta_seconds"] = (
        usable["timestamp"]
        - usable["previous_timestamp"]
    ).dt.total_seconds()

    usable["yes_ask_change"] = (
        usable["yes_ask"]
        - usable["previous_yes_ask"]
    )

    usable["no_ask_change"] = (
        usable["no_ask"]
        - usable["previous_no_ask"]
    )

    usable["gross_edge_change"] = (
        usable["gross_edge"]
        - usable["previous_gross_edge"]
    )

    usable["yes_ask_change_bps"] = (
        usable["yes_ask_change"] * 10000
    )

    usable["no_ask_change_bps"] = (
        usable["no_ask_change"] * 10000
    )

    usable["gross_edge_change_bps"] = (
        usable["gross_edge_change"] * 10000
    )

    # ------------------------------------------------------------
    # DIRECTION
    # ------------------------------------------------------------

    usable["yes_direction"] = np.select(
        [
            usable["yes_ask_change"] > 0,
            usable["yes_ask_change"] < 0
        ],
        [
            "UP",
            "DOWN"
        ],
        default="UNCHANGED"
    )

    usable["no_direction"] = np.select(
        [
            usable["no_ask_change"] > 0,
            usable["no_ask_change"] < 0
        ],
        [
            "UP",
            "DOWN"
        ],
        default="UNCHANGED"
    )

    usable["edge_direction"] = np.select(
        [
            usable["gross_edge_change"] > 0,
            usable["gross_edge_change"] < 0
        ],
        [
            "IMPROVING",
            "WORSENING"
        ],
        default="UNCHANGED"
    )

    # ------------------------------------------------------------
    # EDGE RECOVERY / DISLOCATION
    # ------------------------------------------------------------

    usable["edge_improvement"] = (
        usable["gross_edge_change"] > 0
    )

    usable["edge_deterioration"] = (
        usable["gross_edge_change"] < 0
    )

    usable["gross_edge_positive"] = (
        usable["gross_edge"] > 0
    )

    usable["net_edge_positive"] = (
        usable["net_edge"] > 0
        if "net_edge" in usable.columns
        else False
    )

    # ------------------------------------------------------------
    # SUMMARY STATISTICS
    # ------------------------------------------------------------

    transitions = usable[
        usable["previous_timestamp"].notna()
    ].copy()

    print()
    print("=" * 70)
    print("MOVEMENT RESULTS")
    print("=" * 70)

    print(f"Usable observations: {len(usable)}")
    print(f"Consecutive transitions: {len(transitions)}")

    if len(transitions) > 0:

        print(
            f"Average YES ask change: "
            f"{transitions['yes_ask_change'].mean():.6f}"
        )

        print(
            f"Maximum YES ask increase: "
            f"{transitions['yes_ask_change'].max():.6f}"
        )

        print(
            f"Maximum YES ask decrease: "
            f"{transitions['yes_ask_change'].min():.6f}"
        )

        print(
            f"Average NO ask change: "
            f"{transitions['no_ask_change'].mean():.6f}"
        )

        print(
            f"Maximum NO ask increase: "
            f"{transitions['no_ask_change'].max():.6f}"
        )

        print(
            f"Maximum NO ask decrease: "
            f"{transitions['no_ask_change'].min():.6f}"
        )

        print(
            f"Maximum gross-edge improvement: "
            f"{transitions['gross_edge_change'].max():.6f}"
        )

        print(
            f"Maximum gross-edge deterioration: "
            f"{transitions['gross_edge_change'].min():.6f}"
        )

        improving = int(
            transitions["edge_improvement"].sum()
        )

        deteriorating = int(
            transitions["edge_deterioration"].sum()
        )

        print(
            f"Edge-improving transitions: {improving}"
        )

        print(
            f"Edge-deteriorating transitions: {deteriorating}"
        )

    # ------------------------------------------------------------
    # MARKET-LEVEL STATISTICS
    # ------------------------------------------------------------

    market_stats = (
        usable
        .groupby("question")
        .agg(
            observations=("question", "size"),
            first_timestamp=("timestamp", "min"),
            last_timestamp=("timestamp", "max"),

            yes_ask_min=("yes_ask", "min"),
            yes_ask_max=("yes_ask", "max"),

            no_ask_min=("no_ask", "min"),
            no_ask_max=("no_ask", "max"),

            gross_edge_min=("gross_edge", "min"),
            gross_edge_max=("gross_edge", "max"),

            gross_edge_mean=("gross_edge", "mean"),

            positive_gross_observations=(
                "gross_edge_positive",
                "sum"
            ),
        )
        .reset_index()
    )

    market_stats["yes_move"] = (
        market_stats["yes_ask_max"]
        - market_stats["yes_ask_min"]
    )

    market_stats["no_move"] = (
        market_stats["no_ask_max"]
        - market_stats["no_ask_min"]
    )

    market_stats["gross_edge_move"] = (
        market_stats["gross_edge_max"]
        - market_stats["gross_edge_min"]
    )

    market_stats["yes_move_bps"] = (
        market_stats["yes_move"] * 10000
    )

    market_stats["no_move_bps"] = (
        market_stats["no_move"] * 10000
    )

    market_stats["gross_edge_move_bps"] = (
        market_stats["gross_edge_move"] * 10000
    )

    market_stats = market_stats[
        market_stats["observations"] >= MIN_OBSERVATIONS
    ]

    # ------------------------------------------------------------
    # TOP MOVING MARKETS
    # ------------------------------------------------------------

    print()
    print("=" * 70)
    print("TOP MARKETS BY GROSS-EDGE MOVEMENT")
    print("=" * 70)

    display_columns = [
        "question",
        "observations",
        "yes_move",
        "no_move",
        "gross_edge_min",
        "gross_edge_max",
        "gross_edge_move",
    ]

    print(
        market_stats
        .sort_values(
            "gross_edge_move",
            ascending=False
        )
        .head(20)[display_columns]
        .to_string(index=False)
    )

    # ------------------------------------------------------------
    # SUMMARY FILE
    # ------------------------------------------------------------

    summary = pd.DataFrame([
        [
            "total_raw_observations",
            len(df)
        ],
        [
            "usable_observations",
            len(usable)
        ],
        [
            "consecutive_transitions",
            len(transitions)
        ],
        [
            "unique_markets",
            usable["question"].nunique()
        ],
        [
            "markets_with_multiple_observations",
            len(market_stats)
        ],
        [
            "positive_gross_observations",
            int(
                usable["gross_edge_positive"].sum()
            )
        ],
        [
            "maximum_gross_edge",
            usable["gross_edge"].max()
        ],
        [
            "minimum_gross_edge",
            usable["gross_edge"].min()
        ],
        [
            "maximum_yes_move",
            transitions["yes_ask_change"].max()
            if len(transitions) else np.nan
        ],
        [
            "maximum_no_move",
            transitions["no_ask_change"].max()
            if len(transitions) else np.nan
        ],
        [
            "maximum_gross_edge_improvement",
            transitions["gross_edge_change"].max()
            if len(transitions) else np.nan
        ],
        [
            "maximum_gross_edge_deterioration",
            transitions["gross_edge_change"].min()
            if len(transitions) else np.nan
        ],
        [
            "edge_improving_transitions",
            int(
                transitions["edge_improvement"].sum()
            )
        ],
        [
            "edge_deteriorating_transitions",
            int(
                transitions["edge_deterioration"].sum()
            )
        ],
    ], columns=["metric", "value"])

    # ------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------

    safe_mkdir(OUTPUT_FILE)
    safe_mkdir(SUMMARY_FILE)
    safe_mkdir(MARKET_STATS_FILE)

    usable.to_csv(
        OUTPUT_FILE,
        index=False
    )

    summary.to_csv(
        SUMMARY_FILE,
        index=False
    )

    market_stats.to_csv(
        MARKET_STATS_FILE,
        index=False
    )

    print()
    print("=" * 70)
    print("PHASE 17 COMPLETE")
    print("=" * 70)

    print()
    print("Saved:")
    print(f"  {OUTPUT_FILE}")
    print(f"  {SUMMARY_FILE}")
    print(f"  {MARKET_STATS_FILE}")


if __name__ == "__main__":
    main()
