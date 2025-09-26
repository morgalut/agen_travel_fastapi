#!/usr/bin/env python3
"""
Main entrypoint for the Travel Assistant.
Supports both:
- CLI interactive mode
- FastAPI server mode (via uvicorn)
"""

import os
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware   # ✅ CORS middleware
from travel_assistant.router import routes_assistant
from travel_assistant.utils.helpers import format_response

# ------------------ Logging Setup ------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")  # ./backend/logs
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),  # stdout (docker logs)
        logging.FileHandler(os.path.join(LOG_DIR, "app.log"))  # persistent file
    ]
)
logger = logging.getLogger("travel_assistant.main")

# ------------------ FASTAPI APP ------------------
app = FastAPI(title="Travel Assistant API")

# ✅ Enable CORS
origins = [
    "http://localhost:3000",  # e.g. Next.js frontend
    "http://127.0.0.1:3000",
    "*"  # allow all origins (you can restrict this later)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],            # allow all HTTP methods
    allow_headers=["*"],            # allow all headers
)

# ✅ Register routers
app.include_router(routes_assistant.router, prefix="/assistant", tags=["assistant"])
logger.info("🚀 FastAPI app initialized. Router /assistant mounted.")

# ✅ Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error("❌ Unhandled error during request", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "traceback": tb.splitlines()[-5:],  # last 5 lines for debug
            "path": str(request.url)
        }
    )

# ------------------ CLI MODE ------------------
def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Print application banner"""
    banner = """
    🧭 TRAVEL ASSISTANT 🧭
    Your AI-powered travel planning companion
    
    I can help you with:
    • Destination recommendations
    • Packing suggestions  
    • Local attractions and activities
    • General travel advice
    
    Type 'quit' to exit, 'help' for commands, 'summary' for conversation summary
    """
    print(banner)

def print_help():
    """Print help information"""
    help_text = """
    Available Commands:
    • quit/exit/bye - Exit the application
    • help - Show this help message  
    • summary - Show conversation summary
    • clear - Clear the conversation
    
    Example Questions:
    • "Where should I go for a beach vacation with a $2000 budget?"
    • "What should I pack for a week in Japan in spring?"
    • "What are the best attractions in Paris?"
    • "I need adventure travel ideas for Southeast Asia"
    """
    print(help_text)

def run_cli():
    """Main application loop for CLI"""
    from travel_assistant.core.assistant import TravelAssistant
    assistant = TravelAssistant()

    clear_screen()
    print_banner()
    print("🔮 Assistant: Hello! I'm your travel assistant. How can I help you with your travel plans today?")
    print("-" * 80)

    logger.info("CLI started. Waiting for user input...")

    while True:
        try:
            user_input = input("\n🧳 You: ").strip()
            logger.info(f"Received user input: {user_input}")

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n🔮 Assistant: Safe travels! Come back if you need more travel advice. 👋")
                logger.info("User exited CLI session.")
                break

            elif user_input.lower() == 'help':
                print_help()
                continue

            elif user_input.lower() == 'summary':
                summary = assistant.get_conversation_summary()
                print(f"\n📊 Conversation Summary:\n{summary}")
                continue

            elif user_input.lower() == 'clear':
                clear_screen()
                print_banner()
                print("🔮 Assistant: Conversation cleared! How can I help you now?")
                continue

            # Generate and display response
            print("\n🤖 Thinking...")
            response = assistant.generate_response(user_input)

            formatted_response = format_response(response)
            print(f"🔮 Assistant: {formatted_response}")
            logger.info("Response delivered to user.")

        except KeyboardInterrupt:
            print("\n\n🔮 Assistant: Safe travels! Come back anytime. 👋")
            logger.warning("CLI interrupted with Ctrl+C.")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"\n❌ Error: {e}")
            print("🔮 Assistant: I apologize for the technical issue. Please try again.")

# ------------------ MAIN ------------------
if __name__ == "__main__":
    logger.info("Starting Travel Assistant in CLI mode...")
    run_cli()
