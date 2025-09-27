from .base_responder import BaseResponder

class WeatherResponder(BaseResponder):
    async def respond(self, entities, external, context) -> str:
        destination = entities.get("destination", "your destination")
        country = external.get("country", {}).get("name", "")

        climate = external.get("climate_info")
        if climate:
            return f"""**Weather in {destination}{f', {country}' if country else ''}:**

{climate}

💡 Tip: Always check the daily forecast before you pack — conditions can shift quickly."""
        return f"Could you tell me the destination? I’ll check the weather forecast for you."
