# travel_assistant/__init__.py
"""Travel Assistant Package"""

__version__ = "1.0.0"
__author__ = "Travel Assistant Team"

from .core.assistant import TravelAssistant
from .core.conversation import ConversationManager, QueryType
from .core.prompt_engine import PromptEngine

__all__ = ['TravelAssistant', 'ConversationManager', 'QueryType', 'PromptEngine']