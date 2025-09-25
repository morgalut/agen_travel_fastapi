from fastapi import APIRouter
from pydantic import BaseModel
from travel_assistant.core.assistant import TravelAssistant
from travel_assistant.utils.helpers import format_response

# Router instance
router = APIRouter()

# Shared assistant instance
assistant = TravelAssistant()

# Request/Response models
class QueryRequest(BaseModel):
    text: str

class QueryResponse(BaseModel):
    response: str
    context: dict

@router.post("/ask", response_model=QueryResponse)
def ask_travel_assistant(request: QueryRequest):
    """Endpoint to ask the travel assistant a question"""
    raw_response = assistant.generate_response(request.text)
    formatted = format_response(raw_response)
    return QueryResponse(
        response=formatted,
        context={"summary": assistant.get_conversation_summary()}
    )


@router.get("/summary")
def get_summary():
    return {"summary": assistant.get_conversation_summary()}
