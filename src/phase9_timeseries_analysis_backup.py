import os
import pandas as pd
import matplotlib.pyplot as plt


INPUT_FILE = "data/historical_market_snapshots.csv"
OUTPUT_FILE = "data/phase9_timeseries_analysis.csv"
SUMMARY_FILE = "dashboard/phase9_summary.csv"

EDGE_OVER_TIME_PNG = "dashboard/gross_edge_over_time.png"
COMBINED_ASK_PNG = "dashboard/combined_ask_over_time.png"
OBSERVATION_COUNTS_PNG = "dashboard/market_observation_counts.png"
EDGE_DISTRIBUTION_PNG = "dashboard/edge_distribution.png"


def load_data():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
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
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
        utc=True,
    )

    df["complete_orderbook"] = (
        df["complete_orderbook"]
        .astype(str)
        .str.lower()
        .eq("true")
    )

    numeric_columns = [
        "yes_ask",
        "no_ask",
        "combined_yes_no_ask",
        "gross_edge",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


def prepare_complete_data(df):
    complete = df[
        df["complete_orderbook"]
        & df["yes_ask"].notna()
        & df["no_ask"].notna()
        & df["combined_yes_no_ask"].notna()
        & df["gross_edge"].notna()
    ].copy()

    complete = complete.sort_values(
        ["question", "timestamp"]
    )

    return complete


def calculate_market_statistics(complete):
    if complete.empty:
        return pd.DataFrame()

    grouped = (
        complete
        .groupby("question")
        .agg(
            observations=("question", "size"),
            first_timestamp=("timestamp", "min"),
            last_timestamp=("timestamp", "max"),
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
            maximum_combined_ask=(
                "combined_yes_no_ask",
                "max",
            ),
            average_gross_edge=("gross_edge", "mean"),
            minimum_gross_edge=("gross_edge", "min"),
            maximum_gross_edge=("gross_edge", "max"),
            edge_std=("gross_edge", "std"),
        )
        .reset_index()
    )

    grouped["edge_std"] = grouped["edge_std"].fillna(0)

    grouped["positive_edge_observations"] = (
        complete
        .groupby("question")["gross_edge"]
        .apply(lambda x: (x > 0).sum())
        .values
    )

    grouped["edge_at_least_0_1pct"] = (
        complete
        .groupby("question")["gross_edge"]
        .apply(lambda x: (x >= 0.001).sum())
        .values
    )

    grouped["edge_at_least_0_2pct"] = (
        complete
        .groupby("question")["gross_edge"]
        .apply(lambda x: (x >= 0.002).sum())
        .values
    )

    grouped["time_span_hours"] = (
        (
            grouped["last_timestamp"]
            - grouped["first_timestamp"]
        )
        .dt.total_seconds()
        / 3600
    )

    grouped["time_span_hours"] = (
        grouped["time_span_hours"].fillna(0)
    )

    grouped["gross_arbitrage_rate"] = (
        grouped["positive_edge_observations"]
        / grouped["observations"]
    )

    grouped = grouped.sort_values(
        [
            "maximum_gross_edge",
            "average_gross_edge",
        ],
        ascending=False,
    ).reset_index(drop=True)

    grouped["research_rank"] = (
        grouped.index + 1
    )

    return grouped


def calculate_global_summary(
    raw_df,
    complete,
    market_stats,
):
    total_observations = len(raw_df)
    complete_observations = len(complete)
    incomplete_observations = (
        total_observations
        - complete_observations
    )

    if complete.empty:
        return pd.DataFrame(
            [
                {
                    "total_observations": total_observations,
                    "complete_observations": 0,
                    "incomplete_observations": incomplete_observations,
                    "unique_markets": 0,
                    "average_combined_ask": None,
                    "minimum_combined_ask": None,
                    "maximum_combined_ask": None,
                    "average_gross_edge": None,
                    "minimum_gross_edge": None,
                    "maximum_gross_edge": None,
                    "gross_edge_std": None,
                    "positive_edge_observations": 0,
                    "gross_arbitrage_rate": None,
                    "markets_with_positive_edge": 0,
                    "markets_analyzed": 0,
                }
            ]
        )

    positive_edges = (
        complete["gross_edge"] > 0
    ).sum()

    markets_with_positive_edge = (
        complete.loc[
            complete["gross_edge"] > 0,
            "question",
        ]
        .nunique()
    )

    summary = {
        "total_observations": total_observations,
        "complete_observations": complete_observations,
        "incomplete_observations": incomplete_observations,
        "unique_markets": raw_df["question"].nunique(),
        "markets_analyzed": complete["question"].nunique(),
        "average_combined_ask": complete[
            "combined_yes_no_ask"
        ].mean(),
        "minimum_combined_ask": complete[
            "combined_yes_no_ask"
        ].min(),
        "maximum_combined_ask": complete[
            "combined_yes_no_ask"
        ].max(),
        "average_gross_edge": complete[
            "gross_edge"
        ].mean(),
        "minimum_gross_edge": complete[
            "gross_edge"
        ].min(),
        "maximum_gross_edge": complete[
            "gross_edge"
        ].max(),
        "gross_edge_std": complete[
            "gross_edge"
        ].std(),
        "positive_edge_observations": positive_edges,
        "gross_arbitrage_rate": (
            positive_edges
            / complete_observations
        ),
        "markets_with_positive_edge": (
            markets_with_positive_edge
        ),
    }

    return pd.DataFrame([summary])


def generate_edge_over_time(complete):
    plt.figure(figsize=(12, 6))

    for question, group in complete.groupby(
        "question"
    ):
        group = group.sort_values("timestamp")

        plt.plot(
            group["timestamp"],
            group["gross_edge"],
            marker="o",
            label=question,
        )

    plt.axhline(
        0,
        linestyle="--",
        linewidth=1,
    )

    plt.title(
        "Gross Arbitrage Edge Over Time"
    )
    plt.xlabel("Timestamp")
    plt.ylabel(
        "Gross Edge = 1 - YES Ask - NO Ask"
    )

    if complete["question"].nunique() <= 10:
        plt.legend(
            fontsize=7,
            loc="best",
        )

    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(
        EDGE_OVER_TIME_PNG,
        dpi=150,
    )
    plt.close()


def generate_combined_ask_chart(complete):
    plt.figure(figsize=(12, 6))

    for question, group in complete.groupby(
        "question"
    ):
        group = group.sort_values("timestamp")

        plt.plot(
            group["timestamp"],
            group["combined_yes_no_ask"],
            marker="o",
            label=question,
        )

    plt.axhline(
        1.0,
        linestyle="--",
        linewidth=1,
    )

    plt.title(
        "YES + NO Combined Ask Over Time"
    )
    plt.xlabel("Timestamp")
    plt.ylabel(
        "Combined Ask"
    )

    if complete["question"].nunique() <= 10:
        plt.legend(
            fontsize=7,
            loc="best",
        )

    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(
        COMBINED_ASK_PNG,
        dpi=150,
    )
    plt.close()


def generate_observation_counts(market_stats):
    if market_stats.empty:
        return

    plot_data = market_stats.sort_values(
        "observations",
        ascending=True,
    )

    plt.figure(figsize=(10, 6))

    plt.barh(
        plot_data["question"],
        plot_data["observations"],
    )

    plt.title(
        "Complete Historical Observations by Market"
    )
    plt.xlabel("Observations")
    plt.ylabel("Market")

    plt.tight_layout()
    plt.savefig(
        OBSERVATION_COUNTS_PNG,
        dpi=150,
    )
    plt.close()


def generate_edge_distribution(complete):
    plt.figure(figsize=(10, 6))

    plt.hist(
        complete["gross_edge"],
        bins=20,
    )

    plt.axvline(
        0,
        linestyle="--",
        linewidth=1,
    )

    plt.title(
        "Distribution of Gross Arbitrage Edge"
    )
    plt.xlabel("Gross Edge")
    plt.ylabel("Frequency")

    plt.tight_layout()
    plt.savefig(
        EDGE_DISTRIBUTION_PNG,
        dpi=150,
    )
    plt.close()


def print_summary(
    raw_df,
    complete,
    summary,
    market_stats,
):
    row = summary.iloc[0]

    print("=" * 70)
    print("PHASE 9 - HISTORICAL TIME-SERIES ANALYSIS")
    print("=" * 70)
    print()

    print("DATA QUALITY")
    print("-" * 70)
    print(
        f"Total observations: "
        f"{int(row['total_observations'])}"
    )
    print(
        f"Complete observations: "
        f"{int(row['complete_observations'])}"
    )
    print(
        f"Incomplete observations: "
        f"{int(row['incomplete_observations'])}"
    )
    print(
        f"Unique markets: "
        f"{int(row['unique_markets'])}"
    )
    print(
        f"Markets analyzed: "
        f"{int(row['markets_analyzed'])}"
    )
    print()

    print("GROSS EDGE STATISTICS")
    print("-" * 70)

    if pd.isna(row["average_gross_edge"]):
        print("No complete observations available.")
    else:
        print(
            f"Average gross edge: "
            f"{row['average_gross_edge']:.6f}"
        )
        print(
            f"Minimum gross edge: "
            f"{row['minimum_gross_edge']:.6f}"
        )
        print(
            f"Maximum gross edge: "
            f"{row['maximum_gross_edge']:.6f}"
        )
        print(
            f"Gross edge std dev: "
            f"{row['gross_edge_std']:.6f}"
        )
        print(
            f"Positive-edge observations: "
            f"{int(row['positive_edge_observations'])}"
        )
        print(
            f"Gross arbitrage rate: "
            f"{row['gross_arbitrage_rate']:.4%}"
        )

    print()

    print("TOP MARKETS BY HISTORICAL SIGNAL")
    print("-" * 70)

    if market_stats.empty:
        print("No complete market observations.")
    else:
        columns = [
            "question",
            "observations",
            "average_combined_ask",
            "minimum_combined_ask",
            "maximum_gross_edge",
            "positive_edge_observations",
            "gross_arbitrage_rate",
            "research_rank",
        ]

        print(
            market_stats[
                columns
            ]
            .head(10)
            .to_string(index=False)
        )

    print()


def main():
    os.makedirs("data", exist_ok=True)
    os.makedirs("dashboard", exist_ok=True)

    print("=" * 70)
    print("PHASE 9 - HISTORICAL TIME-SERIES ANALYSIS")
    print("=" * 70)
    print()

    raw_df = load_data()

    print(
        f"Rows loaded: {len(raw_df)}"
    )

    complete = prepare_complete_data(
        raw_df
    )

    print(
        f"Complete observations used: "
        f"{len(complete)}"
    )
    print()

    market_stats = (
        calculate_market_statistics(
            complete
        )
    )

    summary = calculate_global_summary(
        raw_df,
        complete,
        market_stats,
    )

    print_summary(
        raw_df,
        complete,
        summary,
        market_stats,
    )

    if not complete.empty:
        generate_edge_over_time(
            complete
        )

        generate_combined_ask_chart(
            complete
        )

        generate_observation_counts(
            market_stats
        )

        generate_edge_distribution(
            complete
        )

        print(
            "Saved:",
            EDGE_OVER_TIME_PNG,
        )
        print(
            "Saved:",
            COMBINED_ASK_PNG,
        )
        print(
            "Saved:",
            OBSERVATION_COUNTS_PNG,
        )
        print(
            "Saved:",
            EDGE_DISTRIBUTION_PNG,
        )
        print()

    market_stats.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    summary.to_csv(
        SUMMARY_FILE,
        index=False,
    )

    print("=" * 70)
    print("PHASE 9 COMPLETE")
    print("=" * 70)
    print()
    print(
        "Saved time-series analysis to:"
    )
    print(OUTPUT_FILE)
    print()
    print(
        "Saved summary to:"
    )
    print(SUMMARY_FILE)
    print()

    if complete.empty:
        print(
            "No complete historical observations "
            "were available for analysis."
        )
    elif (
        complete["gross_edge"] > 0
    ).sum() == 0:
        print(
            "No positive gross arbitrage edges "
            "were observed in the complete dataset."
        )
    else:
        print(
            "Positive gross-edge observations "
            "were detected and included in the analysis."
        )


if __name__ == "__main__":
    main()
