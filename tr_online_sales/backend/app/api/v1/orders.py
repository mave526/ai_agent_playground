"""
Order API endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from app.api.v1.auth import get_current_user_id
from app.core.database import Database, Collections
from app.models.order import OrderCreate, OrderStatus
from app.models.enums import UserRole
from app.services.order_service import OrderService
from bson import ObjectId


router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new order (consumer only).
    """
    # Check if user is consumer
    user = await Database.get_collection(Collections.USERS).find_one({
        "_id": ObjectId(user_id)
    })
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # For now, assume first merchant (in real app, need to get from items)
    # Get first merchant from products in cart
    if not order_data.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one item"
        )
    
    first_product_id = order_data.items[0].product_id
    product = await Database.get_collection(Collections.PRODUCTS).find_one({
        "_id": ObjectId(first_product_id)
    })
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product not found"
        )
    
    merchant_id = product.get("merchant_id")
    
    try:
        order = await OrderService.create_order(user_id, merchant_id, order_data)
        return order
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{order_id}", response_model=dict)
async def get_order(
    order_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get an order by ID (authorization: owner or merchant or admin).
    """
    order = await OrderService.get_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Authorization check
    user = await Database.get_collection(Collections.USERS).find_one({
        "_id": ObjectId(user_id)
    })
    
    if user.get("role") == UserRole.CONSUMER.value:
        if order["consumer_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized"
            )
    elif user.get("role") == UserRole.MERCHANT.value:
        if order["merchant_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized"
            )
    # Admin can see any order
    
    return order


@router.put("/{order_id}/status", response_model=dict)
async def update_order_status(
    order_id: str,
    status: OrderStatus,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update order status.
    """
    user = await Database.get_collection(Collections.USERS).find_one({
        "_id": ObjectId(user_id)
    })
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    order = await OrderService.update_order_status(
        order_id, 
        status, 
        user_id, 
        user.get("role")
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or unauthorized"
        )
    
    return order


@router.get("/my/orders", response_model=dict)
async def get_my_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get current user's orders.
    """
    return await OrderService.get_orders_by_consumer(user_id, page, per_page)


@router.post("/{order_id}/cancel", response_model=dict)
async def cancel_order(
    order_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Cancel an order (consumer or admin only).
    """
    user = await Database.get_collection(Collections.USERS).find_one({
        "_id": ObjectId(user_id)
    })
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    order = await OrderService.cancel_order(order_id, user_id, user.get("role"))
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found, unauthorized, or cannot be cancelled"
        )
    
    return order