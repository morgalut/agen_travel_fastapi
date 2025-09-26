from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

from travel_assistant.core.assistant import TravelAssistant
from travel_assistant.utils.helpers import format_response

# ------------------ Router ------------------
router = APIRouter()
assistant = TravelAssistant()

# ------------------ Schemas ------------------
class QueryRequest(BaseModel):
    text: str

class QueryResponse(BaseModel):
    answer: str
    followup: Optional[str] = None
    context: Dict[str, Any]

# ------------------ Endpoints ------------------
@router.post("/ask", response_model=QueryResponse)
def ask_travel_assistant(request: QueryRequest):
    """
    Main endpoint to ask the travel assistant a question.
    Returns:
    - answer: main response (formatted)
    - followup: optional follow-up question to guide the user
    - context: current conversation state
    """
    raw_result = assistant.generate_response(request.text)

    # Format only the "answer" part (packing list, destination recs, etc.)
    formatted_answer = format_response(raw_result.get("answer", ""))

    return QueryResponse(
        answer=formatted_answer,
        followup=raw_result.get("followup"),
        context=raw_result.get("context", {})
    )


@router.get("/summary")
def get_summary():
    """
    Get the current conversation summary and context.
    Useful for debugging or for UI components to show history.
    """
    return {"summary": assistant.get_conversation_summary()}
