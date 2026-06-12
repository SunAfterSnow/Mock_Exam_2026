"""
Railway Skills Competition Simulation Exam System
===================================================
Backend: Flask + Waitress, packaged into a single .exe via PyInstaller.

Run: python app.py   (or double-click the built .exe)
"""

import sys
import os
import csv
import re
import json
import socket
import random
import threading
import time
import tempfile
import webbrowser
from datetime import datetime

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# ---------------------------------------------------------------------------
# Path helpers for PyInstaller bundles
# ---------------------------------------------------------------------------

def resource_path(relative_path: str) -> str:
    """Get absolute path to resource — works in dev and in PyInstaller onefile."""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ---------------------------------------------------------------------------
# Flask app — resolve template folder BEFORE creating the app
# ---------------------------------------------------------------------------

template_dir = resource_path("templates")
app = Flask(__name__, template_folder=template_dir, static_folder=resource_path("static"))
CORS(app)


# ---------------------------------------------------------------------------
# Port helpers
# ---------------------------------------------------------------------------

LOCK_FILE = os.path.join(tempfile.gettempdir(), "railway_exam.lock")


def find_free_port(start: int = 5000, end: int = 5099) -> int:
    """Return the first available port in [start, end]."""
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError(f"No free port in range {start}-{end}")


def check_single_instance() -> bool:
    """Return True if this is the only instance (lock acquired)."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                data = json.load(f)
            pid = data.get("pid", 0)
            # Check if the process still exists
            try:
                os.kill(pid, 0)  # signal 0 = existence check
                return False  # another instance is still running
            except OSError:
                pass  # stale lock
        except Exception:
            pass
        # Stale lock — remove it
        try:
            os.remove(LOCK_FILE)
        except OSError:
            pass

    with open(LOCK_FILE, "w") as f:
        json.dump({"pid": os.getpid(), "started": datetime.now().isoformat()}, f)
    return True


def remove_lock():
    """Remove the single-instance lock file."""
    try:
        os.remove(LOCK_FILE)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

CSV_DIR = resource_path("data")

# Map display names to CSV filenames
BANK_CONFIG = {
    "通信工": "2026年职工技能竞赛技术文件-轨道交通通信工-理论.csv",
    "信号工": "第19届股份技能大赛题库-信号（最终版）.csv",
}

# Score-weight types (scored) vs reference-only types
SCORED_TYPES = {"fill", "choice", "judge"}
REFERENCE_TYPES = {"short_answer", "comprehensive"}
# Ordered list — determines exam question display order
ALL_TYPES = ["fill", "choice", "judge", "short_answer", "comprehensive"]
ALL_TYPES_SET = set(ALL_TYPES)


def load_bank(bank_name: str) -> list[dict]:
    """Load and return all questions from a bank CSV as a list of dicts."""
    if bank_name not in BANK_CONFIG:
        raise ValueError(f"Unknown bank: {bank_name}")

    csv_path = os.path.join(CSV_DIR, BANK_CONFIG[bank_name])
    questions: list[dict] = []

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            qtype = row.get("type", "").strip()
            if qtype not in ALL_TYPES_SET:
                continue
            questions.append({
                "type": qtype,
                "number": row.get("number", "").strip(),
                "question": row.get("question", "").strip(),
                "answer": row.get("answer", "").strip(),
            })

    return questions


def get_bank_summary(bank_name: str) -> dict:
    """Return counts per type for a bank."""
    questions = load_bank(bank_name)
    summary: dict[str, int] = {}
    for t in ALL_TYPES:
        summary[t] = sum(1 for q in questions if q["type"] == t)
    summary["total"] = len(questions)
    return summary


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def fuzzy_match(user_answer: str, correct_answer: str) -> bool:
    """
    Fuzzy match for fill-in-the-blank questions.
    Normalises case, whitespace, punctuation; checks that user answer
    contains the key terms from the correct answer.
    """
    def normalise(s: str) -> str:
        # Lowercase, collapse whitespace
        s = s.lower().strip()
        s = re.sub(r"\s+", "", s)
        # Remove common punctuation that doesn't affect meaning
        s = re.sub(r"[，。；：、！？《》（）—…,\.;:!\?\(\)\[\]\{\}]", "", s)
        return s

    user_norm = normalise(user_answer)
    correct_norm = normalise(correct_answer)

    if not user_norm or not correct_norm:
        return False

    # Exact match after normalisation
    if user_norm == correct_norm:
        return True

    # Split correct answer into key tokens (≥2 chars each)
    key_tokens = [t for t in re.split(r"[，,;；\s]+", correct_answer.lower().strip())
                  if len(t) >= 2]
    if not key_tokens:
        key_tokens = [correct_norm]

    # Accept if user answer contains ≥60% of key tokens
    matched = sum(1 for t in key_tokens if t in user_norm)
    ratio = matched / len(key_tokens)
    return ratio >= 0.6


def grade_answer(qtype: str, user_answer: str, correct_answer: str) -> dict:
    """
    Grade a single answer.  Returns a dict:
      { "correct": bool | null,   # None for reference-only types
        "score": float,
        "max_score": float }
    """
    if qtype in REFERENCE_TYPES:
        return {"correct": None, "score": 0, "max_score": 0}

    if qtype == "choice":
        # Exact letter match (case-insensitive, trim)
        u = user_answer.strip().upper()
        c = correct_answer.strip().upper()
        return {"correct": u == c, "score": 0, "max_score": 0}

    if qtype == "judge":
        # Accept ✓/✗/√/×/对/错
        u = user_answer.strip()
        c = correct_answer.strip()
        u_norm = u.replace("✓", "对").replace("√", "对").replace("✗", "错").replace("×", "错")
        c_norm = c.replace("✓", "对").replace("√", "对").replace("✗", "错").replace("×", "错")
        return {"correct": u_norm == c_norm, "score": 0, "max_score": 0}

    if qtype == "fill":
        ok = fuzzy_match(user_answer, correct_answer)
        return {"correct": ok, "score": 0, "max_score": 0}

    return {"correct": False, "score": 0, "max_score": 0}


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Serve the single-page exam application."""
    return render_template("index.html")


