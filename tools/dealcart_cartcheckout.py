import requests
from typing import Dict, Any

def checkout_cart(
    latitude: float,
    longitude: float,
    city: str,
    street_address: str,
    area: str
) -> Dict[str, Any]:
    """Checkout the current cart with delivery details.

    Args:
        latitude: Delivery location latitude
        longitude: Delivery location longitude
        city: City name for delivery
        street_address: Street address for delivery
        area: Area/neighborhood name for delivery

    Returns:
        Dict containing:
            - success: bool indicating if checkout was successful
            - body: str containing order confirmation message with order ID
        
    Raises:
        requests.RequestException: If the API call fails
    """
    base_url_staging = "https://api-staging.dealcart.io/api/integration/cart/checkout"
    base_url_production = "https://api.dealcart.io/api/integration/cart/checkout"
    
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
    
    payload = {
        "latitude": latitude,
        "longitude": longitude,
        "city": city,
        "streetAddress": street_address,
        "area": area
    }
    
    try:
        response = requests.post(base_url_production, json=payload, headers=headers_production)
        response.raise_for_status()  # Raise exception for bad status codes

        return response.json()

    except requests.RequestException as e:
        print(f"Error checking out cart: {e}")
        raise
