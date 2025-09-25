# travel_assistant/core/prompt_engine.py
import json
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class PromptTemplate:
    """Template for different types of prompts"""
    system_prompt: str
    user_prompt: str
    chain_of_thought: bool = False

class PromptEngine:
    """Engine for managing and optimizing prompts"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
        self.conversation_history = []
    
    def _initialize_templates(self) -> Dict[str, PromptTemplate]:
        """Initialize prompt templates for different query types"""
        return {
            "destination_recommendation": PromptTemplate(
                system_prompt=(
                    "You are a helpful, concise travel expert.\n"
                    "GOALS:\n"
                    "- Recommend destinations tailored to user budget, interests, constraints.\n"
                    "- Ask at most one clarifying question when needed.\n"
                    "STYLE:\n"
                    "- Be concrete and actionable.\n"
                    "- Prefer bullet points.\n"
                    "- Keep responses under ~180 words unless asked for more.\n"
                ),
                user_prompt=(
                    "Context:\n{history}\n\n"
                    "User query: {query}\n\n"
                    "External data (JSON): {external_data}\n\n"
                    "Answer concisely with 3–5 options max, each with a one-line why.\n"
                    "If data is insufficient, ask one focused clarifying question."
                ),
                chain_of_thought=False
            ),
            "packing_suggestions": PromptTemplate(
                system_prompt=(
                    "You are a meticulous packing assistant. Think step-by-step internally, "
                    "but only output the final packing list and short justifications.\n"
                    "STYLE: bullet lists, grouped by category, concise, quantities when useful."
                ),
                user_prompt=(
                    "Think through these steps silently:\n"
                    "1) Climate & season: {climate_info}\n"
                    "2) Trip duration: {duration}\n"
                    "3) Activities: {activities}\n"
                    "4) Special needs: {special_needs}\n\n"
                    "Now output ONLY the final packing list for: {query}\n"
                    "Context: {history}\n"
                    "Start with a 1–2 sentence rationale, then categories (Clothing, Toiletries, Electronics, Documents, Extras)."
                ),
                chain_of_thought=True
            ),
            "local_attractions": PromptTemplate(
                system_prompt=(
                    "You are a local travel guide. Recommend both classics and a few hidden gems.\n"
                    "STYLE: concise bullets, practical tips (hours, costs when known), and a logical mini-itinerary."
                ),
                user_prompt=(
                    "Destination: {query}\n"
                    "Context: {history}\n"
                    "External info (JSON): {external_data}\n\n"
                    "Give 6–8 attractions max, grouped by neighborhood/area if sensible. Add a 1-day sample path."
                ),
                chain_of_thought=False
            )
        }
    
    def build_prompt(self, query_type: str, **kwargs) -> Dict[str, str]:
        """Build a complete prompt for the LLM"""
        template = self.templates.get(query_type)
        if not template:
            template = self.templates["destination_recommendation"]
        
        # Format the user prompt with provided kwargs
        formatted_user_prompt = template.user_prompt.format(**kwargs)
        
        return {
            "system": template.system_prompt,
            "user": formatted_user_prompt,
            "chain_of_thought": template.chain_of_thought
        }
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({"role": role, "content": content})
        
        # Keep only last 10 messages to manage context length
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def get_recent_history(self, max_messages: int = 5) -> str:
        """Get recent conversation history as formatted string"""
        recent = self.conversation_history[-max_messages:] if self.conversation_history else []
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent])