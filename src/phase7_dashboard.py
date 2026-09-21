import os
import pandas as pd
import matplotlib.pyplot as plt


INPUT_FILE = "arbitrage_opportunity_ranking.csv"
OUTPUT_DIR = "dashboard"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Could not find {INPUT_FILE}. "
            "Run Phase 6 first."
        )

    df = pd.read_csv(INPUT_FILE)

    return df


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

def create_output_directory():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

def print_summary(df):

    executable = len(df)

    gross_profitable = int(
        (df["gross_profit"] > 0).sum()
    )

    net_profitable = int(
        (df["net_profit"] > 0).sum()
    )

    fully_filled = int(
        (df["status"] == "fully_filled").sum()
    )

    print()
    print("=" * 70)
    print("PHASE 7 - QUANT RESEARCH DASHBOARD")
    print("=" * 70)

    print()
    print("DATASET")
    print("-" * 70)

    print(f"Rows analyzed:              {len(df):,}")
    print(f"Fully executable scenarios: {fully_filled:,}")
    print(f"Gross profitable scenarios: {gross_profitable:,}")
    print(f"Net profitable scenarios:   {net_profitable:,}")

    print()
    print("PROFITABILITY")
    print("-" * 70)

    print(
        f"Maximum gross P/L:          "
        f"${df['gross_profit'].max():,.4f}"
    )

    print(
        f"Maximum net P/L:            "
        f"${df['net_profit'].max():,.4f}"
    )

    print(
        f"Minimum net P/L:            "
        f"${df['net_profit'].min():,.4f}"
    )

    print(
        f"Average gross P/L:          "
        f"${df['gross_profit'].mean():,.4f}"
    )

    print(
        f"Average net P/L:            "
        f"${df['net_profit'].mean():,.4f}"
    )

    print()
    print("ROI")
    print("-" * 70)

    print(
        f"Maximum gross ROI:          "
        f"{df['gross_profit_pct'].max():.4f}%"
    )

    print(
        f"Maximum net ROI:            "
        f"{df['net_roi_pct'].max():.4f}%"
    )

    print(
        f"Average net ROI:            "
        f"{df['net_roi_pct'].mean():.4f}%"
    )

    print()
    print("COST MODEL")
    print("-" * 70)

    print(
        f"Average estimated fees:     "
        f"${df['estimated_fee'].mean():.4f}"
    )

    print(
        f"Average slippage buffer:    "
        f"${df['slippage_buffer'].mean():.4f}"
    )

    print()


# ============================================================
# TOP SCENARIOS
# ============================================================

def print_top_scenarios(df):

    print("=" * 70)
    print("TOP 10 SCENARIOS BY NET PROFIT")
    print("=" * 70)

    columns = [
        "question",
        "quantity",
        "total_cost",
        "gross_profit",
        "estimated_fee",
        "slippage_buffer",
        "net_profit",
        "net_roi_pct",
    ]

    top = (
        df.sort_values(
            "net_profit",
            ascending=False
        )
        .head(10)
    )

    display_df = top[columns].copy()

    display_df["question"] = (
        display_df["question"]
        .str.slice(0, 65)
    )

    print(
        display_df.to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}"
        )
    )

    print()


# ============================================================
# PROFITABILITY CHART
# ============================================================

def create_profit_chart(df):

    plt.figure(figsize=(10, 6))

    plt.hist(
        df["net_profit"],
        bins=30
    )

    plt.axvline(
        0,
        linestyle="--"
    )

    plt.title("Distribution of Net Profit")
    plt.xlabel("Net Profit ($)")
    plt.ylabel("Number of Scenarios")

    plt.tight_layout()

    path = os.path.join(
        OUTPUT_DIR,
        "net_profit_distribution.png"
    )

    plt.savefig(
        path,
        dpi=150
    )

    plt.close()

    print(f"Saved: {path}")


# ============================================================
# ROI CHART
# ============================================================

