# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Railway Skills Competition Simulation Exam System (铁路技能竞赛模拟考试系统) — **PWA / mobile variant**.

Zero-dependency static web app. All logic runs client-side — no Python, no server needed after initial load.

- **Main app**: `index.html` — single-file SPA (~1770 lines), vanilla JS, all backend logic ported inline
- **Offline**: `sw.js` — Service Worker, cache-first for static, network-first for JSON
- **PWA install**: `manifest.json` — app name "铁路技能竞赛模拟考试系统", standalone mode
- **Data**: `data/*.json` — same question banks as PC variant, pre-converted from CSV
- **Distribution**: ZIP (`dist/RailwayExam_PWA_v1.0.zip`) or Capacitor APK
- **PC variant**: see parent directory `../CLAUDE.md`

## Commands

```bash
python start.py                          # local dev server, auto-opens browser at :8080
python -m http.server 5000               # alternative dev server

# APK build (needs Android SDK at $ANDROID_HOME + Java 17+)
npm install                              # only once
npm run cap:update                       # sync web assets → www/ then npx cap sync
npm run cap:open:android                 # open in Android Studio
npm run cap:build:android                # CLI build via Gradle (needs ANDROID_HOME)
build.bat                                # full build: copy www → sync → assembleDebug

# Convert new CSV → JSON
python -c "
import csv, json
TYPES = {'fill','choice','judge','short_answer','comprehensive'}
with open('input.csv','r',encoding='utf-8-sig') as f:
    qs = [{k.strip():v.strip() for k,v in r.items()} for r in csv.DictReader(f) if r['type'].strip() in TYPES]
with open('output.json','w',encoding='utf-8') as f:
    json.dump(qs, f, ensure_ascii=False)
"
# Then update BANK_CONFIG in index.html and bump CACHE_NAME in sw.js
```

## Architecture

**`index.html`** — Complete SPA with CSS + HTML + JS all in one file. No build step, no npm dependencies needed for web use. Key JS functions and what Python code they replace:

| JS Function | Replaces Python | Purpose |
|-------------|----------------|---------|
| `loadBankData(name)` | `load_bank()` + `/api/banks` | Fetch JSON, cache in `bankCache`, compute summary |
| `fuzzyMatch(user, correct)` | `fuzzy_match()` | Normalise + ≥60% token match |
| `gradeAnswer(type, user, correct)` | `grade_answer()` | Dispatch by type, return `{correct, score, max_score}` |
| `generatePaper(bank, counts, scores, duration)` | `/api/generate_paper` | Fisher-Yates shuffle draw, validate counts |
| `submitAndGrade(questions, answers, timeUsed)` | `/api/submit` | Grade all, compute totals |
| `saveResultsToFile()` | `/api/save_results` | Build JSON Blob → trigger browser download |

`/api/shutdown` is removed — not applicable to static web app.

### Data loading

Banks configured in `BANK_CONFIG` object (parallel to Python's `BANK_CONFIG` dict, but values are JSON paths instead of CSV filenames):

```javascript
const BANK_CONFIG = {
  '通信工': 'data/通信工.json',
  '信号工': 'data/信号工.json',
};
```

JSON files are arrays of `{type, number, question, answer}`. Loaded via `fetch()` on init, cached in `bankCache{}` and `bankSummaryCache{}`. Service Worker caches them after first load → fully offline.

### Service Worker (`sw.js`)

- **Cache name**: `railway-exam-v1` — bump to `v2`, `v3` etc. when data or assets change
- **Install**: pre-caches all files listed in `ASSETS_TO_CACHE` array
- **Fetch strategy**: cache-first for static assets (HTML/CSS/JS/PNG), network-first with cache fallback for JSON data
- **Update**: listens for `SKIP_WAITING` message; `index.html` prompts user on new version

### Capacitor (Android APK)

`capacitor.config.json`:
- `appId`: `com.crsc.railwayexam`
- `appName`: `铁路技能竞赛模拟考试系统`
- `webDir`: `www/` (copy of PWA files, synced via `npm run cap:update`)
- `server.androidScheme`: `https`

Android project at `android/`: compileSdk 36, minSdk 24, targetSdk 36. App icons generated from `crsc.ico` (256px) at all mipmap densities.

### Icons

All generated from `static/crsc.ico` (256×256 RGBA) via Pillow:
- `static/icon-192.png` (192×192) — PWA icon
- `static/icon-512.png` (512×512) — PWA icon
- `static/splash-*.png` — Apple/Android splash screens
- `android/app/src/main/res/mipmap-*/ic_launcher.png` — Android app icon (mdpi through xxxhdpi)

### Key differences from PC variant

- **Fuzzy match**: Python `re.sub(r"\s+","",s)` → JS `s.replace(/\s+/g,'')`. Regex char class `[，。；：、！？《》（）—…,\.;:!\?\(\)\[\]\{\}]` — identical characters, JS escape rules (unescaped `}` is fine in JS but escaped in both for safety)
- **CSV**: loaded as pre-converted JSON via `fetch()` + SW cache, not `csv.DictReader`
- **Grading**: entirely client-side, no server round-trip
- **Save**: `Blob` + `URL.createObjectURL()` download instead of `Documents/RailwayExam/`
- **`escapeAttr()`**: also escapes `'` → `&#39;` (a fix over the original)
- **Shuffle**: Fisher-Yates in JS instead of `random.shuffle()`
- **Timer**: same `setInterval` 1-second tick, auto-submit on expiry

### State management

Same pattern as PC frontend: single global `examState` object. No React/Vue — vanilla JS DOM manipulation. Answer inputs bind directly to `examState.answers[idx]`.

### CSS theming

All colors via CSS custom properties on `:root` (light-only theme). QA type badge colors (`--qa-*-bg`) hardcoded. When adding UI, use existing variables. Responsive breakpoint at 640px.
