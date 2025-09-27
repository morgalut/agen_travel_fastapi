# travel_assistant/services/visa_service.py
from __future__ import annotations
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class VisaService:
    """
    Lightweight visa rules helper (non-official).
    Focused on Thailand with pragmatic defaults and branching.
    Always advise the user to verify with official sources.
    """

    # ⚠️ This is a pragmatic subset; real rules change. Keep conservative.
    VISA_EXEMPT_30 = {
        # Common passports with tourist visa exemption up to ~30 days by air
        "united states", "canada", "united kingdom", "germany", "france", "italy",
        "spain", "portugal", "ireland", "netherlands", "belgium", "sweden", "norway",
        "denmark", "finland", "switzerland", "austria", "australia", "new zealand",
        "japan", "south korea", "singapore", "malaysia", "hong kong", "uae",
    }

    # Countries commonly eligible for Thailand eVOA / VOA (indicative list)
    EVOA_ELIGIBLE = {
        "india", "china", "taiwan", "kazakhstan", "saudi arabia",
        "romania", "bulgaria",
    }

    def _normalize(self, s: Optional[str]) -> str:
        return (s or "").strip().lower()

    def _estimate_stay_days(self, duration: Optional[str]) -> Optional[int]:
        """
        Convert simple duration strings like '7 days', '1 week', '2 weeks' to days.
        """
        if not duration:
            return None
        d = duration.lower().strip()
        try:
            if "day" in d:
                # e.g., "7 days"
                for tok in d.split():
                    if tok.isdigit():
                        return int(tok)
            if "week" in d:
                for tok in d.split():
                    if tok.isdigit():
                        return int(tok) * 7
        except Exception:
            pass
        return None

    def get_thailand_advice(
        self,
        passport_country: Optional[str],
        stay_length_days: Optional[int],
        purpose: Optional[str] = "tourism",
    ) -> Dict[str, Any]:
        """
        Compute a pragmatic recommendation tree for Thailand tourist trips.
        Returns data structure the responder can turn into user-facing text.
        """
        pc = self._normalize(passport_country)
        purpose = self._normalize(purpose) or "tourism"
        stay_days = stay_length_days

        logger.info(f"[visa] Thailand visa check: passport={passport_country}, stay_days={stay_days}, purpose={purpose}")

        # Base document expectations (common requirements)
        base_docs: List[str] = [
            "Passport valid 6+ months on arrival",
            "Proof of onward/return ticket within permitted stay",
            "Accommodation address for first nights",
            "Sufficient funds for stay",
        ]

        result: Dict[str, Any] = {
            "country": "Thailand",
            "passport_country": passport_country or "Unknown",
            "purpose": purpose,
            "path": "unknown",
            "allowed_days": None,
            "documents": base_docs[:],
            "next_steps": [],
            "notes": [],
            "disclaimer": (
                "This is general guidance. Visa rules change—verify on an official Thai government/consulate site "
                "or with your airline before you travel."
            ),
        }

        # Non-tourist purposes almost always require pre-arranged visas.
        if purpose not in ("tourism", "leisure", "vacation", "holiday"):
            result["path"] = "non_tourist"
            result["next_steps"].append("Apply for the appropriate non-tourist visa (e.g., business, work, study) in advance.")
            result["notes"].append("You may need invitation/supporting letters and additional documentation.")
            return result

        # Tourism path
        if pc in self.VISA_EXEMPT_30:
            result["path"] = "visa_exempt"
            result["allowed_days"] = 30
            result["notes"].append("Nationals of your country are typically visa-exempt for short tourist visits by air.")
            result["next_steps"].append("Ensure your onward/return flight departs within 30 days of arrival.")
            result["next_steps"].append("If you plan to stay longer, consider a Tourist Visa (TR) or extension.")
        elif pc in self.EVOA_ELIGIBLE:
            result["path"] = "evoa_voa"
            result["allowed_days"] = 15
            result["notes"].append("You’re commonly eligible for Thailand eVOA/VOA for short tourist visits.")
            result["next_steps"].append("Apply for an eVOA online before flying, or prepare for Visa on Arrival at select airports.")
            result["next_steps"].append("Make sure your onward/return flight departs within 15 days of arrival.")
            result["documents"].extend([
                "Passport photo as per eVOA spec",
                "Completed eVOA application (if doing online)",
            ])
        elif pc:
            # Unknown/not in common lists → advise a pre-arranged Tourist Visa (TR)
            result["path"] = "tourist_visa_required"
            result["allowed_days"] = 60
            result["notes"].append("You’ll likely need a Tourist Visa (TR) arranged before travel.")
            result["next_steps"].append("Apply for a single-entry Tourist Visa (TR) at a Thai embassy/consulate.")
        else:
            # No passport specified
            result["path"] = "need_passport_info"
            result["notes"].append("Tell me your passport country to check if you qualify for visa-exempt, eVOA/VOA, or need a Tourist Visa.")
            return result

        # Stay length re
