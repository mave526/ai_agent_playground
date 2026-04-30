"""
Pydantic models for user data validation and serialization.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models.enums import UserRole, UserStatus


# --- Base Schemas ---

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole = UserRole.CONSUMER


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None


# --- Profile Schemas ---

class MerchantProfile(BaseModel):
    """Merchant-specific profile fields."""
    store_name: str
    business_type: Optional[str] = None
    business_license: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    is_verified: bool = False


class DeliveryAgentProfile(BaseModel):
    """Delivery agent-specific profile fields."""
    vehicle_type: Optional[str] = None  # car, motorcycle, bicycle
    license_number: Optional[str] = None
    license_expiry: Optional[datetime] = None
    vehicle_plate: Optional[str] = None
    is_available: bool = True
    is_verified: bool = False


class InfluencerProfile(BaseModel):
    """Influencer-specific profile fields."""
    niche: Optional[str] = None
    social_platforms: Optional[List[str]] = None
    followers_count: int = 0
    engagement_rate: float = 0.0
    is_verified: bool = False


class AdvertiserProfile(BaseModel):
    """Advertiser-specific profile fields."""
    company_name: str
    company_registration: Optional[str] = None
    industry: Optional[str] = None
    budget_total: float = 0.0
    spent_amount: float = 0.0
    is_verified: bool = False


# --- Response Schemas ---

class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)."""
    id: str = Field(..., alias="_id")
    email: str
    phone: Optional[str]
    name: str
    role: UserRole
    status: UserStatus
    avatar: Optional[str]
    bio: Optional[str]
    merchant_profile: Optional[MerchantProfile]
    delivery_agent_profile: Optional[DeliveryAgentProfile]
    influencer_profile: Optional[InfluencerProfile]
    advertiser_profile: Optional[AdvertiserProfile]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
        from_attributes = True


class UserInDB(UserResponse):
    """Schema for user stored in database (with password hash)."""
    password_hash: str
    
    class Config:
        populate_by_name = True


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""
    total: int
    users: List[UserResponse]


# --- Auth Schemas ---

class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(BaseModel):
    """Schema for decoded token payload."""
    sub: str  # user_id
    email: str
    role: UserRole
    exp: int
    type: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str