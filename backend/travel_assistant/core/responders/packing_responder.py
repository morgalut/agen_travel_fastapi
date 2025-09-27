# travel_assistant/core/responders/packing_responder.py
from .base_responder import BaseResponder

class PackingResponder(BaseResponder):
    async def respond(self, entities, external, context) -> str:
        destination = entities.get("destination", "your destination")
        country = external.get("country", {}).get("name", "")
        return f"""**Packing List for {destination}{f', {country}' if country else ''}:**

Clothing
• Weather-appropriate layers
• Comfortable walking shoes
• Light rain protection

Essentials
• Power adapter, power bank
• Copies of documents, insurance

Day Gear
• Small backpack
• Water bottle, sun protection
"""
