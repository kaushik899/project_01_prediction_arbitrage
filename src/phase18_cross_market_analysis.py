"""
PHASE 18 - CROSS-MARKET / STATISTICAL MISPRICING ANALYSIS

Analyzes complete observations from Phase 16 for:

- Price movement
- Gross-edge movement
- Combined YES/NO ask deviations
- Volatility
- Temporary deviations
- Potential mean reversion
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = Path("data/phase16_live_monitor.csv")
OUTPUT_FILE = Path("data/phase18_cross_market_analysis.csv")

PLOT_DIR = Path("data/phase18_plots")

FEE_COST = 0.001
SLIPPAGE_COST = 0.001

WINDOW = 5


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("PHASE 18 - CROSS-MARKET / STATISTICAL MISPRICING ANALYSIS")
print("=" * 70)

print()
print("Loading:", INPUT_FILE)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

print(f"Raw observations: {len(df)}")


# ============================================================
# REMOVE INCOMPLETE / ERROR ROWS
# ============================================================

complete = df[
    df["status"].isin(
        ["NO_OPPORTUNITY", "OPPORTUNITY"]
    )
].copy()

print()
print("VALID OBSERVATIONS")
print("-" * 70)

print(f"Complete observations: {len(complete)}")
print(
    f"Unique markets: "
    f"{complete['question'].nunique()}"
)
print()

if len(complete) == 0:
    print("No complete observations available.")
    print("Phase 18 cannot perform statistical analysis yet.")
    raise SystemExit(0)


# ============================================================
# SORT BY MARKET AND TIME
# ============================================================

complete["timestamp"] = pd.to_datetime(
    complete["timestamp"],
    errors="coerce",
    utc=True
)

complete = complete.sort_values(
    ["question", "timestamp"]
).reset_index(drop=True)


# ============================================================
# NUMERIC COLUMNS
# ============================================================

numeric_columns = [
    "yes_bid",
    "yes_ask",
    "no_bid",
    "no_ask",
    "combined_yes_no_ask",
    "gross_edge",
    "fee_cost",
    "slippage_cost",
    "total_cost",
    "net_edge",
]

for column in numeric_columns:
    if column in complete.columns:
        complete[column] = pd.to_numeric(
            complete[column],
            errors="coerce"
        )


# ============================================================
# CALCULATE MARKET MOVEMENT
# ============================================================

complete["yes_move"] = (
    complete
    .groupby("question")["yes_ask"]
    .diff()
)

complete["no_move"] = (
    complete
    .groupby("question")["no_ask"]
    .diff()
)

complete["combined_ask_move"] = (
    complete
    .groupby("question")["combined_yes_no_ask"]
    .diff()
)

complete["gross_edge_move"] = (
    complete
    .groupby("question")["gross_edge"]
    .diff()
)


# ============================================================
# ABSOLUTE MOVEMENTS
# ============================================================

complete["abs_yes_change"] = (
    complete["yes_move"].abs()
)

complete["abs_no_change"] = (
    complete["no_move"].abs()
)

complete["abs_combined_change"] = (
    complete["combined_ask_move"].abs()
)

complete["abs_gross_edge_change"] = (
    complete["gross_edge_move"].abs()
)


# ============================================================
# ROLLING VOLATILITY
# ============================================================

complete["yes_ask_std_5"] = (
    complete
    .groupby("question")["yes_ask"]
    .transform(
        lambda x: x.rolling(
            WINDOW,
            min_periods=2
        ).std()
    )
)

complete["no_ask_std_5"] = (
    complete
    .groupby("question")["no_ask"]
    .transform(
        lambda x: x.rolling(
            WINDOW,
            min_periods=2
        ).std()
    )
)

complete["combined_ask_std_5"] = (
    complete
    .groupby("question")["combined_yes_no_ask"]
    .transform(
        lambda x: x.rolling(
            WINDOW,
            min_periods=2
        ).std()
    )
)

complete["gross_edge_std_5"] = (
    complete
    .groupby("question")["gross_edge"]
    .transform(
        lambda x: x.rolling(
            WINDOW,
            min_periods=2
        ).std()
    )
)


# ============================================================
# ROLLING MEANS
# ============================================================

complete["combined_ask_mean_5"] = (
    complete
    .groupby("question")["combined_yes_no_ask"]
    .transform(
        lambda x: x.rolling(
            WINDOW,
            min_periods=2
        ).mean()
    )
)

complete["gross_edge_mean_5"] = (
    complete
    .groupby("question")["gross_edge"]
    .transform(
        lambda x: x.rolling(
            WINDOW,
            min_periods=2
        ).mean()
    )
)

# ============================================================
# DEVIATION FROM ROLLING MEAN
# ============================================================

complete["combined_ask_deviation"] = (
    complete["combined_yes_no_ask"]
    - complete["combined_ask_mean_5"]
)

complete["gross_edge_deviation"] = (
    complete["gross_edge"]
    - complete["gross_edge_mean_5"]
)


# ============================================================
# Z-SCORES
# ============================================================

complete["combined_ask_zscore"] = np.where(
    complete["combined_ask_std_5"] > 0,
    complete["combined_ask_deviation"]
    / complete["combined_ask_std_5"],
    np.nan
)

complete["gross_edge_zscore"] = np.where(
    complete["gross_edge_std_5"] > 0,
    complete["gross_edge_deviation"]
    / complete["gross_edge_std_5"],
    np.nan
)


# ============================================================
# DISTANCE FROM FAIR COMPLEMENT
# ============================================================

complete["distance_from_one"] = (
    complete["combined_yes_no_ask"] - 1.0
)

complete["below_one"] = (
    complete["combined_yes_no_ask"] < 1.0
)

complete["at_one"] = (
    complete["combined_yes_no_ask"] == 1.0
)

complete["above_one"] = (
    complete["combined_yes_no_ask"] > 1.0
)


# ============================================================
# RE-CALCULATE EDGE FOR VALIDATION
# ============================================================

complete["calculated_gross_edge"] = (
    1.0 - complete["combined_yes_no_ask"]
)

complete["calculated_net_edge"] = (
    complete["calculated_gross_edge"]
    - FEE_COST
    - SLIPPAGE_COST
)


# ============================================================
# OPPORTUNITY VALIDATION
# ============================================================

complete["calculated_opportunity"] = (
    complete["calculated_net_edge"] > 0
)


# ============================================================
# BASIC STATISTICS
# ============================================================

print("=" * 70)
print("BASIC STATISTICS")
print("=" * 70)

print()

print(
    "YES ASK:"
)

print(
    complete["yes_ask"]
    .describe()
    .to_string()
)

print()

print(
    "NO ASK:"
)

print(
    complete["no_ask"]
    .describe()
    .to_string()
)

print()

print(
    "COMBINED YES + NO ASK:"
)

print(
    complete["combined_yes_no_ask"]
    .describe()
    .to_string()
)

print()

print(
    "GROSS EDGE:"
)

print(
    complete["gross_edge"]
    .describe()
    .to_string()
)

print()

print(
    "NET EDGE:"
)

print(
    complete["net_edge"]
    .describe()
    .to_string()
)


# ============================================================
# ARBITRAGE CHECK
# ============================================================

below_one = (
    complete["combined_yes_no_ask"] < 1.0
).sum()

at_one = (
    complete["combined_yes_no_ask"] == 1.0
).sum()

above_one = (
    complete["combined_yes_no_ask"] > 1.0
).sum()

print()
print("=" * 70)
print("COMBINED ASK ANALYSIS")
print("=" * 70)

print(
    f"Combined ask < 1.000: {below_one}"
)

print(
    f"Combined ask = 1.000: {at_one}"
)

print(
    f"Combined ask > 1.000: {above_one}"
)


# ============================================================
# OPPORTUNITIES
# ============================================================

opportunities = complete[
    complete["calculated_opportunity"]
].copy()

print()
print("=" * 70)
print("ARBITRAGE OPPORTUNITIES")
print("=" * 70)

print(
    f"Potential opportunities: "
    f"{len(opportunities)}"
)

if len(opportunities) > 0:

    print()

    display_columns = [
        "timestamp",
        "question",
        "yes_ask",
        "no_ask",
        "combined_yes_no_ask",
        "gross_edge",
        "net_edge",
    ]

    print(
        opportunities[
            display_columns
        ]
        .head(20)
        .to_string(index=False)
    )

else:

    print(
        "No observations have positive net edge "
        "after fees and slippage."
    )


# ============================================================
# BEST OBSERVATIONS BY GROSS EDGE
# ============================================================

print()
print("=" * 70)
print("BEST OBSERVATIONS BY GROSS EDGE")
print("=" * 70)

best_columns = [
    "timestamp",
    "question",
    "yes_ask",
    "no_ask",
    "combined_yes_no_ask",
    "gross_edge",
    "net_edge",
]

print(
    complete
    .sort_values(
        "gross_edge",
        ascending=False
    )
    [best_columns]
    .head(20)
    .to_string(index=False)
)


# ============================================================
# MARKET-LEVEL SUMMARY
# ============================================================

market_summary = (
    complete
    .groupby("question")
    .agg(
        observations=(
            "question",
            "size"
        ),
        mean_yes_ask=(
            "yes_ask",
            "mean"
        ),
        mean_no_ask=(
            "no_ask",
            "mean"
        ),
        mean_combined_ask=(
            "combined_yes_no_ask",
            "mean"
        ),
        min_combined_ask=(
            "combined_yes_no_ask",
            "min"
        ),
        max_combined_ask=(
            "combined_yes_no_ask",
            "max"
        ),
        mean_gross_edge=(
            "gross_edge",
            "mean"
        ),
        max_gross_edge=(
            "gross_edge",
            "max"
        ),
        mean_net_edge=(
            "net_edge",
            "mean"
        ),
    )
    .reset_index()
)


# ============================================================
# MARKET SUMMARY
# ============================================================

print()
print("=" * 70)
print("MARKET SUMMARY")
print("=" * 70)

print(
    f"Markets analyzed: "
    f"{len(market_summary)}"
)

print()

print(
    market_summary
    .sort_values(
        "max_gross_edge",
        ascending=False
    )
    .head(20)
    .to_string(index=False)
)


# ============================================================
# SAVE ANALYSIS
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

complete.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("=" * 70)
print("PHASE 18 DATA SAVED")
print("=" * 70)

print(
    f"Output: {OUTPUT_FILE}"
)

print(
    f"Rows: {len(complete)}"
)

print(
    f"Markets: "
    f"{complete['question'].nunique()}"
)


# ============================================================
# CREATE PLOT DIRECTORY
# ============================================================

PLOT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# PLOT 1 - COMBINED ASK DISTRIBUTION
# ============================================================

plt.figure(figsize=(10, 6))

plt.hist(
    complete["combined_yes_no_ask"].dropna(),
    bins=30
)

plt.axvline(
    1.0,
    linestyle="--",
    label="Fair complement = 1.0"
)

plt.xlabel(
    "Combined YES + NO Ask"
)

plt.ylabel(
    "Frequency"
)

plt.title(
    "Distribution of Combined YES/NO Ask"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    PLOT_DIR / "combined_ask_distribution.png"
)

plt.close()


# ============================================================
# PLOT 2 - GROSS EDGE DISTRIBUTION
# ============================================================

plt.figure(figsize=(10, 6))

plt.hist(
    complete["gross_edge"].dropna(),
    bins=30
)

plt.axvline(
    0.0,
    linestyle="--",
    label="Zero gross edge"
)

plt.xlabel(
    "Gross Edge"
)

plt.ylabel(
    "Frequency"
)

plt.title(
    "Distribution of Gross Edge"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    PLOT_DIR / "gross_edge_distribution.png"
)

plt.close()


# ============================================================
# PLOT 3 - NET EDGE DISTRIBUTION
# ============================================================

plt.figure(figsize=(10, 6))

plt.hist(
    complete["net_edge"].dropna(),
    bins=30
)

plt.axvline(
    0.0,
    linestyle="--",
    label="Zero net edge"
)

plt.xlabel(
    "Net Edge"
)

plt.ylabel(
    "Frequency"
)

plt.title(
    "Distribution of Net Edge"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    PLOT_DIR / "net_edge_distribution.png"
)

plt.close()


# ============================================================
# FINAL VALIDATION
# ============================================================

print()
print("=" * 70)
print("FINAL VALIDATION")
print("=" * 70)

print(
    "Complete rows:",
    len(complete)
)

print(
    "Unique markets:",
    complete["question"].nunique()
)

print(
    "Combined ask below 1:",
    below_one
)

print(
    "Positive gross edge:",
    (
        complete["gross_edge"] > 0
    ).sum()
)

print(
    "Positive net edge:",
    (
        complete["net_edge"] > 0
    ).sum()
)

print()
print("Phase 18 completed successfully.")
