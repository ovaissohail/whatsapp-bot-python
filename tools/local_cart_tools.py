from langchain_core.tools import tool
from database.cart_store import CartStore
from typing import List, Dict, Any
import os

cart_store = CartStore()

# Global variable to store the current user ID
_CURRENT_USER_ID = "default_user"

def set_current_user_id(user_id):
    """Set the current user ID for cart operations"""
    global _CURRENT_USER_ID
    _CURRENT_USER_ID = user_id

def get_current_user_id():
    """Get the current user ID for cart operations"""
    return _CURRENT_USER_ID

@tool
def add_to_cart(product_id: str, quantity: str, product_name: str = "") -> str:
    """Add an item to the user's cart.
    
    Args:
        product_id: The product ID to add
        quantity: The quantity to add
        product_name: Optional product name for reference
    
    Returns:
        A string indicating if the operation was successful
    """
    try:
        # Get the current user ID
        user_id = get_current_user_id()
        
        product_id_int = int(product_id)
        quantity_int = int(quantity)
        
        if quantity_int <= 0:
            return "Error: Quantity must be greater than zero"
        
        result = cart_store.add_item(
            user_id=user_id,
            product_id=product_id_int,
            quantity=quantity_int,
            product_name=product_name
        )
        
        return f"Successfully added {quantity} of product {product_id} to cart"
        
    except ValueError:
        return "Error: Product ID and quantity must be valid numbers"
    except Exception as e:
        return f"Error adding item to cart: {str(e)}"

@tool
def remove_from_cart(product_id: str) -> str:
    """Remove an item from the user's cart.
    
    Args:
        product_id: The product ID to remove
    
    Returns:
        A string indicating if the operation was successful
    """
    try:
        # Get the current user ID
        user_id = get_current_user_id()
        
        product_id_int = int(product_id)
        
        result = cart_store.remove_item(
            user_id=user_id,
            product_id=product_id_int
        )
        
        if result["success"]:
            return f"Successfully removed product {product_id} from cart"
        else:
            return f"Product {product_id} was not found in the cart"
        
    except ValueError:
        return "Error: Product ID must be a valid number"
    except Exception as e:
        return f"Error removing item from cart: {str(e)}"

@tool
def view_cart() -> str:
    """View all items in the user's cart.
    
    Returns:
        A string listing all items in the cart
    """
    try:
        # Get the current user ID
        user_id = get_current_user_id()
        
        items = cart_store.get_cart_items(user_id)
        
        if not items:
            return "Your cart is empty"
        
        cart_text = "Current cart contents:\n"
        for item in items:
            product_name = item.get("product_name", "")
            name_text = f" ({product_name})" if product_name else ""
            cart_text += f"- Product ID: {item['product_id']}{name_text}, Quantity: {item['quantity']}\n"
        
        return cart_text
        
    except Exception as e:
        return f"Error viewing cart: {str(e)}"

@tool
def clear_cart() -> str:
    """Remove all items from the user's cart.
    
    Returns:
        A string indicating if the operation was successful
    """
    try:
        # Get the current user ID
        user_id = get_current_user_id()
        
        result = cart_store.clear_cart(user_id)
        
        return f"Successfully cleared cart. Removed {result['items_removed']} items."
        
    except Exception as e:
        return f"Error clearing cart: {str(e)}"

@tool
def finalize_cart() -> str:
    """Prepare the cart for checkout with DealCart.
    
    Returns:
        A string in the format needed for the DealCart API
    """
    try:
        # Get the current user ID
        user_id = get_current_user_id()
        
        items = cart_store.get_cart_for_dealcart(user_id)
        
        if not items:
            return "Error: Cannot finalize an empty cart"
        
        # Format as "product_id1:quantity1,product_id2:quantity2"
        items_str = ",".join([f"{item['product']}:{item['quantity']}" for item in items])
        
        return items_str
        
    except Exception as e:
        return f"Error finalizing cart: {str(e)}" 