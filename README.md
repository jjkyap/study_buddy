# 🧠 LLM Study Buddy  
*A lightweight AI-powered note summarizer and flashcard generator with OCR, RAG, and offline evaluation.*

---

## 🎥 Demo Video

[![Watch the video](https://img.youtube.com/vi/Nyptvndcw5s/maxresdefault.jpg)](https://youtu.be/Nyptvndcw5s)

### [Watch this video on YouTube](https://youtu.be/Nyptvndcw5s)

---

## Overview

LLM Study Buddy is a local-first study assistant that:

- Accepts **typed notes** or **uploaded PDFs**
- Extracts text using a **hybrid OCR pipeline**:
  - pdfplumber → Tesseract → EasyOCR
- Uses **RAG (Retrieval-Augmented Generation)** to improve summaries
- Generates:
  - Bullet-point **summaries**
  - 🧠 Structured **flashcards** in JSON
- Stores results in a **local SQLite database**
- Includes:
  - A Flask-based **dashboard**
  - **History** view with delete options
  - Built-in **telemetry** (latency, token usage)
  - **Offline evaluation test suite**
---

## 🚀 Running the App

### 1. Install dependencies
```
pip install -r requirements.txt
```

### 2. Create your `.env`
```
cp .env.example .env
```

Fill in:
```
FLASK_SECRET_KEY=yourkey
DEMO_USERNAME=user
DEMO_PASSWORD=secret_password

OPENAI_API_KEY=or-xxxxxxxxxx
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_MODEL=amazon/nova-2-lite-v1:free
```

### 3. Launch the app
```
python main.py
```

Visit:

http://127.0.0.1:5000/

---

## Offline Evaluation

### Text Tests
```
python tests/run_tests.py
```

### PDF OCR Tests
```
python tests/run_pdf_tests.py
```

Results will display pass/fail patterns and save to `tests/pdf_test_results.json`.

---

## Core Features

### OCR Pipeline
Each PDF page is classified:
- **typed** → pdfplumber
- **scanned** → Tesseract
- **handwritten** → EasyOCR
- **mixed** → combine results

### LLM Processing
Uses **Amazon Nova 2 Lite** via OpenRouter.
- Summary generation
- Flashcards with JSON validation + fallback repair
- RAG context injection using MiniLM embeddings

### Guardrails
- Input length limits
- Sanitized output
- Strict JSON enforcement for flashcards

### Telemetry
Tracks:
- total latency
- tokens in/out (if model supports)
- cost (zero for free-tier Nova Lite)
- error messages

### ✔ History + Delete
Notes stored in SQLite.
Users can browse or delete entries in History.
---

## 🧩 Known Limitations
- EasyOCR may be slow on first load
- OCR accuracy dependent on scan quality
- No concurrency (single-user local mode)
- Not optimized for cloud deployment
- RAG dataset intentionally small
---

## 📄 Tech Note
See: `tech_note.md` for the required 1-page architecture write-up.

---

## 📚 License
MIT — Feel free to reuse parts for learning.



# 📄 **Tech Note **

## **1. Overview**

**LLM Study Buddy** is a lightweight AI assistant that processes handwritten or typed notes (PDF or text), summarizes them, and generates study flashcards. The system integrates:

- A **hybrid OCR pipeline**  
- **RAG (Retrieval-Augmented Generation)** for improved answers  
- **Amazon Nova 2 Lite** for LLM outputs (summaries + JSON flashcards)  
- **Safety guardrails** and **offline evaluation**  
- A small **Flask web UI** for interaction  
- Local **SQLite** for history storage

The design stays fully local and reproducible, without requiring cloud deployment.

---

## **2. Architecture Diagram (ASCII)**

```
                    ┌──────────────────────┐
                    │      Flask UI        │
                    │ dashboard • history  │
                    └───────────┬──────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │       Safety         │
                    │  input guardrails    │
                    └───────────┬──────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │     OCR Pipeline     │
                    │ pdfplumber / tesser. │
                    │ easyocr + classifier │
                    └───────────┬──────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │         RAG          │
                    │ MiniLM embeddings    │
                    │ top-k context        │
                    └───────────┬──────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │         LLM          │
                    │ Nova-2-Lite summary  │
                    │ + JSON flashcards    │
                    └───────────┬──────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │       Telemetry      │
                    │ latency • tokens     │
                    └──────────────────────┘
```

---

## **3. Guardrails (Safety Layer)**

Safety is handled in `safety.py` + input sanitation:

### **Prompt & Input Guardrails**
- Reject jailbreak patterns:
  - “ignore previous instructions”
  - “you are no longer ChatGPT”
  - malicious prompt injections
- Input length limited to prevent overflows
- System prompt enforces:
  - no harmful content  
  - no personal data fabrication  
  - strictly academic tone  
  - JSON-only output for flashcards

### **Model Output Guardrails**
- Flashcards JSON validated  
- Automatic fallback if:
  - malformed JSON  
  - incomplete keys  
  - blank output  

### **OCR Safety**
- All OCR failures degrade gracefully (never crash)  
- Always returns a `(text, method)` tuple  

---

## **4. Evaluation Method (Offline Testing)**

The assignment requires offline evaluation using expected patterns.  
We provide **two separate test suites**:

### **A. Text-Based Evaluation (`run_tests.py`)**
- Uses `tests.json`
- For each input:
  - Run LLM summary
  - Check for expected keywords
  - Calculate total pass rate

Example test:
```json
{
  "input": "Photosynthesis converts light into sugar.",
  "expect": ["photosynthesis", "light", "sugar"]
}
```

### **B. PDF-Based Evaluation (`run_pdf_tests.py`)**
Tests **OCR + LLM together**.

For each PDF:
1) Extract text (OCR hybrid)  
2) Generate summary  
3) Check for domain keywords  
4) Log:
   - OCR method used  
   - latency  
   - missing keywords  

Example expected pattern (Tangent Ratio PDF):
```json
["tangent", "ratio", "opposite", "adjacent", "angle"]
```

Results saved to `pdf_test_results.json`.

This fully satisfies the “offline evaluation with expected patterns” requirement.

---

## **5. Known Limits**

- Handwriting OCR accuracy depends on image clarity  
- RAG uses an in-memory MiniLM index (small-scale)  
- SQLite is local-only (no multi-user concurrency)  
- Some flashcard outputs may simplify details if OCR is noisy  
- No on-device deployment (local only, not optimized for mobile)

---

## **6. Reproducibility**

- `requirements.txt` pins all dependencies  
- `.env.example` included for secrets setup  
- OCR, RAG, and LLM behavior is deterministic for given inputs  
- Offline evaluations reproduce results consistently  
- Flask app runs locally via `python app.py`  

---


