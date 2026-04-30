"""
Pydantic models for product data.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProductVariant(BaseModel):
    """Product variant (size, color, etc.)."""
    sku: str
    size: Optional[str] = None
    color: Optional[str] = None
    price: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    image_url: Optional[str] = None


class ProductCreate(BaseModel):
    """Schema for creating a new product."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    price: float = Field(..., gt=0)
    original_price: Optional[float] = None
    images: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    variants: List[ProductVariant] = Field(default_factory=list)
    commission_rate: float = Field(default=0.0, ge=0, le=1)  # For influencers
    ad_budget: float = Field(default=0.0, ge=0)  # For advertising
    is_active: bool = True


class ProductUpdate(BaseModel):
    """Schema for updating product information."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    original_price: Optional[float] = None
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    variants: Optional[List[ProductVariant]] = None
    commission_rate: Optional[float] = Field(None, ge=0, le=1)
    ad_budget: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    """Schema for product response."""
    id: str = Field(..., alias="_id")
    merchant_id: str
    name: str
    description: Optional[str]
    category: str
    subcategory: Optional[str]
    price: float
    original_price: Optional[float]
    images: List[str]
    tags: List[str]
    variants: List[ProductVariant]
    commission_rate: float
    ad_budget: float
    rating: float = 0.0
    review_count: int = 0
    sold_count: int = 0
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class ProductListResponse(BaseModel):
    """Schema for paginated product list response."""
    total: int
    products: List[ProductResponse]
    page: int
    per_page: int


class CategoryResponse(BaseModel):
    """Schema for category response."""
    id: str = Field(..., alias="_id")
    name: str
    slug: str
    parent_id: Optional[str] = None
    image: Optional[str] = None
    product_count: int = 0