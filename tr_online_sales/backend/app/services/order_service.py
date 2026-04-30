"""
Order service for order management.
"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from app.core.database import Database, Collections
from app.models.order import OrderCreate, OrderUpdate, OrderResponse, OrderStatus, PaymentStatus


class OrderService:
    """Service for handling order operations."""
    
    @staticmethod
    async def create_order(
        consumer_id: str, 
        merchant_id: str,
        order_data: OrderCreate
    ) -> dict:
        """Create a new order."""
        db = Database.get_collection(Collections.ORDERS)
        
        # Calculate totals
        subtotal = sum(item.total_price for item in order_data.items)
        shipping_cost = 0.0  # Could be calculated based on address
        tax = subtotal * 0.07  # 7% VAT
        total_amount = subtotal + shipping_cost + tax
        
        now = datetime.utcnow()
        
        # Generate order number
        order_number = f"TR{now.strftime('%Y%m%d%H%M%S')}{ObjectId().hex[:6].upper()}"
        
        order_doc = {
            "order_number": order_number,
            "consumer_id": consumer_id,
            "merchant_id": merchant_id,
            "items": [item.model_dump() for item in order_data.items],
            "subtotal": subtotal,
            "shipping_cost": shipping_cost,
            "tax": tax,
            "total_amount": total_amount,
            "status": OrderStatus.PENDING.value,
            "payment_status": PaymentStatus.PENDING.value,
            "shipping_address": order_data.shipping_address.model_dump(),
            "delivery_agent_id": None,
            "tracking_number": None,
            "notes": order_data.notes,
            "created_at": now,
            "updated_at": now,
        }
        
        result = await db.insert_one(order_doc)
        order_doc["_id"] = str(result.inserted_id)
        
        return order_doc
    
    @staticmethod
    async def get_order(order_id: str) -> Optional[dict]:
        """Get an order by ID."""
        db = Database.get_collection(Collections.ORDERS)
        
        try:
            order = await db.find_one({"_id": ObjectId(order_id)})
        except Exception:
            return None
        
        if order:
            order["_id"] = str(order["_id"])
        return order
    
    @staticmethod
    async def update_order_status(
        order_id: str, 
        status: OrderStatus,
        user_id: str,
        user_role: str
    ) -> Optional[dict]:
        """Update order status."""
        db = Database.get_collection(Collections.ORDERS)
        
        order = await db.find_one({"_id": ObjectId(order_id)})
        if not order:
            return None
        
        # Authorization check
        if user_role == "merchant":
            if order["merchant_id"] != user_id:
                return None
        elif user_role == "consumer":
            if order["consumer_id"] != user_id:
                return None
        # Admin can update any order
        
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow()
        }
        
        result = await db.find_one_and_update(
            {"_id": ObjectId(order_id)},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            result["_id"] = str(result["_id"])
        
        return result
    
    @staticmethod
    async def get_orders_by_consumer(
        consumer_id: str,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """Get orders by consumer."""
        db = Database.get_collection(Collections.ORDERS)
        
        query = {"consumer_id": consumer_id}
        
        total = await db.count_documents(query)
        
        skip = (page - 1) * per_page
        cursor = db.find(query).skip(skip).limit(per_page).sort("created_at", -1)
        orders = await cursor.to_list(length=per_page)
        
        for order in orders:
            order["_id"] = str(order["_id"])
        
        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "orders": orders
        }
    
    @staticmethod
    async def get_orders_by_merchant(
        merchant_id: str,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """Get orders by merchant."""
        db = Database.get_collection(Collections.ORDERS)
        
        query = {"merchant_id": merchant_id}
        
        total = await db.count_documents(query)
        
        skip = (page - 1) * per_page
        cursor = db.find(query).skip(skip).limit(per_page).sort("created_at", -1)
        orders = await cursor.to_list(length=per_page)
        
        for order in orders:
            order["_id"] = str(order["_id"])
        
        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "orders": orders
        }
    
    @staticmethod
    async def get_order_by_number(order_number: str) -> Optional[dict]:
        """Get an order by order number."""
        db = Database.get_collection(Collections.ORDERS)
        
        order = await db.find_one({"order_number": order_number})
        
        if order:
            order["_id"] = str(order["_id"])
        
        return order
    
    @staticmethod
    async def cancel_order(order_id: str, user_id: str, user_role: str) -> Optional[dict]:
        """Cancel an order."""
        db = Database.get_collection(Collections.ORDERS)
        
        order = await db.find_one({"_id": ObjectId(order_id)})
        if not order:
            return None
        
        # Only consumer or admin can cancel
        if user_role == "consumer" and order["consumer_id"] != user_id:
            return None
        
        # Can only cancel pending or paid orders
        if order["status"] not in [OrderStatus.PENDING.value, OrderStatus.PAID.value]:
            return None
        
        update_data = {
            "status": OrderStatus.CANCELLED.value,
            "updated_at": datetime.utcnow()
        }
        
        result = await db.find_one_and_update(
            {"_id": ObjectId(order_id)},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            result["_id"] = str(result["_id"])
        
        return result