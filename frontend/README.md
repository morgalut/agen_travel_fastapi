# 🎓 Travel Assistant Frontend – Lecture Notes

This document is a **short lecture guide** for introducing the Travel Assistant Frontend in class or demo sessions.

---

## 1. Introduction

- **What it is**:  
  A modern web frontend built with **Next.js**, **TypeScript**, and **Tailwind CSS**.  
  It serves as the **user-facing interface** for the Travel Assistant backend (FastAPI + Ollama).

- **Why it matters**:  
  Demonstrates how to connect a conversational AI backend to a clean, responsive UI.  
  Focus: *developer experience, fast prototyping, and user interaction design*.

---

## 2. Architecture Overview

- **Frontend (Next.js)**  
  - Renders the chat UI and handles user interaction.
  - Talks to the backend over REST (`/assistant/ask` endpoint).
  - Can run in **mock mode** (no backend required) for demos.

- **Backend (FastAPI)**  
  - Processes requests and connects to the **Ollama LLM** service.
  - Handles state, context, and external APIs (weather, country info, etc.).

- **Ollama (LLM Runtime)**  
  - Provides the actual large language model (LLaMA, Mistral, etc.).
  - Runs inside Docker and communicates via HTTP (`:11434`).

---

## 3. Demo Workflow (5 Minutes)

### Step 1 – Install and Run Frontend
```bash
cd Frontend
npm install
npm run dev
