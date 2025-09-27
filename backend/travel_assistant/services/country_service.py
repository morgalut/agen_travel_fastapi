import requests
import logging
from typing import Optional, Dict, Any

from ..utils.helpers import geocode_location, reverse_geocode_country

logger = logging.getLogger(__name__)

class CountryService:
    def __init__(self):
        self.base_url = "https://restcountries.com/v3.1"
        logger.debug(f"CountryService initialized with base_url={self.base_url}")

    def _extract_result(self, payload: Any) -> Optional[Dict[str, Any]]:
        if isinstance(payload, list) and payload:
            return payload[0]
        if isinstance(payload, dict):
            return payload
        return None

    def _build_country_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        currencies = data.get("currencies") or {}
        currency = next(iter(currencies.keys()), "Unknown")
        languages = list((data.get("languages") or {}).values())
        return {
            "name": (data.get("name") or {}).get("common", ""),
            "capital": (data.get("capital") or ["Unknown"])[0],
            "region": data.get("region", "Unknown"),
            "subregion": data.get("subregion", "Unknown"),
            "population": data.get("population", 0),
            "languages": languages,
            "currency": currency,
            "timezones": data.get("timezones", []),
        }

    def get_country_info(self, place_name: str) -> Optional[Dict[str, Any]]:
        logger.info(f" Fetching country info for: {place_name}")
        print(f"[country_service]  Looking up information for: {place_name}")

        try:
            resolved_country = None
            coords = geocode_location(place_name)
            if coords:
                resolved_country = coords.get("country")
                if not resolved_country:
                    rev = reverse_geocode_country(coords["lat"], coords["lon"])
                    resolved_country = rev.get("country") if rev else None

            params = {"fields": "name,capital,region,subregion,population,languages,currencies,timezones"}

            if resolved_country:
                resp = requests.get(f"{self.base_url}/name/{resolved_country}", params=params, timeout=10)
            else:
                resp = requests.get(f"{self.base_url}/name/{place_name}", params=params, timeout=10)

            if resp.status_code == 404:
                resp = requests.get(f"{self.base_url}/capital/{place_name}", params=params, timeout=10)

            resp.raise_for_status()
            data = self._extract_result(resp.json())
            if not data:
                logger.warning("Country data empty/unexpected format")
                return None

            result = self._build_country_summary(data)
            logger.info(f" Country info retrieved successfully for {result.get('name')}")
            print(f"[country_service]  Country info ready: {result['capital']}, {result['region']}")
            return result

        except Exception as e:
            logger.error(f" Country API error for {place_name}: {e}", exc_info=True)
            print(f"[country_service]  Failed to fetch country info for {place_name}: {e}")
            return None
