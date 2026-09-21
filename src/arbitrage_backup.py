import requests
import pandas as pd
import time


GAMMA_URL = "https://gamma-api.polymarket.com"
CLOB_URL = "https://clob.polymarket.com"


# ============================================================
# GET 500 ACTIVE MARKETS
# ============================================================

def get_current_markets(target=500, batch_size=100):

    all_markets = []
    offset = 0

    while len(all_markets) < target:

        print(
            f"Downloading markets "
            f"{offset + 1}-{offset + batch_size}..."
        )

        response = requests.get(
            f"{GAMMA_URL}/markets",
            params={
                "limit": batch_size,
                "offset": offset,
                "active": "true",
                "closed": "false",
            },
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if isinstance(data, list):
            batch = data
        else:
            batch = data.get("data", [])

        if not batch:
            print("No more markets returned.")
            break

        all_markets.extend(batch)

        print(
            f"Received {len(batch)} markets | "
            f"Total: {len(all_markets)}"
        )

        offset += len(batch)

        if len(batch) < batch_size:
            print("API returned fewer markets than requested.")
            break

        time.sleep(0.2)

    return all_markets[:target]


# ============================================================
# EXTRACT YES / NO TOKEN IDS
# ============================================================

def get_token_ids(market):

    yes_token = None
    no_token = None

    # Gamma can expose tokens in different structures.
    tokens = market.get("tokens", [])

    for token in tokens:

        outcome = str(
            token.get("outcome", "")
        ).lower()

        token_id = token.get("token_id")

        if outcome == "yes":
            yes_token = token_id

        elif outcome == "no":
            no_token = token_id

    # Some Gamma responses use clobTokenIds.
    if not yes_token or not no_token:

        clob_ids = market.get("clobTokenIds")

        if clob_ids:

            if isinstance(clob_ids, str):

                try:
                    import json
                    clob_ids = json.loads(clob_ids)
                except Exception:
                    clob_ids = []

            if isinstance(clob_ids, list):

                if len(clob_ids) >= 2:

                    yes_token = yes_token or clob_ids[0]
                    no_token = no_token or clob_ids[1]

    return yes_token, no_token


# ============================================================
# GET ORDER BOOK
# ============================================================

def get_order_book(token_id):

    response = requests.get(
        f"{CLOB_URL}/book",
        params={
            "token_id": token_id
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# GET BEST BID / ASK
# ============================================================

def get_best_prices(token_id):

    book = get_order_book(token_id)

    bids = book.get("bids", [])
    asks = book.get("asks", [])

    best_bid = None
    best_ask = None

    if bids:

        bid_prices = []

        for level in bids:

            try:
                bid_prices.append(
                    float(level["price"])
                )
            except Exception:
                pass

        if bid_prices:
            best_bid = max(bid_prices)

    if asks:

        ask_prices = []

        for level in asks:

            try:
                ask_prices.append(
                    float(level["price"])
                )
            except Exception:
                pass

        if ask_prices:
            best_ask = min(ask_prices)

    return best_bid, best_ask


# ============================================================
# YES + NO ARBITRAGE
# ============================================================

def check_arbitrage(yes_ask, no_ask):

    if yes_ask is None or no_ask is None:
        return None

    total_cost = yes_ask + no_ask

    gross_profit = 1.0 - total_cost

    gross_profit_pct = (
        gross_profit / total_cost
    ) * 100

    return {
        "total_cost": total_cost,
        "gross_profit": gross_profit,
        "gross_profit_pct": gross_profit_pct,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("POLYMARKET ARBITRAGE SCANNER")
    print("=" * 70)

    print("\nConnecting to Polymarket...")

    markets = get_current_markets(
        target=500,
        batch_size=100
    )

    print(
        f"\nTotal markets retrieved: "
        f"{len(markets)}"
    )

    opportunities = []

    rows = []

    # --------------------------------------------------------
    # SCAN MARKETS
    # --------------------------------------------------------

    for i, market in enumerate(
        markets,
        start=1
    ):

        question = market.get(
            "question",
            "Unknown market"
        )

        print("\n" + "=" * 70)
        print(
            f"Market {i}/{len(markets)}"
        )
        print("=" * 70)

        print(question)

        yes_token, no_token = get_token_ids(
            market
        )

        print("\nYES token:", yes_token)
        print("NO token:", no_token)

        if not yes_token or not no_token:

            print(
                "\nMissing YES/NO token IDs."
            )

            continue

        # ----------------------------------------------------
        # YES ORDER BOOK
        # ----------------------------------------------------

        try:

            yes_bid, yes_ask = get_best_prices(
                yes_token
            )

        except requests.RequestException as e:

            print(
                "\nYES order book request failed:"
            )
            print(e)

            continue

        # ----------------------------------------------------
        # NO ORDER BOOK
        # ----------------------------------------------------

        try:

            no_bid, no_ask = get_best_prices(
                no_token
            )

        except requests.RequestException as e:

            print(
                "\nNO order book request failed:"
            )
            print(e)

            continue

        print("\nYES")
        print("Bid:", yes_bid)
        print("Ask:", yes_ask)

        print("\nNO")
        print("Bid:", no_bid)
        print("Ask:", no_ask)

        # ----------------------------------------------------
        # ARBITRAGE CHECK
        # ----------------------------------------------------

        result = check_arbitrage(
            yes_ask,
            no_ask
        )

        if result is None:

            if yes_ask is None and no_ask is None:

                print(
                    "\nCannot calculate arbitrage: "
                    "both YES and NO asks are unavailable."
                )

            elif yes_ask is None:

                print(
                    "\nCannot calculate arbitrage: "
                    "YES ask is unavailable."
                )

            elif no_ask is None:

                print(
                    "\nCannot calculate arbitrage: "
                    "NO ask is unavailable."
                )

            continue

        # ----------------------------------------------------
        # RESULTS
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # POTENTIAL ARBITRAGE
        # ----------------------------------------------------

        if result["gross_profit"] > 0:

            print(
                "\n*** POTENTIAL ARBITRAGE ***"
            )

            opportunities.append({
                "question": question,
                "yes_token": yes_token,
                "no_token": no_token,
                "yes_ask": yes_ask,
                "no_ask": no_ask,
                "total_cost": result[
                    "total_cost"
                ],
                "gross_profit": result[
                    "gross_profit"
                ],
                "gross_profit_pct": result[
                    "gross_profit_pct"
                ],
            })

        else:

            print(
                "\nNo YES + NO arbitrage."
            )

        # ----------------------------------------------------
        # SAVE DATA
        # ----------------------------------------------------

        rows.append({
            "question": question,
            "yes_token": yes_token,
            "no_token": no_token,
            "yes_bid": yes_bid,
            "yes_ask": yes_ask,
            "no_bid": no_bid,
            "no_ask": no_ask,
            "total_cost": result[
                "total_cost"
            ],
            "gross_profit": result[
                "gross_profit"
            ],
            "gross_profit_pct": result[
                "gross_profit_pct"
            ],
        })

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n")
    print("=" * 70)
    print("ARBITRAGE SUMMARY")
    print("=" * 70)

    print(
        f"\nPotential opportunities found: "
        f"{len(opportunities)}"
    )

    if opportunities:

        print(
            "\nPotential opportunities:"
        )

        for opportunity in opportunities:

            print("\n" + "-" * 70)

            print(
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
                    opportunity[
                        "gross_profit_pct"
                    ],
                    4
                ),
                "%"
            )

    else:

        print(
            "\nNo gross YES + NO arbitrage "
            "opportunities detected."
        )

    # ========================================================
    # SAVE CSV
    # ========================================================

    if rows:

        df = pd.DataFrame(rows)

        df.to_csv(
            "arbitrage_scan.csv",
            index=False
        )

        print(
            "\nSaved scan results to:"
        )

        print(
            "arbitrage_scan.csv"
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
