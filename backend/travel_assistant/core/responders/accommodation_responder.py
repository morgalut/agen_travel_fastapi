# travel_assistant/core/responders/accommodation_responder.py
from .base_responder import BaseResponder

class AccommodationResponder(BaseResponder):
    async def respond(self, entities, external, context) -> str:
        destination = entities.get("destination", "your destination")
        country = external.get("country", {}).get("name", "")
        hotels = external.get("hotels", [])
        acc_type = entities.get("accommodation_type")

        if hotels:
            lines = []
            for h in hotels[:5]:
                extras = []
                if h.get("rating"):
                    extras.append(f"{h['rating']}/5")
                if h.get("distance_km") is not None:
                    extras.append(f"{h['distance_km']:.1f} km from center")
                extra_str = f" — {', '.join(extras)}" if extras else ""
                lines.append(f"• {h.get('name','Unnamed')} ({h.get('type','hotel')}){extra_str}")
            hotel_list = "\n".join(lines)

            return (
                f"**Where to Stay in {destination}{f', {country}' if country else ''}{' ('+acc_type+')' if acc_type else ''}:**\n\n"
                f"{hotel_list}\n\n"
                "Tips:\n• Book early for peak seasons.\n• Compare reviews across platforms.\n• Stay near your top sights or reliable transit."
            )
        return (
            f"**Accommodation in {destination}{f', {country}' if country else ''}:**\n\n"
            "I can tailor recommendations — quick questions:\n"
            "• Budget range (per night)?\n• Preferred type (hotel, apartment, hostel, boutique)?\n• Travel dates?"
        )
