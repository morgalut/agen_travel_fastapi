# travel_assistant/core/assistant.py
from typing import Dict, Any, Optional
import json
import logging
import os
import asyncio
import httpx

from .prompt_engine import PromptEngine
from .conversation import ConversationManager, QueryType
from .assistant_response import AssistantResponse

# Responders
from .responders.destination_responder import DestinationResponder
from .responders.packing_responder import PackingResponder
from .responders.attractions_responder import AttractionsResponder
from .responders.accommodation_responder import AccommodationResponder
from .responders.general_responder import GeneralResponder
from .responders.visa_responder import VisaResponder 

# Services
from ..services.weather_service import WeatherService
from ..services.country_service import CountryService
from ..services.hotel_service import HotelService
from ..services.transport_service import TransportService
from ..services.visa_service import VisaService         
from ..utils.helpers import geocode_location

logger = logging.getLogger(__name__)

class TravelAssistant:
    """Modular travel assistant with responders and layered fallback."""

    def __init__(self, model: str = "gemma:2b"):
        self.llm_api_url = os.getenv("LLM_API_URL", "http://localhost:11434/api/generate")
        self.model = model

        self.prompt_engine = PromptEngine()
        self.conversation_manager = ConversationManager()

        self.weather_service = WeatherService()
        self.country_service = CountryService()
        self.hotel_service = HotelService()
        self.transport_service = TransportService()
        self.visa_service = VisaService()  # ✅

        limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
        self._client = httpx.AsyncClient(timeout=20, limits=limits)

        # Responders registry
        self.responders = {
            QueryType.DESTINATION: DestinationResponder(),
            QueryType.PACKING:     PackingResponder(),
            QueryType.ATTRACTIONS: AttractionsResponder(),
            QueryType.ACCOMMODATION: AccommodationResponder(),
            QueryType.WEATHER:     GeneralResponder(),  # keep general unless you have a WeatherResponder
            QueryType.BEST_TIME:   GeneralResponder(),
            QueryType.BUDGET:      GeneralResponder(),
            QueryType.SAFETY:      GeneralResponder(),
            QueryType.VISA:        VisaResponder(self.visa_service), 
            QueryType.GENERAL:     GeneralResponder(),
        }

    # ---------------- LLM ----------------
    async def call_llm(self, messages: list) -> str:
        payload = {"model": self.model, "prompt": "\n".join([f"{m['role']}: {m['content']}" for m in messages])}
        try:
            resp = await self._client.post(self.llm_api_url, json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return "__LLM_ERROR__"

    # ---------------- External Lookups ----------------
    async def _orchestrate_targeted_queries(self, query_type: QueryType, entities: Dict[str, Any]) -> Dict[str, Any]:
        destination = entities.get("destination")
        results: Dict[str, Any] = {}

        # Geocode + weather/hotels/country (shared)
        if destination:
            try:
                coords = await asyncio.to_thread(geocode_location, destination)
                if coords:
                    results["coords"] = coords
                    results["climate_info"] = await asyncio.to_thread(
                        self.weather_service.get_climate_summary, coords["lat"], coords["lon"]
                    )
                    results["hotels"] = await asyncio.to_thread(
                        self.hotel_service.get_hotels_nearby, coords["lat"], coords["lon"]
                    )
            except Exception as e:
                logger.warning(f"Geo/Weather/Hotel failed: {e}")

            try:
                country_info = await asyncio.to_thread(self.country_service.get_country_info, destination)
                if country_info:
                    results["country"] = country_info
            except Exception as e:
                logger.warning(f"Country info failed: {e}")

        # Visa (Thailand focus) — do it when asked or when destination is Thailand
        try:
            dest_lower = (destination or "").lower()
            if query_type == QueryType.VISA or "thailand" in dest_lower or dest_lower in ("bangkok", "phuket", "chiang mai"):
                stay_days = None
                if entities.get("duration"):
                    stay_days = self._estimate_days(entities["duration"])
                advice = self.visa_service.get_thailand_advice(
                    passport_country=entities.get("citizenship"),
                    stay_length_days=stay_days,
                    purpose=(entities.get("purpose") or "tourism"),
                )
                results["visa_th"] = advice
            # (Optional) You could add other country branches here later.
        except Exception as e:
            logger.warning(f"Visa lookup failed: {e}")

        return results

    def _estimate_days(self, duration: str) -> Optional[int]:
        try:
            d = duration.lower()
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

    # ---------------- Main ----------------
    async def generate_response(self, user_input: str) -> Dict[str, Any]:
        try:
            # 1) Classify + extract
            query_type = self.conversation_manager.classify_query(user_input)
            entities = self.conversation_manager.extract_entities(user_input)
            self.conversation_manager.update_context(user_input, query_type, entities)

            # 2) External lookups (adds visa_th when relevant)
            external = await self._orchestrate_targeted_queries(query_type, entities)

            # 3) Heuristic responder
            responder = self.responders.get(query_type, GeneralResponder())
            heuristic_answer = await responder.respond(entities, external, self.conversation_manager.context)

            # 4) LLM enrich
            messages = [
                {"role": "system", "content": "You are a precise, up-to-date travel assistant. Improve the answer naturally. Never hallucinate hard rules; if uncertain, include a brief 'verify with official sources' note."},
                {"role": "user", "content": f"Answer: {heuristic_answer}\nEntities: {json.dumps(entities)}\nExternal: {json.dumps(list(external.keys()))}"}
            ]
            llm_answer = await self.call_llm(messages)
            answer = llm_answer if llm_answer and not llm_answer.startswith("__LLM_") else heuristic_answer

            # 5) Lightweight follow-up
            followup = None
            if query_type == QueryType.VISA:
                if not entities.get("citizenship"):
                    followup = "Which passport will you travel with?"
                elif not entities.get("duration"):
                    followup = "How long do you plan to stay?"
                elif not entities.get("purpose"):
                    followup = "Is the trip for tourism, business, or something else?"

            # 6) History
            self.prompt_engine.add_to_history("user", user_input)
            self.prompt_engine.add_to_history("assistant", answer)

            return AssistantResponse(
                answer=answer,
                followup=followup,
                context=self.get_conversation_summary(),
                confidence=0.9,
                sources=list(external.keys())
            ).__dict__

        except Exception as e:
            logger.error(f"generate_response failed: {e}", exc_info=True)
            return AssistantResponse(
                answer="⚠️ Sorry, I hit an error while generating your response.",
                followup="Can you rephrase or ask a simpler question?",
                context=self.get_conversation_summary(),
                confidence=0.2
            ).__dict__

    def get_conversation_summary(self) -> Dict[str, Any]:
        from .conversation import QueryType as QT
        safe_ctx = {
            k: (v.value if isinstance(v, QT) else v)
            for k, v in self.conversation_manager.context.items()
        }
        return {
            "context": safe_ctx,
            "recent_history": self.prompt_engine.get_recent_history(),
            "current_topic": (self.conversation_manager.current_topic.value
                              if self.conversation_manager.current_topic else None),
        }
