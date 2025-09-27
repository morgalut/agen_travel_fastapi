# travel_assistant/services/hotel_service.py
import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class HotelService:
    """Fetch hotels & accommodations using Overpass API (OpenStreetMap)."""

    def __init__(self):
        # Multiple Overpass API mirrors (try them in order)
        self.base_urls = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://lz4.overpass-api.de/api/interpreter"
        ]
        logger.debug("HotelService initialized with multiple mirrors")

    def _build_query(self, lat: float, lon: float, radius: int, limit: int) -> str:
        return f"""
        [out:json][timeout:25];
        (
          node(around:{radius},{lat},{lon})["tourism"="hotel"];
          node(around:{radius},{lat},{lon})["tourism"="hostel"];
          node(around:{radius},{lat},{lon})["tourism"="guest_house"];
        );
        out body {limit};
        """

    def get_hotels_nearby(
        self, lat: float, lon: float, radius: int = 3000, limit: int = 5
    ) -> List[Dict[str, Any]]:
        logger.info(f"Fetching hotels near {lat},{lon}")
        print(f"[hotel_service] Hotels lookup for {lat},{lon}")

        # Retry with multiple mirrors and decreasing radius
        radii = [radius, int(radius * 0.5), int(radius * 0.25)]
        for base_url in self.base_urls:
            for r in radii:
                query = self._build_query(lat, lon, r, limit)
                try:
                    resp = requests.post(base_url, data={"data": query}, timeout=20)
                    resp.raise_for_status()
                    elements = resp.json().get("elements", [])
                    if not elements:
                        continue

                    hotels = [
                        {
                            "name": el.get("tags", {}).get("name", "Unnamed Hotel"),
                            "lat": el.get("lat"),
                            "lon": el.get("lon"),
                            "type": el.get("tags", {}).get("tourism", "hotel"),
                        }
                        for el in elements[:limit]
                    ]
                    logger.info(f"Found {len(hotels)} hotels via {base_url} with radius={r}")
                    print(f"[hotel_service] Found {len(hotels)} hotels near {lat},{lon}")
                    return hotels
                except Exception as e:
                    logger.warning(f"Hotel API error on {base_url} (radius={r}): {e}")

        # If all fails
        logger.error("All hotel API attempts failed")
        print("[hotel_service] Failed to fetch hotels from all mirrors")
        return [
            {
                "name": "Hotel data temporarily unavailable",
                "lat": lat,
                "lon": lon,
                "type": "error"
            }
        ]
