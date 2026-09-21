"""
Phase 4 - Order Book Execution Simulator

This module calculates the realistic cost of executing
a market order across multiple order-book levels.

It does NOT place real trades.
"""

from typing import List, Dict, Optional


def calculate_buy_cost(
    asks: List[Dict],
    quantity: float
) -> Optional[Dict]:
    """
    Calculate the cost of buying a given quantity
    across multiple ask levels.

    Each ask level should contain:

        {
            "price": float,
            "size": float
        }

    Returns:

        {
            "quantity_requested": ...,
            "quantity_filled": ...,
            "total_cost": ...,
            "average_price": ...,
            "fully_filled": ...
        }

    Returns None if the order book is invalid.
    """

    if quantity <= 0:
        return None

    if not asks:
        return None

    remaining = quantity
    total_cost = 0.0
    filled = 0.0

    for level in asks:

        try:
            price = float(level["price"])
            size = float(level["size"])
        except (KeyError, TypeError, ValueError):
            continue

        if price <= 0 or size <= 0:
            continue

        quantity_from_level = min(
            remaining,
            size
        )

        total_cost += (
            quantity_from_level * price
        )

        filled += quantity_from_level
        remaining -= quantity_from_level

        if remaining <= 1e-12:
            break

    if filled <= 0:
        return None

    average_price = total_cost / filled

    return {
        "quantity_requested": quantity,
        "quantity_filled": filled,
        "total_cost": total_cost,
        "average_price": average_price,
        "fully_filled": remaining <= 1e-12,
    }


def calculate_combined_execution(
    yes_asks: List[Dict],
    no_asks: List[Dict],
    quantity: float
) -> Optional[Dict]:
    """
    Simulate buying the same quantity of YES and NO.

    Since YES + NO settle to $1 combined for a binary
    market, we compare the combined execution cost
    against the $1 guaranteed combined settlement.

    This is a gross calculation only.
    Fees and other costs are handled later.
    """

    yes_result = calculate_buy_cost(
        yes_asks,
        quantity
    )

    no_result = calculate_buy_cost(
        no_asks,
        quantity
    )

    if yes_result is None or no_result is None:
        return None

    if not yes_result["fully_filled"]:
        return None

    if not no_result["fully_filled"]:
        return None

    total_cost = (
        yes_result["total_cost"]
        + no_result["total_cost"]
    )

    guaranteed_value = quantity * 1.0

    gross_profit = (
        guaranteed_value - total_cost
    )

    gross_profit_pct = (
        gross_profit / total_cost * 100
        if total_cost > 0
        else 0.0
    )

    return {
        "quantity": quantity,

        "yes_cost": yes_result["total_cost"],
        "no_cost": no_result["total_cost"],

        "total_cost": total_cost,

        "yes_average_price":
            yes_result["average_price"],

        "no_average_price":
            no_result["average_price"],

        "gross_profit": gross_profit,

        "gross_profit_pct":
            gross_profit_pct,
    }
