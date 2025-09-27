# travel_assistant/core/assistant_response.py
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass
class AssistantResponse:
    answer: str
    followup: Optional[str]
    context: Dict[str, Any]
    confidence: float = 0.8
    sources: List[str] = None
