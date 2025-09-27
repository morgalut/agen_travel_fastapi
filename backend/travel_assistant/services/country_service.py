# travel_assistant/services/country_service.py
import requests
import logging
from typing import Optional, Dict, Any, List

from ..utils.helpers import geocode_location, reverse_geocode_country


# Setup logger
logger = logging.getLogger(__name__)


# -------------------- Country Service --------------------
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
            # 1) Try to resolve a country name
            resolved_country = None
            coords = geocode_location(place_name)
            if coords:
                # prefer forward geocode country
                resolved_country = coords.get("country")
                if not resolved_country:
                    # reverse fallback
                    rev = reverse_geocode_country(coords["lat"], coords["lon"])
                    resolved_country = rev.get("country") if rev else None

            # 2) Query RestCountries
            params = {"fields": "name,capital,region,subregion,population,languages,currencies,timezones"}
            resp = None

            # Prefer resolved country; else try by name directly
            if resolved_country:
                resp = requests.get(f"{self.base_url}/name/{resolved_country}", params=params, timeout=10)
            else:
                resp = requests.get(f"{self.base_url}/name/{place_name}", params=params, timeout=10)

            # Capital fallback for cases like “Paris”
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

# -------------------- Hotel Service --------------------
class HotelService:
    """
    Fetch hotels & accommodations using Overpass API (OpenStreetMap).
    No API key required.
    """

    def __init__(self):
        self.base_url = "https://overpass-api.de/api/interpreter"
        logger.debug("HotelService initialized (Overpass)")

    def get_hotels_nearby(self, lat: float, lon: float, radius: int = 3000, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get a list of nearby hotels/hostels (basic info).
        """
        logger.info(f" Fetching hotels near {lat},{lon}")
        print(f"[hotel_service]  Hotels lookup for {lat},{lon}")

        query = f"""
        [out:json];
        (
          node(around:{radius},{lat},{lon})["tourism"="hotel"];
          node(around:{radius},{lat},{lon})["tourism"="hostel"];
          node(around:{radius},{lat},{lon})["tourism"="guest_house"];
        );
        out body {limit};
        """

        try:
            resp = requests.post(self.base_url, data={"data": query}, timeout=15)
            resp.raise_for_status()
            elements = resp.json().get("elements", [])

            hotels = [
                {
                    "name": el.get("tags", {}).get("name", "Unnamed Hotel"),
                    "lat": el.get("lat"),
                    "lon": el.get("lon"),
                    "type": el.get("tags", {}).get("tourism", "hotel")
                }
                for el in elements[:limit]
            ]

            logger.info(f" Found {len(hotels)} hotels")
            print(f"[hotel_service]  Found {len(hotels)} hotels near {lat},{lon}")
            return hotels
        except Exception as e:
            logger.error(f" Hotel API error: {e}", exc_info=True)
            print(f"[hotel_service]  Failed to fetch hotels: {e}")
            return []


# -------------------- Transport Service --------------------
class TransportService:
    """
    Fetch transport info using Overpass API (OpenStreetMap).
    Example: nearby train/metro/bus stations.
    """

    def __init__(self):
        self.base_url = "https://overpass-api.de/api/interpreter"
        logger.debug("TransportService initialized")

    def get_transport_stops(self, lat: float, lon: float, radius: int = 1000) -> List[Dict[str, Any]]:
        """
        Get transport stops (bus, train, metro) within a radius.
        """
        logger.info(f" Fetching transport stops near {lat},{lon}")
        print(f"[transport_service]  Transport stops lookup for {lat},{lon}")

        query = f"""
        [out:json];
        (
          node(around:{radius},{lat},{lon})[public_transport=platform];
          node(around:{radius},{lat},{lon})[railway=station];
          node(around:{radius},{lat},{lon})[highway=bus_stop];
        );
        out body;
        """

        try:
            resp = requests.post(self.base_url, data={"data": query}, timeout=15)
            resp.raise_for_status()
            elements = resp.json().get("elements", [])
            stops = [
                {
                    "name": el.get("tags", {}).get("name", "Unnamed Stop"),
                    "type": el.get("tags", {}).get("railway") or el.get("tags", {}).get("highway"),
                    "lat": el.get("lat"),
                    "lon": el.get("lon"),
                }
                for el in elements
            ]
            logger.info(f" Found {len(stops)} stops")
            return stops
        except Exception as e:
            logger.error(f" Transport API error: {e}", exc_info=True)
            print(f"[transport_service]  Failed to fetch transport info: {e}")
            return []


# -------------------- Attractions Service --------------------
class AttractionsService:
    """
    Fetch tourist attractions using Overpass API (OpenStreetMap).
    Works globally (e.g., France, USA, Japan).
    """

    def __init__(self):
        self.base_url = "https://overpass-api.de/api/interpreter"
        logger.debug("AttractionsService initialized")

    def get_attractions(self, lat: float, lon: float, radius: int = 5000, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get tourist attractions (museums, historic sites, landmarks, parks).
        """
        logger.info(f" Fetching attractions near {lat},{lon}")
        print(f"[attractions_service]  Attractions lookup for {lat},{lon}")

        query = f"""
        [out:json];
        (
          node(around:{radius},{lat},{lon})["tourism"="museum"];
          node(around:{radius},{lat},{lon})["tourism"="attraction"];
          node(around:{radius},{lat},{lon})["historic"];
          node(around:{radius},{lat},{lon})["tourism"="theme_park"];
          node(around:{radius},{lat},{lon})["natural"];
        );
        out body {limit};
        """

        try:
            resp = requests.post(self.base_url, data={"data": query}, timeout=20)
            resp.raise_for_status()
            elements = resp.json().get("elements", [])

            attractions = [
                {
                    "name": el.get("tags", {}).get("name", "Unnamed Attraction"),
                    "type": (
                        el.get("tags", {}).get("tourism")
                        or el.get("tags", {}).get("historic")
                        or el.get("tags", {}).get("natural")
                        or "attraction"
                    ),
                    "lat": el.get("lat"),
                    "lon": el.get("lon"),
                }
                for el in elements[:limit]
            ]

            logger.info(f" Found {len(attractions)} attractions")
            print(f"[attractions_service]  Found {len(attractions)} attractions near {lat},{lon}")
            return attractions
        except Exception as e:
            logger.error(f" Attractions API error: {e}", exc_info=True)
            print(f"[attractions_service]  Failed to fetch attractions: {e}")
            return []


    def get_attractions_by_country_code(self, iso2: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get attractions across a whole country via ISO3166-1 alpha-2 code (e.g., 'FR', 'US').
        """
        iso2 = iso2.upper()
        query = f"""
        [out:json][timeout:25];
        area["ISO3166-1"="{iso2}"][admin_level=2]->.country;
        (
        node["tourism"~"^(attraction|museum|theme_park)$"](area.country);
        way["tourism"~"^(attraction|museum|theme_park)$"](area.country);
        relation["tourism"~"^(attraction|museum|theme_park)$"](area.country);
        node["historic"](area.country);
        way["historic"](area.country);
        relation["historic"](area.country);
        node["natural"](area.country);
        way["natural"](area.country);
        relation["natural"](area.country);
        );
        out center {limit};
        """

        try:
            resp = requests.post(self.base_url, data={"data": query}, timeout=30)
            resp.raise_for_status()
            elements = resp.json().get("elements", [])
            out = []
            for el in elements[:limit]:
                tags = el.get("tags", {})
                center = el.get("center") or {}
                lat = el.get("lat") or center.get("lat")
                lon = el.get("lon") or center.get("lon")
                out.append({
                    "name": tags.get("name", "Unnamed Attraction"),
                    "type": tags.get("tourism") or tags.get("historic") or tags.get("natural") or "attraction",
                    "lat": lat, "lon": lon,
                })
            return out
        except Exception as e:
            logger.error(f" Attractions-by-country API error: {e}", exc_info=True)
            return []