import requests
from typing import Optional, Dict, Any

def extract_product_info(data):
    products = data['body']['results']
    simplified_products = []

    for product in products:
        info = {
                    "id": product["id"],
                    "name": product["name"],
                    "discountedPrice": product["groupRanges"][0]["discountedPrice"],
                    "quantity": product["inventories"][0]["quantity"],
                    "productPurchaseLimit":product["productPurchaseLimit"],
                    
                }
                
        simplified_products.append(info)
        
    return simplified_products

def search_inventory (search_term: str) -> Dict[str, Any]:
    """Search DealCart inventory for products.

    Args:
        search_term: Term to search for in product names

    Returns:
        Dict containing API response with product data
        
    Raises:
        requests.RequestException: If the API call fails
    """
    base_url = "https://api.dealcart.io/api/consumer/products/pricing"
    
    params = {
        "name": search_term,
        "warehouse_id": 1,
        "page": 1,
        "limit": 10
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