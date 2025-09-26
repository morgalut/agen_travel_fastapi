# travel_assistant/utils/helpers.py
import json
import requests
import logging
from typing import Optional, Dict, Any

# Configure logger for this module
logger = logging.getLogger(__name__)



def geocode_location(query: str):
    """Forward geocode a place name and return lat/lon + country when available."""
    logger.info(f"🌍 Geocoding request for city: {query}")
    print(f"[helpers] 🌍 Looking up coordinates for: {query}")

    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": query, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        r.raise_for_status()
        js = r.json()
        if js.get("results"):
            res = js["results"][0]
            data = {
                "lat": res["latitude"],
                "lon": res["longitude"],
                "name": res.get("name"),
                "country": res.get("country"),           # ✅ new
                "country_code": res.get("country_code"), # ✅ new (ISO-2)
            }
            logger.info(f"✅ Geocode success: {query} → {data}")
            print(f"[helpers] ✅ Found coordinates for {query}: {data}")
            return data
        return None
    except Exception as e:
        logger.error(f"❌ Geocode error for {query}: {e}", exc_info=True)
        return None



def format_response(response: str) -> str:
    """Format LLM response for better readability"""
    logger.debug("Formatting LLM response")
    print("[helpers] ✏️ Formatting LLM response")

    # Clean up common LLM artifacts
    response = response.replace("\\n", "\n").strip()

    # Ensure proper paragraph spacing
    paragraphs = response.split('\n\n')
    formatted_paragraphs = []

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if paragraph and not paragraph.isspace():
            formatted_paragraphs.append(paragraph)

    formatted = '\n\n'.join(formatted_paragraphs)
    logger.debug(f"Formatted response length: {len(formatted)}")
    return formatted


def validate_travel_data(data: Dict[str, Any]) -> bool:
    """Validate travel-related data"""
    logger.debug(f"Validating travel data: keys={list(data.keys())}")
    print("[helpers] 🔍 Validating travel data")
    required_fields = {
        'destination_recommendation': ['interests'],
        'packing_suggestions': ['destination'],
        'local_attractions': ['destination']
    }
    # Basic validation logic (expand if needed)
    return True


def save_conversation(conversation_data: Dict[str, Any], filename: str):
    """Save conversation to file"""
    logger.info(f"💾 Saving conversation to {filename}")
    print(f"[helpers] 💾 Saving conversation to {filename}")
    try:
        with open(filename, 'w') as f:
            json.dump(conversation_data, f, indent=2)
        logger.info("✅ Conversation saved successfully")
    except Exception as e:
        logger.error(f"❌ Failed to save conversation: {e}", exc_info=True)
        print(f"[helpers] ❌ Failed to save conversation: {e}")


def load_conversation(filename: str) -> Dict[str, Any]:
    """Load conversation from file"""
    logger.info(f"📂 Loading conversation from {filename}")
    print(f"[helpers] 📂 Loading conversation from {filename}")
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        logger.info("✅ Conversation loaded successfully")
        return data
    except Exception as e:
        logger.error(f"❌ Failed to load conversation: {e}", exc_info=True)
        print(f"[helpers] ❌ Failed to load conversation: {e}")
        return {}


def reverse_geocode_country(lat: float, lon: float):
    """Reverse geocode to country and ISO code."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"format": "jsonv2", "lat": lat, "lon": lon, "zoom": 5, "addressdetails": 1},
            headers={"User-Agent": "travel-assistant/1.0 (contact: you@example.com)"},
            timeout=10,
        )
        r.raise_for_status()
        js = r.json()
        addr = js.get("address", {}) or {}
        country = addr.get("country")
        code = addr.get("country_code")
        return {"country": country, "country_code": code.upper() if code else None} if country else None
    except Exception:
        return None