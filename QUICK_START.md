# 🚀 AI ASSISTANT - QUICK REFERENCE CARD

## ✅ PROJECT STATUS
- ✅ All 3 phases complete (A, B, C)
- ✅ 9/9 unit tests passing
- ✅ Ready for integration testing
- ⚠️ Requires external services: Ollama, Piper

---

## 📋 TESTING CHECKLIST

### Step 0: Unit Tests (No External Dependencies)
```powershell
cd d:\ASHWINI\project\voice\ai-assistant
D:\program\conda\envs\ryzen-ai1.6\python.exe -m pytest -v
```
**Expected:** 9/9 PASS ✅ (17 seconds)

---

### Step 1: Install External Services

| Service | Download | Command | Port | Status |
|---------|----------|---------|------|--------|
| **Ollama** | ollama.ai | `ollama serve` | 11434 | ⚠️ Manual |
| **Piper** | repo.github.com/rhasspy/piper | `piper --server` | 59125 | ⚠️ Manual |

### How to Start:

**Terminal 1 - Ollama:**
```bash
ollama serve
# Wait for: "Listening on 127.0.0.1:11434"
```

**Terminal 2 - Piper:**
```bash
piper --server
# Wait for: "Listening on HTTP server on port 59125"
```

---

### Step 2: Start Microservices Stack

**Terminal 3:**
```powershell
cd d:\ASHWINI\project\voice\ai-assistant
.\start_stack.ps1
```

Or manually:
```powershell
# Service 1: Whisper (GPU)
D:\program\conda\envs\ryzen-ai1.6\python.exe -m uvicorn services.whisper_service:app --port 8001

# Service 2: LLM (Ollama)
D:\program\conda\envs\ryzen-ai1.6\python.exe -m uvicorn services.llm_service:app --port 8002

# Service 3: TTS (Piper)
D:\program\conda\envs\ryzen-ai1.6\python.exe -m uvicorn services.tts_service:app --port 8003

# Service 4: Intent (ONNX)
D:\program\conda\envs\ryzen-ai1.6\python.exe -m uvicorn services.intent_service:app --port 8004
```

**Wait for all to start (~10 sec). Look for:**
```
INFO: Uvicorn running on http://0.0.0.0:800X
INFO: Loaded Whisper model...
INFO: Warmed up Ollama model...
INFO: Loaded intent model...
```

---

### Step 3: Test Individual Services

#### 3.1 - Intent Service (NPU)
```powershell
curl -X POST http://127.0.0.1:8004/classify `
  -H "Content-Type: application/json" `
  -d '{"text": "Turn on the lights"}'
```
**Expected:** `{"label": "label_1", "scores": {...}, ...}`

#### 3.2 - LLM Service (GPU)
```powershell
curl -X POST http://127.0.0.1:8002/generate `
  -H "Content-Type: application/json" `
  -d '{"prompt": "Hello, how are you?"}'
```
**Expected:** `{"model": "qwen2.5-coder:7b", "response": "..."}`

#### 3.3 - TTS Service (CPU)
```powershell
curl -X POST http://127.0.0.1:8003/speak `
  -H "Content-Type: application/json" `
  -d '{"text": "Hello world"}'
```
**Expected:** `{"accepted": true, "backend_status": 200}`

#### 3.4 - Whisper Service (GPU)
```powershell
# Need audio file first
curl -X POST http://127.0.0.1:8001/transcribe `
  -F "audio_file=@test.wav"
