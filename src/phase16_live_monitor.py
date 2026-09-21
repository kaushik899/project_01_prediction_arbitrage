"""
PHASE 16 - LIVE ARBITRAGE MONITOR

Collects live YES/NO order-book observations and calculates:

- Best YES bid / ask
- Best NO bid / ask
- Combined YES + NO ask
- Gross arbitrage edge
- Fees
- Slippage
- Net edge
- Opportunity status

IMPORTANT:
If either YES ask or NO ask is missing, the observation is
marked INCOMPLETE and no arbitrage metrics are calculated.
"""

from pathlib import Path
from datetime import datetime, timezone
import time

import pandas as pd

from src.market_data import (
    get_current_markets,
    parse_token_ids,
    get_order_book,
    get_best_prices,
)


# ============================================================
# CONFIGURATION
# ============================================================

MARKET_LIMIT = 100

POLL_INTERVAL = 60

OUTPUT_FILE = Path(
    "data/phase16_live_monitor.csv"
)

FEE_COST = 0.001
SLIPPAGE_COST = 0.001


# ============================================================
# HELPERS
# ============================================================

def ensure_directories():
    """Create output directory if it does not exist."""
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


def timestamp_now():
    """Return current UTC timestamp."""
    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# PROCESS ONE MARKET
# ============================================================

def process_market(market):
    """
    Fetch one market's order books and calculate
    arbitrage metrics.

    Missing best asks are classified as INCOMPLETE.
    """

    timestamp = timestamp_now()

    question = market.get(
        "question"
    )

    try:
        yes_token, no_token = parse_token_ids(
            market
        )

        # ----------------------------------------------------
        # GET ORDER BOOKS
        # ----------------------------------------------------

        yes_book = get_order_book(
            yes_token
        )

        no_book = get_order_book(
            no_token
        )

        # ----------------------------------------------------
        # GET BEST PRICES
        # ----------------------------------------------------

        yes_bid, yes_ask = get_best_prices(
            yes_book
        )

        no_bid, no_ask = get_best_prices(
            no_book
        )

        # ====================================================
        # VALIDATE BEST ASKS
        # ====================================================

        if yes_ask is None or no_ask is None:

            return {
                "timestamp": timestamp,
                "question": question,

                "yes_token": yes_token,
                "no_token": no_token,

                "yes_bid": yes_bid,
                "yes_ask": yes_ask,

                "no_bid": no_bid,
                "no_ask": no_ask,

                "combined_yes_no_ask": None,

                "gross_edge": None,

                "fee_cost": None,
                "slippage_cost": None,
                "total_cost": None,

                "net_edge": None,

                "qualified_opportunity": False,

                "status": "INCOMPLETE",

                "error": (
                    "missing_yes_ask"
                    if yes_ask is None
                    else "missing_no_ask"
                ),
            }

        # ====================================================
        # CALCULATE ARBITRAGE METRICS
        # ====================================================

        combined_ask = (
            yes_ask + no_ask
        )

        gross_edge = (
            1.0 - combined_ask
        )

        fee_cost = FEE_COST

        slippage_cost = (
            SLIPPAGE_COST
        )

        total_cost = (
            fee_cost +
            slippage_cost
        )

        net_edge = (
            gross_edge -
            total_cost
        )

        qualified_opportunity = (
            net_edge > 0
        )

        status = (
            "OPPORTUNITY"
            if qualified_opportunity
            else "NO_OPPORTUNITY"
        )

        # ====================================================
        # RETURN COMPLETE OBSERVATION
        # ====================================================

        return {
            "timestamp": timestamp,
            "question": question,

            "yes_token": yes_token,
            "no_token": no_token,

            "yes_bid": yes_bid,
            "yes_ask": yes_ask,

            "no_bid": no_bid,
            "no_ask": no_ask,

            "combined_yes_no_ask": combined_ask,

            "gross_edge": gross_edge,

            "fee_cost": fee_cost,
            "slippage_cost": slippage_cost,
            "total_cost": total_cost,

            "net_edge": net_edge,

            "qualified_opportunity":
                qualified_opportunity,

            "status": status,

            "error": None,
        }

    except Exception as e:

        return {
            "timestamp": timestamp,
            "question": question,

            "yes_token": (
                None
            ),

            "no_token": (
                None
            ),

            "yes_bid": None,
            "yes_ask": None,

            "no_bid": None,
            "no_ask": None,

            "combined_yes_no_ask": None,

            "gross_edge": None,

            "fee_cost": None,
            "slippage_cost": None,
            "total_cost": None,

            "net_edge": None,

            "qualified_opportunity":
                False,

            "status": "ERROR",

            "error": str(e),
        }


# ============================================================
# COLLECT ONE SNAPSHOT
# ============================================================

def collect_snapshot():
    """
    Retrieve the current markets and process each market once.
    """

    print()
    print("=" * 70)
    print("PHASE 16 - LIVE ARBITRAGE MONITOR")
    print("=" * 70)
    print(
        f"Market limit: {MARKET_LIMIT}"
    )

    markets = get_current_markets(
        limit=MARKET_LIMIT
    )

    rows = []

    for index, market in enumerate(
        markets,
        start=1
    ):

        result = process_market(
            market
        )

        rows.append(result)

        print(
            f"[{index}/{len(markets)}] "
            f"{result['question']}"
        )

        print(
            f"    YES → bid: "
            f"{result['yes_bid']}, "
            f"ask: "
            f"{result['yes_ask']}"
        )

        print(
            f"    NO  → bid: "
            f"{result['no_bid']}, "
            f"ask: "
            f"{result['no_ask']}"
        )

        print(
            f"    status: "
            f"{result['status']}"
        )

        if result["error"] is not None:
            print(
                f"    error: "
                f"{result['error']}"
            )

    return pd.DataFrame(
        rows
    )


# ============================================================
# SAVE DATA
# ============================================================

def save_snapshot(df):
    """
    Save the current snapshot to CSV.

    This overwrites the Phase 16 dataset so that each run
    represents the current collection.
    """

    ensure_directories()

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("=" * 70)
    print("PHASE 16 DATA SAVED")
    print("=" * 70)

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print(
        f"Rows: {len(df)}"
    )

    if not df.empty:

        print()
        print("STATUS COUNTS:")
        print(
            df["status"]
            .value_counts(
                dropna=False
            )
        )


# ============================================================
# MAIN
# ============================================================

def main():

    ensure_directories()

    df = collect_snapshot()

    save_snapshot(
        df
    )


if __name__ == "__main__":
    main()
