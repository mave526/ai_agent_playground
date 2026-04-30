"""
Pydantic models for order data.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class OrderItem(BaseModel):
    """Individual item in an order."""
    product_id: str
    product_name: str
    variant_sku: Optional[str] = None
    quantity: int = Field(..., gt=0)
    unit_price: float
    total_price: float
    image_url: Optional[str] = None


class ShippingAddress(BaseModel):
    """Shipping address information."""
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str = "Thailand"


class OrderCreate(BaseModel):
    """Schema for creating a new order."""
    items: List[OrderItem] = Field(..., min_length=1)
    shipping_address: ShippingAddress
    notes: Optional[str] = None


class OrderUpdate(BaseModel):
    """Schema for updating order information."""
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None
    tracking_number: Optional[str] = None


class OrderResponse(BaseModel):
    """Schema for order response."""
    id: str = Field(..., alias="_id")
    order_number: str
    consumer_id: str
    merchant_id: str
    items: List[OrderItem]
    subtotal: float
    shipping_cost: float
    tax: float
    total_amount: float
    status: OrderStatus
    payment_status: PaymentStatus
    shipping_address: ShippingAddress
    delivery_agent_id: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class OrderListResponse(BaseModel):
    """Schema for paginated order list response."""
    total: int
    orders: List[OrderResponse]
    page: int
    per_page: int


# --- Cart Schemas ---

class CartItem(BaseModel):
    """Item in shopping cart."""
    product_id: str
    variant_sku: Optional[str] = None
    quantity: int = Field(..., gt=0)


class CartCreate(BaseModel):
    """Schema for cart data."""
    items: List[CartItem] = Field(default_factory=list)


class CartItemResponse(BaseModel):
    """Cart item with product details."""
    product_id: str
    product_name: str
    variant_sku: Optional[str] = None
    quantity: int
    unit_price: float
    total_price: float
    image_url: Optional[str] = None


class CartResponse(BaseModel):
    """Schema for cart response."""
    user_id: str
    items: List[CartItemResponse]
    total_items: int
    total_amount: float