def create_roi_chart(df):

    plt.figure(figsize=(10, 6))

    plt.hist(
        df["net_roi_pct"],
        bins=30
    )

    plt.axvline(
        0,
        linestyle="--"
    )

    plt.title("Distribution of Net ROI")
    plt.xlabel("Net ROI (%)")
    plt.ylabel("Number of Scenarios")

    plt.tight_layout()

    path = os.path.join(
        OUTPUT_DIR,
        "net_roi_distribution.png"
    )

    plt.savefig(
        path,
        dpi=150
    )

    plt.close()

    print(f"Saved: {path}")


# ============================================================
# GROSS VS NET PROFIT
# ============================================================

def create_gross_vs_net_chart(df):

    sample = (
        df.sort_values(
            "net_profit",
            ascending=False
        )
        .head(25)
        .copy()
    )

    plt.figure(figsize=(12, 7))

    x = range(len(sample))

    plt.plot(
        x,
        sample["gross_profit"],
        marker="o",
        label="Gross Profit"
    )

    plt.plot(
        x,
        sample["net_profit"],
        marker="o",
        label="Net Profit"
    )

    plt.axhline(
        0,
        linestyle="--"
    )

    plt.title(
        "Gross Profit vs Net Profit - Top 25 Scenarios"
    )

    plt.xlabel("Scenario")
    plt.ylabel("Profit ($)")

    plt.legend()

    plt.tight_layout()

    path = os.path.join(
        OUTPUT_DIR,
        "gross_vs_net_profit.png"
    )

    plt.savefig(
        path,
        dpi=150
    )

    plt.close()

    print(f"Saved: {path}")


# ============================================================
# POSITION SIZE ANALYSIS
# ============================================================

def create_position_size_chart(df):

    grouped = (
        df.groupby("quantity")
        .agg(
            average_net_profit=(
                "net_profit",
                "mean"
            ),
            maximum_net_profit=(
                "net_profit",
                "max"
            ),
            scenarios=(
                "net_profit",
                "count"
            ),
        )
        .reset_index()
    )

    plt.figure(figsize=(10, 6))

    plt.plot(
        grouped["quantity"],
        grouped["average_net_profit"],
        marker="o",
        label="Average Net Profit"
    )

    plt.plot(
        grouped["quantity"],
        grouped["maximum_net_profit"],
        marker="o",
        label="Maximum Net Profit"
    )

    plt.axhline(
        0,
        linestyle="--"
    )

    plt.title(
        "Net Profit by Position Size"
    )

    plt.xlabel("Position Size ($)")
    plt.ylabel("Net Profit ($)")

    plt.legend()

    plt.tight_layout()

    path = os.path.join(
        OUTPUT_DIR,
        "position_size_analysis.png"
    )

    plt.savefig(
        path,
        dpi=150
    )

    plt.close()

    print(f"Saved: {path}")


# ============================================================
# COST IMPACT ANALYSIS
# ============================================================

def create_cost_impact_chart(df):

    grouped = (
        df.groupby("quantity")
        .agg(
            gross_profit=(
                "gross_profit",
                "mean"
            ),
            estimated_fee=(
                "estimated_fee",
                "mean"
            ),
            slippage_buffer=(
                "slippage_buffer",
                "mean"
            ),
            net_profit=(
                "net_profit",
                "mean"
            ),
        )
        .reset_index()
    )

    plt.figure(figsize=(11, 7))

    plt.plot(
        grouped["quantity"],
        grouped["gross_profit"],
        marker="o",
        label="Gross Profit"
    )

    plt.plot(
        grouped["quantity"],
        grouped["estimated_fee"],
        marker="o",
        label="Estimated Fees"
    )

    plt.plot(
        grouped["quantity"],
        grouped["slippage_buffer"],
        marker="o",
        label="Slippage Buffer"
    )

    plt.plot(
        grouped["quantity"],
        grouped["net_profit"],
        marker="o",
        label="Net Profit"
    )

    plt.axhline(
        0,
        linestyle="--"
    )

    plt.title(
        "Impact of Trading Costs"
    )

    plt.xlabel("Position Size ($)")
    plt.ylabel("Dollar Value ($)")

    plt.legend()

    plt.tight_layout()

    path = os.path.join(
        OUTPUT_DIR,
        "cost_impact_analysis.png"
    )

    plt.savefig(
        path,
        dpi=150
    )

    plt.close()

    print(f"Saved: {path}")


