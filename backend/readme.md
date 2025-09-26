# How run 
```sh
curl -fsSL https://ollama.com/install.sh | sh

ollama serve

ollama pull llama3.2:1b
ollama run phi3:mini 
```
----
# Install 
```sh 
pip install -r requirements.txt
```
---

# How run 
```sh
uvicorn main:app --reload --port 8000
```

---



## 🧪 How to run & test

Run the API:

```bash
# 1. First question
curl -s -X POST "http://127.0.0.1:8000/assistant/ask" \
  -H "Content-Type: application/json" \
  -d '{"text": "What should I pack for a 5-day trip to Paris in winter?"}' | jq

# 2. Continue without repeating context
curl -s -X POST "http://127.0.0.1:8000/assistant/ask" \
  -H "Content-Type: application/json" \
  -d '{"text": "What should I wear if I also go to a fancy dinner?"}' | jq

# 3. Ask another topic
curl -s -X POST "http://127.0.0.1:8000/assistant/ask" \
  -H "Content-Type: application/json" \
  -d '{"text": "What attractions should I see while in Paris?"}' | jq

# 4. Inspect memory
curl -s "http://127.0.0.1:8000/assistant/summary" | jq

```

---
לבדוק משכיות ולבדוקת איפוס 
לשפר דיבור ושיחה 

