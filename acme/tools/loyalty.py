"""Loyalty tool: points, tier status and upgrade cost."""

from copy import deepcopy

from acme.data import LOYALTY
from acme.errors import LoyaltyAccountNotFound


def get_loyalty_account(loyalty_id: str) -> dict:
    account = LOYALTY.get(loyalty_id.upper())
    if account is None:
        raise LoyaltyAccountNotFound(f"Loyalty account {loyalty_id} not found")
    return deepcopy(account)
