"""
API v1 router - combines all v1 endpoints.
"""
from fastapi import APIRouter
from app.api.v1 import auth, users


router = APIRouter(prefix="/v1")

# Include routers
router.include_router(auth.router)
router.include_router(users.router)