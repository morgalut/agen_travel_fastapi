# How run 
```sh
curl -fsSL https://ollama.com/install.sh | sh

ollama serve

ollama pull phi3:mini
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
uvicorn travel_assistant.main:app --reload --port 8000
```

Test packing with real weather (triggers geocode → Open-Meteo):

```bash
curl -s -X POST "http://127.0.0.1:8000/assistant/ask" \
  -H "Content-Type: application/json" \
  -d '{"text": "What should I pack for a 5-day trip to Paris in winter?"}' | jq
```

Test destination recs (concise bullets):

```bash
curl -s -X POST "http://127.0.0.1:8000/assistant/ask" \
  -H "Content-Type: application/json" \
  -d '{"text": "I have $2000 and love food & museums. Where should I go in Europe?"}' | jq
```

Check summary:

```bash
curl -s "http://127.0.0.1:8000/assistant/summary" | jq
```

---

