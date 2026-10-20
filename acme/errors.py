class ToolError(Exception):
    """Base class for every error a tool raises on purpose."""


class BookingNotFound(ToolError): ...


class FlightNotFound(ToolError): ...


class BagNotFound(ToolError): ...


class LoyaltyAccountNotFound(ToolError): ...


class FareClassNotFound(ToolError): ...
