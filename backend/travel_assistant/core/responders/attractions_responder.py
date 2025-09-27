# travel_assistant/core/responders/attractions_responder.py
from .base_responder import BaseResponder

class AttractionsResponder(BaseResponder):
    async def respond(self, entities, external, context) -> str:
        destination = entities.get("destination", "your destination")
        country = external.get("country", {}).get("name", "")
        return f"""**Top Attractions in {destination}{f', {country}' if country else ''}:**

Cultural & Historical Sites
• Main museums and historical landmarks
• Important religious or government buildings
• Local architectural highlights

Neighborhoods & Local Life
• Popular shopping and dining areas
• Scenic viewpoints and parks
• Cultural districts and markets

Activities & Entertainment
• Local festivals and events
• Outdoor activities and nature spots
• Evening entertainment options
"""
