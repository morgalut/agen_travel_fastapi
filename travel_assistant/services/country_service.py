# travel_assistant/services/country_service.py
import requests
import logging
from typing import Optional, Dict, Any

# Setup logger
logger = logging.getLogger(__name__)

class CountryService:
    """Service for fetching country information"""
    
    def __init__(self):
        self.base_url = "https://restcountries.com/v3.1"
        logger.debug(f"CountryService initialized with base_url={self.base_url}")

    def get_country_info(self, country_name: str) -> Optional[Dict[str, Any]]:
        """Get basic country information"""
        logger.info(f"🌍 Fetching country info for: {country_name}")
        print(f"[country_service] 🌍 Looking up information for: {country_name}")

        try:
            response = requests.get(f"{self.base_url}/name/{country_name}", timeout=10)
            logger.debug(f"Country API request URL: {response.url} | Status={response.status_code}")
            response.raise_for_status()
            
            data = response.json()[0]  # Take first result
            logger.debug(f"Raw country API data received: {str(data)[:200]}...")

            result = {
                'name': data.get('name', {}).get('common', ''),
                'capital': data.get('capital', ['Unknown'])[0],
                'region': data.get('region', 'Unknown'),
                'subregion': data.get('subregion', 'Unknown'),
                'population': data.get('population', 0),
                'languages': list(data.get('languages', {}).values()) if data.get('languages') else [],
                'currency': list(data.get('currencies', {}).keys())[0] if data.get('currencies') else 'Unknown',
                'timezones': data.get('timezones', [])
            }

            logger.info(f"✅ Country info retrieved successfully for {country_name}")
            print(f"[country_service] ✅ Country info ready for {country_name}: {result['capital']}, {result['region']}")
            return result

        except Exception as e:
            logger.error(f"❌ Country API error for {country_name}: {e}", exc_info=True)
            print(f"[country_service] ❌ Failed to fetch country info for {country_name}: {e}")
            return None
