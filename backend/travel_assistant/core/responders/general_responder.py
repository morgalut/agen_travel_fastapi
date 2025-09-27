# travel_assistant/core/responders/general_responder.py
from .base_responder import BaseResponder

class GeneralResponder(BaseResponder):
    async def respond(self, entities, external, context) -> str:
        return "Happy to help! Tell me if you want destinations, things to do, packing, or places to stay."