```
**Expected:** `{"text": "...", "language": "en", ...}`

---

### Step 4: Run Full Pipeline (Synchronous)

```powershell
# Terminal 4:
cd d:\ASHWINI\project\voice\ai-assistant
D:\program\conda\envs\ryzen-ai1.6\python.exe orchestrator/main.py --text "What is AI?"
```

**Expected Output:**
```json
{
  "intent": "chat",
  "assistant_text": "Artificial intelligence is...",
  "tts_status": 200,
  "timings_ms": {
    "intent_ms": 42.5,
    "llm_ms": 1240.0,
    "tts_ms": 150.0,
    "memory_ms": 25.0,
    "embedding_ms": 20.0
  },
  "emotional_context": "User sentiment: neutral.",
  "memories_used": "Memory 1: User: What is AI..."
}
```

**Total time: 1.5-2.5 seconds** ⏱️

---

### Step 5: Run Full Pipeline (Streaming)

```powershell
D:\program\conda\envs\ryzen-ai1.6\python.exe orchestrator/main.py --text "Tell me a story" --stream
```

**What changes:**
- LLM tokens stream in real-time
- TTS buffers chunks progressively
- First-token latency reported separately
- Better perceived responsiveness ⚡

---

### Step 6: Check Device Info (Optional)

```powershell
D:\program\conda\envs\ryzen-ai1.6\python.exe -c "from core.device_manager import get_device_report; print(get_device_report())"
```

**Expected:**
```json
{
  "cpu": {"cores": 8},
  "cuda": {"available": true, "total_memory_mb": 6144},
  "npu": {"available": true, "preferred": "DmlExecutionProvider"}
}
```

---

### Step 7: Monitor Resources (Optional)

```powershell
D:\program\conda\envs\ryzen-ai1.6\python.exe monitoring/resource_monitor.py
```

**Outputs every 5 seconds:**
```
timestamp,name,utilization.gpu,memory.used,memory.total
2026-02-28 14:32:15,NVIDIA RTX 4050,65,4200,6144
CPU: 28.3% | RAM used: 8192 MB / 16384 MB
```

---

## 🐛 TROUBLESHOOTING

| Error | Cause | Fix |
|-------|-------|-----|
| `502 Bad Gateway` | Service not running | Check service terminal, restart |
| `Connection refused 127.0.0.1:11434` | Ollama not running | Start `ollama serve` in terminal |
| `Connection refused 127.0.0.1:59125` | Piper not running | Start `piper --server` in terminal |
| `CUDA out of memory` | GPU full | Close other GPU apps, restart services |
| `ModuleNotFoundError: sentence_transformers` | Deps missing | `pip install -r requirements.txt` |
| `No module named 'tests'` | Wrong directory | `cd ai-assistant` first |
| `Port 8001 already in use` | Service already running | Kill process or use different port |

---

## 📊 EXPECTED LATENCIES (RTX 4050)

| Stage | Time | Device |
|-------|------|--------|
| Intent | 20-50ms | NPU/CPU |
| Memory Retrieval | 20-40ms | CPU |
| LLM Generate | 800-2000ms | GPU ⚠️ |
| TTS Stream | 100-300ms | CPU |
| Embedding | 15-30ms | CPU |
| **TOTAL** | **1.2-2.5s** | Mixed |

💡 **LLM is the bottleneck** (7B model on 6GB VRAM) — this is expected!

---

## 🎯 SUCCESS CRITERIA

Check all before declaring "working":

- [ ] `pytest -v` → 9/9 pass
- [ ] `ollama serve` → listening on 11434
- [ ] `piper --server` → listening on 59125
- [ ] All 4 services start without errors
- [ ] `curl .../classify` → returns intent
- [ ] `curl .../generate` → returns text
- [ ] `curl .../speak` → returns status 200
- [ ] `main.py --text "hello"` → returns full JSON
- [ ] Response JSON includes: `intent`, `assistant_text`, `timings_ms`
- [ ] Latency under 3 seconds per turn

---

## 📁 KEY FILES

| File | Purpose |
|------|---------|
| `requirements.txt` | All dependencies (pinned versions) |
| `start_stack.ps1` | Windows launcher for all services |
| `core/config.py` | Configuration (ports, API URLs, model paths) |
| `orchestrator/main.py` | CLI entry point (text or streaming) |
| `orchestrator/pipeline.py` | Main async orchestration logic |
| `TESTING.md` | Detailed testing guide |
| `README.md` | Project overview |

---

## 💻 COMMANDS REFERENCE

```powershell
# Unit tests (no external deps)
pytest -v

# Device detection
python -c "from core.device_manager import get_device_report; print(get_device_report())"

# Start all services
.\start_stack.ps1

# Text input (sync)
python orchestrator/main.py --text "Hello"

# Text input (streaming)
python orchestrator/main.py --text "Hello" --stream

# Monitor resources
python monitoring/resource_monitor.py

# Check specific service
curl -X GET http://127.0.0.1:8001/docs  # Swagger docs
curl -X GET http://127.0.0.1:8002/docs  # etc
```

---

## 🔗 PORTS AT A GLANCE

```
8001  ← Whisper (speech to text)
8002  ← LLM (text generation)
8003  ← TTS (text to speech)
8004  ← Intent (classification)
11434 ← Ollama (external)
59125 ← Piper (external)
```

---

## 📞 EXTERNAL SERVICE SETUPS

### Ollama
1. Download from https://ollama.ai
2. Install Windows version
3. Run: `ollama serve`
4. Wait 10 sec, check localhost:11434

### Piper TTS
1. Download release from https://github.com/rhasspy/piper/releases
2. Extract to any folder
3. Run: `piper --server`
4. Wait 5 sec, check localhost:59125
5. (Optional) Download `en_IN-priya-medium.onnx` for Indian accent

---

## 🎓 NEXT: AFTER SUCCESSFUL TEST

Once all tests pass:

1. **Extend system prompt** → Edit `prompts/system_prompt.txt`
2. **Add custom intents** → Modify `orchestrator/pipeline.py`
3. **Swap TTS model** → Change config or Piper model
4. **Optimize for smaller GPU** → Use quantized LLM via Ollama
5. **Deploy as service** → See Phase D docs

---

**Status: READY FOR HUMAN TESTING** ✅🚀

Follow steps 0-7 above. Should take **~30-40 minutes** total.

Good luck! 🎉
