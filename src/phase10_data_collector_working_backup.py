"""
PHASE 10 - REPEATED HISTORICAL DATA COLLECTOR

Collects repeated YES/NO order-book observations and appends
them to the historical snapshot dataset.
"""

import argparse
import os
import time
from datetime import datetime, timezone

import pandas as pd

from src.arbitrage import (
    get_current_markets,
    get_order_book,
    get_best_prices,
)


OUTPUT_FILE = "data/historical_market_snapshots.csv"


def safe_float(value):
    """Convert a value to float safely."""
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def collect_snapshot(markets):
    """Collect one timestamped snapshot."""

    timestamp = datetime.now(timezone.utc).isoformat()

    rows = []

    successful = 0
    failed = 0

    print()
    print("=" * 70)
    print("PHASE 10 - REPEATED MARKET DATA COLLECTION")
    print("=" * 70)
    print()
    print(f"Markets retrieved: {len(markets)}")
    print(f"Timestamp: {timestamp}")
    print()

    for index, market in enumerate(markets, start=1):

        question = market.get("question", "")
        tokens = market.get("clobTokenIds")

        if not isinstance(tokens, list) or len(tokens) < 2:

            failed += 1

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

            if yes_ask is not None and no_ask is not None:

                combined_ask = yes_ask + no_ask
                gross_edge = 1.0 - combined_ask
                complete = True

                successful += 1

            else:

                combined_ask = None
                gross_edge = None
                complete = False

                failed += 1

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
                    "error": None,
                }
            )

        except Exception as exc:

            failed += 1

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

            print()
            print("ORDER BOOK ERROR")
            print(f"Market: {question}")
            print(f"Error: {exc}")

        if index % 10 == 0 or index == len(markets):

            print(
                f"Processed {index}/{len(markets)} markets"
            )

    return rows, successful, failed


def append_rows(rows):
    """Append observations to the historical CSV."""

    os.makedirs("data", exist_ok=True)

    new_df = pd.DataFrame(rows)

    if os.path.exists(OUTPUT_FILE):

        old_df = pd.read_csv(OUTPUT_FILE)

        combined_df = pd.concat(
            [old_df, new_df],
            ignore_index=True,
        )

    else:

        combined_df = new_df

    combined_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    return combined_df


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--markets",
        type=int,
        default=100,
        help="Number of markets to collect",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="Seconds between repeated snapshots",
    )

    parser.add_argument(
        "--snapshots",
        type=int,
        default=1,
        help="Number of snapshots to collect",
    )

    args = parser.parse_args()

    print()
    print("=" * 70)
    print("PHASE 10 - HISTORICAL DATA COLLECTION ENGINE")
    print("=" * 70)
    print()

    for snapshot_number in range(1, args.snapshots + 1):

        print(
            f"SNAPSHOT {snapshot_number}/{args.snapshots}"
        )

        markets = get_current_markets(args.markets)

        rows, successful, failed = collect_snapshot(markets)

        dataframe = append_rows(rows)

        print()
        print("=" * 70)
        print("COLLECTION RESULT")
        print("=" * 70)
        print()
        print(f"Successful complete books: {successful}")
        print(f"Incomplete/failed books: {failed}")
        print()
        print("SNAPSHOT SAVED")
        print()
        print(f"New observations: {len(rows)}")
        print(f"Total observations: {len(dataframe)}")
        print(
            f"Unique markets: "
            f"{dataframe['question'].nunique()}"
        )
        print()
        print(f"Output: {OUTPUT_FILE}")
        print()

        if (
            snapshot_number < args.snapshots
            and args.interval > 0
        ):

            print(
                f"Waiting {args.interval} seconds..."
            )

            time.sleep(args.interval)


if __name__ == "__main__":
    main()
