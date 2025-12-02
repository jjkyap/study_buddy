from dotenv import load_dotenv
import os
from functools import wraps
import time
import json
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)

from llm import generate_summary, generate_flashcards
from rag import init_vector_store, add_note_to_rag, query_context
from safety import validate_user_input
from telemetry import log_telemetry
from database import init_db, save_note, get_all_notes, get_note_by_id, delete_note

# ----- Environment & Flask setup ----- #

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

DEMO_USERNAME = os.getenv("DEMO_USERNAME", "demo")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "password123")

# Initialize SQLite + RAG
init_db()
rag_client, rag_collection = init_vector_store()  # kept for compatibility, not used

ALLOWED_EXTENSIONS = {"txt", "pdf"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ----- Auth helper ----- #

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


# ----- Routes: auth & pages ----- #

@app.route("/", methods=["GET"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def handle_login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if username == DEMO_USERNAME and password == DEMO_PASSWORD:
        session["logged_in"] = True
        session["username"] = username
        return redirect(url_for("dashboard"))

    flash("Invalid username or password", "error")
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/history", methods=["GET"])
@login_required
def history():
    notes = get_all_notes()
    return render_template("history.html", notes=notes)


@app.route("/note/<int:note_id>", methods=["GET"])
@login_required
def view_note(note_id):
    note = get_note_by_id(note_id)
    if not note:
        return "Note not found", 404

    # note: (id, timestamp, raw_text, summary, flashcards_json)
    _, timestamp, raw_text, summary, flashcards_json = note
    flashcards = json.loads(flashcards_json or "[]")

    return render_template(
        "note_detail.html",
        timestamp=timestamp,
        raw_text=raw_text,
        summary=summary,
        flashcards=flashcards
    )

@app.route("/delete/<int:note_id>", methods=["POST"])
def delete_note_route(note_id):
    try:
        delete_note(note_id)
        return redirect("/history")
    except Exception as e:
        print("Delete error:", e)
        return "Failed to delete note.", 500



# ----- Core API: process note ----- #

@app.route("/api/process-note", methods=["POST"])
@login_required
def process_note():
    """
    Core user flow:
      - Input: raw note text OR uploaded file (.txt / .pdf)
      - OCR for PDFs (pdfplumber -> Tesseract -> EasyOCR)
      - RAG: store note text + retrieve similar notes
      - LLM: generate summary + flashcards
      - Save to SQLite for long-term memory
      - Log telemetry (latency, tokens, cost, error)
    """
    t_start = time.time()
    pathway = "rag"

    raw_text = ""

    # 1) Check if user uploaded a file
    file = request.files.get("file")

    if file and file.filename and file.filename.strip():
        filename = file.filename
        if not allowed_file(filename):
            return jsonify({"error": "Unsupported file type. Use .txt or .pdf"}), 400

        ext = filename.rsplit(".", 1)[1].lower()

        if ext == "txt":
            raw_text = file.read().decode("utf-8", errors="ignore")

        elif ext == "pdf":
            from ocr_utils import extract_text_pdf
            pdf_bytes = file.read()
            raw_text, method_used = extract_text_pdf(pdf_bytes)
            print("OCR method used:", method_used)

    else:
        # 2) Fallback: use pasted textarea content
        raw_text = request.form.get("note_text", "")
        print("DEBUG pasted text:", repr(raw_text))

    # 3) Safety guardrails
    is_valid, error_message = validate_user_input(raw_text)
    if not is_valid:
        latency_ms = int((time.time() - t_start) * 1000)
        log_telemetry(pathway, latency_ms, None, None, None, error_message)
        return jsonify({"error": error_message}), 400

    # 4) Add to RAG corpus (in-memory)
    note_id = f"note-{int(time.time())}"
    add_note_to_rag(note_id, raw_text)

    # 5) Retrieve RAG context using this note as query
    context_chunks = query_context(query=raw_text, k=4)

    try:
        # 6) LLM: summary + flashcards
        summary, usage_sum = generate_summary(raw_text, context_chunks)
        flashcards, usage_cards = generate_flashcards(raw_text, context_chunks)

        latency_ms = int((time.time() - t_start) * 1000)

        tokens_in = (usage_sum.get("prompt_tokens", 0) +
                     usage_cards.get("prompt_tokens", 0))
        tokens_out = (usage_sum.get("completion_tokens", 0) +
                      usage_cards.get("completion_tokens", 0))
        cost = usage_sum.get("cost_usd", 0.0) + usage_cards.get("cost_usd", 0.0)

        # 7) Persist note to SQLite
        timestamp = datetime.now().isoformat(timespec="seconds")
        save_note(raw_text, summary, json.dumps(flashcards), timestamp)

        # 8) Telemetry logging
        log_telemetry(pathway, latency_ms, tokens_in, tokens_out, cost, None)

        return jsonify({
            "summary": summary,
            "flashcards": flashcards,
            "latency_ms": latency_ms,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": cost
        })

    except Exception as e:
        print("🔥 ERROR in process_note:", type(e), str(e))
        latency_ms = int((time.time() - t_start) * 1000)
        log_telemetry(pathway, latency_ms, None, None, None, str(e))
        return jsonify({"error": "AI failed to process the note"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
