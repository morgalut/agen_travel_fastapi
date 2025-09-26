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
from ..services.country_service import CountryService, HotelService, TransportService
from ..utils.helpers import geocode_location

# Setup logger
logger = logging.getLogger(__name__)


class TravelAssistant:
    """Optimized travel assistant with reliable fallback responses."""

    def __init__(self, llm_api_url: str = "http://localhost:11434/api/generate", model: str = "llama3.2:1b"):
        logger.info("🚀 Initializing TravelAssistant...")
        print("[assistant] 🚀 Initializing TravelAssistant...")

        self.llm_api_url = llm_api_url
        self.model = model
        self.prompt_engine = PromptEngine()
        self.conversation_manager = ConversationManager()
        self.weather_service = WeatherService()
        self.country_service = CountryService()
        self.hotel_service = HotelService()
        self.transport_service = TransportService()

        # Performance-optimized settings
        self.llm_connect_timeout = float(os.getenv("LLM_CONNECT_TIMEOUT", "10"))
        self.llm_read_timeout = float(os.getenv("LLM_READ_TIMEOUT", "45"))
        self.llm_num_predict = int(os.getenv("LLM_NUM_PREDICT", "200"))

        # Robust session configuration
        self.session = requests.Session()
        retries = Retry(
            total=1,
            backoff_factor=0.5,
            status_forcelist=[429, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=5, pool_maxsize=5)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Performance tracking
        self.consecutive_errors = 0
        self.max_consecutive_errors = 2

        logger.info(f"✅ TravelAssistant ready with model: {model}")
        print(f"[assistant] ✅ TravelAssistant initialized with model: {model}")

    def call_llm(self, messages: list) -> str:
        """Efficient LLM call with comprehensive error handling."""
        logger.info("🤖 Calling LLM...")
        
        # Skip LLM if too many consecutive errors
        if self.consecutive_errors >= self.max_consecutive_errors:
            logger.warning("🔄 Skipping LLM due to consecutive errors")
            return "__LLM_SKIPPED__"

        # Create compact prompt
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": self.llm_num_predict,
                "top_k": 20,
                "top_p": 0.9,
            }
        }
        
        timeout = (self.llm_connect_timeout, self.llm_read_timeout)

        try:
            logger.debug(f"📤 Sending request, prompt length: {len(prompt)}")
            t0 = time.monotonic()
            
            resp = self.session.post(
                self.llm_api_url, 
                json=payload, 
                timeout=timeout
            )
            resp.raise_for_status()
            
            result = resp.json()
            text = result.get("response", "").strip()
            response_time = time.monotonic() - t0
            
            logger.info(f"✅ LLM responded in {response_time:.2f}s")
            
            # Reset error counter on success
            self.consecutive_errors = 0
            
            if not text:
                return "__LLM_EMPTY_RESPONSE__"
                
            return text
            
        except requests.exceptions.Timeout:
            logger.error(f"⏰ LLM timeout after {self.llm_read_timeout}s")
            self.consecutive_errors += 1
            return "__LLM_TIMEOUT__"
        except requests.exceptions.ConnectionError:
            logger.error("🔌 LLM connection error")
            self.consecutive_errors += 1
            return "__LLM_CONNECTION_ERROR__"
        except Exception as e:
            logger.error(f"❌ LLM call failed: {e}")
            self.consecutive_errors += 1
            return "__LLM_ERROR__"

    def needs_clarification(self, query_type: QueryType, entities: Dict[str, Any]) -> bool:
        """Check if clarification is needed before processing."""
        if query_type == QueryType.DESTINATION and not entities.get('interests') and not entities.get('destination'):
            return True
        if query_type == QueryType.PACKING and not entities.get('destination'):
            return True
        if query_type == QueryType.ATTRACTIONS and not entities.get('destination'):
            return True
        return False

    def _ask_for_clarification(self, query_type: QueryType) -> str:
        """Ask user for clarification based on query type."""
        clarifications = {
            QueryType.DESTINATION: "What kind of experience are you looking for? (beaches, cities, culture, adventure) And what's your budget?",
            QueryType.PACKING: "To give you the best packing advice, where are you traveling to?",
            QueryType.ATTRACTIONS: "I'd love to suggest attractions! Which city or country are you visiting?",
            QueryType.GENERAL: "Could you tell me more about what you're looking for?"
        }
        return clarifications.get(query_type, "Could you provide more details?")

    def _generate_followup_question(self, query_type: QueryType, entities: Dict[str, Any]) -> Optional[str]:
        """Generate simple follow-up questions."""
        if query_type == QueryType.ATTRACTIONS:
            if not entities.get('interests'):
                return "Are you more interested in art, history, food, or outdoor activities?"
        elif query_type == QueryType.PACKING:
            if not entities.get('duration'):
                return "How long will you be traveling for?"
        elif query_type == QueryType.DESTINATION:
            if not entities.get('budget'):
                return "What budget range are you considering?"
        return None

    def _get_intelligent_response(self, query_type: QueryType, entities: Dict[str, Any], external_data: Dict[str, Any]) -> str:
        """Generate high-quality responses without relying on LLM."""
        destination = entities.get('destination', 'your destination')
        country_info = external_data.get('summary', {}).get('country', {})
        country_name = country_info.get('name', '')
        
        responses = {
            QueryType.ATTRACTIONS: self._get_attractions_response(destination, country_name),
            QueryType.PACKING: self._get_packing_response(destination, country_name),
            QueryType.DESTINATION: self._get_destination_response(),
            QueryType.GENERAL: "I'd be happy to help with your travel plans! Could you tell me more about what you're looking for?"
        }
        
        return responses.get(query_type, responses[QueryType.GENERAL])

    def _get_attractions_response(self, destination: str, country: str) -> str:
        """Generate comprehensive attractions response."""
        base_responses = {
            'Paris': """**Top Attractions in Paris, France:**

🏛️ **Iconic Landmarks**
• Eiffel Tower - City views, evening light show
• Louvre Museum - Mona Lisa, Venus de Milo, vast art collection
• Notre-Dame Cathedral - Gothic architecture (check reopening status)
• Arc de Triomphe - Panoramic city views

🎨 **Arts & Culture**
• Musée d'Orsay - Impressionist masterpieces
• Centre Pompidou - Modern art & architecture
• Sainte-Chapelle - Stunning stained glass windows

🌆 **Neighborhoods & Views**
• Montmartre & Sacré-Cœur - Artistic area, hilltop views
• Champs-Élysées - Shopping & walking
• Seine River Cruise - See Paris from the water

💡 **Tips:** Purchase museum passes online, use Metro for transportation, book Eiffel Tower tickets in advance.""",

            'London': """**Top Attractions in London, UK:**

🏰 **Historic Sites**
• Buckingham Palace - Royal residence & Changing of the Guard
• Tower of London - Crown Jewels, Beefeaters, history
• Westminster Abbey - Coronation church, royal tombs
• St. Paul's Cathedral - Iconic dome, city views

🎭 **Culture & Museums** (Free entry!)
• British Museum - Rosetta Stone, Egyptian mummies
• National Gallery - European masterpieces
• Tate Modern - Contemporary art
• West End - World-class theater

🌉 **Modern London**
• London Eye - River Thames panorama
• Tower Bridge - Victorian engineering marvel
• Covent Garden - Street performers, shopping

💡 **Tips:** Get an Oyster card for transport, book popular attractions online, explore different neighborhoods.""",

            'Rome': """**Top Attractions in Rome, Italy:**

🏛️ **Ancient History**
• Colosseum - Ancient gladiator arena
• Roman Forum - Ancient government center
• Pantheon - Perfect ancient dome, Raphael's tomb
• Palatine Hill - Original Roman settlement

🎨 **Art & Religion**
• Vatican Museums - Sistine Chapel, Raphael Rooms
• St. Peter's Basilica - World's largest church
• Trevi Fountain - Baroque masterpiece (throw a coin!)
• Spanish Steps - Famous staircase, shopping area

🍝 **Local Experience**
• Trastevere - Charming medieval streets, restaurants
• Piazza Navona - Baroque squares, fountains
• Jewish Ghetto - Ancient Roman ruins, great food

💡 **Tips:** Book Colosseum/Vatican tickets online, wear comfortable shoes, try local gelato!"""
        }
        
        if destination in base_responses:
            return base_responses[destination]
        else:
            return f"""**Top Attractions in {destination}{f', {country}' if country else ''}:**

🏛️ **Cultural & Historical Sites**
• Main museums and historical landmarks
• Important religious or government buildings
• Local architectural highlights

🌆 **Neighborhoods & Local Life**
• Popular shopping and dining areas
• Scenic viewpoints and parks
• Cultural districts and markets

🎭 **Activities & Entertainment**
• Local festivals and events
• Outdoor activities and nature spots
• Evening entertainment options

💡 **Tips:** Research opening hours in advance, consider local transportation passes, and try regional cuisine!"""

    def _get_packing_response(self, destination: str, country: str) -> str:
        """Generate intelligent packing recommendations."""
        climate_tips = {
            'Paris': "• Layers for changeable weather\n• Comfortable walking shoes\n• Rain jacket or umbrella",
            'London': "• Waterproof jacket essential\n• Layers for unpredictable weather\n• Comfortable walking shoes",
            'Rome': "• Light layers for warm days\n• Modest clothing for churches\n• Comfortable walking shoes",
        }
        
        general_tips = climate_tips.get(destination, "• Weather-appropriate clothing\n• Comfortable walking shoes\n• Layers for temperature changes")
        
        return f"""**Packing List for {destination}{f', {country}' if country else ''}:**

👕 **Clothing Essentials**
{general_tips}
• Smart-casual outfits for dining
• Swimwear if hotel has pool

📱 **Travel Essentials**
• Universal power adapter
• Portable charger/power bank
• Copies of important documents
• Travel insurance details

🎒 **Day Trip Gear**
• Small backpack or crossbody bag
• Reusable water bottle
• Sun protection (sunglasses, hat, sunscreen)
• Basic first aid kit

💡 **Additional Tips**
• Check airline baggage restrictions
• Leave space for souvenirs
• Pack medications in carry-on"""

    def _get_destination_response(self) -> str:
        """Generate destination recommendations."""
        return """**Travel Destination Ideas Based on Interests:**

🌊 **Beach & Relaxation**
• **Bali, Indonesia** - Culture, beaches, affordable luxury
• **Greek Islands** - Stunning views, history, island hopping
• **Thailand** - Beautiful beaches, amazing food, great value

🏙️ **City & Culture**
• **Tokyo, Japan** - Modern meets traditional, incredible food
• **Rome, Italy** - Ancient history, art, world-class cuisine
• **New York City, USA** - Energy, diversity, endless activities

⛰️ **Adventure & Nature**
• **Swiss Alps** - Hiking, stunning scenery, outdoor activities
• **Costa Rica** - Rainforests, wildlife, eco-tourism
• **New Zealand** - Dramatic landscapes, adventure sports

🎨 **Arts & Food**
• **Paris, France** - Art museums, architecture, cuisine
• **Barcelona, Spain** - Gaudi architecture, tapas, Mediterranean vibe
• **Mexico City, Mexico** - Vibrant culture, amazing food, museums

**What type of experience are you most interested in?**"""

    def _orchestrate_targeted_queries(self, query_type: QueryType, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Run targeted lookups with error handling."""
        logger.info("🧭 Running targeted queries...")
        
        external = {"raw": {}, "summary": {}}
        destination = entities.get("destination")
        
        if not destination:
            return external

        try:
            # Geocode first
            coords = geocode_location(destination)
            if coords:
                external["summary"]["coords"] = {
                    "lat": round(coords["lat"], 4),
                    "lon": round(coords["lon"], 4),
                }
                external["raw"]["coords"] = coords

                # Basic weather info
                try:
                    climate = self.weather_service.get_climate_summary(coords["lat"], coords["lon"])
                    if climate:
                        external["summary"]["climate_info"] = climate
                except:
                    pass

            # Country info
            try:
                cinfo = self.country_service.get_country_info(destination)
                if cinfo:
                    external["summary"]["country"] = {
                        "name": cinfo.get("name"),
                        "capital": cinfo.get("capital"),
                        "region": cinfo.get("region"),
                        "currency": cinfo.get("currency"),
                    }
            except:
                pass

        except Exception as e:
            logger.warning(f"⚠️ Targeted queries partially failed: {e}")

        return external

    def generate_response(self, user_input: str) -> Dict[str, Any]:
        """Main response generation with optimal performance."""
        logger.info(f"📝 Generating response for: {user_input}")
        
        try:
            query_type = self.conversation_manager.classify_query(user_input)
            entities = self.conversation_manager.extract_entities(user_input)

            # Handle clarification needs
            if self.needs_clarification(query_type, entities):
                return {
                    "answer": self._ask_for_clarification(query_type),
                    "followup": None,
                    "context": self.get_conversation_summary()
                }

            # Update context
            self.conversation_manager.update_context(user_input, query_type, entities)

            # Get external data (non-blocking)
            external = {}
            try:
                external = self._orchestrate_targeted_queries(query_type, entities)
            except Exception as e:
                logger.warning(f"⚠️ External queries failed: {e}")

            # Decide response strategy
            if self.consecutive_errors < self.max_consecutive_errors:
                # Try LLM with optimized prompt
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

                answer = self.call_llm(messages)
                
                # Use fallback if LLM failed
                if answer.startswith("__LLM_"):
                    answer = self._get_intelligent_response(query_type, entities, external)
            else:
                # Use intelligent fallback directly
                answer = self._get_intelligent_response(query_type, entities, external)

            # Store conversation
            self.prompt_engine.add_to_history("user", user_input)
            self.prompt_engine.add_to_history("assistant", answer)

            # Generate follow-up
            followup = self._generate_followup_question(query_type, entities)

            return {
                "answer": answer,
                "followup": followup,
                "context": self.get_conversation_summary()
            }

        except Exception as e:
            logger.error(f"❌ Error in generate_response: {e}")
            return {
                "answer": "I'd love to help you plan your trip! Here are some popular attractions: Eiffel Tower (Paris), Colosseum (Rome), British Museum (London). What destination interests you?",
                "followup": "Which city or country would you like to explore?",
                "context": self.get_conversation_summary()
            }

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get current conversation state."""
        safe_ctx = {
            k: (v.value if isinstance(v, QueryType) else v)
            for k, v in self.conversation_manager.context.items()
        }
        return {
            "context": safe_ctx,
            "recent_history": self.prompt_engine.get_recent_history(),
            "current_topic": (
                self.conversation_manager.current_topic.value if self.conversation_manager.current_topic else None
            ),
            "consecutive_errors": self.consecutive_errors
        }