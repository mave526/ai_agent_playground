"""
API v1 router - combines all v1 endpoints.
"""
from fastapi import APIRouter
from app.api.v1 import auth, users, products, orders, cart


router = APIRouter(prefix="/v1")

# Include routers
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(products.router)
router.include_router(orders.router)
router.include_router(cart.router)