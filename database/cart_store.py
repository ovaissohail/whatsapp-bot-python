from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from pymongo.collection import Collection
from database.config import MongoDBConnection

class CartStore:
    def __init__(self):
        self.db = MongoDBConnection().db
        self.carts: Collection = self.db.carts
        self.cart_items: Collection = self.db.cart_items
        
        # Create indexes
        self.carts.create_index("user_id", unique=True)
        self.cart_items.create_index([("cart_id", 1), ("product_id", 1)], unique=True)

    def get_or_create_cart(self, user_id: str) -> str:
        """Get existing cart or create a new one for the user"""
        cart = self.carts.find_one({"user_id": user_id})
        
        if not cart:
            cart_doc = {
                "user_id": user_id,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "status": "active"
            }
            result = self.carts.insert_one(cart_doc)
            return str(result.inserted_id)
        
        return str(cart["_id"])

    def add_item(self, user_id: str, product_id: int, quantity: int, product_name: str = "") -> Dict[str, Any]:
        """Add an item to the user's cart"""
        cart_id = self.get_or_create_cart(user_id)
        
        # Update if exists, insert if not
        result = self.cart_items.update_one(
            {"cart_id": cart_id, "product_id": product_id},
            {"$set": {
                "quantity": quantity,
                "product_name": product_name,
                "updated_at": datetime.now(UTC)
            }},
            upsert=True
        )
        
        # Update cart's last activity
        self.carts.update_one(
            {"_id": cart_id},
            {"$set": {"updated_at": datetime.now(UTC)}}
        )
        
        return {
            "success": True,
            "product_id": product_id,
            "quantity": quantity,
            "operation": "insert" if result.upserted_id else "update"
        }

    def remove_item(self, user_id: str, product_id: int) -> Dict[str, Any]:
        """Remove an item from the user's cart"""
        cart_id = self.get_or_create_cart(user_id)
        
        result = self.cart_items.delete_one(
            {"cart_id": cart_id, "product_id": product_id}
        )
        
        return {
            "success": result.deleted_count > 0,
            "product_id": product_id
        }

    def get_cart_items(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all items in the user's cart"""
        cart_id = self.get_or_create_cart(user_id)
        
        items = list(self.cart_items.find(
            {"cart_id": cart_id},
            {"_id": 0, "cart_id": 0}
        ))
        
        return items

    def clear_cart(self, user_id: str) -> Dict[str, Any]:
        """Remove all items from the user's cart"""
        cart_id = self.get_or_create_cart(user_id)
        
        result = self.cart_items.delete_many({"cart_id": cart_id})
        
        return {
            "success": True,
            "items_removed": result.deleted_count
        }

    def get_cart_for_dealcart(self, user_id: str) -> List[Dict[str, Any]]:
        """Format cart items for the DealCart API"""
        items = self.get_cart_items(user_id)
        
        dealcart_items = []
        for item in items:
            dealcart_items.append({
                "product": item["product_id"],
                "quantity": item["quantity"]
            })
        
        return dealcart_items 