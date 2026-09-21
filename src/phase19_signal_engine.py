"""
PHASE 19 - ARBITRAGE SIGNAL ENGINE

Reads Phase 16 live observations and identifies:
- NEAR_ARBITRAGE
- PRICE_MOVEMENT
- EDGE_MOVEMENT
- WATCHLIST
- QUALIFIED opportunities

This phase DOES NOT execute trades.
"""

from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = Path("data/phase16_live_monitor.csv")

OUTPUT_FILE = Path("data/phase19_signal_engine.csv")
SUMMARY_FILE = Path("dashboard/phase19_summary.csv")
MARKET_STATS_FILE = Path("dashboard/phase19_market_stats.csv")

FEE_RATE = 0.001
SLIPPAGE_RATE = 0.001
TOTAL_COST = FEE_RATE + SLIPPAGE_RATE

# Existing configured requirement
MIN_NET_EDGE = 0.002

# Watchlist thresholds
NEAR_GROSS_EDGE = 0.000
PRICE_MOVE_THRESHOLD = 0.005
EDGE_MOVE_THRESHOLD = 0.003


# ============================================================
# HELPERS
# ============================================================

def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def classify_signal(row):
    gross_edge = safe_float(row["latest_gross_edge"])
    net_edge = safe_float(row["latest_net_edge"])

    yes_move = safe_float(row["yes_move"])
    no_move = safe_float(row["no_move"])
    edge_move = safe_float(row["gross_edge_move"])

    signals = []

    if pd.notna(net_edge) and net_edge >= MIN_NET_EDGE:
        signals.append("QUALIFIED")

    if pd.notna(gross_edge) and gross_edge >= NEAR_GROSS_EDGE:
        signals.append("NEAR_ARBITRAGE")

    if (
        (pd.notna(yes_move) and yes_move >= PRICE_MOVE_THRESHOLD)
        or
        (pd.notna(no_move) and no_move >= PRICE_MOVE_THRESHOLD)
    ):
        signals.append("PRICE_MOVEMENT")

    if pd.notna(edge_move) and abs(edge_move) >= EDGE_MOVE_THRESHOLD:
        signals.append("EDGE_MOVEMENT")

    if signals:
        return "|".join(signals)

    return "NO_SIGNAL"
# ============================================================
# LOAD DATA
# ============================================================

print()
print("=" * 70)
print("PHASE 19 - ARBITRAGE SIGNAL ENGINE")
print("=" * 70)
print()

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

print("RAW DATA")
print("-" * 70)
print(f"Total observations: {len(df)}")

required_columns = [
    "timestamp",
    "question",
    "yes_ask",
    "no_ask",
    "gross_edge",
    "net_edge",
    "status",
]

missing = [
    col for col in required_columns
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )

print()


# ============================================================
# CLEAN DATA
# ============================================================

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

numeric_columns = [
    "yes_ask",
    "no_ask",
    "gross_edge",
    "net_edge",
]

for col in numeric_columns:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df = df.sort_values(
    ["question", "timestamp"]
).reset_index(drop=True)


# ============================================================
# REMOVE INCOMPLETE / ERROR ROWS
# ============================================================

complete = df[
    (df["status"] != "INCOMPLETE")
    &
    (df["status"] != "ERROR")
].copy()

print("VALID OBSERVATIONS")
print("-" * 70)
print(f"Complete observations: {len(complete)}")
print(
    f"Unique markets: "
    f"{complete['question'].nunique()}"
)
print()


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

complete["gross_edge_move"] = (
    complete
    .groupby("question")["gross_edge"]
    .diff()
)

complete["net_edge_move"] = (
    complete
    .groupby("question")["net_edge"]
    .diff()
)

complete["yes_move_abs"] = complete["yes_move"].abs()
complete["no_move_abs"] = complete["no_move"].abs()
complete["gross_edge_move_abs"] = (
    complete["gross_edge_move"].abs()
)


# ============================================================
# MARKET STATISTICS
# ============================================================

