#!/usr/bin/env python3
"""
Main entrypoint for the Travel Assistant.
Supports both:
- CLI interactive mode
- FastAPI server mode (via uvicorn)
"""

import os
from fastapi import FastAPI
from travel_assistant.router import routes_assistant
from travel_assistant.core.assistant import TravelAssistant
from travel_assistant.utils.helpers import format_response

# ------------------ FASTAPI APP ------------------
app = FastAPI(title="Travel Assistant API")

# Include routers
app.include_router(routes_assistant.router, prefix="/assistant", tags=["assistant"])

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

    while True:
        try:
            user_input = input("\n🧳 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n🔮 Assistant: Safe travels! Come back if you need more travel advice. 👋")
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
            print("\n🤖 Thinking...", end="")
            response = assistant.generate_response(user_input)
            print("\r" + " " * 50 + "\r")  # Clear thinking message

            formatted_response = format_response(response)
            print(f"🔮 Assistant: {formatted_response}")

        except KeyboardInterrupt:
            print("\n\n🔮 Assistant: Safe travels! Come back anytime. 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("🔮 Assistant: I apologize for the technical issue. Please try again.")


# ------------------ MAIN ------------------
if __name__ == "__main__":
    run_cli()
