from acme.data import BOOKINGS, DISCLAIMER, FARE_RULES, FLIGHTS


def test_four_bookings():
    assert set(BOOKINGS) == {"ACME01", "ACME02", "ACME03", "ACME04"}


def test_bookings_share_one_shape():
    keys = set(BOOKINGS["ACME01"])
    for pnr, booking in BOOKINGS.items():
        assert set(booking) == keys, pnr


def test_class_z_is_missing_on_purpose():
    assert "Z" not in FARE_RULES


def test_acme01_family_of_three_with_three_bags():
    booking = BOOKINGS["ACME01"]
    assert len(booking["passengers"]) == 3
    assert booking["checked_bags"] == 3


def test_every_segment_has_a_flight():
    for booking in BOOKINGS.values():
        for segment in booking["segments"]:
            assert segment["flight_no"] in FLIGHTS


def test_disclaimer_is_exact():
    assert DISCLAIMER == (
        "Acme Air is fictional. Fares, rules and compensation amounts "
        "are synthetic and are not EU261 advice."
    )
