"""
User role enumerations.
"""
from enum import Enum


class UserRole(str, Enum):
    """Available user roles in the platform."""
    CONSUMER = "consumer"
    MERCHANT = "merchant"
    DELIVERY_AGENT = "delivery_agent"
    INFLUENCER = "influencer"
    ADVERTISER = "advertiser"
    ADMIN = "admin"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"