import requests
import pandas as pd
import json


CLOB_URL = "https://clob.polymarket.com"
GAMMA_URL = "https://gamma-api.polymarket.com"


def get_current_markets(limit=20):
    """Get active, non-closed markets from Gamma."""

    response = requests.get(
        f"{GAMMA_URL}/markets",
        params={
            "limit": limit,
            "active": "true",
            "closed": "false",
        },
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if isinstance(data, dict):
        return data.get("data", data.get("markets", []))

    return data


def parse_token_ids(market):
    """Extract YES and NO CLOB token IDs."""

    token_ids = market.get("clobTokenIds")

    if not token_ids:
        return None, None

    # Gamma may return token IDs as a JSON string
    if isinstance(token_ids, str):
        try:
            token_ids = json.loads(token_ids)
        except json.JSONDecodeError:
            return None, None

    if not isinstance(token_ids, list):
        return None, None

    if len(token_ids) < 2:
        return None, None

    return token_ids[0], token_ids[1]


def get_order_book(token_id):
    """Get order book from the CLOB."""

    response = requests.get(
        f"{CLOB_URL}/book",
        params={
            "token_id": token_id
        },
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def get_best_prices(token_id):
    """Get best bid and best ask."""

    book = get_order_book(token_id)

    bids = book.get("bids", [])
    asks = book.get("asks", [])

    best_bid = None
    best_ask = None

    if bids:
        best_bid = max(
            float(order["price"])
            for order in bids
        )

    if asks:
        best_ask = min(
            float(order["price"])
            for order in asks
        )

    return best_bid, best_ask


def main():

    print("Connecting to Polymarket...")

    markets = get_current_markets(limit=20)

    print(
        f"Current markets retrieved: {len(markets)}"
    )

    rows = []

    for i, market in enumerate(markets):

        question = market.get("question")

        yes_token_id, no_token_id = parse_token_ids(
            market
        )

        print(
            f"\nMarket {i + 1}/{len(markets)}"
        )

        print(question)

        if not yes_token_id or not no_token_id:

            print("Missing token IDs — skipping.")

            continue

        try:

            yes_bid, yes_ask = get_best_prices(
                yes_token_id
            )

            no_bid, no_ask = get_best_prices(
                no_token_id
            )

            rows.append({
                "question": question,
                "yes_token_id": yes_token_id,
                "no_token_id": no_token_id,
                "yes_bid": yes_bid,
                "yes_ask": yes_ask,
                "no_bid": no_bid,
                "no_ask": no_ask,
            })

            print(
                f"YES → bid: {yes_bid}, ask: {yes_ask}"
            )

            print(
                f"NO  → bid: {no_bid}, ask: {no_ask}"
            )

        except requests.RequestException as e:

            print("Order book request failed:")
            print(e)

    df = pd.DataFrame(rows)

    print("\n================================")
    print("ORDER BOOK DATA")
    print("================================")

    if df.empty:

        print("No order-book data retrieved.")

    else:

        print(
            df.to_string(index=False)
        )


if __name__ == "__main__":
    main()
