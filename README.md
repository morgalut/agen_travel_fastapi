# 🧳 Travel Assistant LLM Agent

An intelligent travel planning assistant powered by LLaMA that helps you create personalized trip itineraries, packing lists, and travel recommendations. Simply ask your travel questions and let the AI guide you through your journey planning!

## ✨ Features

- **Smart Trip Planning**: Get personalized itineraries based on your preferences
- **Packing Assistance**: Receive tailored packing lists for any destination and season
- **Local Recommendations**: Discover attractions, restaurants, and hidden gems
- **Conversational Memory**: Maintains context across multiple questions for natural conversations
- **RESTful API**: Easy integration with web applications or mobile apps

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker (optional)
- Ollama

```markdown
### 1. Install Ollama & DeepSeek Model

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama server
ollama serve

# Download and run DeepSeek (choose your variant, e.g., deepseek:7b)
ollama pull deepseek:7b
ollama run deepseek:7b
```
### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

#### Option A: Direct Python
```bash
uvicorn main:app --reload --port 8000
```

### Step 1 – Install and Run Frontend
```bash
cd Frontend
npm install
npm run dev
```

#### Option B: Docker (Recommended)
```bash
sudo docker compose up -d --build
```

The API will be available at `http://localhost:8000`

## 🧪 Testing & Usage

### Basic Usage Examples

#### Ask about packing for a trip:
```bash
curl -s -X POST "http://127.0.0.1:8000/assistant/ask" \
  -H "Content-Type: application/json" \
  -d '{"text": "What should I pack for a 5-day trip to Paris in winter?"}' | jq
```

#### Follow-up questions (maintains context):
```bash
curl -s -X POST "http://127.0.0.1:8000/assistant/ask" \
  -H "Content-Type: application/json" \
  -d '{"text": "What should I wear if I also go to a fancy dinner?"}' | jq
```

#### Ask about attractions:
```bash
curl -s -X POST "http://127.0.0.1:8000/assistant/ask" \
  -H "Content-Type: application/json" \
  -d '{"text": "What attractions should I see while in Paris?"}' | jq
```

#### Check conversation memory:
```bash
curl -s "http://127.0.0.1:8000/assistant/summary" | jq
```

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/assistant/ask` | Send a travel-related question |
| `GET` | `/assistant/summary` | Get conversation history summary |

### Request Format

```json
{
  "text": "Your travel question here"
}
```

## 🏗️ Project Structure

```
travel_assistant/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies  
│   ├── docker-compose.yml   # Docker configuration
│   └── README.md           # This file
└── ...
```

## 🔧 Configuration

The application uses the following default settings:
- **Model**: LLaMA 3.2 1B
- **Port**: 8000
- **Host**: 127.0.0.1

You can modify these settings in the `main.py` file or through environment variables.

## 💡 Example Conversations

**Planning a weekend getaway:**
- "I want to plan a romantic weekend in Rome for two people"
- "What's the best time to visit the Colosseum?"
- "Recommend some authentic Italian restaurants nearby"

**Business travel assistance:**
- "I'm traveling to Tokyo for a business meeting, what should I pack?"
- "How should I dress for meetings in Japanese corporate culture?"
- "What are some good networking spots in Shibuya?"

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

**Common Issues:**

- **Ollama not starting**: Make sure port 11434 is available
- **Model download fails**: Check your internet connection and disk space
- **API connection errors**: Verify the server is running on the correct port

**Need Help?** Open an issue on GitHub or check our documentation.

---

