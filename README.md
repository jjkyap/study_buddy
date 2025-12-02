# LLM Study Buddy – Notes → Summary + Flashcards (RAG)

## Overview

This app is a minimal web-based "study buddy" that:
- Takes raw lecture notes as input.
- Stores them in a small RAG (retrieval-augmented generation) store.
- Uses an LLM to generate:
  - A concise summary.
  - A set of Q/A flashcards.
- Logs telemetry and supports offline evaluation.

It is built as an individual assignment project.

## Stack

- **Model:** OpenAI `gpt-4o-mini` via API.
- **App:** Flask web app (single-user demo login).
- **RAG:** ChromaDB local persistent vector store (`chroma_db`).
- **Telemetry:** `telemetry.csv` structured log.
- **Offline Eval:** `tests.json` + `eval.py`.

## Architecture (ASCII Diagram)

```text
Browser
  |
  v
Flask app (app.py)  -- (safety checks) --> safety.py
  |
  |-- /api/process-note
  |      |
  |      v
  |   rag.py  <----> Chroma (local vector store)
  |
  v
llm.py  ---> OpenAI API (summary + flashcards)
  |
  v
telemetry.py  ---> telemetry.csv
