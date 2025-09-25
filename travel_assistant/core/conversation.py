# travel_assistant/core/conversation.py
from typing import Dict, List, Any, Optional
from enum import Enum
import re

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

    def classify_query(self, user_input: str) -> QueryType:
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
                return QueryType.DESTINATION
        for p in packing_patterns:
            if re.search(p, input_lower):
                return QueryType.PACKING
        for p in attractions_patterns:
            if re.search(p, input_lower):
                return QueryType.ATTRACTIONS
        return QueryType.GENERAL

    def extract_entities(self, user_input: str) -> Dict[str, Any]:
        """Extract key entities from user input (naive but effective)."""
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

        # Budget like "$2000", "2000 USD", "2k dollars"
        mb = re.search(r'(\$|€|£)?\s*(\d+(?:,\d{3})*|\d+)(?:\s*(k|thousand))?\s*(usd|dollars|eur|euros|gbp|pounds)?',
                       user_input, flags=re.I)
        if mb:
            entities['budget'] = mb.group(0)

        # Interests (simple keywords)
        interests = ['beach', 'mountain', 'city', 'culture', 'adventure', 'food', 'shopping', 'nature', 'museum']
        entities['interests'] = [w for w in interests if re.search(rf'\b{w}\b', user_input, flags=re.I)]

        # Destination by hint: "... in Paris", "... to Tokyo"
        md = re.search(_CITY_HINT, user_input)
        if md:
            entities['destination'] = md.group(1)
        else:
            # Fallback: last proper-noun phrase not at sentence start
            tokens = re.findall(_PROPER_NOUN, user_input)
            if tokens:
                entities['destination'] = tokens[-1]

        # If still missing, reuse last known destination from context
        if not entities['destination'] and self.context.get('destination'):
            entities['destination'] = self.context['destination']

        return entities

    def update_context(self, user_input: str, query_type: QueryType, entities: Dict[str, Any]):
        """Update conversation context based on current interaction."""
        # Track topics properly
        prev = self.context.get('current_topic')
        if prev:
            self.context['previous_topic'] = prev
        self.context['current_topic'] = query_type.value
        self.current_topic = query_type

        # Persist discovered entities
        for k, v in entities.items():
            if v:
                self.context[k] = v
