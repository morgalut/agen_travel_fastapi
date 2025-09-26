from fastapi import APIRouter

from travel_assistant.core.assistant import TravelAssistant

# ------------------ Router ------------------
router = APIRouter()
assistant = TravelAssistant()


@router.post("/reset")
def reset_conversation():
    assistant.prompt_engine.conversation_history.clear()
    assistant.conversation_manager.context.clear()
    return {"status": "conversation reset"}
