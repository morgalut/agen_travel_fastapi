from fastapi import APIRouter, HTTPException
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
async def ask_travel_assistant(request: QueryRequest) -> QueryResponse:
    """
    Main endpoint to ask the travel assistant a question.
    Returns:
    - answer: main response (formatted)
    - followup: optional follow-up question to guide the user
    - context: current conversation state
    """
    try:
        raw_result = await assistant.generate_response(request.text)

        formatted_answer = format_response(raw_result.get("answer", ""))

        return QueryResponse(
            answer=formatted_answer,
            followup=raw_result.get("followup"),
            context=raw_result.get("context", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant error: {str(e)}")




@router.post("/reset")
async def reset_conversation() -> Dict[str, Any]:
    """
    Reset the assistant's conversation state.
    Clears context and history so a new conversation can start.
    """
    try:
        assistant.conversation_manager.reset()
        return {"ok": True, "message": "Conversation reset successfully."}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Reset error: {str(e)}")

