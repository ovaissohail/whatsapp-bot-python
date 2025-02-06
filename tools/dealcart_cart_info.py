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
    base_url = "https://api-staging.dealcart.io/api/integration/cart"
    
    headers = {
        'dc-phone-number': '03310000290',
        'dc-api-key': 'xy@dealc@rt',
        'warehouse': '1'
    }
    
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()  # Raise exception for bad status codes

        return response.json()

    except requests.RequestException as e:
        print(f"Error fetching cart status: {e}")
        raise
