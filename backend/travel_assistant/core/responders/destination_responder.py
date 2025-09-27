# travel_assistant/core/responders/destination_responder.py
from .base_responder import BaseResponder

class DestinationResponder(BaseResponder):
    async def respond(self, entities, external, context) -> str:
        return """**Destination Ideas (by vibe):**
• Beach & Relaxation: Greek Islands, Thailand, Bali
• City & Culture: Tokyo, Rome, NYC
• Nature & Adventure: Swiss Alps, Costa Rica, New Zealand

What vibe are you after and when?"""
