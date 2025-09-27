# core/intent.py
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import date

@dataclass
class AccommodationPrefs:
    type: Optional[str] = None          # "hotel", "hostel", etc.
    vibe: Optional[str] = None          # "luxury", "boutique", "family", "any"
    budget_unlimited: bool = False
    max_price_per_night: Optional[float] = None
    currency: Optional[str] = None

@dataclass
class TripIntent:
    destination: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    nights: Optional[int] = None
    purpose: Optional[str] = "tourism"
    interests: List[str] = field(default_factory=list)
    accommodation: AccommodationPrefs = field(default_factory=AccommodationPrefs)

    def as_context(self) -> Dict[str, Any]:
        return {
            "destination": self.destination,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "nights": self.nights,
            "purpose": self.purpose,
            "interests": self.interests,
            "accommodation": {
                "type": self.accommodation.type,
                "vibe": self.accommodation.vibe,
                "budget_unlimited": self.accommodation.budget_unlimited,
                "max_price_per_night": self.accommodation.max_price_per_night,
                "currency": self.accommodation.currency,
            }
        }
