"""
Authentication service for user registration, login, and token management.
"""
from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId
from app.core.database import Database, Collections
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from app.models.enums import UserRole, UserStatus
from app.models.user import UserCreate, UserResponse, TokenResponse


# In-memory storage for demo mode
DEMO_USERS = {}


class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    async def register_user(user_data: UserCreate) -> TokenResponse:
        """
        Register a new user and return authentication tokens.
        """
        # Check if MongoDB is connected
        if not Database.is_connected():
            # Demo mode - use in-memory storage
            if user_data.email in DEMO_USERS:
                raise ValueError("Email already registered")
            
            now = datetime.utcnow()
            user_id = f"demo_{len(DEMO_USERS) + 1}"
            
            DEMO_USERS[user_data.email] = {
                "_id": user_id,
                "email": user_data.email,
                "password_hash": get_password_hash(user_data.password),
                "phone": user_data.phone,
                "name": user_data.name,
                "role": user_data.role.value,
                "status": UserStatus.ACTIVE.value,
                "created_at": now,
                "updated_at": now,
            }
            
            token_data = {"sub": user_id, "email": user_data.email, "role": user_data.role.value}
            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=1800
            )
        
        # Real MongoDB mode
        db = Database.get_collection(Collections.USERS)
        
        # Check if email already exists
        existing = await db.find_one({"email": user_data.email})
        if existing:
            raise ValueError("Email already registered")
        
        # Create user document
        now = datetime.utcnow()
        user_doc = {
            "email": user_data.email,
            "password_hash": get_password_hash(user_data.password),
            "phone": user_data.phone,
            "name": user_data.name,
            "role": user_data.role.value,
            "status": UserStatus.ACTIVE.value,
            "avatar": None,
            "bio": None,
            "merchant_profile": None,
            "delivery_agent_profile": None,
            "influencer_profile": None,
            "advertiser_profile": None,
            "created_at": now,
            "updated_at": now,
        }
        
        # Insert user
        result = await db.insert_one(user_doc)
        user_id = str(result.inserted_id)
        
        # Generate tokens
        token_data = {"sub": user_id, "email": user_data.email, "role": user_data.role.value}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Store refresh token
        await Database.get_collection(Collections.REFRESH_TOKENS).insert_one({
            "user_id": user_id,
            "token": refresh_token,
            "created_at": now,
            "expires_at": datetime.utcnow() + timedelta(days=7)
        })
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800
        )
    
    @staticmethod
    async def login_user(email: str, password: str) -> TokenResponse:
        """
        Authenticate user and return tokens.
        """
        # Demo mode
        if not Database.is_connected():
            user = DEMO_USERS.get(email)
            if not user:
                raise ValueError("Invalid email or password")
            
            if not verify_password(password, user["password_hash"]):
                raise ValueError("Invalid email or password")
            
            user_id = user["_id"]
            token_data = {
                "sub": user_id,
                "email": user["email"],
                "role": user["role"]
            }
            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=1800
            )
        
        # MongoDB mode
        db = Database.get_collection(Collections.USERS)
        
        user = await db.find_one({"email": email})
        if not user:
            raise ValueError("Invalid email or password")
        
        if not verify_password(password, user["password_hash"]):
            raise ValueError("Invalid email or password")
        
        if user.get("status") != UserStatus.ACTIVE.value:
            raise ValueError("Account is not active")
        
        user_id = str(user["_id"])
        
        token_data = {
            "sub": user_id,
            "email": user["email"],
            "role": user["role"]
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        now = datetime.utcnow()
        await Database.get_collection(Collections.REFRESH_TOKENS).insert_one({
            "user_id": user_id,
            "token": refresh_token,
            "created_at": now,
            "expires_at": now + timedelta(days=7)
        })
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800
        )
    
    @staticmethod
    async def refresh_access_token(refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token."""
        if not verify_token_type(refresh_token, "refresh"):
            raise ValueError("Invalid token type")
        
        payload = decode_token(refresh_token)
        if not payload:
            raise ValueError("Invalid or expired token")
        
        user_id = payload.get("sub")
        
        # Demo mode
        if not Database.is_connected():
            # Find user in demo users
            for email, user in DEMO_USERS.items():
                if user["_id"] == user_id:
                    token_data = {
                        "sub": user_id,
                        "email": user["email"],
                        "role": user["role"]
                    }
                    new_access_token = create_access_token(token_data)
                    new_refresh_token = create_refresh_token(token_data)
                    
                    return TokenResponse(
                        access_token=new_access_token,
                        refresh_token=new_refresh_token,
                        token_type="bearer",
                        expires_in=1800
                    )
            raise ValueError("User not found")
        
        # MongoDB mode
        token_doc = await Database.get_collection(Collections.REFRESH_TOKENS).find_one({
            "user_id": user_id,
            "token": refresh_token
        })
        
        if not token_doc:
            raise ValueError("Refresh token not found")
        
        user = await Database.get_collection(Collections.USERS).find_one({
            "_id": ObjectId(user_id)
        })
        
        if not user or user.get("status") != UserStatus.ACTIVE.value:
            raise ValueError("User not found or inactive")
        
        token_data = {
            "sub": user_id,
            "email": user["email"],
            "role": user["role"]
        }
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        now = datetime.utcnow()
        await Database.get_collection(Collections.REFRESH_TOKENS).delete_many({
            "user_id": user_id,
            "token": refresh_token
        })
        await Database.get_collection(Collections.REFRESH_TOKENS).insert_one({
            "user_id": user_id,
            "token": new_refresh_token,
            "created_at": now,
            "expires_at": now + timedelta(days=7)
        })
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=1800
        )
    
    @staticmethod
    async def get_current_user(user_id: str) -> Optional[dict]:
        """Get current user by ID."""
        if not Database.is_connected():
            for user in DEMO_USERS.values():
                if user["_id"] == user_id:
                    return user
            return None
        
        user = await Database.get_collection(Collections.USERS).find_one({
            "_id": ObjectId(user_id)
        })
        return user
    
    @staticmethod
    async def logout_user(user_id: str, refresh_token: str) -> bool:
        """Logout user by removing refresh token."""
        if not Database.is_connected():
            return True
        
        result = await Database.get_collection(Collections.REFRESH_TOKENS).delete_many({
            "user_id": user_id,
            "token": refresh_token
        })
        return result.deleted_count > 0