market_stats = (
    complete
    .groupby("question")
    .agg(
        observations=("question", "size"),

        yes_min=("yes_ask", "min"),
        yes_max=("yes_ask", "max"),

        no_min=("no_ask", "min"),
        no_max=("no_ask", "max"),

        gross_min=("gross_edge", "min"),
        gross_max=("gross_edge", "max"),

        net_min=("net_edge", "min"),
        net_max=("net_edge", "max"),

        max_yes_move=("yes_move_abs", "max"),
        max_no_move=("no_move_abs", "max"),

        max_gross_edge_move=(
            "gross_edge_move_abs",
            "max"
        ),

        average_gross_edge=(
            "gross_edge",
            "mean"
        ),

        average_net_edge=(
            "net_edge",
            "mean"
        ),
    )
    .reset_index()
)

market_stats["yes_range"] = (
    market_stats["yes_max"]
    - market_stats["yes_min"]
)

market_stats["no_range"] = (
    market_stats["no_max"]
    - market_stats["no_min"]
)

market_stats["gross_edge_range"] = (
    market_stats["gross_max"]
    - market_stats["gross_min"]
)

market_stats["net_edge_range"] = (
    market_stats["net_max"]
    - market_stats["net_min"]
)


# ============================================================
# ADD CURRENT MARKET INFORMATION
# ============================================================

latest = (
    complete
    .sort_values("timestamp")
    .groupby("question")
    .tail(1)
    .copy()
)

latest_columns = [
    "question",
    "timestamp",
    "yes_ask",
    "no_ask",
    "gross_edge",
    "net_edge",
]

latest = latest[latest_columns].rename(
    columns={
        "timestamp": "latest_timestamp",
        "yes_ask": "latest_yes_ask",
        "no_ask": "latest_no_ask",
        "gross_edge": "latest_gross_edge",
        "net_edge": "latest_net_edge",
    }
)

market_stats = market_stats.merge(
    latest,
    on="question",
    how="left"
)


# ============================================================
# SIGNAL CLASSIFICATION
# ============================================================

market_stats["yes_move"] = (
    market_stats["yes_max"]
    - market_stats["yes_min"]
)

market_stats["no_move"] = (
    market_stats["no_max"]
    - market_stats["no_min"]
)

market_stats["gross_edge_move"] = (
    market_stats["gross_max"]
    - market_stats["gross_min"]
)

market_stats["net_edge_move"] = (
    market_stats["net_max"]
    - market_stats["net_min"]
)

market_stats["signal"] = market_stats.apply(
    classify_signal,
    axis=1
)

market_stats["watchlist"] = (
    market_stats["signal"] != "NO_SIGNAL"
)


# ============================================================
# RANK WATCHLIST
# ============================================================

market_stats["watch_score"] = (
    market_stats["gross_edge_range"].fillna(0)
    + market_stats["yes_range"].fillna(0)
    + market_stats["no_range"].fillna(0)
)

market_stats = market_stats.sort_values(
    ["watchlist", "watch_score"],
    ascending=[False, False]
).reset_index(drop=True)

market_stats["rank"] = (
    market_stats.index + 1
)


# ============================================================
# OBSERVATION-LEVEL SIGNALS
# ============================================================

signal_rows = complete.copy()

signal_rows["signal"] = "NO_SIGNAL"

signal_rows.loc[
    signal_rows["net_edge"] >= MIN_NET_EDGE,
    "signal"
] = "QUALIFIED"

signal_rows.loc[
    (
        (signal_rows["gross_edge"] >= NEAR_GROSS_EDGE)
        &
        (signal_rows["signal"] == "NO_SIGNAL")
    ),
    "signal"
] = "NEAR_ARBITRAGE"

movement_mask = (
    (
        signal_rows["yes_move_abs"]
        >= PRICE_MOVE_THRESHOLD
    )
    |
    (
        signal_rows["no_move_abs"]
        >= PRICE_MOVE_THRESHOLD
    )
)

signal_rows.loc[
    movement_mask
    &
    (signal_rows["signal"] == "NO_SIGNAL"),
    "signal"
] = "PRICE_MOVEMENT"

edge_mask = (
    signal_rows["gross_edge_move_abs"]
    >= EDGE_MOVE_THRESHOLD
)

