"""
MongoDB database connection using motor async driver.
Provides async database and client instances.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from app.core.config import settings
import asyncio


class Database:
    """MongoDB database connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None
    _connected: bool = False
    
    @classmethod
    async def connect(cls) -> None:
        """Establish connection to MongoDB."""
        try:
            cls.client = AsyncIOMotorClient(settings.mongodb_url)
            # Verify connection
            await cls.client.admin.command("ping")
            cls.database = cls.client[settings.database_name]
            cls._connected = True
            print(f"✓ Connected to MongoDB: {settings.database_name}")
        except Exception as e:
            print(f"⚠ MongoDB connection failed: {e}")
            print("⚠ Running in DEMO mode (no database)")
            cls._connected = False
            # Create a mock database for testing
            cls.database = None
    
    @classmethod
    async def disconnect(cls) -> None:
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            print("✓ Disconnected from MongoDB")
    
    @classmethod
    def get_database(cls) -> Optional[AsyncIOMotorDatabase]:
        """Get the database instance."""
        return cls.database
    
    @classmethod
    def get_collection(cls, name: str):
        """Get a specific collection by name."""
        if cls.database is None:
            return None
        return cls.database[name]
    
    @classmethod
    def is_connected(cls) -> bool:
        """Check if MongoDB is connected."""
        return cls._connected


# Collection names as constants
class Collections:
    USERS = "users"
    PRODUCTS = "products"
    ORDERS = "orders"
    CARTS = "carts"
    DELIVERY_JOBS = "delivery_jobs"
    AFFILIATE_COMMISSIONS = "affiliate_commissions"
    AD_CAMPAIGNS = "ad_campaigns"
    REVIEWS = "reviews"
    PAYMENTS = "payments"
    REFRESH_TOKENS = "refresh_tokens"
    CATEGORIES = "categories"