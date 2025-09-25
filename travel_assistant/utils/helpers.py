# travel_assistant/utils/helpers.py
import json
import requests
from typing import Optional, Dict,Any

def geocode_location(city: str) -> Optional[Dict[str, float]]:
    """Convert a city name to latitude/longitude using Nominatim (OpenStreetMap)."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1}
    resp = requests.get(url, params=params, headers={"User-Agent": "travel-assistant"})
    if resp.ok and resp.json():
        data = resp.json()[0]
        return {"lat": float(data["lat"]), "lon": float(data["lon"])}
    return None


def format_response(response: str) -> str:
    """Format LLM response for better readability"""
    # Clean up common LLM artifacts
    response = response.replace("\\n", "\n").strip()
    
    # Ensure proper paragraph spacing
    paragraphs = response.split('\n\n')
    formatted_paragraphs = []
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if paragraph and not paragraph.isspace():
            formatted_paragraphs.append(paragraph)
    
    return '\n\n'.join(formatted_paragraphs)

def validate_travel_data(data: Dict[str, Any]) -> bool:
    """Validate travel-related data"""
    required_fields = {
        'destination_recommendation': ['interests'],
        'packing_suggestions': ['destination'],
        'local_attractions': ['destination']
    }
    
    # Basic validation logic
    return True  # Simplified for this example

def save_conversation(conversation_data: Dict[str, Any], filename: str):
    """Save conversation to file"""
    with open(filename, 'w') as f:
        json.dump(conversation_data, f, indent=2)

def load_conversation(filename: str) -> Dict[str, Any]:
    """Load conversation from file"""
    with open(filename, 'r') as f:
        return json.load(f)