"""
Phase 5 - Full Market Execution Analysis

Scans Polymarket markets and evaluates realistic
YES + NO execution across multiple trade sizes.

This script DOES NOT place real orders.
It is research/simulation only.
"""

import time
import pandas as pd

from src.arbitrage import (
    get_current_markets,
    get_order_book,
    simulate_execution_sizes,
)


TRADE_SIZES = [
    10,
    50,
    100,
    250,
    500,
    1000,
]


def main():

    print("=" * 70)
    print("PHASE 5 - EXECUTION ANALYSIS")
    print("=" * 70)

    markets = get_current_markets(500)

    print(f"\nMarkets retrieved: {len(markets)}")

    rows = []

    for index, market in enumerate(markets, start=1):

        question = market.get(
            "question",
            "Unknown market"
        )

        print("\n" + "=" * 70)
        print(f"Market {index}/{len(markets)}")
        print("=" * 70)

        print(question)

        token_ids = market.get(
            "clobTokenIds"
        )

        if not isinstance(token_ids, list):
            print("Invalid token IDs")
            continue

        if len(token_ids) < 2:
            print("Missing YES/NO token IDs")
            continue

        yes_token = token_ids[0]
        no_token = token_ids[1]

        try:

            yes_book = get_order_book(
                yes_token
            )

            no_book = get_order_book(
                no_token
            )

        except Exception as e:

            print("Order book request failed:")
            print(e)

            continue

        try:

            results = simulate_execution_sizes(
                yes_book,
                no_book,
                TRADE_SIZES
            )

        except Exception as e:

            print("Execution simulation failed:")
            print(e)

            continue

        for result in results:

            row = {
                "question": question,
                "yes_token": yes_token,
                "no_token": no_token,
                "quantity": result["quantity"],
                "status": result["status"],
            }

            if result["status"] == "fully_filled":

                row.update({
                    "yes_cost": result["yes_cost"],
                    "no_cost": result["no_cost"],
                    "total_cost": result["total_cost"],
                    "yes_average_price":
                        result["yes_average_price"],
                    "no_average_price":
                        result["no_average_price"],
                    "gross_profit":
                        result["gross_profit"],
                    "gross_profit_pct":
                        result["gross_profit_pct"],
                })

            else:

                row.update({
                    "yes_cost": None,
                    "no_cost": None,
                    "total_cost": None,
                    "yes_average_price": None,
                    "no_average_price": None,
                    "gross_profit": None,
                    "gross_profit_pct": None,
                })

            rows.append(row)

            print(
                f"${result['quantity']:>6} | "
                f"{result['status']}"
            )

            if result["status"] == "fully_filled":

                print(
                    f"  Total cost: "
                    f"${result['total_cost']:.4f}"
                )

                print(
                    f"  Gross P/L: "
                    f"${result['gross_profit']:.4f}"
                )

                print(
                    f"  Gross P/L %: "
                    f"{result['gross_profit_pct']:.4f}%"
                )

        # Small delay to avoid hammering the API
        time.sleep(0.05)

    df = pd.DataFrame(rows)

    output_file = (
        "arbitrage_execution_analysis.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print("\n" + "=" * 70)
    print("PHASE 5 SUMMARY")
    print("=" * 70)

    print(
        f"Markets retrieved: {len(markets)}"
    )

    print(
        f"Execution rows recorded: {len(df)}"
    )

    if not df.empty:

        fully_filled = (
            df["status"] == "fully_filled"
        ).sum()

        profitable = (
            (df["status"] == "fully_filled")
            & (df["gross_profit"] > 0)
        ).sum()

        print(
            f"Fully executable scenarios: "
            f"{fully_filled}"
        )

        print(
            f"Gross profitable scenarios: "
            f"{profitable}"
        )

    print(
        f"\nSaved results to:\n{output_file}"
    )


if __name__ == "__main__":
    main()
