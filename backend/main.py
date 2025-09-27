#!/usr/bin/env python3
"""
Main entrypoint for the Travel Assistant.
Supports:
- FastAPI server (cloud/local)
- CLI (local)
"""

import os
import sys
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from travel_assistant.router import routes_assistant
from travel_assistant.utils.helpers import format_response

# ------------------ Logging Setup ------------------
def _is_writable(path: str) -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        test_file = os.path.join(path, ".write_test")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        return True
    except Exception:
        return False

# Prefer env, then /app/logs, fall back to /tmp/app-logs, else stdout only
DEFAULT_LOG_DIRS = [
    os.getenv("LOG_DIR") or "",                    # explicit env
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"),  # ./backend/logs (local dev)
    "/app/logs",                                   # container path (if writable)
    "/var/log/app",                                # if running as root and writable
    "/tmp/app-logs"                                # always writable in containers
]

log_dir = None
for cand in DEFAULT_LOG_DIRS:
    if not cand:
        continue
    if _is_writable(cand):
        log_dir = cand
        break

handlers = [logging.StreamHandler(sys.stdout)]
if log_dir:
    try:
        handlers.append(logging.FileHandler(os.path.join(log_dir, "app.log")))
    except Exception:
        # If file handler fails, we’ll just stream logs.
        pass

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=handlers,
)
logger = logging.getLogger("travel_assistant.main")
if log_dir:
    logger.info(f" Logging to {log_dir}/app.log")
else:
    logger.info(" File logging disabled (stdout only).")

# ------------------ FASTAPI APP ------------------
app = FastAPI(title="Travel Assistant API")

origins = [
    os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"),
    "http://127.0.0.1:3000",
    os.getenv("ALLOW_ORIGIN_WILDCARD", "*"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in origins if o],  # filter Nones
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_assistant.router, prefix="/assistant", tags=["assistant"])
logger.info(" FastAPI app initialized. Router /assistant mounted.")

# ------------------ Global Exception Handler ------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error(" Unhandled error during request", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "traceback": tb.splitlines()[-5:],
            "path": str(request.url),
        },
    )

# ------------------ CLI MODE (optional local) ------------------
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = """
     TRAVEL ASSISTANT 
    Your AI-powered travel planning companion
    """
    print(banner)

def run_cli():
    from travel_assistant.core.assistant import TravelAssistant
    assistant = TravelAssistant()

    clear_screen()
    print_banner()
    print(" Assistant: Hello! How can I help you with your travel plans today?")

    while True:
        try:
            user_input = input("\n🧳 You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "bye"):
                print("\n Safe travels!")
                break
            print("\n Thinking...")
            # If your assistant.generate_response is async, you can adapt with asyncio.run here.
            resp = asyncio.run(assistant.generate_response(user_input))  # if generate_response is async
            print(f"\n Assistant: {format_response(resp)}")
        except KeyboardInterrupt:
            print("\n\n Safe travels!")
            break
        except Exception as e:
            logger.exception("CLI error")
            print(f" Error: {e}")

if __name__ == "__main__":
    # Local CLI
    try:
        import asyncio
        run_cli()
    except Exception as e:
        logger.exception("Failed to start CLI")
