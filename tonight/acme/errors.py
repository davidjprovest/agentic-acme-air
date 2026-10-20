"""Error classes for Acme Air tools - all subclasses of Exception."""

# Base class for tool errors
class ToolError(Exception):
    """Base exception for all tool errors in acme/tools/*.py"""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


# Specific booking error
class BookingNotFound(ToolError):
    """Raised when a booking PNR is not found."""
    
    def __init__(self, pnr: str):
        super().__init__(f"Booking {pnr} not found")


# Specific flight error  
class FlightNotFound(ToolError):
    """Raised when a flight number is not found."""
    
    def __init__(self, flight_no: str):
        super().__init__(f"Flight {flight_no} not found")


# Specific baggage error
class BagNotFound(ToolError):
    """Raised when a bag file reference is not found."""
    
    def __init__(self, file_reference: str):
        super().__init__(f"Bag file {file_reference} not found")


# Specific loyalty account error
class LoyaltyAccountNotFound(ToolError):
    """Raised when a loyalty ID is not found."""
    
    def __init__(self, loyalty_id: str):
        super().__init__(f"Loyalty account {loyalty_id} not found")


# Specific fare class error
class FareClassNotFound(ToolError):
    """Raised when a fare class is not found."""
    
    def __init__(self, fare_class: str):
        super().__init__(f"Fare class {fare_class} not found")
