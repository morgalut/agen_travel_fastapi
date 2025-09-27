# travel_assistant/core/responders/visa_responder.py
from __future__ import annotations
from typing import Dict, Any, Optional
from ..conversation import QueryType

class VisaResponder:
    """
    Produces helpful, structured guidance for Thailand visa questions.
    Uses precomputed external['visa_th'] if present; otherwise asks targeted follow-ups.
    """

    def __init__(self, visa_service):
        self.visa_service = visa_service

    async def respond(self, entities: Dict[str, Any], external: Dict[str, Any], context: Dict[str, Any]) -> str:
        destination = (entities.get("destination") or context.get("destination") or "").lower()
        citizenship = entities.get("citizenship") or context.get("citizenship")
        purpose = entities.get("purpose") or context.get("purpose") or "tourism"

        # Normalize a basic stay-days estimate
        stay_days = None
        if entities.get("duration"):
            stay_days = self._estimate_days(entities["duration"])

        # If not clearly Thailand, nudge
        if "thailand" not in destination and destination.lower() not in ("bangkok", "phuket", "chiang mai"):
            return (
                "For visa advice I need 2 basics:\n"
                "• **Destination country** (e.g., Thailand)\n"
                "• **Passport country** (e.g., United States)\n"
                "Optionally, tell me **trip length** and **purpose** (tourism/business) so I can tailor it."
            )

        # If missing passport country, ask
        if not citizenship:
            return (
                "Great — focusing on **Thailand**. What **passport** will you travel with? "
                "If you can, also share **trip length** (days/weeks) and **purpose** (tourism or business)."
            )

        # Prefer pre-fetched data in external; otherwise compute now
        advice = external.get("visa_th")
        if not advice:
            advice = self.visa_service.get_thailand_advice(
                passport_country=citizenship,
                stay_length_days=stay_days,
                purpose=purpose,
            )

        # Format a clean, compact answer
        lines = []
        lines.append(f"**Thailand — Visa Guidance for {advice.get('passport_country','your passport')}**")
        path = advice.get("path")
        if path == "visa_exempt":
            lines.append("• Likely **visa-exempt** for short tourist visits by air.")
        elif path == "evoa_voa":
            lines.append("• Likely **eVOA/VOA** eligible for short tourist visits.")
        elif path == "tourist_visa_required":
            lines.append("• You’ll likely need a **Tourist Visa (TR)** **before** traveling.")
        elif path == "non_tourist":
            lines.append("• **Non-tourist purpose** — apply in advance for the correct visa category.")
        elif path == "need_passport_info":
            lines.append("• I need your **passport country** to check options.")

        if advice.get("allowed_days"):
            lines.append(f"• Typical permitted stay: **up to {advice['allowed_days']} days** for this path.")

        if advice.get("documents"):
            lines.append("\n**Documents usually checked at the border**")
            for d in advice["documents"]:
                lines.append(f"• {d}")

        if advice.get("next_steps"):
            lines.append("\n**Next steps**")
            for s in advice["next_steps"]:
                lines.append(f"• {s}")

        if advice.get("notes"):
            lines.append("\n**Notes**")
            for n in advice["notes"]:
                lines.append(f"• {n}")

        if advice.get("disclaimer"):
            lines.append(f"\n_{advice['disclaimer']}_")

        return "\n".join(lines)

    def _estimate_days(self, duration: str) -> Optional[int]:
        d = duration.lower()
        try:
            if "day" in d:
                for tok in d.replace("-", " ").split():
                    if tok.isdigit():
                        return int(tok)
            if "week" in d:
                for tok in d.replace("-", " ").split():
                    if tok.isdigit():
                        return int(tok) * 7
        except Exception:
            pass
        return None
