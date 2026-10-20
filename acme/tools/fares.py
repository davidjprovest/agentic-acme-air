"""Fares tools: fare rules by class and the list of valid classes.

PLANTED DEFECT: the fare table has no class Z, so check_fare_rule("Z")
fails. The error names the class and points to list_fare_classes, and the
fares agent must report it rather than invent a rule.
"""

from copy import deepcopy

from acme.data import FARE_RULES
from acme.errors import FareClassNotFound


def check_fare_rule(fare_class: str) -> dict:
    rule = FARE_RULES.get(fare_class.upper())
    if rule is None:
        raise FareClassNotFound(
            f"Fare class {fare_class} not in fare table. "
            "Call list_fare_classes for valid classes."
        )
    return deepcopy(rule)


def list_fare_classes() -> list[str]:
    return sorted(FARE_RULES)
