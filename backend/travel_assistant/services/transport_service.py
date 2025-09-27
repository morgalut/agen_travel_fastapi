import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TransportService:
    """Fetch transport info using Overpass API (OpenStreetMap)."""

    def __init__(self):
        self.base_url = "https://overpass-api.de/api/interpreter"
        logger.debug("TransportService initialized")

    def get_transport_stops(self, lat: float, lon: float, radius: int = 1000) -> List[Dict[str, Any]]:
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
