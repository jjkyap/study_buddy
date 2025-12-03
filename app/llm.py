import os
import json
import re
from openai import OpenAI

# ------------------------------
# Shared Client
# ------------------------------
def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    base = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")

    if not api_key:
        raise ValueError("Missing API key. Set OPENAI_API_KEY in .env.")

    return OpenAI(api_key=api_key, base_url=base)

# ------------------------------
# Summary (Nova-safe)
# ------------------------------
def generate_summary(note_text, context_chunks):
    client = get_client()
    model = os.getenv("OPENAI_MODEL", "amazon/nova-2-lite-v1:free")

    context = "\n\n".join(context_chunks)

    prompt = f"""
Summarize the student's notes into 3–7 bullet points. 
Do NOT include markdown code fences. 
Do NOT add headings, titles, or commentary.

Context:
{context}

Notes:
{note_text}
"""

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You summarize academic notes cleanly."},
            {"role": "user", "content": prompt},
        ],
    )

    summary = resp.choices[0].message.content or ""
    # Remove accidental code fences/output
    summary = summary.replace("```", "").strip()

    return summary, {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "cost_usd": 0,
    }

# ------------------------------
# Flashcards (Nova-safe)
# ------------------------------
def generate_flashcards(note_text, context_chunks):
    client = get_client()
    model = os.getenv("OPENAI_MODEL", "amazon/nova-2-lite-v1:free")

    context = "\n\n".join(context_chunks)

    prompt = f"""
You MUST output valid JSON. Nothing except JSON.

JSON Format:
{{
  "flashcards": [
    {{ "question": "string", "answer": "string" }},
    {{ "question": "string", "answer": "string" }}
  ]
}}

Rules:
- Do NOT include markdown code fences.
- Do NOT include explanations.
- Do NOT include commentary.
- Output ONLY the JSON object.

Generate 5–10 flashcards.

Context:
{context}

Notes:
{note_text}
"""

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Output ONLY a JSON object following the schema."},
            {"role": "user", "content": prompt},
        ],
    )

    content = resp.choices[0].message.content or ""

    # ---- CLEANING LAYER ----
    # Strip code fences & markdown
    content = content.replace("```json", "").replace("```", "").strip()

    # Extract only the JSON object
    match = re.search(r"{[\s\S]*}", content)
    if match:
        content = match.group(0).strip()

    # ---- PARSING ----
    try:
        data = json.loads(content)
    except Exception:
        data = None

    # ---- FALLBACK ----
    if not data or "flashcards" not in data:
        data = {
            "flashcards": [
                {
                    "question": "What is the main idea of the notes?",
                    "answer": note_text[:500],
                }
            ]
        }

    return data["flashcards"], {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "cost_usd": 0,
    }
