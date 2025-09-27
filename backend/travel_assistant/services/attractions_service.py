import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class AttractionsService:
    """Fetch tourist attractions using Overpass API (OpenStreetMap)."""

    def __init__(self):
        self.base_url = "https://overpass-api.de/api/interpreter"
        logger.debug("AttractionsService initialized")

    def get_attractions(self, lat: float, lon: float, radius: int = 5000, limit: int = 10) -> List[Dict[str, Any]]:
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

            return [
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
        except Exception as e:
            logger.error(f" Attractions API error: {e}", exc_info=True)
            print(f"[attractions_service]  Failed to fetch attractions: {e}")
            return []

    def get_attractions_by_country_code(self, iso2: str, limit: int = 20) -> List[Dict[str, Any]]:
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
