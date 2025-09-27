# travel_assistant/core/responders/safety_responder.py
from typing import Dict, Any
from .base_responder import BaseResponder

class SafetyResponder(BaseResponder):
    """
    Inclusive solo-travel safety guidance.
    - Uses destination + climate snapshot (weather) + country info when available
    - Gives universally applicable safety best practices
    - Adds optional notes commonly requested by women solo travelers
    - Requests one concrete next detail to tighten guidance (neighborhoods, arrival time, etc.)
    """

    def _norm(self, s: str) -> str:
        return (s or "").strip()

    def _region_hint(self, country: Dict[str, Any]) -> str:
        # Lightweight, non-prescriptive nudge
        if not country:
            return ""
        region = (country.get("region") or "").lower()
        if "europe" in region:
            return "EU emergency number is **112**; major hubs are well-lit with frequent transit."
        if "americas" in region:
            return "In the US/Canada, emergency number is **911**; rideshare coverage is broad in cities."
        if "asia" in region:
            return "In much of Asia, metro systems are excellent; learn a few local phrases for quicker help."
        if "africa" in region:
            return "In large cities, prefer registered taxis/rideshare; confirm fares/routes before boarding."
        if "oceania" in region:
            return "Urban areas are straightforward; in remote areas carry extra water and sun protection."
        return ""

    def _climate_watchouts(self, climate_info: str) -> str:
        if not climate_info:
            return ""
        # Heuristic patterning for rapid climate-linked advice
        text = climate_info.lower()
        notes = []
        if any(k in text for k in ["rain", "drizzle", "shower"]):
            notes.append("rain expected — sidewalks & scooter lanes can be slick; pack a compact rain shell")
        if any(k in text for k in ["hot", "30", "32", "33", "34", "35"]):  # crude temp cues
            notes.append("hot conditions — prioritize shade, carry water, and avoid long walks at midday")
        if any(k in text for k in ["cold", "10°", "9°", "8°", "7°", "6°", "5°"]):
            notes.append("cool/cold — pack warm layers; prefer well-lit routes to avoid icy or poorly maintained paths")
        return ("• " + "\n• ".join(notes)) if notes else ""

    async def respond(self, entities: Dict[str, Any], external: Dict[str, Any], context: Dict[str, Any]) -> str:
        destination = self._norm(entities.get("destination") or context.get("destination") or "your destination")
        country = external.get("country") or {}
        climate = external.get("climate_info")  # from WeatherService.get_climate_summary
        region_hint = self._region_hint(country)
        climate_tiplist = self._climate_watchouts(climate)

        lines = []
        lines.append(f"**Solo Travel Safety Guide — {destination}**")

        if region_hint:
            lines += ["", f"**Local Context**", f"• {region_hint}"]

        if climate:
            lines += ["", "**Next 7-Day Snapshot (weather)**", climate.strip()]
            if climate_tiplist:
                lines += ["", "**Weather Watch-outs**", climate_tiplist]

        lines += [
            "",
            "**Personal Safety Basics (for everyone)**",
            "• Share your live location with a trusted contact; set a check-in plan.",
            "• Arrive at new accommodations **in daylight** when possible.",
            "• Prefer well-reviewed stays (24/7 desk/security) and rooms on **2nd–5th floors** (safer, still evacuable).",
            "• Use reputable rideshare or registered taxis; confirm plate/driver and sit behind the driver.",
            "• Keep valuables split (primary wallet + backup cash card in a hidden pocket).",
            "• Lock phone with PIN/biometrics; use hotel safe; enable ‘Find My’ or equivalent.",
            "• Be cautious with public Wi-Fi; consider a travel eSIM and avoid sensitive logins on unknown networks.",
            "• In crowded areas, wear daypacks in front; avoid displaying expensive jewelry/cameras unnecessarily.",
        ]

        lines += [
            "",
            "**Neighborhood & Movement**",
            "• Ask your host/hotel which blocks to avoid at night; save safe late-night routes on your map.",
            "• Stick to **well-lit main roads** after dark; if in doubt, rideshare for last-mile connections.",
            "• For hikes/remote areas: log route and time window with a contact; pack water, sun/bug protection, and a basic kit.",
        ]

        lines += [
            "",
            "**Women-Focused Notes (optional, use what’s useful)**",
            "• If unwanted attention occurs, move into a staffed shop/café and ask for help; trust your instincts.",
            "• Consider women-only dorms/cars (where available); set doorstops and use secondary locks when feasible.",
            "• Carry a small audible alarm/whistle; keep your phone unlocked to emergency dial on the lock screen.",
        ]

        lines += [
            "",
            "**Scam & Money Hygiene**",
            "• Common patterns: overfriendly ‘helpers’, closed-then-open venues redirecting you, unofficial ticket sellers.",
            "• Use ATMs inside banks; cover keypad; decline ‘assistance’. Verify taxi meters or agree on fares before entry.",
            "• Keep digital copies of passport/ID and your insurance details in a secure cloud folder.",
        ]

        if country.get("currency"):
            lines += [f"• Local currency: **{country['currency']}** (carry small bills for tips and transit kiosks)."]

        lines += [
            "",
            "**If You Need Help Fast**",
            "• Head to a staffed hotel, pharmacy, police kiosk, metro office, or large store to ask for assistance.",
            "• Save your accommodation’s name/address in local language in your notes for quick sharing.",
        ]

        lines += [
            "",
            "If you share **neighborhoods** you’ll stay in, **arrival time**, and any **late-night events**, "
            "I can tailor a safety route plan and late-night transit options."
        ]

        return "\n".join(lines)
