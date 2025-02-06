from geopy.geocoders import Nominatim
from typing import Dict, Optional

def get_location_details(latitude: float, longitude: float) -> Dict[str, str]:
    """Get location details from latitude and longitude coordinates.
    
    Args:
        latitude: The latitude coordinate
        longitude: The longitude coordinate
    """
    try:
        # Initialize Nominatim geocoder
        geolocator = Nominatim(user_agent="dealcart_bot")
        
        # Get location data
        location = geolocator.reverse(f"{latitude}, {longitude}", language="en")
        
        if location and location.raw.get('address'):
            address = location.raw['address']
            
            # Extract relevant information
            details = {
                "city": address.get('city') or address.get('town') or address.get('state_district', 'N/A'),
                "street_address": address.get('road', 'N/A'),
                "area": address.get('suburb') or address.get('neighbourhood') or address.get('residential', 'N/A')
            }
            
            return details
            
    except Exception as e:
        print(f"Error getting location details: {str(e)}")
        
    # Return default structure if anything fails
    return {
        "city": "N/A",
        "street_address": "N/A",
        "area": "N/A"
    } 