from langchain_core.tools import tool
import requests
from typing import List, Dict, Any

@tool
def create_cart(items: str) -> str:
    """Create a cart with specified items on DealCart.
    
    Args:
        items: String in format "product_id1:quantity1,product_id2:quantity2"
              Example: "1353:1,1352:2" for product 1353 (qty 1) and 1352 (qty 2)
    
    Returns:
        A string indicating if cart creation was successful
    """
    base_url_staging = "https://api-staging.dealcart.io/api/integration/cart/create"
    base_url_production = "https://api.dealcart.io/api/integration/cart/create"
    
    headers_staging = {
        'dc-phone-number': '03310000290',
        'dc-api-key': 'xy@dealc@rt',
        'warehouse': '1',
        'Content-Type': 'application/json'
    }
    
    headers_production = {
        'dc-phone-number': '03310000290',
        'dc-api-key': '8fbc1214-d82d-41ee-9698-fd4f9c108772',
        'warehouse': '1',
        'Content-Type': 'application/json'
    }
    
    # Parse the items string into the required format
    try:
        # Convert "1353:1,1352:2" into proper JSON structure
        items_list = []
        for item in items.split(','):
            if ':' in item:
                product_id, quantity = item.split(':')
                items_list.append({
                    "product": int(product_id.strip()),
                    "quantity": int(quantity.strip())
                })
        
        response = requests.post(base_url_production, json=items_list, headers=headers_production)
        response.raise_for_status()
        
        result = response.json()
        return f"Cart created successfully: {result}"

    except requests.RequestException as e:
        return f"Error creating cart: {str(e)}"
    except ValueError as e:
        return f"Error parsing items format. Please use format 'product_id:quantity,product_id:quantity'. Error: {str(e)}"
