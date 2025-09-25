# travel_assistant/services/country_service.py
import requests
from typing import Optional, Dict, Any

class CountryService:
    """Service for fetching country information"""
    
    def __init__(self):
        self.base_url = "https://restcountries.com/v3.1"
    
    def get_country_info(self, country_name: str) -> Optional[Dict[str, Any]]:
        """Get basic country information"""
        try:
            response = requests.get(f"{self.base_url}/name/{country_name}")
            response.raise_for_status()
            
            data = response.json()[0]  # Take first result
            
            return {
                'name': data.get('name', {}).get('common', ''),
                'capital': data.get('capital', ['Unknown'])[0],
                'region': data.get('region', 'Unknown'),
                'subregion': data.get('subregion', 'Unknown'),
                'population': data.get('population', 0),
                'languages': list(data.get('languages', {}).values()) if data.get('languages') else [],
                'currency': list(data.get('currencies', {}).keys())[0] if data.get('currencies') else 'Unknown',
                'timezones': data.get('timezones', [])
            }
        except Exception as e:
            print(f"Country API error: {e}")
            return None