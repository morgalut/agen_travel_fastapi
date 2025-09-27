# travel_assistant/core/assistant.py
from typing import Dict, Any, Optional
import json
import logging
import os
import asyncio
import httpx

from .prompt_engine import PromptEngine
from .conversation import ConversationManager, QueryType
from ..services.weather_service import WeatherService
from ..services.country_service import CountryService, HotelService, TransportService
from ..utils.helpers import geocode_location

logger = logging.getLogger(__name__)


class TravelAssistant:
    """Optimized travel assistant with stronger intent detection and hotel integration."""

    def __init__(self, llm_api_url: str = "http://localhost:11434/api/generate", model: str = "gemma:2b"):
        logger.info(" Initializing TravelAssistant...")
        print("[assistant]  Initializing TravelAssistant...")

        self.llm_api_url = os.getenv("LLM_API_URL", "http://localhost:11434/api/generate")

        self.model = model
        self.prompt_engine = PromptEngine()
        self.conversation_manager = ConversationManager()
        self.weather_service = WeatherService()
        self.country_service = CountryService()
        self.hotel_service = HotelService()
        self.transport_service = TransportService()

        # Tunables
        self.llm_timeout = float(os.getenv("LLM_TIMEOUT", "20"))
        self.llm_num_predict = int(os.getenv("LLM_NUM_PREDICT", "200"))

        # Reusable async HTTP client for pooling
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
        self._client = httpx.AsyncClient(timeout=self.llm_timeout, limits=limits)

        # Error tracking
        self.consecutive_errors = 0
        self.max_consecutive_errors = 2

        logger.info(f" TravelAssistant ready with model: {model}")
        print(f"[assistant]  TravelAssistant initialized with model: {model}")

    async def _close(self):
        try:
            await self._client.aclose()
        except Exception:
            pass

    # ---------------- LLM call ----------------
    async def call_llm(self, messages: list) -> str:
        """Non-blocking LLM call with timeout + safe fallbacks."""
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        payload = {"model": self.model, "prompt": prompt, "stream": False, "options": {"num_predict": self.llm_num_predict}}
        try:
            resp = await self._client.post(self.llm_api_url, json=payload)
            resp.raise_for_status()
            result = resp.json()
            return (result.get("response") or "").strip() or "__LLM_EMPTY__"
        except httpx.TimeoutException:
            return "__LLM_TIMEOUT__"
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return "__LLM_ERROR__"

    # ---------------- Clarifications ----------------
    def needs_clarification(self, query_type: QueryType, entities: Dict[str, Any]) -> bool:
        """Check if clarification is needed before processing."""
        if query_type == QueryType.DESTINATION:
            if not entities.get("destination") and not entities.get("interests"):
                return True
        if query_type == QueryType.PACKING:
            needed = ("destination", "duration")
            for k in needed:
                if not entities.get(k) and not self.conversation_manager.context.get(k):
                    return True
            return False
        if query_type == QueryType.ATTRACTIONS:
            return not entities.get("destination")
        if query_type == QueryType.ACCOMMODATION:
            return not (entities.get("destination") or self.conversation_manager.context.get("destination"))
        return False


    def _ask_for_clarification(self, query_type: QueryType) -> str:
        clarifications = {
            QueryType.DESTINATION: (
                "Great! To narrow it down, do you have a budget range and preferred month? "
                "Are you into food, museums, outdoors, nightlife, or something else?"
            ),
            QueryType.PACKING: (
                "Got it. Where are you going and for how many days? Any special activities (hiking, beach, business)?"
            ),
            QueryType.ATTRACTIONS: (
                "Perfect! Which city are we focusing on, and do you prefer museums, food tours, or outdoor walks?"
            ),
            QueryType.ACCOMMODATION: (
                "Happy to help with places to stay! What’s the destination and rough budget? "
                "Do you prefer hotel, apartment, hostel, or boutique?"
            ),
            QueryType.GENERAL: (
                "Are you choosing a destination, figuring out what to do there, or looking for where to stay?"
            ),
        }
        return clarifications.get(query_type, "Could you provide more details?")

    # ---------------- Meta-intent ----------------
    def detect_followup_intent(self, user_input: str, query_type: QueryType) -> Optional[str]:
        text = user_input.lower()
        if "how many days" in text or "time" in text or "long should i stay" in text:
            return "duration_estimate"
        if "cost" in text or "price" in text or "budget" in text:
            return "cost_estimate"
        if "food" in text or "restaurant" in text:
            return "food_recommendations"
        return None

    #  Make this async and await call_llm properly
    async def _generate_followup_question(self, query_type: QueryType, entities: Dict[str, Any]) -> Optional[str]:
        known_facts = [f"{k}: {v}" for k, v in entities.items() if v]
        known_context = "; ".join(known_facts) if known_facts else "None yet"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a friendly, proactive travel planning assistant. "
                    "Ask the single most relevant next question given what you already know. "
                    "Do not repeat prior questions. Keep it short and conversational."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Current query type: {query_type.value}\n"
                    f"Known info: {known_context}\n\n"
                    "What is the next most natural follow-up question?"
                ),
            },
        ]

        followup = await self.call_llm(messages)
        if not followup or followup.startswith("__LLM_"):
            return None
        return followup.strip()

    # ---------------- Heuristic responses ----------------
    def _get_accommodation_response(self, destination: str, country: str, entities: Dict[str, Any], external: Dict[str, Any]) -> str:
        """Generate intelligent accommodation recommendations with available hotel data."""
        hotels = external.get("hotels") or []
        acc_type = entities.get("accommodation_type")
        type_note = f" ({acc_type})" if acc_type else ""

        if hotels:
            lines = []
            for h in hotels[:5]:
                t = h.get("type") or "hotel"
                extras = []
                if h.get("rating"):
                    extras.append(f"{h['rating']}/5")
                if h.get("distance_km") is not None:
                    extras.append(f"{h['distance_km']:.1f} km from center")
                extra_str = f" — {', '.join(extras)}" if extras else ""
                lines.append(f"• {h.get('name','Unnamed')} ({t}){extra_str}")
            hotel_list = "\n".join(lines)

            return (
                f"**Where to Stay in {destination}{f', {country}' if country else ''}{type_note}:**\n\n"
                f" **Options**\n{hotel_list}\n\n"
                " **Booking Tips**\n"
                "• Book early for peak seasons.\n"
                "• Compare reviews across platforms.\n"
                "• Pick walkable areas near your top sights or reliable transit."
            )
        else:
            return (
                f"**Accommodation in {destination}{f', {country}' if country else ''}{type_note}:**\n\n"
                "I can tailor recommendations — quick questions:\n"
                "• Budget range (per night)?\n"
                "• Preferred type (hotel, apartment, hostel, boutique)?\n"
                "• Travel dates and neighborhood vibe (central/nightlife/quiet)?"
            )

    def _get_attractions_response(self, destination: str, country: str) -> str:
        # (unchanged content shortened for brevity)
        return f"""**Top Attractions in {destination}{f', {country}' if country else ''}:**

 **Cultural & Historical Sites**
• Main museums and historical landmarks
• Important religious or government buildings
• Local architectural highlights

 **Neighborhoods & Local Life**
• Popular shopping and dining areas
• Scenic viewpoints and parks
• Cultural districts and markets

 **Activities & Entertainment**
• Local festivals and events
• Outdoor activities and nature spots
• Evening entertainment options

 **Tips:** Check opening hours, consider transit passes, try regional cuisine!
"""

    def _get_packing_response(self, destination: str, country: str) -> str:
        return f"""**Packing List for {destination}{f', {country}' if country else ''}:**

 Clothing
• Weather-appropriate layers
• Comfortable walking shoes
• Light rain protection

 Essentials
• Power adapter, power bank
• Copies of documents, insurance

 Day Gear
• Small backpack
• Water bottle, sun protection
"""

    def _get_destination_response(self) -> str:
        return """**Destination Ideas (by vibe):**
• Beach & Relaxation: Greek Islands, Thailand, Bali
• City & Culture: Tokyo, Rome, NYC
• Nature & Adventure: Swiss Alps, Costa Rica, New Zealand
What vibe are you after and when?"""

    def _get_intelligent_response(self, query_type: QueryType, entities: Dict[str, Any], external_data: Dict[str, Any]) -> str:
        destination = entities.get("destination", "your destination")
        country_info = external_data.get("summary", {}).get("country", {})
        country_name = country_info.get("name", "")

        if query_type == QueryType.ACCOMMODATION:
            return self._get_accommodation_response(destination, country_name, entities, external_data)

        responses = {
            QueryType.ATTRACTIONS: self._get_attractions_response(destination, country_name),
            QueryType.PACKING: self._get_packing_response(destination, country_name),
            QueryType.DESTINATION: self._get_destination_response(),
            QueryType.GENERAL: "Happy to help! Tell me if you want destinations, things to do, packing, or places to stay.",
        }
        return responses.get(query_type, responses[QueryType.GENERAL])

    # ---------------- External lookups (parallel) ----------------
    async def _orchestrate_targeted_queries(self, destination: Optional[str]) -> Dict[str, Any]:
        if not destination:
            return {}
        results: Dict[str, Any] = {}

        try:
            coords = await asyncio.to_thread(geocode_location, destination)
            if coords:
                results["coords"] = {"lat": coords["lat"], "lon": coords["lon"]}

                # Weather / climate
                climate = await asyncio.to_thread(
                    self.weather_service.get_climate_summary, coords["lat"], coords["lon"]
                )
                if climate:
                    results["climate_info"] = climate

                # Hotels nearby (quick list)
                hotels = await asyncio.to_thread(
                    self.hotel_service.get_hotels_nearby, coords["lat"], coords["lon"]
                )
                if hotels:
                    # Normalize a bit
                    norm = []
                    for h in hotels:
                        norm.append({
                            "name": h.get("name"),
                            "type": h.get("type") or "hotel",
                            "rating": h.get("rating"),
                            "distance_km": h.get("distance_km"),
                        })
                    results["hotels"] = norm

            country_info = await asyncio.to_thread(self.country_service.get_country_info, destination)
            if country_info:
                results["country"] = {
                    "name": country_info.get("name"),
                    "capital": country_info.get("capital"),
                    "region": country_info.get("region"),
                    "currency": country_info.get("currency"),
                }

            try:
                if coords:
                    t = await asyncio.to_thread(self.transport_service.get_transport_summary, destination)
                    if t:
                        results["transport"] = t
            except Exception:
                pass

        except Exception as e:
            logger.warning(f" Targeted queries failed: {e}")

        return results

    # ---------------- Main pipeline ----------------
    async def generate_response(self, user_input: str) -> Dict[str, Any]:
        """Async response pipeline with robust accommodations support."""
        try:
            logger.info(f"📝 Generating response for: {user_input}")

            # 1) Classify + extract
            query_type = self.conversation_manager.classify_query(user_input)
            entities = self.conversation_manager.extract_entities(user_input)
            self.conversation_manager.update_context(user_input, query_type, entities)

            # 2) Meta-intent fast path (example)
            intent = self.detect_followup_intent(user_input, query_type)
            if intent == "duration_estimate" and query_type == QueryType.ATTRACTIONS:
                answer = (
                    "Plan at least **3 full days** to cover highlights.\n"
                    "• Day 1: Icons & river views\n• Day 2: Museums & neighborhoods\n• Day 3: Old town & markets"
                )
                return {"answer": answer, "followup": None, "context": self.get_conversation_summary()}

            # 3) Clarify if necessary
            if self.needs_clarification(query_type, entities):
                followup = self._ask_for_clarification(query_type)
                return {"answer": followup, "followup": None, "context": self.get_conversation_summary()}

            # 4) External lookups
            external = await self._orchestrate_targeted_queries(entities.get("destination"))

            # 5) Build prompt
            prompt_data = self.prompt_engine.build_prompt(
                query_type.value,
                query=user_input,
                history=self.prompt_engine.get_recent_history(),
                external_data=json.dumps(external, indent=2),
                climate_info=external.get("climate_info", "N/A"),
                duration=entities.get("duration", "Not specified"),
                activities=", ".join(entities.get("interests", [])) or "Not specified",
                special_needs="None"
            )
            messages = [
                {"role": "system", "content": prompt_data["system"]},
                {"role": "user", "content": prompt_data["user"]},
            ]

            # 6) Call LLM
            answer = await self.call_llm(messages)

            # 7) Fallback heuristics if LLM failed
            if not answer or answer.startswith("__LLM_"):
                answer = self._get_intelligent_response(query_type, entities, {"summary": external, **external})

            # 8) Follow-up (natural) — best-effort
            followup_q = await self._generate_followup_question(query_type, entities)

            # 9) Store history
            self.prompt_engine.add_to_history("user", user_input)
            self.prompt_engine.add_to_history("assistant", answer)

            return {
                "answer": answer or "I wasn’t able to generate a response.",
                "followup": followup_q,
                "context": self.get_conversation_summary(),
            }

        except Exception as e:
            logger.error(f" generate_response failed: {e}", exc_info=True)
            return {
                "answer": " Sorry, I hit an error while generating your response.",
                "followup": "Can you rephrase or ask a simpler question?",
                "context": self.get_conversation_summary(),
            }

    def get_conversation_summary(self) -> Dict[str, Any]:
        safe_ctx = {
            k: (v.value if isinstance(v, QueryType) else v)
            for k, v in self.conversation_manager.context.items()
        }
        return {
            "context": safe_ctx,
            "recent_history": self.prompt_engine.get_recent_history(),
            "current_topic": (self.conversation_manager.current_topic.value
                              if self.conversation_manager.current_topic else None),
            "consecutive_errors": self.consecutive_errors,
        }
