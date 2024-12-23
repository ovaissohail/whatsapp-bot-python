import requests
from typing import Optional, Dict, Any
from tools.dealcart_search_helper import extract_product_info


def search_inventory (search_term: str) -> Dict[str, Any]:
    """Search DealCart inventory for products.

    Args:
        search_term: Term to search for in product names

    Returns:
        Dict containing API response with the following product data information:
        id, name, discountedPrice (in rupees that the customer pays), quantity (available quantity in the warehouse), productPurchaseLimit (max quantity that can be purchased in a single order)
        
    Raises:
        requests.RequestException: If the API call fails
    """
    base_url = "https://api.dealcart.io/api/consumer/products/pricing"
    
    params = {
        "name": search_term,
        "warehouse_id": 1,
        "page": 1,
        "limit": 15
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise exception for bad status codes

        data = response.json()
        
        result = extract_product_info(data)
        return result

    except requests.RequestException as e:
        print(f"Error fetching inventory: {e}")
        raise
