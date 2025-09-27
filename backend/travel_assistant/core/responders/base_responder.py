# travel_assistant/core/responders/base_responder.py
from typing import Dict, Any

class BaseResponder:
    async def respond(self, entities: Dict[str, Any], external: Dict[str, Any], context: Dict[str, Any]) -> str:
        raise NotImplementedError
