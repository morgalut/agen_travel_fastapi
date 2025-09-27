import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class HotelService:
    """Fetch hotels & accommodations using Overpass API (OpenStreetMap)."""

    def __init__(self):
        self.base_url = "https://overpass-api.de/api/interpreter"
        logger.debug("HotelService initialized (Overpass)")

    def get_hotels_nearby(self, lat: float, lon: float, radius: int = 3000, limit: int = 5) -> List[Dict[str, Any]]:
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
