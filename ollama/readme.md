
# Here are the install commands for different systems:

---

### 🐧 **Linux (Ubuntu/Debian)**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

This will download and install Ollama, plus set up the system service.

---

### 🍎 **macOS**

```bash
brew install ollama/tap/ollama
```

After install, you can start the service with:

```bash
ollama serve
```

---

### 🖥️ **Windows (preview build)**

1. Go to 👉 [Ollama Downloads](https://ollama.com/download)
2. Download the Windows installer `.exe` and run it.
3. It will install and run Ollama as a background service.

---

### ✅ Verify Installation

Run:

```bash
ollama --version
```

---

### 🚀 Run a Model

For example, to run **llama2** locally:

```bash
ollama run llama2
```

That will start pulling the model the first time (can take a while).
Then you can chat with it directly in the terminal, or via API at `http://localhost:11434`.

---

