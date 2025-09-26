# travel_assistant/utils/helpers.py
import json
import requests
import logging
from typing import Optional, Dict, Any

# Configure logger for this module
logger = logging.getLogger(__name__)


def geocode_location(city: str) -> Optional[Dict[str, float]]:
    """Convert a city name to latitude/longitude using Nominatim (OpenStreetMap)."""
    logger.info(f"🌍 Geocoding request for city: {city}")
    print(f"[helpers] 🌍 Looking up coordinates for: {city}")

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1}

    try:
        resp = requests.get(url, params=params, headers={"User-Agent": "travel-assistant"}, timeout=10)
        logger.debug(f"Geocode API call URL: {resp.url} | Status: {resp.status_code}")

        if resp.ok and resp.json():
            data = resp.json()[0]
            coords = {"lat": float(data["lat"]), "lon": float(data["lon"])}
            logger.info(f"✅ Geocode success: {city} → {coords}")
            print(f"[helpers] ✅ Found coordinates for {city}: {coords}")
            return coords

        logger.warning(f"⚠️ Geocode: No results for {city}")
        print(f"[helpers] ⚠️ No geocoding results for {city}")
        return None

    except Exception as e:
        logger.error(f"❌ Geocode API error for {city}: {e}", exc_info=True)
        print(f"[helpers] ❌ Error during geocoding for {city}: {e}")
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
