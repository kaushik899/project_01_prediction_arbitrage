"""
PHASE 8A - HISTORICAL MARKET COLLECTOR
DEBUG / ROBUST VERSION

Collects current YES/NO order-book snapshots and stores them
for historical analysis.

Output:
    data/historical_market_snapshots.csv
"""

import os
from datetime import datetime, timezone

import pandas as pd

from src.arbitrage import (
    get_current_markets,
    get_order_book,
    get_best_prices,
)


OUTPUT_FILE = "data/historical_market_snapshots.csv"


def ensure_data_directory():
    os.makedirs("data", exist_ok=True)


def safe_float(value):
    try:
        if value is None:
            return None

        return float(value)

    except (TypeError, ValueError):
        return None


def collect_snapshot(limit=100):

    markets = get_current_markets(limit)

    timestamp = datetime.now(timezone.utc).isoformat()

    rows = []

    print()
    print("=" * 70)
    print("PHASE 8 - HISTORICAL SNAPSHOT")
    print("=" * 70)

    print(f"Markets retrieved: {len(markets)}")
    print(f"Timestamp: {timestamp}")
    print()

    successful_books = 0
    failed_books = 0

    for index, market in enumerate(markets, start=1):

        question = market.get("question", "")

        tokens = market.get("clobTokenIds")

        if not isinstance(tokens, list) or len(tokens) < 2:

            rows.append(
                {
                    "timestamp": timestamp,
                    "question": question,
                    "yes_token": None,
                    "no_token": None,
                    "yes_bid": None,
                    "yes_ask": None,
                    "no_bid": None,
                    "no_ask": None,
                    "combined_yes_no_ask": None,
                    "gross_edge": None,
                    "complete_orderbook": False,
                    "error": "invalid_token_data",
                }
            )

            continue

        yes_token = tokens[0]
        no_token = tokens[1]

        try:
            yes_book = get_order_book(yes_token)
            no_book = get_order_book(no_token)

            yes_bid_raw, yes_ask_raw = get_best_prices(yes_book)
            no_bid_raw, no_ask_raw = get_best_prices(no_book)

            yes_bid = safe_float(yes_bid_raw)
            yes_ask = safe_float(yes_ask_raw)

            no_bid = safe_float(no_bid_raw)
            no_ask = safe_float(no_ask_raw)

            if (
                yes_ask is not None
                and no_ask is not None
            ):
                combined_ask = (
                    yes_ask + no_ask
                )

                gross_edge = (
                    1.0 - combined_ask
                )

                complete = True

            else:
                combined_ask = None
                gross_edge = None
                complete = False
            if complete:

                successful_books += 1

                error = None

            else:

                failed_books += 1

                error = "missing_best_ask"

            rows.append(
                {
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
                    "complete_orderbook": complete,
                    "error": error,
                }
            )

        except Exception as exc:

            failed_books += 1

            rows.append(
                {
                    "timestamp": timestamp,
                    "question": question,
                    "yes_token": yes_token,
                    "no_token": no_token,
                    "yes_bid": None,
                    "yes_ask": None,
                    "no_bid": None,
                    "no_ask": None,
                    "combined_yes_no_ask": None,
                    "gross_edge": None,
                    "complete_orderbook": False,
                    "error": str(exc),
                }
            )

            if failed_books <= 5:

                print()
                print("ORDER BOOK ERROR")
                print(f"Market: {question}")
                print(f"Error: {exc}")

        if index % 10 == 0:

            print(
                f"Processed {index}/{len(markets)} markets"
            )

    print()
    print("=" * 70)
    print("COLLECTION RESULT")
    print("=" * 70)

    print(
        f"Successful complete books: "
        f"{successful_books}"
    )

    print(
        f"Incomplete/failed books: "
        f"{failed_books}"
    )

    return rows


def save_snapshot(rows):

    ensure_data_directory()

    new_data = pd.DataFrame(rows)

    if new_data.empty:

        print("No observations collected.")

        return

    if os.path.exists(OUTPUT_FILE):

        try:

            old_data = pd.read_csv(
                OUTPUT_FILE
            )

            combined = pd.concat(
                [
                    old_data,
                    new_data,
                ],
                ignore_index=True,
            )

        except Exception:

            combined = new_data

    else:

        combined = new_data

    combined.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("=" * 70)
    print("SNAPSHOT SAVED")
    print("=" * 70)

    print(
        f"New observations: "
        f"{len(new_data)}"
    )

    print(
        f"Total observations: "
        f"{len(combined)}"
    )

    print(
        f"Unique markets: "
        f"{combined['question'].nunique()}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


def main():

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--markets",
        type=int,
        default=100,
    )

    args = parser.parse_args()

    rows = collect_snapshot(
        args.markets
    )

    save_snapshot(rows)


if __name__ == "__main__":

    main()
