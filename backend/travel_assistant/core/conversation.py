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
    ACCOMMODATION = "accommodation"  # ✅ NEW
    GENERAL = "general"

# Proper nouns like "New York", "San Francisco"
_PROPER_NOUN = r"\b([A-Z][a-zA-Z]{2,}(?:[\s\-][A-Z][a-zA-Z]{2,})*)\b"
# Hints like "in Paris", "to London"
_CITY_HINT = r"(?:\bin|\bto|\bfor|\bat)\s+([A-Z][a-zA-Z]{2,}(?:[\s\-][A-Z][a-zA-Z]{2,})*)"

# Words that derail naive destination extraction when used at sentence start
_QUESTION_WORDS = {"which", "where", "what", "when", "how", "who", "whom", "whose"}


class ConversationManager:
    """Manages conversation flow and context."""

    def __init__(self):
        self.context: Dict[str, Any] = {}
        self.current_topic: Optional[QueryType] = None
        logger.info("🗨️ ConversationManager initialized")
        print("[conversation] 🗨️ ConversationManager initialized")

    # ---------------- Classification ----------------
    def classify_query(self, user_input: str) -> QueryType:
        logger.info(f"📌 Classifying query: {user_input}")
        print(f"[conversation] 📌 Classifying: {user_input}")

        text = user_input.lower()

        # ✅ Robust hotel/accommodation detection
        hotel_patterns = [
            r"\bhotel(s)?\b", r"\bhostel(s)?\b", r"\bguesthouse(s)?\b",
            r"\b(accommodation|lodging)\b", r"\bwhere to stay\b",
            r"\bplace to (sleep|stay)\b", r"\binn\b", r"\bmotel(s)?\b",
            r"\bbnb\b", r"\bbed and breakfast\b", r"\bboutique hotel\b"
        ]

        destination_patterns = [
            r"where.*(should|to).*(go|travel)", r"recommend.*destination",
            r"place.*visit", r"vacation.*ideas", r"trip.*suggestions"
        ]
        packing_patterns = [
            r"\bpack\b.*\bwhat\b", r"\bwhat\b.*\bpack\b", r"\bpacking list\b",
            r"\bbring\b.*\btrip\b", r"\bwhat\b.*\bwear\b", r"\bessentials\b.*\bbring\b"
        ]
        attractions_patterns = [
            r"\bthings\b.*\bdo\b", r"\battraction(s)?\b", r"\bsightseeing\b",
            r"\bplaces\b.*\bsee\b", r"\bactivities\b", r"\bwhat\b.*\bdo\b.*\bin\b"
        ]

        if any(re.search(p, text) for p in hotel_patterns):
            logger.info("✅ Classified as ACCOMMODATION")
            print("[conversation] ✅ Classified as ACCOMMODATION")
            return QueryType.ACCOMMODATION
        if any(re.search(p, text) for p in destination_patterns):
            logger.info("✅ Classified as DESTINATION")
            print("[conversation] ✅ Classified as DESTINATION")
            return QueryType.DESTINATION
        if any(re.search(p, text) for p in packing_patterns):
            logger.info("✅ Classified as PACKING")
            print("[conversation] ✅ Classified as PACKING")
            return QueryType.PACKING
        if any(re.search(p, text) for p in attractions_patterns):
            logger.info("✅ Classified as ATTRACTIONS")
            print("[conversation] ✅ Classified as ATTRACTIONS")
            return QueryType.ATTRACTIONS

        logger.info("ℹ️ Classified as GENERAL")
        print("[conversation] ℹ️ Classified as GENERAL")
        return QueryType.GENERAL

    # ---------------- Entity Extraction ----------------
    def _strip_leading_question_words(self, text: str) -> str:
        # Remove first token if it's a question word (and common commas)
        tokens = [t for t in re.split(r"\s+", text) if t]
        while tokens and tokens[0].lower().strip(",.?") in _QUESTION_WORDS:
            tokens.pop(0)
        return " ".join(tokens)

    def extract_entities(self, user_input: str) -> Dict[str, Any]:
        """Extract key entities from user input with context-aware fallbacks."""
        logger.info(f"🔎 Extracting entities from: {user_input}")
        print(f"[conversation] 🔎 Extracting entities from: {user_input}")

        entities = {
            "destination": None,
            "duration": None,
            "budget": None,
            "interests": [],
            "travel_dates": None,
            # accommodation-specific (optional)
            "accommodation_type": None,
        }

        cleaned = self._strip_leading_question_words(user_input)

        # Duration like "5 days", "2 weeks"
        if m := re.search(r"(\d+)\s*(days?|weeks?|months?)", cleaned, flags=re.I):
            entities["duration"] = m.group(0)
            print(f"[conversation] ⏳ Duration: {entities['duration']}")

        # Budget like "$2000", "2000 USD", "2k dollars", "budget 150 €/night"
        mb = re.search(
            r"(?:(?:budget|up to|around)\s*)?(\$|€|£)?\s*(\d+(?:,\d{3})*|\d+)(?:\s*(k|thousand))?\s*(usd|dollars|eur|euros|gbp|pounds|per night|/night|a night)?",
            cleaned, flags=re.I
        )
        if mb:
            entities["budget"] = mb.group(0)
            print(f"[conversation] 💰 Budget: {entities['budget']}")

        # Interests
        interests = [
            "beach", "mountain", "city", "culture", "adventure", "food",
            "shopping", "nature", "museum", "nightlife", "family", "romantic"
        ]
        entities["interests"] = [w for w in interests if re.search(rf"\b{w}\b", cleaned, flags=re.I)]
        if entities["interests"]:
            print(f"[conversation] 🎯 Interests: {entities['interests']}")

        # Accommodation type hints
        acc_types = ["hotel", "hostel", "apartment", "boutique", "guesthouse", "bnb", "motel", "resort"]
        for t in acc_types:
            if re.search(rf"\b{t}s?\b", cleaned, re.I):
                entities["accommodation_type"] = t
                break

        # Destination from "in/at/to <City>"
        md = re.search(_CITY_HINT, cleaned)
        if md:
            entities["destination"] = md.group(1)
            print(f"[conversation] 🌍 Destination: {entities['destination']}")
        else:
            # Fallback to last capitalized phrase, but skip leading question tokens like "Which", "Where"
            tokens = re.findall(_PROPER_NOUN, cleaned)
            if tokens:
                entities["destination"] = tokens[-1]
                print(f"[conversation] 🌍 Destination fallback: {entities['destination']}")

        # Reuse last known destination if missing
        if not entities["destination"] and self.context.get("destination"):
            entities["destination"] = self.context["destination"]
            print(f"[conversation] ♻️ Using context destination: {entities['destination']}")

        logger.info(f"✅ Entities extracted: {entities}")
        print(f"[conversation] ✅ Entities extracted: {entities}")
        return entities

    # ---------------- Context ----------------
    def update_context(self, user_input: str, query_type: QueryType, entities: Dict[str, Any]):
        """Update conversation context and keep accommodation intent sticky."""
        logger.info("🗂️ Updating conversation context...")
        print("[conversation] 🗂️ Updating context...")

        # Track previous/current topic
        prev = self.context.get("current_topic")
        if prev:
            self.context["previous_topic"] = prev
            print(f"[conversation] ↩️ Previous topic set: {prev}")

        self.context["current_topic"] = query_type.value
        self.current_topic = query_type
        print(f"[conversation] 📌 Current topic set: {query_type.value}")

        # Persist entities
        for k, v in entities.items():
            if v:
                self.context[k] = v
                print(f"[conversation] ➕ Stored entity {k}={v}")

        # Sticky accommodation intent
        if query_type == QueryType.ACCOMMODATION:
            self.context["accommodation_intent"] = True
            self.context["last_accommodation_query"] = user_input

        logger.info(f"✅ Context updated: {self.context}")
        print(f"[conversation] ✅ Context updated: {self.context}")
