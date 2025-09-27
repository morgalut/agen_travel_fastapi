# travel_assistant/services/weather_service.py
from datetime import time
import requests
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

_CODE_MAP = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
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
    """Service for fetching free weather & climate data using Open-Meteo."""

    def __init__(self):
        self.base_urls = [
            "https://api.open-meteo.com/v1/forecast",
            "https://api.open-meteo.net/v1/forecast",
            "https://api.open-meteo.org/v1/forecast",
        ]

    # ---------------- HELPER ----------------
    def _fetch_with_retries(self, url: str, params: Dict[str, Any], max_retries: int = 3) -> Optional[Dict[str, Any]]:
        timeout = 10
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, params=params, timeout=timeout)
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.Timeout:
                logger.warning(f" Weather API timeout (attempt {attempt+1}/{max_retries}, url={url})")
                time.sleep(1.5 * (attempt + 1))  # backoff
                timeout += 5
            except Exception as e:
                logger.warning(f" Weather API error on {url}: {e}")
                break
        return None

    # ---------------- DAILY FORECAST ----------------
    def get_weather_forecast(self, latitude: float, longitude: float, days: int = 7) -> Optional[Dict[str, Any]]:
        logger.info(f" Fetching daily forecast lat={latitude}, lon={longitude}, days={days}")
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "current_weather": True,
            "forecast_days": days,
            "timezone": "auto"
        }

        for base_url in self.base_urls:
            data = self._fetch_with_retries(base_url, params)
            if not data:
                continue

            try:
                forecast = [
                    {
                        "date": data["daily"]["time"][i],
                        "max_temp": data["daily"]["temperature_2m_max"][i],
                        "min_temp": data["daily"]["temperature_2m_min"][i],
                        "precipitation": data["daily"]["precipitation_sum"][i],
                        "weathercode": data["daily"]["weathercode"][i],
                        "condition": _code_text(data["daily"]["weathercode"][i]),
                    }
                    for i in range(len(data["daily"]["time"]))
                ]
                return {
                    "latitude": data["latitude"],
                    "longitude": data["longitude"],
                    "current_temp": data["current_weather"]["temperature"],
                    "condition": _code_text(data["current_weather"]["weathercode"]),
                    "forecast": forecast
                }
            except Exception as e:
                logger.error(f" Failed to parse weather response from {base_url}: {e}", exc_info=True)

        # Fallback if all APIs failed
        logger.error("All weather API attempts failed")
        return {
            "latitude": latitude,
            "longitude": longitude,
            "current_temp": None,
            "condition": "Weather data unavailable",
            "forecast": []
        }

    # ---------------- HOURLY FORECAST ----------------
    def get_hourly_forecast(self, latitude: float, longitude: float, hours: int = 24) -> Optional[List[Dict[str, Any]]]:
        logger.info(f" Fetching hourly forecast for next {hours}h")
        print(f"[weather_service]  Hourly forecast for {hours} hours")
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "temperature_2m,precipitation,weathercode,windspeed_10m",
                "forecast_hours": hours,
                "timezone": "auto"
            }
            resp = requests.get(self.base_url, params=params, timeout=12)
            resp.raise_for_status()
            data = resp.json()
            hourly = [
                {
                    "time": data["hourly"]["time"][i],
                    "temp": data["hourly"]["temperature_2m"][i],
                    "precipitation": data["hourly"]["precipitation"][i],
                    "windspeed": data["hourly"]["windspeed_10m"][i],
                    "condition": _code_text(data["hourly"]["weathercode"][i]),
                }
                for i in range(len(data["hourly"]["time"]))
            ]
            return hourly
        except Exception as e:
            logger.error(f" Hourly forecast error: {e}", exc_info=True)
            print(f"[weather_service]  Hourly forecast error: {e}")
            return None

    # ---------------- AIR QUALITY ----------------
    def get_air_quality(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        logger.info(" Fetching air quality (AQI)")
        print("[weather_service]  Requesting AQI data")
        try:
            url = "https://air-quality-api.open-meteo.com/v1/air-quality"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "pm10,pm2_5,carbon_monoxide,ozone,nitrogen_dioxide,sulphur_dioxide,us_aqi",
                "timezone": "auto"
            }
            resp = requests.get(url, params=params, timeout=12)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f" Air quality error: {e}", exc_info=True)
            print(f"[weather_service]  Air quality error: {e}")
            return None

    # ---------------- CLIMATE SUMMARY ----------------
    def get_climate_summary(self, latitude: float, longitude: float) -> Optional[str]:
        f = self.get_weather_forecast(latitude, longitude)
        if not f:
            return None
        temps = [d['max_temp'] for d in f['forecast']]
        conds = [d['condition'].lower() for d in f['forecast']]

        summary = (
            f"Current: {f['current_temp']}°C, {f['condition']}. "
            f"Highs up to {max(temps):.1f}°C and lows down to {min(temps):.1f}°C. "
        )
        if any("rain" in c or "drizzle" in c or "shower" in c for c in conds):
            summary += "Rain likely — pack waterproofs. "
        if max(temps) > 30:
            summary += "Hot weather — light clothing. "
        if min(temps) < 10:
            summary += "Cold temps — warm layers."
        return summary

    # ---------------- BEST TRAVEL DAY ----------------
    def get_best_travel_day(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Pick the 'nicest' day in the forecast for travel.
        Criteria:
        - Mild temperatures (ideal range 18–28°C)
        - Low precipitation (rain penalized heavily)
        Returns the best day's data + natural language explanation.
        """
        forecast_data = self.get_weather_forecast(latitude, longitude, days=7)
        if not forecast_data:
            return None

        forecast = forecast_data["forecast"]

        IDEAL_MIN, IDEAL_MAX = 18, 28  # °C comfort band
        best_day = None
        best_score = float("inf")

        for day in forecast:
            avg_temp = (day["max_temp"] + day["min_temp"]) / 2
            temp_penalty = max(0, abs(avg_temp - (IDEAL_MIN + IDEAL_MAX) / 2))
            rain_penalty = day["precipitation"] * 2  # rain is more disruptive
            score = temp_penalty + rain_penalty

            if score < best_score:
                best_score = score
                best_day = day

        if best_day:
            best_day["score"] = round(best_score, 2)

            # ✅ Build natural explanation
            reasons = []
            avg_temp = (best_day["max_temp"] + best_day["min_temp"]) / 2

            if IDEAL_MIN <= avg_temp <= IDEAL_MAX:
                reasons.append(f"comfortable average temperature around {avg_temp:.1f}°C")
            else:
                reasons.append(f"temperature of {avg_temp:.1f}°C (slightly outside comfort range)")

            if best_day["precipitation"] == 0:
                reasons.append("no expected rain")
            elif best_day["precipitation"] < 2:
                reasons.append("very little rain")
            else:
                reasons.append(f"{best_day['precipitation']}mm rain (light chance)")

            reasons.append(f"overall condition: {best_day['condition'].lower()}")

            explanation = (
                f" The best travel day is **{best_day['date']}**, "
                f"with {best_day['min_temp']}–{best_day['max_temp']}°C and "
                f"{best_day['precipitation']}mm rain. "
                f"This day was chosen because of " + ", ".join(reasons) + "."
            )

            best_day["advice"] = explanation

            logger.info(f" Best travel day selected: {explanation}")
            print(f"[weather_service]  Best travel day: {explanation}")
            return best_day

        return None
