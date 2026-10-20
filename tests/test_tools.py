import time

import pytest

from acme.data import BOOKINGS
from acme.errors import BookingNotFound, FareClassNotFound
from acme.tools.baggage import trace_bag
from acme.tools.fares import check_fare_rule, list_fare_classes
from acme.tools.loyalty import get_loyalty_account
from acme.tools.ops import get_booking, get_flight_status, search_alternative_flights


def test_get_booking_is_case_insensitive():
    assert get_booking("acme01")["pnr"] == "ACME01"


def test_get_booking_returns_a_copy():
    booking = get_booking("ACME01")
    booking["passengers"].append("Intruder")
    assert len(BOOKINGS["ACME01"]["passengers"]) == 3


def test_unknown_booking_raises_not_invents():
    with pytest.raises(BookingNotFound, match="NOPE99"):
        get_booking("NOPE99")


def test_flight_status():
    assert get_flight_status("AC245")["status"] == "CANCELLED"


def test_alternatives_sorted_by_departure():
    flights = [f["flight_no"] for f in search_alternative_flights("FRA", "HEL")]
    assert flights == ["AC247", "AC1803", "AC251"]


def test_no_alternatives_is_empty_list():
    assert search_alternative_flights("XXX", "YYY") == []


def test_trace_bag_planted_stall():
    start = time.perf_counter()
    result = trace_bag("ARNAC10234")
    elapsed = time.perf_counter() - start
    assert result["status"] == "LOCATED_CDG"
    assert elapsed >= 4.5


def test_fare_rule_basic():
    assert check_fare_rule("B")["change_fee_eur"] == 120


def test_fare_class_z_planted_failure():
    with pytest.raises(FareClassNotFound) as excinfo:
        check_fare_rule("Z")
    message = str(excinfo.value)
    assert "Z" in message
    assert "list_fare_classes" in message


def test_list_fare_classes():
    assert list_fare_classes() == ["B", "J", "M", "Y"]


def test_loyalty_account():
    assert get_loyalty_account("LY3003")["tier"] == "Gold"
