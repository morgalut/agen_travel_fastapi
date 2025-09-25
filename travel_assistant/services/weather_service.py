# travel_assistant/services/weather_service.py
import requests
from typing import Optional, Dict, Any

_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Freezing drizzle (light)", 57: "Freezing drizzle (dense)",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Freezing rain (light)", 67: "Freezing rain (heavy)",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Rain showers (slight)", 81: "Rain showers (moderate)", 82: "Rain showers (violent)",
    85: "Snow showers (slight)", 86: "Snow showers (heavy)",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
}

def _code_text(code: int) -> str:
    return _CODE_MAP.get(code, f"Weather code {code}")

class WeatherService:
    """Service for fetching free weather data using Open-Meteo"""

    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"

    def get_weather_forecast(self, latitude: float, longitude: float, days: int = 7) -> Optional[Dict[str, Any]]:
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
                "current_weather": True,
                "forecast_days": days,
                "timezone": "auto"
            }
            resp = requests.get(self.base_url, params=params, timeout=12)
            resp.raise_for_status()
            data = resp.json()

            forecast = []
            for i, date in enumerate(data["daily"]["time"]):
                forecast.append({
                    "date": date,
                    "max_temp": data["daily"]["temperature_2m_max"][i],
                    "min_temp": data["daily"]["temperature_2m_min"][i],
                    "precipitation": data["daily"]["precipitation_sum"][i],
                    "weathercode": data["daily"]["weathercode"][i],
                    "condition": _code_text(data["daily"]["weathercode"][i]),
                })

            cur_code = data["current_weather"]["weathercode"]
            return {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "current_temp": data["current_weather"]["temperature"],
                "condition": _code_text(cur_code),
                "forecast": forecast
            }
        except Exception as e:
            print(f"Weather API error: {e}")
            return None

    def get_climate_summary(self, latitude: float, longitude: float) -> Optional[str]:
        f = self.get_weather_forecast(latitude, longitude)
        if not f:
            return None
        temps = [d['max_temp'] for d in f['forecast']]
        conds = [d['condition'].lower() for d in f['forecast']]

        summary = (
            f"Current: {f['current_temp']}°C, {f['condition']}. "
            f"Highs up to {max(temps):.1f}°C and lows down to {min(temps):.1f}°C over the next days. "
        )
        if any("rain" in c or "drizzle" in c or "shower" in c for c in conds):
            summary += "Rain expected — pack waterproofs. "
        if max(temps) > 30:
            summary += "Hot weather — light clothing. "
        if min(temps) < 10:
            summary += "Cold temps — warm layers."
        return summary
