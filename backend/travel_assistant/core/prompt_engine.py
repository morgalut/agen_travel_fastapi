# travel_assistant/core/prompt_engine.py
import json
import logging
from typing import Dict, Any
from dataclasses import dataclass

# Setup logger
logger = logging.getLogger(__name__)

@dataclass
class PromptTemplate:
    """Template for different types of prompts"""
    system_prompt: str
    user_prompt: str
    chain_of_thought: bool = False


class PromptEngine:
    """Engine for managing and optimizing prompts"""
    
    def __init__(self):
        logger.info("🛠️ Initializing PromptEngine...")
        print("[prompt_engine] 🛠️ Initializing PromptEngine...")
        self.templates = self._initialize_templates()
        self.conversation_history = []
        logger.info("✅ PromptEngine ready with templates loaded")
        print("[prompt_engine] ✅ Templates loaded successfully")

    def _initialize_templates(self) -> Dict[str, PromptTemplate]:
        """Initialize prompt templates for different query types"""
        logger.debug("Loading default prompt templates...")
        print("[prompt_engine] 📦 Loading default prompt templates...")

        return {
            "destination_recommendation": PromptTemplate(
                system_prompt=(
                    "You are a helpful, concise travel expert.\n"
                    "GOALS:\n"
                    "- Recommend destinations tailored to user budget, interests, constraints.\n"
                    "- If hotel/transport info is available, weave it naturally into suggestions.\n"
                    "- Ask at most one clarifying question when needed.\n"
                    "STYLE:\n"
                    "- Use concrete bullet points.\n"
                    "- Keep under ~180 words unless explicitly asked.\n"
                ),
                user_prompt=(
                    "Context:\n{history}\n\n"
                    "User query: {query}\n\n"
                    "External data (JSON): {external_data}\n\n"
                    "Answer concisely with 3–5 recommendations max, each with a one-line why.\n"
                    "If hotels are provided, mention 1–2 nearby options.\n"
                    "If transport info is provided, add how to get around briefly.\n"
                ),
                chain_of_thought=False
            ),
            "packing_suggestions": PromptTemplate(
                system_prompt=(
                    "You are a meticulous packing assistant. Think step-by-step internally, "
                    "but only output the final packing list and short justifications.\n"
                    "STYLE: bullet lists grouped by category, concise, quantities when useful.\n"
                    "If hotel info is available, suggest if any dress code applies.\n"
                    "If transport info is available, suggest items like metro cards or walking shoes.\n"
                ),
                user_prompt=(
                    "Think through silently:\n"
                    "1) Climate & season: {climate_info}\n"
                    "2) Trip duration: {duration}\n"
                    "3) Activities: {activities}\n"
                    "4) Hotels nearby: (from external data if available)\n"
                    "5) Transport context: (from external data if available)\n\n"
                    "Now output ONLY the final packing list for: {query}\n"
                    "Context: {history}\n"
                    "Start with a short rationale, then categories (Clothing, Toiletries, Electronics, Documents, Extras).\n"
                ),
                chain_of_thought=True
            ),
            "local_attractions": PromptTemplate(
                system_prompt=(
                    "You are a local travel guide. Recommend both classics and hidden gems.\n"
                    "STYLE: concise bullets, practical tips (hours, costs when known), logical mini-itinerary.\n"
                    "If hotels are available, suggest 1–2 nearby as base options.\n"
                    "If transport info is available, include how to reach some attractions.\n"
                ),
                user_prompt=(
                    "Destination: {query}\n"
                    "Context: {history}\n"
                    "External info (JSON): {external_data}\n\n"
                    "Give 6–8 attractions max, grouped by neighborhood/area if sensible.\n"
                    "If transport info is present, explain briefly how to move around.\n"
                    "If hotel info is present, suggest where the user could stay nearby.\n"
                    "Add a 1-day sample path.\n"
                ),
                chain_of_thought=False
            )
        }
    
    def build_prompt(self, query_type: str, **kwargs) -> Dict[str, str]:
        """Build a complete prompt for the LLM"""
        logger.info(f"📝 Building prompt for query_type={query_type}")
        print(f"[prompt_engine] 📝 Building prompt for query_type={query_type}")

        template = self.templates.get(query_type)
        if not template:
            logger.warning(f"⚠️ Unknown query_type={query_type}, defaulting to destination_recommendation")
            print(f"[prompt_engine] ⚠️ Unknown type={query_type}, using default")
            template = self.templates["destination_recommendation"]
        
        # Format the user prompt
        formatted_user_prompt = template.user_prompt.format(**kwargs)
        logger.debug(f"User prompt length: {len(formatted_user_prompt)}")
        print(f"[prompt_engine] ✅ Prompt built, length={len(formatted_user_prompt)}")

        return {
            "system": template.system_prompt,
            "user": formatted_user_prompt,
            "chain_of_thought": template.chain_of_thought
        }
    
    def add_to_history(self, role: str, content: str):
        logger.info(f"💬 Adding to history: role={role}")
        print(f"[prompt_engine] 💬 History updated: {role} says {content[:50]}...")
        self.conversation_history.append({"role": role, "content": content})
        
        if len(self.conversation_history) > 10:
            logger.debug("Trimming conversation history to last 10 messages")
            print("[prompt_engine] ✂️ Trimming history to last 10 messages")
            self.conversation_history = self.conversation_history[-10:]
    
    def get_recent_history(self, max_messages: int = 5) -> str:
        logger.debug(f"Fetching last {max_messages} messages from history")
        print(f"[prompt_engine] 📜 Returning last {max_messages} history entries")
        recent = self.conversation_history[-max_messages:] if self.conversation_history else []
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent])
