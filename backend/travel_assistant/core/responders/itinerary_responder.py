# core/responders/itinerary_responder.py
from .base_responder import BaseResponder
from typing import Dict, Any

class ItineraryResponder(BaseResponder):
    async def respond(self, entities: Dict[str, Any], external: Dict[str, Any], context: Dict[str, Any]) -> str:
        # Pull normalized trip intent (already attached to context by assistant)
        ti = context.get("trip_intent", {})
        start = ti.get("start_date")
        end = ti.get("end_date")
        nights = ti.get("nights")
        acc = ti.get("accommodation", {})
        acc_type = acc.get("type") or "hotel"
        vibe = (acc.get("vibe") or "any")
        budget_text = "Unlimited" if acc.get("budget_unlimited") else (
            f"Up to {acc.get('max_price_per_night')} {acc.get('currency') or ''}".strip()
            if acc.get("max_price_per_night") else "Not specified"
        )

        lines = []
        lines.append("### Your Plan (draft)")
        lines.append(f"- Stay: **{acc_type.title()}** ({'no vibe preference' if vibe=='any' else vibe})")
        if start and end and nights:
            lines.append(f"- Dates: **{start} → {end}**  (**{nights} nights**)")
        lines.append(f"- Budget: **{budget_text}**")
        if not ti.get("destination"):
            lines.append("- Destination: **Missing** → tell me the city (e.g., *Paris*, *Bangkok*) and I’ll fetch weather & hotels.")

        # If destination + coords are available, reflect readiness
        if ti.get("destination") and ("coords" in external):
            lines.append(f"- Destination: **{ti['destination']}** (ready to fetch hotels & weather)")

        # Next action
        if not ti.get("destination"):
            lines.append("\n**Next:** Tell me your destination city. I’ll immediately check the 14-day window forecast and shortlist top hotels.")
        else:
            lines.append("\n**Next:** I’ll pull top hotels that match your preferences and show a quick weather overview for your dates.")

        return "\n".join(lines)