# ============================================================
# EXECUTION STATUS
# ============================================================

def create_execution_status_chart(df):

    status_counts = (
        df["status"]
        .value_counts()
    )

    plt.figure(figsize=(8, 6))

    status_counts.plot(
        kind="bar"
    )

    plt.title(
        "Execution Status"
    )

    plt.xlabel("Execution Status")
    plt.ylabel("Number of Scenarios")

    plt.xticks(
        rotation=0
    )

    plt.tight_layout()

    path = os.path.join(
        OUTPUT_DIR,
        "execution_status.png"
    )

    plt.savefig(
        path,
        dpi=150
    )

    plt.close()

    print(f"Saved: {path}")


# ============================================================
# RESEARCH CSV EXPORTS
# ============================================================

def save_research_tables(df):

    top_net = (
        df.sort_values(
            "net_profit",
            ascending=False
        )
        .head(25)
    )

    top_roi = (
        df.sort_values(
            "net_roi_pct",
            ascending=False
        )
        .head(25)
    )

    profitable = df[
        df["net_profit"] > 0
    ].copy()

    top_net_path = os.path.join(
        OUTPUT_DIR,
        "top_25_net_profit.csv"
    )

    top_roi_path = os.path.join(
        OUTPUT_DIR,
        "top_25_net_roi.csv"
    )

    profitable_path = os.path.join(
        OUTPUT_DIR,
        "net_profitable_scenarios.csv"
    )

    top_net.to_csv(
        top_net_path,
        index=False
    )

    top_roi.to_csv(
        top_roi_path,
        index=False
    )

    profitable.to_csv(
        profitable_path,
        index=False
    )

    print(f"Saved: {top_net_path}")
    print(f"Saved: {top_roi_path}")
    print(f"Saved: {profitable_path}")


# ============================================================
# RESEARCH CONCLUSION
# ============================================================

def print_research_conclusion(df):

    gross_profitable = int(
        (df["gross_profit"] > 0).sum()
    )

    net_profitable = int(
        (df["net_profit"] > 0).sum()
    )

    print()
    print("=" * 70)
    print("RESEARCH CONCLUSION")
    print("=" * 70)

    print()

    if gross_profitable == 0:

        print(
            "No gross YES + NO arbitrage opportunities "
            "were identified in the tested executable scenarios."
        )

    else:

        print(
            f"{gross_profitable} scenarios showed positive "
            "gross profit before estimated trading costs."
        )

    print()

    if net_profitable == 0:

        print(
            "No scenario produced positive modeled net profit "
            "after the configured fee and slippage assumptions."
        )

    else:

        print(
            f"{net_profitable} scenarios produced positive "
            "modeled net profit after estimated costs."
        )

    print()

    print(
        "Interpretation: the absence of profitable scenarios "
        "is itself a research result. The engine evaluates "
        "whether apparent pricing discrepancies survive "
        "execution constraints and estimated trading costs."
    )

    print()

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("LOADING RESEARCH DATASET")
    print("=" * 70)

    df = load_data()

    create_output_directory()

    print(
        f"Dataset loaded successfully: "
        f"{len(df):,} rows"
    )

    print()

    print_summary(df)

    print_top_scenarios(df)

    print("=" * 70)
    print("GENERATING RESEARCH VISUALIZATIONS")
    print("=" * 70)

    create_profit_chart(df)

    create_roi_chart(df)

    create_gross_vs_net_chart(df)

    create_position_size_chart(df)

    create_cost_impact_chart(df)

    create_execution_status_chart(df)

    print()

    print("=" * 70)
    print("EXPORTING RESEARCH TABLES")
    print("=" * 70)

    save_research_tables(df)

    print_research_conclusion(df)

    print()
    print("PHASE 7 COMPLETE")
    print()
    print(f"Dashboard files saved inside: {OUTPUT_DIR}/")
    print()


if __name__ == "__main__":
    main()
