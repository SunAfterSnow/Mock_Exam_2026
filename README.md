# Railway Skills Competition Simulation Exam System

**铁路技能竞赛模拟考试系统** — PC desktop + mobile (PWA/Android).

Two question banks: 信号工 (~817 questions) and 通信工 (~796 questions). Five question types: fill-in-the-blank, single-choice, true/false, short-answer, comprehensive.

---

## Variants

| Variant | Directory | Distribution | Tech |
|---------|-----------|-------------|------|
| **PC Desktop** | root | `dist/RailwayExam.exe` (single-file) | Flask + Waitress + PyInstaller |
| **PWA / Mobile** | `pwa/` | `pwa/dist/RailwayExam_PWA_v1.0.zip` or Android APK | Vanilla JS + Service Worker + Capacitor |

Both variants share the same grading logic, question banks, and UI theming. See each directory's `CLAUDE.md` for developer documentation.

---

## PC Variant (Flask + PyInstaller)

### Quick Start

```bash
pip install -r requirements.txt
python app.py                      # Opens browser at http://127.0.0.1:5000
```

### Build single .exe

```bash
rm -rf build dist *.spec
pyinstaller --onefile --noconsole \
  --add-data "templates;templates" --add-data "data;data" --add-data "static;static" \
  --hidden-import flask --hidden-import jinja2.ext \
  --hidden-import waitress --hidden-import flask_cors \
  --icon crsc.ico --name "RailwayExam" app.py
# Output: dist/RailwayExam.exe
```

The `.exe` is self-contained — send it to users, no Python installation needed. On launch it starts a local server and opens the browser.

### Architecture

- **Backend**: `app.py` (~480 lines) — 6 REST API routes (generate paper, submit, grade, save results, shutdown)
- **Frontend**: `templates/index.html` (~1450 lines) — single-file SPA, vanilla JS
- **Data**: `data/*.csv` — UTF-8-BOM encoded, columns `type,number,question,answer`
- **Grading**: server-side — fuzzy token match (≥60%) for fill-in-the-blank, exact match for choice, symbol normalization for true/false

---

## PWA / Mobile Variant (Static Web App + Capacitor)

### Quick Start

```bash
cd pwa
python start.py                    # Opens browser at http://127.0.0.1:8080
```

Or deploy the contents of `pwa/dist/RailwayExam_PWA/` to any static host (GitHub Pages, Netlify, etc.).

### Install on phone

| Platform | Steps |
|----------|-------|
| **Android** | Chrome → menu → "Add to Home screen" |
| **iOS** | Safari → Share → "Add to Home Screen" |
| **HarmonyOS** | Browser → menu → "Add to desktop" |

Works **completely offline** after first visit — Service Worker caches all assets and question data.

### Build Android APK

Prerequisites: Android Studio (with Android SDK) + Java 17+.

```bash
cd pwa
npm install
npm run cap:update                 # Sync web assets to www/
npx cap open android               # Open in Android Studio → Build → Build APK(s)
# Or: build.bat
```

Output: `android/app/build/outputs/apk/debug/app-debug.apk`

### Key differences from PC variant

- All grading is **client-side** (no server round-trip needed)
- Question data stored as pre-converted JSON (`data/*.json`) instead of CSV
- Save results via browser download instead of server-side file write
- Service Worker provides offline support

---

## Question Types & Grading

| Type | Scored | Input | Grading Method |
|------|--------|-------|----------------|
| 填空 (fill-in) | Yes | Text | Fuzzy token match ≥60% |
| 单选 (choice) | Yes | Radio A/B/C/D | Exact letter match |
| 判断 (true/false) | Yes | Radio 对/错 | Normalized symbol match |
| 简答 (short-answer) | No | Textarea | Reference only |
| 综合 (comprehensive) | No | Textarea | Reference only |

---

## File Structure

```
Mock Exam/
├── app.py                          # Flask backend (PC)
├── requirements.txt                # Python dependencies
├── crsc.ico                        # App icon
├── templates/index.html            # PC frontend SPA
├── data/*.csv                      # Question banks (PC)
├── dist/RailwayExam.exe            # Built PC executable
├── CLAUDE.md                       # Developer docs (PC)
├── README.md                       # This file
└── pwa/
    ├── index.html                  # PWA frontend SPA
    ├── manifest.json               # PWA manifest
    ├── sw.js                       # Service Worker
    ├── start.py                    # Dev server
    ├── build.bat                   # APK build script
    ├── capacitor.config.json       # Capacitor config
    ├── package.json                # npm config
    ├── data/*.json                 # Question banks (mobile)
    ├── static/                     # Icons & splash screens
    ├── dist/                       # PWA distributable ZIP
    ├── CLAUDE.md                   # Developer docs (PWA)
    └── android/                    # Capacitor Android project
```

---

## App Info

- **App Name**: 铁路技能竞赛模拟考试系统
- **App ID** (Android): `com.crsc.railwayexam`
- **Icon**: `crsc.ico` (rendered at all required sizes for both platforms)
