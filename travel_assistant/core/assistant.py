# travel_assistant/core/assistant.py
from typing import Dict, Any, Optional
import requests
import json
from .prompt_engine import PromptEngine
from .conversation import ConversationManager, QueryType
from ..services.weather_service import WeatherService
from ..services.country_service import CountryService
from ..utils.helpers import geocode_location   # ✅ free geocoding helper


class TravelAssistant:
    """Main travel assistant class"""

    def __init__(self, llm_api_url: str = "http://localhost:11434/api/generate", model: str = "llama2"):
        self.llm_api_url = llm_api_url
        self.model = model
        self.prompt_engine = PromptEngine()
        self.conversation_manager = ConversationManager()
        self.weather_service = WeatherService()
        self.country_service = CountryService()

        # Track conversation state
        self.awaiting_clarification = False
        self.clarification_topic = None

    # -------------------- LLM --------------------
    def call_llm(self, messages: list) -> str:
        """Make API call to LLM (Ollama-style endpoint)"""
        try:
            # Prepare payload for Ollama
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(self.llm_api_url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "I apologize, but I couldn't process your request.")
        except Exception as e:
            return f"I'm experiencing technical difficulties. Error: {str(e)}"

    # -------------------- External Data --------------------
    def should_use_external_data(self, query_type: QueryType, entities: Dict[str, Any]) -> bool:
        """Decide when to use external data vs LLM knowledge"""
        if query_type == QueryType.PACKING and entities.get('destination'):
            return True
        if query_type == QueryType.ATTRACTIONS and entities.get('destination'):
            return True
        if query_type == QueryType.DESTINATION and entities.get('interests'):
            return True
        return False

    def gather_external_data(self, query_type: QueryType, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Gather relevant external data based on query type"""
        external_data = {}
        destination = entities.get('destination')

        if query_type == QueryType.PACKING and destination:
            # ✅ Use geocoding + Open-Meteo for climate
            coords = geocode_location(destination)
            if coords:
                climate_info = self.weather_service.get_climate_summary(coords["lat"], coords["lon"])
                if climate_info:
                    external_data['climate_info'] = climate_info

        elif query_type == QueryType.ATTRACTIONS and destination:
            # Basic country info for attractions
            country_info = self.country_service.get_country_info(destination)
            if country_info:
                external_data['country_info'] = country_info

        elif query_type == QueryType.DESTINATION:
            # Placeholder for future flight/advisory APIs
            pass

        return external_data

    # -------------------- Clarification --------------------
    def needs_clarification(self, query_type: QueryType, entities: Dict[str, Any]) -> bool:
        """Check if we need to ask for clarification"""
        if query_type == QueryType.DESTINATION and not entities.get('interests'):
            return True
        if query_type == QueryType.PACKING and not entities.get('destination'):
            return True
        if query_type == QueryType.ATTRACTIONS and not entities.get('destination'):
            return True
        return False

    def _ask_for_clarification(self, query_type: QueryType, entities: Dict[str, Any]) -> str:
        """Ask user for clarification based on query type"""
        if query_type == QueryType.DESTINATION:
            return (
                "I'd love to help you find the perfect destination! "
                "Could you tell me what kind of experiences you're looking for? "
                "For example, are you interested in beaches, mountains, cities, cultural experiences, or adventure?"
            )
        elif query_type == QueryType.PACKING:
            return "To give you the best packing advice, I need to know your destination. Where are you planning to travel?"
        elif query_type == QueryType.ATTRACTIONS:
            return "I can suggest some great attractions! Which city or country are you planning to visit?"
        return "Could you please provide a bit more detail about what you're looking for?"

    def _handle_clarification_response(self, user_input: str, query_type: QueryType, entities: Dict[str, Any]) -> str:
        """Handle user's response to clarification request"""
        self.conversation_manager.update_context(user_input, query_type, entities)
        return self.generate_response(user_input)

    # -------------------- Guard Helpers --------------------
    def _is_on_topic(self, text: str, query_type: QueryType) -> bool:
        """Check if the LLM response is roughly on-topic for the query type"""
        t = text.lower()
        if query_type == QueryType.PACKING:
            keys = ["pack", "packing", "clothing", "layers", "toiletries"]
        elif query_type == QueryType.DESTINATION:
            keys = ["go", "destination", "visit", "recommend"]
        elif query_type == QueryType.ATTRACTIONS:
            keys = ["attraction", "things to do", "sightseeing", "museum", "park"]
        else:
            keys = ["travel", "trip", "itinerary"]
        return any(k in t for k in keys)

    def _trim_if_too_long(self, text: str, limit: int = 1200) -> str:
        """Trim LLM response if it's too long to keep answers concise"""
        return text if len(text) <= limit else text[:limit] + "…"

    # -------------------- Response Generation --------------------
    def generate_response(self, user_input: str) -> str:
        """Generate response for user input"""
        try:
            # Classify query and extract entities
            query_type = self.conversation_manager.classify_query(user_input)
            entities = self.conversation_manager.extract_entities(user_input)

            # Handle clarification flow
            if self.awaiting_clarification:
                response = self._handle_clarification_response(user_input, query_type, entities)
                self.awaiting_clarification = False
                return response

            # Check if we need clarification
            if self.needs_clarification(query_type, entities):
                self.awaiting_clarification = True
                self.clarification_topic = query_type
                return self._ask_for_clarification(query_type, entities)

            # Update conversation context
            self.conversation_manager.update_context(user_input, query_type, entities)

            # Gather external data if needed
            external_data = {}
            if self.should_use_external_data(query_type, entities):
                external_data = self.gather_external_data(query_type, entities)

            # Build prompt
            prompt_data = self.prompt_engine.build_prompt(
                query_type.value,
                query=user_input,
                history=self.prompt_engine.get_recent_history(),
                external_data=json.dumps(external_data, indent=2),
                climate_info=external_data.get('climate_info', 'Not available'),
                duration=entities.get('duration', 'Not specified'),
                activities=", ".join(entities.get('interests', [])),
                special_needs="None specified"
            )

            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": prompt_data["system"]},
                {"role": "user", "content": prompt_data["user"]}
            ]
            if self.prompt_engine.conversation_history:
                for msg in self.prompt_engine.conversation_history[-3:]:
                    messages.insert(-1, msg)

            # Get LLM response
            response = self.call_llm(messages)

            # ✅ Basic sanity check & length guard
            if not self._is_on_topic(response, query_type):
                return self._ask_for_clarification(query_type, entities)
            response = self._trim_if_too_long(response)

            # Update conversation history
            self.prompt_engine.add_to_history("user", user_input)
            self.prompt_engine.add_to_history("assistant", response)

            return response

        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}. Please try again."
            self.prompt_engine.add_to_history("assistant", error_msg)
            return error_msg

    # -------------------- Conversation Summary --------------------
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation (safe for JSON)"""
        safe_context = {
            k: (v.value if isinstance(v, QueryType) else v)
            for k, v in self.conversation_manager.context.items()
        }

        return json.dumps({
            "context": safe_context,
            "recent_history": self.prompt_engine.get_recent_history(),
            "current_topic": (
                self.conversation_manager.current_topic.value
                if self.conversation_manager.current_topic else None
            )
        }, indent=2)
