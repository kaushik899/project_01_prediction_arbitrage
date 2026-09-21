"""
PHASE 14 - LIVE ARBITRAGE OPPORTUNITY SCANNER

Purpose:
- Retrieve active markets
- Inspect YES/NO order books
- Calculate gross arbitrage edge
- Apply configurable execution costs
- Estimate net edge
- Classify opportunities
- Save scan results

This phase is research/paper-trading only.
It does NOT place orders.
"""

import os
import time
from datetime import datetime, timezone

import pandas as pd

from src.arbitrage import (
    get_current_markets,
    get_order_book,
    get_best_prices,
)


# ============================================================
# CONFIGURATION
# ============================================================

MARKET_LIMIT = 100

# Conservative configurable assumptions.
# These are NOT claimed to be the actual exchange fee schedule.
FEE_RATE = 0.001

SLIPPAGE_RATE = 0.001

MIN_NET_EDGE = 0.002

OUTPUT_FILE = "data/phase14_opportunity_scan.csv"


# ============================================================
# SETUP
# ============================================================

os.makedirs("data", exist_ok=True)


# ============================================================
# HELPERS
# ============================================================

def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_token_ids(market):
    token_ids = market.get("clobTokenIds")

    if not isinstance(token_ids, list):
        return None, None

    if len(token_ids) < 2:
        return None, None

    return token_ids[0], token_ids[1]


def calculate_opportunity(yes_book, no_book):
    yes_bid, yes_ask = get_best_prices(yes_book)
    no_bid, no_ask = get_best_prices(no_book)

    if yes_ask is None or no_ask is None:
        return None

    combined_cost = yes_ask + no_ask

    gross_edge = 1.0 - combined_cost

    estimated_fees = combined_cost * FEE_RATE

    estimated_slippage = combined_cost * SLIPPAGE_RATE

    net_edge = (
        gross_edge
        - estimated_fees
        - estimated_slippage
    )

    return {
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": no_bid,
        "no_ask": no_ask,
        "combined_yes_no_ask": combined_cost,
        "gross_edge": gross_edge,
        "estimated_fees": estimated_fees,
        "estimated_slippage": estimated_slippage,
        "net_edge": net_edge,
    }


# ============================================================
# MARKET SCAN
# ============================================================

print()
print("=" * 70)
print("PHASE 14 - LIVE ARBITRAGE OPPORTUNITY SCANNER")
print("=" * 70)

print()
print(f"Market limit:          {MARKET_LIMIT}")
print(f"Fee assumption:        {FEE_RATE:.4%}")
print(f"Slippage assumption:   {SLIPPAGE_RATE:.4%}")
print(f"Minimum net edge:      {MIN_NET_EDGE:.4%}")

print()
print("Retrieving active markets...")

markets = get_current_markets(MARKET_LIMIT)

print(f"Markets retrieved: {len(markets)}")


# ============================================================
# PROCESS MARKETS
# ============================================================

results = []

complete_count = 0
incomplete_count = 0
error_count = 0


for i, market in enumerate(markets, start=1):

    question = market.get(
        "question",
        "Unknown market"
    )

    yes_token, no_token = extract_token_ids(market)

    if yes_token is None or no_token is None:

        incomplete_count += 1

        results.append({
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),

            "question": question,

            "complete_orderbook": False,

            "gross_edge": None,

            "net_edge": None,

            "opportunity": False,

            "status": "missing_token_ids",
        })

        continue

    try:

        yes_book = get_order_book(yes_token)

        no_book = get_order_book(no_token)

        opportunity = calculate_opportunity(
            yes_book,
            no_book
        )

        if opportunity is None:

            incomplete_count += 1

            results.append({
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),

                "question": question,

                "complete_orderbook": False,

                "gross_edge": None,

                "net_edge": None,

                "opportunity": False,

                "status": "incomplete_orderbook",
            })

            continue

        complete_count += 1

        net_edge = opportunity["net_edge"]

        is_opportunity = (
            net_edge >= MIN_NET_EDGE
        )

        results.append({

            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),

            "question": question,

            **opportunity,

            "complete_orderbook": True,

            "opportunity": is_opportunity,

            "status": (
                "OPPORTUNITY"
                if is_opportunity
                else "NO_SIGNAL"
            ),
        })

    except Exception as exc:

        error_count += 1

        results.append({

            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),

            "question": question,

            "complete_orderbook": False,

            "gross_edge": None,

            "net_edge": None,

            "opportunity": False,

            "status": f"error: {exc}",
        })

    if i % 10 == 0 or i == len(markets):

        print(
            f"Processed {i}/{len(markets)} markets"
        )


# ============================================================
# SAVE RESULTS
# ============================================================

result_df = pd.DataFrame(results)

result_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

opportunities = result_df[
    result_df["opportunity"] == True
]

complete = result_df[
    result_df["complete_orderbook"] == True
]


print()
print("=" * 70)
print("SCAN RESULT")
print("=" * 70)

print()
print(f"Markets scanned:             {len(result_df)}")
print(f"Complete order books:        {complete_count}")
print(f"Incomplete order books:      {incomplete_count}")
print(f"Errors:                       {error_count}")

print()
print(
    f"Positive gross edges:        "
    f"{(complete['gross_edge'] > 0).sum()}"
)

print(
    f"Positive net edges:          "
    f"{(complete['net_edge'] > 0).sum()}"
)

print(
    f"Qualified opportunities:     "
    f"{len(opportunities)}"
)


if not complete.empty:

    print()
    print("EDGE STATISTICS")
    print("-" * 70)

    print(
        f"Average gross edge:          "
        f"{complete['gross_edge'].mean():.6f}"
    )

    print(
        f"Maximum gross edge:          "
        f"{complete['gross_edge'].max():.6f}"
    )

    print(
        f"Average net edge:            "
        f"{complete['net_edge'].mean():.6f}"
    )

    print(
        f"Maximum net edge:            "
        f"{complete['net_edge'].max():.6f}"
    )


if not opportunities.empty:

    print()
    print("QUALIFIED OPPORTUNITIES")
    print("-" * 70)

    print(
        opportunities[
            [
                "question",
                "combined_yes_no_ask",
                "gross_edge",
                "net_edge",
            ]
        ]
        .sort_values(
            "net_edge",
            ascending=False
        )
        .to_string(index=False)
    )

else:

    print()
    print(
        "No qualified arbitrage opportunities "
        "were detected."
    )


print()
print(f"Saved: {OUTPUT_FILE}")

print()
print("=" * 70)
print("PHASE 14 COMPLETE")
print("=" * 70)
