# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Railway Skills Competition Simulation Exam System (铁路技能竞赛模拟考试系统) — **PC desktop variant**.

- **Backend**: `app.py` — Flask + Waitress, ~480 lines
- **Frontend**: `templates/index.html` — single-file SPA, vanilla JS, ~1450 lines
- **Data**: `data/*.csv` — two question banks (信号工 ≈817 Q, 通信工 ≈796 Q)
- **Distribution**: PyInstaller → single `dist/RailwayExam.exe`
- **PWA/mobile variant**: see `pwa/CLAUDE.md`

## Commands

```bash
python app.py                              # dev mode (browser auto-opens)
pip install -r requirements.txt            # install deps

# Build single .exe
rm -rf build dist *.spec
pyinstaller --onefile --noconsole \
  --add-data "templates;templates" --add-data "data;data" --add-data "static;static" \
  --hidden-import flask --hidden-import jinja2.ext \
  --hidden-import waitress --hidden-import flask_cors \
  --icon crsc.ico --name "RailwayExam" app.py
# Output: dist/RailwayExam.exe

# Test APIs without server
python -c "
from app import app
with app.test_client() as c:
    resp = c.post('/api/generate_paper', json={
        'bank':'信号工','counts':{'fill':5,'choice':5,'judge':5,'short_answer':0,'comprehensive':0},
        'scores':{'fill':2,'choice':1,'judge':1},'duration_minutes':60})
    print(resp.get_json())
"
```

## Architecture

**Flask backend** (`app.py`) + **single-file frontend** (`templates/index.html`) → packaged via PyInstaller into `dist/RailwayExam.exe`.

### API surface (6 routes)

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Serves the SPA frontend |
| `/api/banks` | GET | Returns bank names + per-type question counts |
| `/api/generate_paper` | POST | Validates config, randomly draws questions, returns paper |
| `/api/submit` | POST | Grades all answers, returns per-question results |
| `/api/save_results` | POST | Saves results JSON to `Documents/RailwayExam/` |
| `/api/shutdown` | POST | Stops the server (`os._exit(0)` under Waitress) |

### Data flow

1. User selects bank + config → `POST /api/generate_paper`
2. Frontend stores paper in `examState`, renders one question at a time, collects answers client-side
3. On submit (manual or timer auto-submit) → `POST /api/submit` with all answers
4. Backend grades scored types; reference answers returned for `short_answer/comprehensive`
5. Results displayed; user can save to disk via `/api/save_results`

### Question types

| Key | Type | Scored | Input | Grading |
|-----|------|--------|-------|---------|
| `fill` | 填空 | Yes | Text | Fuzzy token match (≥60% key terms) |
| `choice` | 单选 | Yes | Radio A/B/C/D | Exact letter match |
| `judge` | 判断 | Yes | Radio 对/错 | Normalised symbol match |
| `short_answer` | 简答 | No | Textarea | None (reference only) |
| `comprehensive` | 综合 | No | Textarea | None (reference only) |

`ALL_TYPES = ["fill", "choice", "judge", "short_answer", "comprehensive"]` — a **list**, not a set. Order matters for question grouping.

### CSV format

Columns: `type,number,question,answer`. Encoding: **UTF-8-BOM** (`utf-8-sig`). Bank config maps display names to filenames in `BANK_CONFIG` dict.

### PyInstaller quirks

- `resource_path()` uses `getattr(sys, "frozen", False)` to detect frozen mode — never `hasattr(sys, '_MEIPASS')`
- `template_folder` and `static_folder` must be set explicitly on `Flask(__name__)` via `resource_path()`
- `--add-data` separator is `;` on Windows, `:` on Linux/Mac
- `debug=False, use_reloader=False` is mandatory in frozen builds
- Never write to `sys._MEIPASS` — it's a temp directory auto-deleted on exit
- Single-instance enforced via lock file at `%TEMP%/railway_exam.lock` (stores PID + port)

### Frontend

All colors controlled by CSS custom properties on `:root` (light-only theme). Single global `examState` object — no framework. Submit disabled until all **scored** questions answered.

### Key functions in `app.py`

- `resource_path()` — resolves paths in both dev and PyInstaller-frozen modes
- `load_bank(bank_name)` → `list[dict]` — reads CSV, filters by `ALL_TYPES_SET`
- `get_bank_summary(bank_name)` → `dict` — counts per type
- `fuzzy_match(user, correct)` → `bool` — normalises + checks ≥60% key tokens
- `grade_answer(qtype, user, correct)` → `{correct, score, max_score}`
- `check_single_instance()` — lock-file based, stores PID+port
