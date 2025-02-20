import requests
from typing import Dict, Any

def get_cart_status() -> Dict[str, Any]:
    """Get the current cart status from DealCart.

    Returns:
        Dict containing the current cart information with details about items,

        quantities, and prices
        
    Raises:
        requests.RequestException: If the API call fails
    """
    base_url_staging = "https://api-staging.dealcart.io/api/integration/cart"
    base_url_production = "https://api.dealcart.io/api/integration/cart"
    
    headers_staging = {
        'dc-phone-number': '03310000290',
        'dc-api-key': 'xy@dealc@rt',
        'warehouse': '1'
    }
    
    headers_production = {
        'dc-phone-number': '03310000290',
        'dc-api-key': '8fbc1214-d82d-41ee-9698-fd4f9c108772',
        'warehouse': '1'
    }
    
    try:
        response = requests.get(base_url_production, headers=headers_production)
        response.raise_for_status()  # Raise exception for bad status codes

        return response.json()

    except requests.RequestException as e:
        print(f"Error fetching cart status: {e}")
        raise