@app.route("/api/banks")
def api_banks():
    """Return available banks with question counts per type."""
    result = {}
    for name in BANK_CONFIG:
        summary = get_bank_summary(name)
        result[name] = summary
    return jsonify(result)


@app.route("/api/generate_paper", methods=["POST"])
def api_generate_paper():
    """
    Receive exam configuration, randomly draw questions, return the paper.

    Expected JSON body:
      {
        "bank": "通信工",
        "counts": { "fill": 10, "choice": 10, "judge": 10,
                    "short_answer": 2, "comprehensive": 1 },
        "scores": { "fill": 2, "choice": 1, "judge": 1 },
        "duration_minutes": 60
      }
    """
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON body"}), 400
    bank_name = data.get("bank", "")
    counts: dict = data.get("counts", {})
    scores: dict = data.get("scores", {})
    duration = data.get("duration_minutes", 60)

    if bank_name not in BANK_CONFIG:
        return jsonify({"error": f"Unknown bank: {bank_name}"}), 400

    # Validate type counts
    all_qs = load_bank(bank_name)
    by_type: dict[str, list[dict]] = {}
    for t in ALL_TYPES:
        by_type[t] = [q for q in all_qs if q["type"] == t]

    for t in ALL_TYPES:
        requested = int(counts.get(t, 0))
        available = len(by_type[t])
        if requested < 0:
            return jsonify({"error": f"Invalid count for {t}: {requested}"}), 400
        if requested > available:
            return jsonify({
                "error": f"Not enough {t} questions. Requested: {requested}, Available: {available}"
            }), 400

    # Validate duration
    if not isinstance(duration, (int, float)) or duration < 1:
        return jsonify({"error": "Duration must be at least 1 minute"}), 400

    # Validate scores (only for scored types)
    for t in SCORED_TYPES:
        s = scores.get(t, 0)
        if not isinstance(s, (int, float)) or s < 0:
            return jsonify({"error": f"Invalid score for {t}: {s}"}), 400

    # Draw random questions without duplicates per type
    drawn: list[dict] = []
    for t in ALL_TYPES:
        n = int(counts.get(t, 0))
        if n > 0:
            pool = by_type[t].copy()
            random.shuffle(pool)
            for q in pool[:n]:
                q_copy = q.copy()
                q_copy["score_per"] = scores.get(t, 0) if t in SCORED_TYPES else 0
                drawn.append(q_copy)

    # Shuffle interleaved or keep grouped by type?  Group by type for clarity.
    # question_index is assigned sequentially.
    for i, q in enumerate(drawn):
        q["index"] = i  # 0-based

    # Compute max possible score
    max_score = sum(
        q["score_per"] for q in drawn if q["type"] in SCORED_TYPES
    )

    return jsonify({
        "questions": drawn,
        "total": len(drawn),
        "max_score": max_score,
        "duration_seconds": int(duration * 60),
        "scores": scores,
    })


