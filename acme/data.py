"""Synthetic Acme Air data. Fictional only, never use operationally."""

NOW = "2026-11-02T10:30"

DISCLAIMER = (
    "Acme Air is fictional. Fares, rules and compensation amounts "
    "are synthetic and are not EU261 advice."
)

BOOKINGS = {
    "ACME01": {
        "pnr": "ACME01",
        "passengers": ["Anna Becker", "Jonas Becker", "Mia Becker"],
        "segments": [
            {"flight_no": "AC101", "origin": "LIS", "destination": "FRA", "departure": "2026-11-02T06:00"},
            {"flight_no": "AC245", "origin": "FRA", "destination": "HEL", "departure": "2026-11-02T10:15"},
        ],
        "fare_class": "M",
        "checked_bags": 3,
        "loyalty_id": None,
        "bag_file_reference": None,
        "pet_in_cabin": False,
        "time_critical": True,
        "owning_desk": "rebooking",
        "situation": "Family of three, Frankfurt connection cancelled, three checked bags",
    },
    "ACME02": {
        "pnr": "ACME02",
        "passengers": ["Claire Dubois"],
        "segments": [
            {"flight_no": "AC330", "origin": "CDG", "destination": "ARN", "departure": "2026-11-01T17:40"},
        ],
        "fare_class": "Y",
        "checked_bags": 1,
        "loyalty_id": None,
        "bag_file_reference": "ARNAC10234",
        "pet_in_cabin": False,
        "time_critical": False,
        "owning_desk": "baggage",
        "situation": "Bag delayed on Paris to Stockholm, file reference raised",
    },
    "ACME03": {
        "pnr": "ACME03",
        "passengers": ["Erik Lindqvist"],
        "segments": [
            {"flight_no": "AC900", "origin": "ARN", "destination": "JFK", "departure": "2026-11-20T11:00"},
        ],
        "fare_class": "Y",
        "checked_bags": 1,
        "loyalty_id": "LY3003",
        "bag_file_reference": None,
        "pet_in_cabin": False,
        "time_critical": False,
        "owning_desk": "loyalty",
        "situation": "Gold member asking for a long-haul upgrade",
    },
    "ACME04": {
        "pnr": "ACME04",
        "passengers": ["Sofia Rossi"],
        "segments": [
            {"flight_no": "AC512", "origin": "FCO", "destination": "MUC", "departure": "2026-11-12T08:25"},
        ],
        "fare_class": "B",
        "checked_bags": 0,
        "loyalty_id": None,
        "bag_file_reference": None,
        "pet_in_cabin": True,
        "time_critical": False,
        "owning_desk": "fares",
        "situation": "Basic fare holder changing dates, pet booked in cabin",
    },
}

FLIGHTS = {
    "AC101": {"flight_no": "AC101", "status": "LANDED", "long_haul": False},
    "AC245": {"flight_no": "AC245", "status": "CANCELLED", "long_haul": False},
    "AC330": {"flight_no": "AC330", "status": "ARRIVED", "long_haul": False},
    "AC900": {"flight_no": "AC900", "status": "SCHEDULED", "long_haul": True},
    "AC512": {"flight_no": "AC512", "status": "SCHEDULED", "long_haul": False},
}

# Deliberately unsorted: search_alternative_flights must sort by departure.
ALTERNATIVES = {
    ("FRA", "HEL"): [
        {"flight_no": "AC251", "departure": "2026-11-02T19:45", "via": None, "seats_available": 9},
        {"flight_no": "AC247", "departure": "2026-11-02T11:10", "via": None, "seats_available": 3},
        {"flight_no": "AC1803", "departure": "2026-11-02T14:05", "via": "MUC", "seats_available": 6},
    ],
}

BAG_TRACES = {
    "ARNAC10234": {
        "file_reference": "ARNAC10234",
        "bag_tag": "AC123456",
        "status": "LOCATED_CDG",
        "forwarded_on": "AC332",
        "delivery_eta": "next day by 18:00",
    },
}

LOYALTY = {
    "LY3003": {
        "loyalty_id": "LY3003",
        "name": "Erik Lindqvist",
        "tier": "Gold",
        "points": 84200,
        "long_haul_upgrade_cost": 60000,
    },
}

# Deliberately no class Z: check_fare_rule("Z") is a planted failure.
FARE_RULES = {
    "Y": {"fare_class": "Y", "name": "Flex", "change_fee_eur": 0, "refundable": True, "pet_in_cabin_fee_eur": 60},
    "J": {"fare_class": "J", "name": "Business", "change_fee_eur": 0, "refundable": True, "pet_in_cabin_fee_eur": 60},
    "M": {"fare_class": "M", "name": "Semi-flex", "change_fee_eur": 75, "refundable": False, "pet_in_cabin_fee_eur": 60},
    "B": {"fare_class": "B", "name": "Basic", "change_fee_eur": 120, "refundable": False, "pet_in_cabin_fee_eur": 60},
}
