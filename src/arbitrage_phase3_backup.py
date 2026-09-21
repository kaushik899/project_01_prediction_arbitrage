import requests
import pandas as pd
import time


GAMMA_API = "https://gamma-api.polymarket.com/markets"
CLOB_API = "https://clob.polymarket.com/book"


# ============================================================
# GET MARKETS
# ============================================================

def get_current_markets(limit=500):
    params = {
        "limit": limit,
        "active": "true",
        "closed": "false",
    }

    response = requests.get(
        GAMMA_API,
        params=params,
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    if isinstance(data, list):
        return data

    return data.get("data", [])


# ============================================================
# GET ORDER BOOK
# ============================================================

def get_order_book(token_id):
    response = requests.get(
        CLOB_API,
        params={"token_id": token_id},
        timeout=20,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# BEST PRICE
# ============================================================

def get_best_prices(orderbook):
    bids = orderbook.get("bids", [])
    asks = orderbook.get("asks", [])

    best_bid = None
    best_ask = None

    if bids:
        best_bid = max(
            float(level["price"])
            for level in bids
        )

    if asks:
        best_ask = min(
            float(level["price"])
            for level in asks
        )

    return best_bid, best_ask


# ============================================================
# BEST-ASK LIQUIDITY
# ============================================================

def get_best_ask_liquidity(orderbook):
    asks = orderbook.get("asks", [])

    if not asks:
        return 0.0

    best_ask = min(
        float(level["price"])
        for level in asks
    )

    quantity = 0.0

    for level in asks:
        price = float(level["price"])

        if price == best_ask:
            quantity += float(level["size"])

    return quantity


# ============================================================
# ARBITRAGE CALCULATION
# ============================================================

def check_arbitrage(yes_ask, no_ask):

    if yes_ask is None and no_ask is None:
        return None

    if yes_ask is None:
        return {
            "status": "missing_yes_ask",
            "total_cost": None,
            "gross_profit": None,
            "gross_profit_pct": None,
        }

    if no_ask is None:
        return {
            "status": "missing_no_ask",
            "total_cost": None,
            "gross_profit": None,
            "gross_profit_pct": None,
        }

    total_cost = yes_ask + no_ask

    gross_profit = 1.0 - total_cost

    if total_cost > 0:
        gross_profit_pct = (
            gross_profit / total_cost
        ) * 100
    else:
        gross_profit_pct = None

    if gross_profit > 0:
        status = "potential_arbitrage"
    else:
        status = "no_arbitrage"

    return {
        "status": status,
        "total_cost": total_cost,
        "gross_profit": gross_profit,
        "gross_profit_pct": gross_profit_pct,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("Connecting to Polymarket...")

    markets = get_current_markets(limit=500)

    print(
        f"\nMarkets retrieved from API: "
        f"{len(markets)}"
    )

    rows = []
    opportunities = []

    for i, market in enumerate(
        markets,
        start=1
    ):

        print("\n" + "=" * 70)
        print(f"Market {i}/{len(markets)}")
        print("=" * 70)

        question = market.get(
            "question",
            "Unknown market"
        )

        print(f"\n{question}")

        token_ids = market.get(
            "clobTokenIds"
        )

        # ----------------------------------------------------
        # TOKEN VALIDATION
        # ----------------------------------------------------

        if not token_ids:

            print(
                "Missing CLOB token IDs."
            )

            rows.append({
                "market_index": i,
                "question": question,
                "status": "missing_token_ids",
                "yes_token": None,
                "no_token": None,
                "yes_bid": None,
                "yes_ask": None,
                "no_bid": None,
                "no_ask": None,
                "yes_quantity": None,
                "no_quantity": None,
                "yes_notional": None,
                "no_notional": None,
                "total_cost": None,
                "gross_profit": None,
                "gross_profit_pct": None,
            })

            continue

        # ----------------------------------------------------
        # TOKEN IDS
        # ----------------------------------------------------

        try:

            if isinstance(
                token_ids,
                str
            ):
                token_ids = eval(token_ids)

            yes_token = token_ids[0]
            no_token = token_ids[1]

        except Exception as e:

            print(
                "Could not parse token IDs:"
            )
            print(e)

            rows.append({
                "market_index": i,
                "question": question,
                "status": "invalid_token_ids",
                "yes_token": None,
                "no_token": None,
                "yes_bid": None,
                "yes_ask": None,
                "no_bid": None,
                "no_ask": None,
                "yes_quantity": None,
                "no_quantity": None,
                "yes_notional": None,
                "no_notional": None,
                "total_cost": None,
                "gross_profit": None,
                "gross_profit_pct": None,
            })

            continue

        print(
            f"\nYES token: {yes_token}"
        )

        print(
            f"NO token: {no_token}"
        )

        # ----------------------------------------------------
        # ORDER BOOKS
        # ----------------------------------------------------

        try:

            yes_book = get_order_book(
                yes_token
            )

            time.sleep(0.05)

            no_book = get_order_book(
                no_token
            )

        except requests.RequestException as e:

            print(
                "\nOrder book request failed:"
            )
            print(e)

            rows.append({
                "market_index": i,
                "question": question,
                "status": "orderbook_request_failed",
                "yes_token": yes_token,
                "no_token": no_token,
                "yes_bid": None,
                "yes_ask": None,
                "no_bid": None,
                "no_ask": None,
                "yes_quantity": None,
                "no_quantity": None,
                "yes_notional": None,
                "no_notional": None,
                "total_cost": None,
                "gross_profit": None,
                "gross_profit_pct": None,
            })

            continue

        # ----------------------------------------------------
        # PRICES
        # ----------------------------------------------------

        yes_bid, yes_ask = get_best_prices(
            yes_book
        )

        no_bid, no_ask = get_best_prices(
            no_book
        )

        # ----------------------------------------------------
        # LIQUIDITY
        # ----------------------------------------------------

        yes_quantity = get_best_ask_liquidity(
            yes_book
        )

        no_quantity = get_best_ask_liquidity(
            no_book
        )

        yes_notional = (
            yes_quantity * yes_ask
            if yes_ask is not None
            else 0.0
        )

        no_notional = (
            no_quantity * no_ask
            if no_ask is not None
            else 0.0
        )

        # ----------------------------------------------------
        # DISPLAY
        # ----------------------------------------------------

        print("\nYES")

        print(
            "Bid:",
            yes_bid
        )

        print(
            "Ask:",
            yes_ask
        )

        print(
            "YES available at best ask:"
        )

        print(
            "Token quantity:",
            round(
                yes_quantity,
                6
            )
        )

        print(
            "Dollar notional:",
            round(
                yes_notional,
                6
            )
        )

        print("\nNO")

        print(
            "Bid:",
            no_bid
        )

        print(
            "Ask:",
            no_ask
        )

        print(
            "NO available at best ask:"
        )

        print(
            "Token quantity:",
            round(
                no_quantity,
                6
            )
        )

        print(
            "Dollar notional:",
            round(
                no_notional,
                6
            )
        )

        # ----------------------------------------------------
        # ARBITRAGE
        # ----------------------------------------------------

        result = check_arbitrage(
            yes_ask,
            no_ask
        )

        # ----------------------------------------------------
        # INCOMPLETE ORDER BOOK
        # ----------------------------------------------------

        if result is None:

            print(
                "\nCannot calculate arbitrage:"
            )

            print(
                "Both YES and NO asks "
                "are unavailable."
            )

            rows.append({
                "market_index": i,
                "question": question,
                "status": "missing_both_asks",
                "yes_token": yes_token,
                "no_token": no_token,
                "yes_bid": yes_bid,
                "yes_ask": yes_ask,
                "no_bid": no_bid,
                "no_ask": no_ask,
                "yes_quantity": yes_quantity,
                "no_quantity": no_quantity,
                "yes_notional": yes_notional,
                "no_notional": no_notional,
                "total_cost": None,
                "gross_profit": None,
                "gross_profit_pct": None,
            })

            continue

        # ----------------------------------------------------
        # MISSING ONE SIDE
        # ----------------------------------------------------

        if result["status"] == "missing_yes_ask":

            print(
                "\nCannot calculate arbitrage:"
            )

            print(
                "YES ask is unavailable."
            )

        elif result["status"] == "missing_no_ask":

            print(
                "\nCannot calculate arbitrage:"
            )

            print(
                "NO ask is unavailable."
            )

        # ----------------------------------------------------
        # COMPLETE ORDER BOOK
        # ----------------------------------------------------

        else:

            print(
                "\nTotal YES + NO cost:"
            )

            print(
                round(
                    result["total_cost"],
                    6
                )
            )

            print(
                "Gross profit:"
            )

            print(
                round(
                    result["gross_profit"],
                    6
                )
            )

            print(
                "Gross profit %:"
            )

            print(
                round(
                    result["gross_profit_pct"],
                    4
                ),
                "%"
            )

            if result["status"] == "potential_arbitrage":

                print(
                    "\n*** POTENTIAL "
                    "GROSS ARBITRAGE ***"
                )

                opportunities.append({
                    "question": question,
                    "yes_ask": yes_ask,
                    "no_ask": no_ask,
                    "total_cost": result["total_cost"],
                    "gross_profit": result["gross_profit"],
                    "gross_profit_pct": result["gross_profit_pct"],
                    "yes_notional": yes_notional,
                    "no_notional": no_notional,
                })

            else:

                print(
                    "\nNo YES + NO arbitrage."
                )

        # ----------------------------------------------------
        # SAVE EVERY MARKET
        # ----------------------------------------------------

        rows.append({
            "market_index": i,
            "question": question,
            "status": result["status"],
            "yes_token": yes_token,
            "no_token": no_token,
            "yes_bid": yes_bid,
            "yes_ask": yes_ask,
            "no_bid": no_bid,
            "no_ask": no_ask,
            "yes_quantity": yes_quantity,
            "no_quantity": no_quantity,
            "yes_notional": yes_notional,
            "no_notional": no_notional,
            "total_cost": result["total_cost"],
            "gross_profit": result["gross_profit"],
            "gross_profit_pct": result["gross_profit_pct"],
        })

    # ========================================================
    # SAVE CSV
    # ========================================================

    df = pd.DataFrame(rows)

    output_file = (
        "arbitrage_scan_phase3.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n")
    print("=" * 70)
    print("ARBITRAGE SUMMARY")
    print("=" * 70)

    print(
        f"\nMarkets retrieved: "
        f"{len(markets)}"
    )

    print(
        f"Markets recorded: "
        f"{len(df)}"
    )

    print(
        f"Potential gross arbitrage "
        f"opportunities: "
        f"{len(opportunities)}"
    )

    complete = df[
        df["status"].isin(
            [
                "no_arbitrage",
                "potential_arbitrage"
            ]
        )
    ]

    incomplete = len(df) - len(complete)

    print(
        f"Complete order books: "
        f"{len(complete)}"
    )

    print(
        f"Incomplete order books: "
        f"{incomplete}"
    )

    if opportunities:

        print(
            "\nPotential opportunities:"
        )

        for opportunity in opportunities:

            print(
                "\n" +
                opportunity["question"]
            )

            print(
                "YES ask:",
                opportunity["yes_ask"]
            )

            print(
                "NO ask:",
                opportunity["no_ask"]
            )

            print(
                "Total cost:",
                round(
                    opportunity["total_cost"],
                    6
                )
            )

            print(
                "Gross profit:",
                round(
                    opportunity["gross_profit"],
                    6
                )
            )

            print(
                "Gross profit %:",
                round(
                    opportunity["gross_profit_pct"],
                    4
                )
            )

    else:

        print(
            "\nNo gross YES + NO "
            "arbitrage opportunities "
            "detected."
        )

    print(
        "\nSaved complete scan to:"
    )

    print(output_file)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
