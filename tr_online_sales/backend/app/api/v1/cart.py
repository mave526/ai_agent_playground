"""
Cart API endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from app.api.v1.auth import get_current_user_id
from app.models.order import CartItem
from app.services.cart_service import CartService


router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("/", response_model=dict)
async def get_cart(user_id: str = Depends(get_current_user_id)):
    """
    Get current user's shopping cart.
    """
    return await CartService.get_cart(user_id)


@router.post("/items", response_model=dict, status_code=status.HTTP_200_OK)
async def add_to_cart(
    item: CartItem,
    user_id: str = Depends(get_current_user_id)
):
    """
    Add an item to cart.
    """
    try:
        return await CartService.add_to_cart(user_id, item)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/items/{product_id}", response_model=dict)
async def update_cart_item(
    product_id: str,
    quantity: int = Query(..., ge=0),
    variant_sku: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id)
):
    """
    Update quantity of a cart item. Set quantity to 0 to remove item.
    """
    try:
        return await CartService.update_cart_item(user_id, product_id, quantity, variant_sku)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/items/{product_id}", response_model=dict)
async def remove_from_cart(
    product_id: str,
    variant_sku: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id)
):
    """
    Remove an item from cart.
    """
    try:
        return await CartService.remove_from_cart(user_id, product_id, variant_sku)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/", response_model=dict)
async def clear_cart(user_id: str = Depends(get_current_user_id)):
    """
    Clear all items from cart.
    """
    return await CartService.clear_cart(user_id)