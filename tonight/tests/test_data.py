"""Test assertions for acme/data.py - all from BUILD_SPEC.md Task 1."""

from pathlib import Path
from copy import deepcopy


def test_all_bookings_present():
    """Assert: set(BOOKINGS) == {'ACME01','ACME02','ACME03','ACME04'}"""
    assert set(BOOKINGS.keys()) == {"ACME01", "ACME02", "ACME03", "ACME04"}


def test_all_bookings_have_same_keys():
    """Assert: every booking has the same set of keys as ACME01"""
    acme01_keys = set(BOOKINGS["ACME01"].keys())
    for pnr in BOOKINGS.keys():
        assert set(BOOKINGS[pnr].keys()) == acme01_keys, f"{pnr} has unexpected keys: {set(BOOKINGS[pnr].keys()) - acme01_keys}"


def test_z_not_in_fare_rules():
    """Assert: 'Z' not in FARE_RULES (deliberate omission)"""
    assert "Z" not in FARE_RULES


def test_acme01_has_3_passengers():
    """Assert: ACME01 has 3 passengers"""
    assert len(BOOKINGS["ACME01"]["passengers"]) == 3


def test_acme01_checked_bags_3():
    """Assert: ACME01 has checked_bags == 3"""
    assert BOOKINGS["ACME01"]["checked_bags"] == 3


def test_segments_flight_nos_in_flights():
    """Assert: every segment's flight_no is in FLIGHTS"""
    all_flight_numbers = set()
    for segments in BOOKINGS.values():
        for segment in segments["segments"]:
            all_flight_numbers.add(segment["flight_no"])
    
    for flight_number in all_flight_numbers:
        assert flight_number in FLIGHTS


def test_disclaimer_exact():
    """Assert: DISCLAIMER equals the exact sentence from spec"""
    expected = "Acme Air is fictional. Fares, rules and compensation amounts are synthetic and are not EU261 advice."
    assert DISCLAIMER == expected


if __name__ == "__main__":
    import sys
    
    try:
        # Import errors for testing  
        from acme.errors import ToolError, BookingNotFound, FlightNotFound, BagNotFound, LoyaltyAccountNotFound, FareClassNotFound
        
        print("✓ All imports successful")
        
        # Run tests
        test_all_bookings_present()
        print("✓ test_all_bookings_present passed")
        
        test_all_bookings_have_same_keys()
        print("✓ test_all_bookings_have_same_keys passed")
        
        test_z_not_in_fare_rules()
        print("✓ test_z_not_in_fare_rules passed")
        
        test_acme01_has_3_passengers()
        print("✓ test_acme01_has_3_passengers passed")
        
        test_acme01_checked_bags_3()
        print("✓ test_acme01_checked_bags_3 passed")
        
        test_segments_flight_nos_in_flights()
        print("✓ test_segments_flight_nos_in_flights passed")
        
        test_disclaimer_exact()
        print("✓ test_disclaimer_exact passed")
        
        print("\nAll tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ ASSERTION FAILED: {e}")
        sys.exit(1)
    finally:
        import traceback
        traceback.print_exc()