signal_rows.loc[
    edge_mask
    &
    (signal_rows["signal"] == "NO_SIGNAL"),
    "signal"
] = "EDGE_MOVEMENT"


# ============================================================
# SUMMARY
# ============================================================

qualified_count = int(
    (complete["net_edge"] >= MIN_NET_EDGE).sum()
)

near_count = int(
    (complete["gross_edge"] >= NEAR_GROSS_EDGE).sum()
)

price_movement_count = int(
    movement_mask.sum()
)

edge_movement_count = int(
    edge_mask.sum()
)

watchlist_markets = int(
    market_stats["watchlist"].sum()
)

summary = pd.DataFrame(
    [
        ["total_observations", len(df)],
        ["complete_observations", len(complete)],
        [
            "unique_markets",
            complete["question"].nunique()
        ],
        [
            "unique_timestamps",
            complete["timestamp"].nunique()
        ],
        [
            "average_gross_edge",
            complete["gross_edge"].mean()
        ],
        [
            "maximum_gross_edge",
            complete["gross_edge"].max()
        ],
        [
            "average_net_edge",
            complete["net_edge"].mean()
        ],
        [
            "maximum_net_edge",
            complete["net_edge"].max()
        ],
        [
            "qualified_observations",
            qualified_count
        ],
        [
            "near_arbitrage_observations",
            near_count
        ],
        [
            "price_movement_observations",
            price_movement_count
        ],
        [
            "edge_movement_observations",
            edge_movement_count
        ],
        [
            "watchlist_markets",
            watchlist_markets
        ],
        [
            "fee_rate",
            FEE_RATE
        ],
        [
            "slippage_rate",
            SLIPPAGE_RATE
        ],
        [
            "minimum_net_edge",
            MIN_NET_EDGE
        ],
        [
            "near_gross_edge_threshold",
            NEAR_GROSS_EDGE
        ],
        [
            "price_move_threshold",
            PRICE_MOVE_THRESHOLD
        ],
        [
            "edge_move_threshold",
            EDGE_MOVE_THRESHOLD
        ],
    ],
    columns=["metric", "value"]
)


# ============================================================
# SAVE OUTPUTS
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

SUMMARY_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

signal_rows.to_csv(
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


# ============================================================
# PRINT RESULTS
# ============================================================

print("=" * 70)
print("PHASE 19 RESULTS")
print("=" * 70)
print()

print(f"Complete observations:       {len(complete)}")
print(
    f"Markets analysed:            "
    f"{complete['question'].nunique()}"
)
print(
    f"Maximum gross edge:          "
    f"{complete['gross_edge'].max():.4f}"
)
print(
    f"Maximum net edge:            "
    f"{complete['net_edge'].max():.4f}"
)
print()

print(f"Qualified observations:      {qualified_count}")
print(f"Near-arbitrage observations: {near_count}")
print(
    f"Price movement observations:{price_movement_count}"
)
print(
    f"Edge movement observations:  {edge_movement_count}"
)
print(f"Watchlist markets:           {watchlist_markets}")

print()
print("=" * 70)
print("TOP WATCHLIST MARKETS")
print("=" * 70)
print()

watchlist = market_stats[
    market_stats["watchlist"]
].copy()

if len(watchlist) == 0:
    print("No watchlist signals detected.")

else:
    display_columns = [
        "question",
        "latest_yes_ask",
        "latest_no_ask",
        "latest_gross_edge",
        "latest_net_edge",
        "yes_range",
        "no_range",
        "gross_edge_range",
        "signal",
    ]

    print(
        watchlist[
            display_columns
        ]
        .head(20)
        .to_string(index=False)
    )

print()
print("=" * 70)
print("PHASE 19 COMPLETE")
print("=" * 70)
print()
print("Saved:")
print(f"  {OUTPUT_FILE}")
print(f"  {SUMMARY_FILE}")
print(f"  {MARKET_STATS_FILE}")
print()

if qualified_count == 0:
    print(
        "RESULT: No observations currently meet "
        "the configured net-edge threshold."
    )
else:
    print(
        f"RESULT: {qualified_count} "
        "qualified observations detected."
    )

print()
