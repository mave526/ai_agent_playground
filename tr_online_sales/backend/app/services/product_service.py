"""
Product service for product catalog management.
"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from app.core.database import Database, Collections
from app.models.product import ProductCreate, ProductUpdate, ProductResponse


class ProductService:
    """Service for handling product operations."""
    
    @staticmethod
    async def create_product(merchant_id: str, product_data: ProductCreate) -> dict:
        """Create a new product."""
        db = Database.get_collection(Collections.PRODUCTS)
        
        now = datetime.utcnow()
        product_doc = {
            "merchant_id": merchant_id,
            "name": product_data.name,
            "description": product_data.description,
            "category": product_data.category,
            "subcategory": product_data.subcategory,
            "price": product_data.price,
            "original_price": product_data.original_price,
            "images": product_data.images,
            "tags": product_data.tags,
            "variants": [v.model_dump() for v in product_data.variants],
            "commission_rate": product_data.commission_rate,
            "ad_budget": product_data.ad_budget,
            "rating": 0.0,
            "review_count": 0,
            "sold_count": 0,
            "is_active": product_data.is_active,
            "created_at": now,
            "updated_at": now,
        }
        
        result = await db.insert_one(product_doc)
        product_doc["_id"] = str(result.inserted_id)
        
        return product_doc
    
    @staticmethod
    async def get_product(product_id: str) -> Optional[dict]:
        """Get a product by ID."""
        db = Database.get_collection(Collections.PRODUCTS)
        
        try:
            product = await db.find_one({"_id": ObjectId(product_id)})
        except Exception:
            return None
        
        if product:
            product["_id"] = str(product["_id"])
        return product
    
    @staticmethod
    async def update_product(
        product_id: str, 
        merchant_id: str, 
        product_data: ProductUpdate
    ) -> Optional[dict]:
        """Update a product (only by the owner merchant)."""
        db = Database.get_collection(Collections.PRODUCTS)
        
        # Build update document
        update_data = {k: v for k, v in product_data.model_dump().items() if v is not None}
        
        # Handle variants specially
        if "variants" in update_data and update_data["variants"]:
            update_data["variants"] = [v.model_dump() if hasattr(v, 'model_dump') else v for v in update_data["variants"]]
        
        update_data["updated_at"] = datetime.utcnow()
        
        result = await db.find_one_and_update(
            {"_id": ObjectId(product_id), "merchant_id": merchant_id},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            result["_id"] = str(result["_id"])
        
        return result
    
    @staticmethod
    async def delete_product(product_id: str, merchant_id: str) -> bool:
        """Delete a product (only by the owner merchant)."""
        db = Database.get_collection(Collections.PRODUCTS)
        
        result = await db.delete_one({
            "_id": ObjectId(product_id),
            "merchant_id": merchant_id
        })
        
        return result.deleted_count > 0
    
    @staticmethod
    async def list_products(
        merchant_id: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """List products with filters and pagination."""
        db = Database.get_collection(Collections.PRODUCTS)
        
        # Build query
        query = {"is_active": True}
        
        if merchant_id:
            query["merchant_id"] = merchant_id
        
        if category:
            query["category"] = category
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"tags": {"$in": [search]}}
            ]
        
        # Get total count
        total = await db.count_documents(query)
        
        # Get products
        skip = (page - 1) * per_page
        cursor = db.find(query).skip(skip).limit(per_page).sort("created_at", -1)
        products = await cursor.to_list(length=per_page)
        
        # Convert ObjectId to string
        for product in products:
            product["_id"] = str(product["_id"])
        
        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "products": products
        }
    
    @staticmethod
    async def get_products_by_ids(product_ids: List[str]) -> List[dict]:
        """Get multiple products by IDs."""
        db = Database.get_collection(Collections.PRODUCTS)
        
        products = await db.find({
            "_id": {"$in": [ObjectId(pid) for pid in product_ids]},
            "is_active": True
        }).to_list(length=len(product_ids))
        
        for product in products:
            product["_id"] = str(product["_id"])
        
        return products
    
    @staticmethod
    async def get_featured_products(limit: int = 10) -> List[dict]:
        """Get featured products (highest rating)."""
        db = Database.get_collection(Collections.PRODUCTS)
        
        products = await db.find({"is_active": True}).sort("rating", -1).limit(limit).to_list(length=limit)
        
        for product in products:
            product["_id"] = str(product["_id"])
        
        return products
    
    @staticmethod
    async def get_products_by_category(category: str, limit: int = 20) -> List[dict]:
        """Get products by category."""
        db = Database.get_collection(Collections.PRODUCTS)
        
        products = await db.find({
            "category": category,
            "is_active": True
        }).sort("sold_count", -1).limit(limit).to_list(length=limit)
        
        for product in products:
            product["_id"] = str(product["_id"])
        
        return products