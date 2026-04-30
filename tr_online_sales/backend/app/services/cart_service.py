"""
Cart service for shopping cart management.
"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from app.core.database import Database, Collections
from app.models.order import CartItem, CartCreate, CartItemResponse


class CartService:
    """Service for handling cart operations."""
    
    @staticmethod
    async def get_cart(user_id: str) -> dict:
        """Get user's cart."""
        db = Database.get_collection(Collections.CARTS)
        
        cart = await db.find_one({"user_id": user_id})
        
        if not cart:
            return {
                "user_id": user_id,
                "items": [],
                "total_items": 0,
                "total_amount": 0.0
            }
        
        # Get product details for each item
        product_ids = [item["product_id"] for item in cart.get("items", [])]
        
        if product_ids:
            products = await Database.get_collection(Collections.PRODUCTS).find({
                "_id": {"$in": [ObjectId(pid) for pid in product_ids]},
                "is_active": True
            }).to_list(length=len(product_ids))
            
            product_map = {str(p["_id"]): p for p in products}
            
            # Build cart items with product details
            cart_items = []
            total_amount = 0.0
            
            for item in cart.get("items", []):
                product = product_map.get(item["product_id"])
                if product:
                    unit_price = product["price"]
                    # Check if variant specified
                    if item.get("variant_sku"):
                        for variant in product.get("variants", []):
                            if variant.get("sku") == item["variant_sku"]:
                                unit_price = variant.get("price", unit_price)
                                break
                    
                    total_price = unit_price * item["quantity"]
                    
                    cart_items.append({
                        "product_id": item["product_id"],
                        "product_name": product["name"],
                        "variant_sku": item.get("variant_sku"),
                        "quantity": item["quantity"],
                        "unit_price": unit_price,
                        "total_price": total_price,
                        "image_url": product["images"][0] if product.get("images") else None
                    })
                    
                    total_amount += total_price
        else:
            cart_items = []
            total_amount = 0.0
        
        return {
            "user_id": user_id,
            "items": cart_items,
            "total_items": sum(item["quantity"] for item in cart_items),
            "total_amount": total_amount
        }
    
    @staticmethod
    async def add_to_cart(user_id: str, item: CartItem) -> dict:
        """Add item to cart."""
        db = Database.get_collection(Collections.CARTS)
        
        # Check if product exists
        product = await Database.get_collection(Collections.PRODUCTS).find_one({
            "_id": ObjectId(item.product_id),
            "is_active": True
        })
        
        if not product:
            raise ValueError("Product not found")
        
        # Check stock
        if item.variant_sku:
            for variant in product.get("variants", []):
                if variant.get("sku") == item.variant_sku:
                    if variant.get("stock", 0) < item.quantity:
                        raise ValueError("Insufficient stock")
                    break
        else:
            # Simple stock check (could be enhanced)
            pass
        
        # Find or create cart
        cart = await db.find_one({"user_id": user_id})
        
        now = datetime.utcnow()
        
        if not cart:
            # Create new cart
            cart_doc = {
                "user_id": user_id,
                "items": [{
                    "product_id": item.product_id,
                    "variant_sku": item.variant_sku,
                    "quantity": item.quantity
                }],
                "created_at": now,
                "updated_at": now
            }
            await db.insert_one(cart_doc)
        else:
            # Update existing cart
            items = cart.get("items", [])
            
            # Check if product already in cart
            found = False
            for existing_item in items:
                if existing_item["product_id"] == item.product_id:
                    if existing_item.get("variant_sku") == item.variant_sku:
                        existing_item["quantity"] += item.quantity
                        found = True
                        break
            
            if not found:
                items.append({
                    "product_id": item.product_id,
                    "variant_sku": item.variant_sku,
                    "quantity": item.quantity
                })
            
            await db.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "items": items,
                        "updated_at": now
                    }
                }
            )
        
        return await CartService.get_cart(user_id)
    
    @staticmethod
    async def update_cart_item(
        user_id: str, 
        product_id: str, 
        quantity: int,
        variant_sku: Optional[str] = None
    ) -> dict:
        """Update cart item quantity."""
        db = Database.get_collection(Collections.CARTS)
        
        cart = await db.find_one({"user_id": user_id})
        
        if not cart:
            raise ValueError("Cart not found")
        
        items = cart.get("items", [])
        
        for item in items:
            if item["product_id"] == product_id:
                if item.get("variant_sku") == variant_sku:
                    if quantity <= 0:
                        items.remove(item)
                    else:
                        item["quantity"] = quantity
                    break
        
        await db.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "items": items,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return await CartService.get_cart(user_id)
    
    @staticmethod
    async def remove_from_cart(
        user_id: str, 
        product_id: str,
        variant_sku: Optional[str] = None
    ) -> dict:
        """Remove item from cart."""
        return await CartService.update_cart_item(user_id, product_id, 0, variant_sku)
    
    @staticmethod
    async def clear_cart(user_id: str) -> dict:
        """Clear all items from cart."""
        db = Database.get_collection(Collections.CARTS)
        
        await db.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "items": [],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "user_id": user_id,
            "items": [],
            "total_items": 0,
            "total_amount": 0.0
        }