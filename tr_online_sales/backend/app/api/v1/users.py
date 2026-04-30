"""
User management API endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from typing import Optional
from app.api.v1.auth import get_current_user_id
from app.core.database import Database, Collections
from app.models.user import UserUpdate, UserResponse, UserListResponse
from app.models.enums import UserRole, UserStatus
from app.services.auth_service import AuthService, DEMO_USERS


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=dict)
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """
    Get current user profile.
    """
    # Demo mode
    if not Database.is_connected():
        for user in DEMO_USERS.values():
            if user["_id"] == user_id:
                user_copy = user.copy()
                user_copy.pop("password_hash", None)
                return user_copy
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # MongoDB mode
    user = await Database.get_collection(Collections.USERS).find_one({
        "_id": ObjectId(user_id)
    })
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user["_id"] = str(user["_id"])
    user.pop("password_hash", None)
    
    return user


@router.put("/me", response_model=dict)
async def update_current_user(
    user_data: UserUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update current user profile.
    """
    # Build update document
    update_data = {k: v for k, v in user_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    # Demo mode
    if not Database.is_connected():
        for email, user in DEMO_USERS.items():
            if user["_id"] == user_id:
                user.update(update_data)
                user_copy = user.copy()
                user_copy.pop("password_hash", None)
                return user_copy
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # MongoDB mode
    result = await Database.get_collection(Collections.USERS).update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = await Database.get_collection(Collections.USERS).find_one({
        "_id": ObjectId(user_id)
    })
    user["_id"] = str(user["_id"])
    user.pop("password_hash", None)
    
    return user


@router.get("/{user_id}", response_model=dict)
async def get_user_by_id(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get user by ID (admin only).
    """
    # Check if current user is admin
    current_user = await AuthService.get_current_user(current_user_id)
    
    if not current_user or current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        user = await Database.get_collection(Collections.USERS).find_one({
            "_id": ObjectId(user_id)
        })
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_INVALID_REQUEST,
            detail="Invalid user ID"
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user["_id"] = str(user["_id"])
    user.pop("password_hash", None)
    
    return user


@router.get("/", response_model=dict)
async def list_users(
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    page: int = 1,
    per_page: int = 20,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    List users with pagination (admin only).
    """
    # Check if current user is admin
    current_user = await AuthService.get_current_user(current_user_id)
    
    if not current_user or current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Build query
    query = {}
    if role:
        query["role"] = role.value
    if status:
        query["status"] = status.value
    
    # Get total count
    total = await Database.get_collection(Collections.USERS).count_documents(query)
    
    # Get users
    skip = (page - 1) * per_page
    users = await Database.get_collection(Collections.USERS).find(query).skip(skip).limit(per_page).to_list(length=per_page)
    
    # Convert ObjectId to string
    for user in users:
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
    
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "users": users
    }