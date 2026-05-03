"""
Product API endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from app.api.v1.auth import get_current_user_id
from app.core.database import Database, Collections
from app.models.product import ProductCreate, ProductUpdate, ProductResponse
from app.models.enums import UserRole
from app.services.product_service import ProductService
from bson import ObjectId


router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new product (merchant only).
    """
    # Check if user is merchant
    user = await Database.get_collection(Collections.USERS).find_one({
        "_id": ObjectId(user_id)
    })
    
    if not user or user.get("role") != UserRole.MERCHANT.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only merchants can create products"
        )
    
    try:
        product = await ProductService.create_product(user_id, product_data)
        return product
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{product_id}", response_model=dict)
async def get_product(product_id: str):
    """
    Get a product by ID.
    """
    product = await ProductService.get_product(product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.put("/{product_id}", response_model=dict)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update a product (merchant only - owner can update).
    """
    product = await ProductService.update_product(product_id, user_id, product_data)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or unauthorized"
        )
    
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete a product (merchant only - owner can delete).
    """
    deleted = await ProductService.delete_product(product_id, user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or unauthorized"
        )
    
    return None


@router.get("/", response_model=dict)
async def list_products(
    merchant_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """
    List products with filters and pagination.
    """
    return await ProductService.list_products(
        merchant_id=merchant_id,
        category=category,
        search=search,
        page=page,
        per_page=per_page
    )


@router.get("/featured/products", response_model=dict)
async def get_featured_products(limit: int = Query(10, ge=1, le=50)):
    """
    Get featured products (highest rated).
    """
    products = await ProductService.get_featured_products(limit=limit)
    return {
        "total": len(products),
        "products": products
    }


@router.get("/category/{category}", response_model=dict)
async def get_products_by_category(
    category: str,
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get products by category.
    """
    products = await ProductService.get_products_by_category(category, limit=limit)
    return {
        "total": len(products),
        "category": category,
        "products": products
    }