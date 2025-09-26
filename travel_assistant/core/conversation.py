# travel_assistant/core/conversation.py
from typing import Dict, Any, Optional
from enum import Enum
import re
import logging

# Setup logger
logger = logging.getLogger(__name__)

class QueryType(Enum):
    DESTINATION = "destination_recommendation"
    PACKING = "packing_suggestions"
    ATTRACTIONS = "local_attractions"
    GENERAL = "general"

_PROPER_NOUN = r"\b([A-Z][a-zA-Z]{2,}(?:[\s\-][A-Z][a-zA-Z]{2,})*)\b"
_CITY_HINT = r"(?:in|to|for|at)\s+([A-Z][a-zA-Z]{2,}(?:[\s\-][A-Z][a-zA-Z]{2,})*)"


class ConversationManager:
    """Manages conversation flow and context"""

    def __init__(self):
        self.context: Dict[str, Any] = {}
        self.current_topic: Optional[QueryType] = None
        logger.info("🗨️ ConversationManager initialized")
        print("[conversation] 🗨️ ConversationManager initialized")

    def classify_query(self, user_input: str) -> QueryType:
        logger.info(f"📌 Classifying query: {user_input}")
        print(f"[conversation] 📌 Classifying: {user_input}")

        input_lower = user_input.lower()
        destination_patterns = [
            r'.*where.*should.*go', r'.*recommend.*destination', r'.*place.*visit',
            r'.*travel.*where', r'.*vacation.*ideas', r'.*trip.*suggestions'
        ]
        packing_patterns = [
            r'.*pack.*what', r'.*bring.*trip', r'.*what.*pack',
            r'.*packing.*list', r'.*what.*wear', r'.*essentials.*bring'
        ]
        attractions_patterns = [
            r'.*things.*do', r'.*attractions', r'.*sightseeing',
            r'.*places.*see', r'.*activities', r'.*what.*do.*in'
        ]

        for p in destination_patterns:
            if re.search(p, input_lower):
                logger.info("✅ Classified as DESTINATION")
                print("[conversation] ✅ Classified as DESTINATION")
                return QueryType.DESTINATION
        for p in packing_patterns:
            if re.search(p, input_lower):
                logger.info("✅ Classified as PACKING")
                print("[conversation] ✅ Classified as PACKING")
                return QueryType.PACKING
        for p in attractions_patterns:
            if re.search(p, input_lower):
                logger.info("✅ Classified as ATTRACTIONS")
                print("[conversation] ✅ Classified as ATTRACTIONS")
                return QueryType.ATTRACTIONS

        logger.info("ℹ️ Classified as GENERAL")
        print("[conversation] ℹ️ Classified as GENERAL")
        return QueryType.GENERAL

    def extract_entities(self, user_input: str) -> Dict[str, Any]:
        """Extract key entities from user input (naive but effective)."""
        logger.info(f"🔎 Extracting entities from: {user_input}")
        print(f"[conversation] 🔎 Extracting entities from: {user_input}")

        entities = {
            'destination': None,
            'duration': None,
            'budget': None,
            'interests': [],
            'travel_dates': None
        }

        # Duration like "5 days", "2 weeks"
        m = re.search(r'(\d+)\s*(days?|weeks?|months?)', user_input, flags=re.I)
        if m:
            entities['duration'] = m.group(0)
            logger.debug(f"⏳ Duration detected: {entities['duration']}")
            print(f"[conversation] ⏳ Duration: {entities['duration']}")

        # Budget like "$2000", "2000 USD", "2k dollars"
        mb = re.search(
            r'(\$|€|£)?\s*(\d+(?:,\d{3})*|\d+)(?:\s*(k|thousand))?\s*(usd|dollars|eur|euros|gbp|pounds)?',
            user_input, flags=re.I
        )
        if mb:
            entities['budget'] = mb.group(0)
            logger.debug(f"💰 Budget detected: {entities['budget']}")
            print(f"[conversation] 💰 Budget: {entities['budget']}")

        # Interests
        interests = ['beach', 'mountain', 'city', 'culture', 'adventure', 'food', 'shopping', 'nature', 'museum']
        entities['interests'] = [w for w in interests if re.search(rf'\b{w}\b', user_input, flags=re.I)]
        if entities['interests']:
            logger.debug(f"🎯 Interests detected: {entities['interests']}")
            print(f"[conversation] 🎯 Interests: {entities['interests']}")

        # Destination
        md = re.search(_CITY_HINT, user_input)
        if md:
            entities['destination'] = md.group(1)
            logger.debug(f"🌍 Destination detected: {entities['destination']}")
            print(f"[conversation] 🌍 Destination: {entities['destination']}")
        else:
            tokens = re.findall(_PROPER_NOUN, user_input)
            if tokens:
                entities['destination'] = tokens[-1]
                logger.debug(f"🌍 Destination fallback: {entities['destination']}")
                print(f"[conversation] 🌍 Destination fallback: {entities['destination']}")

        # Reuse last known destination if missing
        if not entities['destination'] and self.context.get('destination'):
            entities['destination'] = self.context['destination']
            logger.debug(f"♻️ Reused context destination: {entities['destination']}")
            print(f"[conversation] ♻️ Using context destination: {entities['destination']}")

        logger.info(f"✅ Entities extracted: {entities}")
        print(f"[conversation] ✅ Entities extracted: {entities}")
        return entities

    def update_context(self, user_input: str, query_type: QueryType, entities: Dict[str, Any]):
        """Update conversation context based on current interaction."""
        logger.info("🗂️ Updating conversation context...")
        print("[conversation] 🗂️ Updating context...")

        # Track topics properly
        prev = self.context.get('current_topic')
        if prev:
            self.context['previous_topic'] = prev
            logger.debug(f"↩️ Previous topic set: {prev}")
            print(f"[conversation] ↩️ Previous topic set: {prev}")

        self.context['current_topic'] = query_type.value
        self.current_topic = query_type
        logger.debug(f"📌 Current topic set: {query_type.value}")
        print(f"[conversation] 📌 Current topic set: {query_type.value}")

        # Persist discovered entities
        for k, v in entities.items():
            if v:
                self.context[k] = v
                logger.debug(f"➕ Stored entity {k}={v}")
                print(f"[conversation] ➕ Stored entity {k}={v}")

        logger.info(f"✅ Context updated: {self.context}")
        print(f"[conversation] ✅ Context updated: {self.context}")
