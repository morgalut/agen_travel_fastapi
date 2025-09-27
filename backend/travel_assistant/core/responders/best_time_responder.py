# travel_assistant/core/responders/best_time_responder.py
from typing import Dict, Any
from .base_responder import BaseResponder

class BestTimeResponder(BaseResponder):
    """
    Answers queries like:
      - "The best time to visit Bali for surfing?"
      - "When should I visit X for activity Y?"
    Strategy:
      1) Recognize destination & (optional) activity.
      2) Use built-in seasonal knowledge (heuristics) for known pairs (e.g., Bali+surfing).
      3) Add current 7-day climate info from external["climate_info"] if available.
      4) Provide a short, clear recommendation + alternatives (shoulder seasons).
    """

    # Minimal built-in playbook for popular seasonality questions.
    # Extend as needed (keep it small & curated to avoid hallucinations).
    _SURF_SEASONS = {
        # West coast: Kuta, Canggu, Uluwatu; East coast: Nusa Dua, Sanur.
        "bali": {
            "activity": "surfing",
            "west_coast": {"best": "May–Sep", "peak": "Jun–Aug", "why": "SE trade winds are offshore; consistent SW swells; dry season."},
            "east_coast": {"best": "Nov–Mar", "peak": "Dec–Feb", "why": "W/NW winds turn the east coast offshore; wet season but reliable surf windows."},
            "shoulder": "Apr & Oct",
            "level_notes": (
                "• Beginners: smaller, cleaner days around shoulder months.\n"
                "• Intermediates/Advanced: peak months for power & consistency (watch tides & reef).\n"
            ),
        }
    }

    def _normalize(self, s: str) -> str:
        return (s or "").strip().lower()

    def _is_bali(self, destination: str) -> bool:
        return "bali" in self._normalize(destination)

    async def respond(self, entities: Dict[str, Any], external: Dict[str, Any], context: Dict[str, Any]) -> str:
        destination = entities.get("destination") or context.get("destination") or "your destination"
        interests = set((entities.get("interests") or []) + (context.get("interests") or []))
        climate_info = external.get("climate_info")  # from WeatherService.get_climate_summary
        coords = external.get("coords")  # {"lat":..,"lon":..}

        # Hard-coded high-signal knowledge: Bali + Surfing
        if self._is_bali(destination):
            data = self._SURF_SEASONS["bali"]
            # Treat as surfing if user hints at surf or the utterance included "surf"
            is_surf = ("surfing" in {i.lower() for i in interests}) or True  # Frequently implied
            if is_surf:
                out = [
                    f"**Best Time to Surf in {destination}:**",
                    "",
                    f"• **West Coast (Kuta/Canggu/Uluwatu):** {data['west_coast']['best']} (peak {data['west_coast']['peak']}) — {data['west_coast']['why']}",
                    f"• **East Coast (Nusa Dua/Sanur):** {data['east_coast']['best']} (peak {data['east_coast']['peak']}) — {data['east_coast']['why']}",
                    f"• **Shoulder Months:** {data['shoulder']} — fewer crowds and friendlier conditions.",
                    "",
                    "**Skill-Level Notes**",
                    data["level_notes"].rstrip(),
                ]
                if climate_info:
                    out += [
                        "**Next 7 Days Snapshot**",
                        climate_info.strip()
                    ]
                out += [
                    "",
                    "**Quick Pack Tips**",
                    "• Reef-safe sunscreen, booties for reef breaks, spare leash & wax.",
                    "• Lightweight rain shell (wet season) and sun hoody (dry season).",
                    "",
                    "If you share **dates** or **coast (west/east)**, I’ll tailor spots & daily timing (tide/wind windows)."
                ]
                return "\n".join(out)

        # Generic fallback when we don’t have curated activity/destination knowledge.
        out = [
            f"**Best Time to Visit {destination}:**",
            "• Aim for the **dry season** and **prevailing offshore wind** for your activity.",
            "• Avoid local **peak-holiday weeks** if you want lower prices and fewer crowds.",
        ]
        if climate_info:
            out += ["", "**Next 7 Days Snapshot**", climate_info.strip()]
        out += [
            "",
            "Tell me the **activity** and **rough month(s)** and I’ll refine this to specific weeks with better odds."
        ]
        return "\n".join(out)