@app.route("/api/submit", methods=["POST"])
def api_submit():
    """
    Receive answers, grade them, return results.

    Expected JSON body:
      {
        "questions": [...],   # the exam questions (with score_per etc.)
        "answers": { "0": "answer text", "1": "A", ... },
        "time_used_seconds": 1234
      }
    """
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON body"}), 400
    questions = data.get("questions", [])
    answers: dict = data.get("answers", {})
    time_used = data.get("time_used_seconds", 0)

    results = []
    total_score = 0
    max_score = 0

    for q in questions:
        idx = str(q["index"])
        qtype = q["type"]
        correct = q["answer"]
        user = answers.get(idx, "")

        grade = grade_answer(qtype, user, correct)

        if qtype in SCORED_TYPES:
            sp = q.get("score_per", 0)
            grade["score"] = sp if grade["correct"] else 0
            grade["max_score"] = sp
            max_score += sp
            total_score += grade["score"]
        else:
            grade["score"] = 0
            grade["max_score"] = 0

        results.append({
            "index": q["index"],
            "type": qtype,
            "number": q["number"],
            "question": q["question"],
            "user_answer": user,
            "correct_answer": correct,
            "is_correct": grade["correct"],
            "score": grade["score"],
            "max_score": grade["max_score"],
        })

    return jsonify({
        "results": results,
        "total_score": total_score,
        "max_score": max_score,
        "time_used_seconds": time_used,
    })


@app.route("/api/save_results", methods=["POST"])
def api_save_results():
    """
    Save exam results as a JSON file in the user's home directory.
    """
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON body"}), 400
    bank_name = data.get("bank", "unknown")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"RailwayExam_{bank_name}_{timestamp}.json"

    # Save to user's Documents folder (or Desktop as fallback)
    save_dir = os.path.join(os.path.expanduser("~"), "Documents", "RailwayExam")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return jsonify({"saved": True, "path": save_path})


@app.route("/api/shutdown", methods=["POST"])
def api_shutdown():
    """Shut down the server gracefully."""
    shutdown_func = request.environ.get("werkzeug.server.shutdown")
    if shutdown_func:
        shutdown_func()
        return jsonify({"status": "shutting down"})

    # When running under waitress or other WSGI, fall back to os._exit
    import atexit
    atexit.register(remove_lock)

    def delayed_exit():
        time.sleep(0.5)
        os._exit(0)

    threading.Thread(target=delayed_exit, daemon=True).start()
    return jsonify({"status": "shutting down"})


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    # Single-instance check
    if not check_single_instance():
        print("Another instance of Railway Exam is already running.")
        print("Check your browser or system tray.")
        # Still open the browser to the existing instance
        # Try to find which port the existing instance is on
        try:
            with open(LOCK_FILE, "r") as f:
                lock_data = json.load(f)
            existing_port = lock_data.get("port", 5000)
        except Exception:
            existing_port = 5000
        webbrowser.open(f"http://127.0.0.1:{existing_port}")
        sys.exit(0)

    # Find a free port
    port = find_free_port()
    print(f"Starting Railway Exam on http://127.0.0.1:{port}")

    # Update lock file with port
    with open(LOCK_FILE, "w") as f:
        json.dump({"pid": os.getpid(), "port": port,
                    "started": datetime.now().isoformat()}, f)

    # Auto-open browser after a short delay
    def open_browser():
        time.sleep(1.0)
        webbrowser.open(f"http://127.0.0.1:{port}")

    threading.Thread(target=open_browser, daemon=True).start()

    # Use Waitress as the production WSGI server
    try:
        from waitress import serve
        print("Using Waitress production server.")
        serve(app, host="127.0.0.1", port=port, threads=6)
    except ImportError:
        print("Waitress not found, falling back to Flask dev server.")
        print("WARNING: Dev server is not suitable for production.")
        app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
    finally:
        remove_lock()


if __name__ == "__main__":
    main()
