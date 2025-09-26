# travel_assistant/core/assistant.py
from typing import Dict, Any, Optional
import requests
import json
import logging
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .prompt_engine import PromptEngine
from .conversation import ConversationManager, QueryType
from ..services.weather_service import WeatherService
from ..services.country_service import CountryService
from ..utils.helpers import geocode_location

# Setup logger
logger = logging.getLogger(__name__)


class TravelAssistant:
    """Main travel assistant class with external-data orchestration and structured responses."""

    def __init__(self, llm_api_url: str = "http://localhost:11434/api/generate", model: str = "llama2"):
        logger.info("🚀 Initializing TravelAssistant...")
        print("[assistant] 🚀 Initializing TravelAssistant...")

        self.llm_api_url = llm_api_url
        self.model = model
        self.prompt_engine = PromptEngine()
        self.conversation_manager = ConversationManager()
        self.weather_service = WeatherService()
        self.country_service = CountryService()

        # Clarification state
        self.awaiting_clarification = False
        self.clarification_topic = None

        # Timeout + options (from env or defaults)
        self.llm_connect_timeout = float(os.getenv("LLM_CONNECT_TIMEOUT", "5"))
        self.llm_read_timeout = float(os.getenv("LLM_READ_TIMEOUT", "120"))
        self.llm_num_predict = int(os.getenv("LLM_NUM_PREDICT", "320"))

        # Robust requests session with retries
        self.session = requests.Session()
        retries = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=[429, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        logger.info("✅ TravelAssistant ready")
        print("[assistant] ✅ TravelAssistant initialized successfully")

    # -------------------- LLM --------------------
    def call_llm(self, messages: list) -> str:
        """Call Ollama-style LLM API with retries + fallback streaming."""
        logger.info("🤖 Calling LLM...")
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.6, "num_predict": self.llm_num_predict}
        }
        timeout = (self.llm_connect_timeout, self.llm_read_timeout)

        try:
            t0 = time.monotonic()
            resp = self.session.post(self.llm_api_url, json=payload, timeout=timeout)
            resp.raise_for_status()
            result = resp.json()
            text = result.get("response", "").strip()
            logger.info(f"✅ LLM responded in {time.monotonic() - t0:.2f}s")
            return text or "__LLM_ERROR__"
        except Exception as e:
            logger.error(f"❌ LLM call failed: {e}", exc_info=True)
            return "__LLM_ERROR__"

    # -------------------- Targeted Data Orchestration --------------------
    def _summarize_forecast(self, forecast: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not forecast:
            return None
        try:
            days = forecast.get("forecast", [])[:3]
            return {
                "now": {"temp_c": forecast.get("current_temp"), "condition": forecast.get("condition")},
                "next_days": [
                    {
                        "date": d["date"],
                        "min_max_c": [d["min_temp"], d["max_temp"]],
                        "rain_mm": d["precipitation"],
                        "condition": d["condition"]
                    }
                    for d in days
                ]
            }
        except Exception:
            return None

    def _summarize_aqi(self, aqi_raw: Optional[Dict[str, Any]]) -> Optional[str]:
        if not aqi_raw:
            return None
        try:
            hourly = aqi_raw.get("hourly", {})
            us_aqi = hourly.get("us_aqi", [])
            if not us_aqi:
                return None
            val = us_aqi[0]
            if val <= 50:
                level = "Good"
            elif val <= 100:
                level = "Moderate"
            elif val <= 150:
                level = "Unhealthy (sensitive)"
            else:
                level = "Unhealthy"
            return f"AQI {val} ({level})"
        except Exception:
            return None

    def _orchestrate_targeted_queries(self, query_type: QueryType, entities: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("🧭 Running targeted queries (weather, AQI, country info)...")
        external = {"raw": {}, "summary": {}}
        destination = entities.get("destination")

        coords = None
        if destination:
            coords = geocode_location(destination)
            if coords:
                external["summary"]["coords"] = {"lat": round(coords["lat"], 4), "lon": round(coords["lon"], 4)}

        if coords:
            daily = self.weather_service.get_weather_forecast(coords["lat"], coords["lon"], days=7)
            best_day = self.weather_service.get_best_travel_day(coords["lat"], coords["lon"])
            aqi = self.weather_service.get_air_quality(coords["lat"], coords["lon"])
            external["summary"]["climate_info"] = self.weather_service.get_climate_summary(coords["lat"], coords["lon"])
            external["summary"]["forecast"] = self._summarize_forecast(daily)
            if best_day:
                external["summary"]["best_travel_day"] = {
                    "date": best_day.get("date"),
                    "min_max_c": [best_day.get("min_temp"), best_day.get("max_temp")],
                    "rain_mm": best_day.get("precipitation"),
                    "condition": best_day.get("condition"),
                    "why": best_day.get("advice")
                }
            aqi_note = self._summarize_aqi(aqi)
            if aqi_note:
                external["summary"]["aqi"] = aqi_note

        if destination and (query_type in (QueryType.ATTRACTIONS, QueryType.DESTINATION)):
            cinfo = self.country_service.get_country_info(destination)
            if cinfo:
                external["summary"]["country"] = {
                    "name": cinfo.get("name"),
                    "capital": cinfo.get("capital"),
                    "region": cinfo.get("region"),
                    "currency": cinfo.get("currency")
                }

        return external

    # -------------------- Clarifications --------------------
    def needs_clarification(self, query_type: QueryType, entities: Dict[str, Any]) -> bool:
        if query_type == QueryType.DESTINATION and not entities.get('interests') and not entities.get('destination'):
            return True
        if query_type == QueryType.PACKING and not entities.get('destination'):
            return True
        if query_type == QueryType.ATTRACTIONS and not entities.get('destination'):
            return True
        return False

    def _ask_for_clarification(self, query_type: QueryType) -> str:
        if query_type == QueryType.DESTINATION:
            return "What kind of experience do you want—beaches, cities, culture, or adventure? And what's your budget?"
        if query_type == QueryType.PACKING:
            return "To give packing advice, I need to know your destination. Where are you going?"
        if query_type == QueryType.ATTRACTIONS:
            return "I can suggest attractions! Which city or country are you visiting?"
        return "Could you provide more details?"

    # -------------------- Follow-up --------------------
    # -------------------- Follow-up --------------------
    def _generate_followup_question(self, query_type: QueryType, entities: Dict[str, Any]) -> Optional[str]:
        """
        Suggest a caring follow-up question to deepen the conversation.
        Only ask about entities that are clearly missing.
        """
        missing = []

        # Normalize duration: only treat as missing if None or empty
        duration = entities.get("duration")
        if query_type == QueryType.PACKING:
            if not duration or str(duration).strip().lower() in ["", "0", "none"]:
                missing.append("trip duration")
            if not entities.get("activities"):
                missing.append("activities")

        elif query_type == QueryType.DESTINATION:
            if not entities.get("budget"):
                missing.append("budget")
            if not entities.get("interests"):
                missing.append("interests")

        elif query_type == QueryType.ATTRACTIONS and not entities.get("destination"):
            missing.append("destination")

        # Nothing missing → no follow-up needed
        if not missing:
            return None

        # Try LLM-driven follow-up
        try:
            prompt = (
                f"You are a warm, caring travel assistant.\n"
                f"Query type: {query_type.value}\n"
                f"Known entities: {json.dumps(entities, indent=2)}\n"
                f"Missing: {', '.join(missing)}\n\n"
                "Ask ONE short follow-up question (<20 words)."
            )
            messages = [
                {"role": "system", "content": "Be concise and empathetic."},
                {"role": "user", "content": prompt}
            ]
            followup = self.call_llm(messages).strip()
            if followup and len(followup.split()) < 25:
                return followup
        except Exception:
            pass

        # Template fallback — pick first missing field
        if "trip duration" in missing:
            return "Any special activities planned, like sightseeing or fine dining?"
        if "activities" in missing:
            return "Do you have specific activities planned—museums, hiking, nightlife?"
        if "budget" in missing:
            return "What budget range feels comfortable for this trip?"
        if "interests" in missing:
            return "Are you more into culture, food, adventure, or relaxation?"
        if "destination" in missing:
            return "Which city or country should I focus on for attractions?"

        return None


    # -------------------- Response Generation --------------------
    def generate_response(self, user_input: str) -> Dict[str, Any]:
        logger.info(f"📝 Generating response for: {user_input}")
        try:
            query_type = self.conversation_manager.classify_query(user_input)
            entities = self.conversation_manager.extract_entities(user_input)

            # Clarification before querying
            if self.needs_clarification(query_type, entities):
                return {
                    "answer": self._ask_for_clarification(query_type),
                    "followup": None,
                    "context": self.get_conversation_summary()
                }

            # Update context
            self.conversation_manager.update_context(user_input, query_type, entities)

            # Targeted queries first
            external = self._orchestrate_targeted_queries(query_type, entities) if entities.get("destination") else {}

            # Build prompt
            compact_ext = json.dumps(external.get("summary", {}), indent=2)
            prompt_data = self.prompt_engine.build_prompt(
                query_type.value,
                query=user_input,
                history=self.prompt_engine.get_recent_history(),
                external_data=compact_ext,
                climate_info=external.get("summary", {}).get("climate_info", "N/A"),
                duration=entities.get('duration', 'Not specified'),
                activities=", ".join(entities.get('interests', [])),
                special_needs="None"
            )
            messages = [
                {"role": "system", "content": prompt_data["system"]},
                {"role": "user", "content": prompt_data["user"]}
            ]

            # Call LLM
            answer = self.call_llm(messages)
            if answer == "__LLM_ERROR__":
                return {
                    "answer": "⚠️ I’m having trouble reaching the model. Please try again later.",
                    "followup": None,
                    "context": self.get_conversation_summary()
                }

            # Store history
            self.prompt_engine.add_to_history("user", user_input)
            self.prompt_engine.add_to_history("assistant", answer)

            # Add follow-up
            followup = self._generate_followup_question(query_type, entities)

            return {
                "answer": answer,
                "followup": followup,
                "context": self.get_conversation_summary()
            }

        except Exception as e:
            logger.error(f"❌ Error in generate_response: {e}", exc_info=True)
            return {
                "answer": f"❌ Error: {e}",
                "followup": None,
                "context": self.get_conversation_summary()
            }

    # -------------------- Summary --------------------
    def get_conversation_summary(self) -> Dict[str, Any]:
        safe_ctx = {
            k: (v.value if isinstance(v, QueryType) else v)
            for k, v in self.conversation_manager.context.items()
        }
        return {
            "context": safe_ctx,
            "recent_history": self.prompt_engine.get_recent_history(),
            "current_topic": (
                self.conversation_manager.current_topic.value if self.conversation_manager.current_topic else None
            )
        }
