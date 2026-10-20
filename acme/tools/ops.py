"""Duty manager and rebooking tools: bookings, flight status, alternatives."""

from copy import deepcopy

from acme.data import ALTERNATIVES, BOOKINGS, FLIGHTS
from acme.errors import BookingNotFound, FlightNotFound


def get_booking(pnr: str) -> dict:
    booking = BOOKINGS.get(pnr.upper())
    if booking is None:
        raise BookingNotFound(f"Booking {pnr} not found")
    return deepcopy(booking)


def get_flight_status(flight_no: str) -> dict:
    flight = FLIGHTS.get(flight_no.upper())
    if flight is None:
        raise FlightNotFound(f"Flight {flight_no} not found")
    return deepcopy(flight)


def search_alternative_flights(origin: str, destination: str) -> list[dict]:
    options = ALTERNATIVES.get((origin.upper(), destination.upper()), [])
    return deepcopy(sorted(options, key=lambda flight: flight["departure"]))
