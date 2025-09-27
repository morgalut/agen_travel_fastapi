# core/flow/accommodation_planner.py
import re
from typing import Optional

class AccommodationPlanner:
    @staticmethod
    def parse_type(text: str) -> Optional[str]:
        for t in ["hotel", "hostel", "apartment", "resort", "guesthouse", "bnb", "motel", "boutique"]:
            if re.search(rf"\b{t}s?\b", text, re.I):
                return "hotel" if t == "boutique" else t
        return None

    @staticmethod
    def parse_vibe(text: str) -> Optional[str]:
        if re.search(r"\b(don'?t care|don’t care|no preference|any|flexible)\b", text, re.I):
            return "any"
        for v in ["luxury", "boutique", "business", "family", "romantic", "party", "quiet"]:
            if re.search(rf"\b{v}\b", text, re.I):
                return v
        return None
