# Railway Exam — Mobile App

**铁路技能竞赛模拟考试系统** — 移动版

Available in two forms:

| Form | File | Description |
|------|------|-------------|
| **PWA** | `dist/RailwayExam_PWA_v1.0.zip` | Static web app — deploy to any server, install to phone home screen |
| **Android APK** | build via Capacitor | Native Android app — build with Android Studio |

---

## Quick Start — PWA (Immediate)

Serve the folder with any HTTP server:

```bash
cd pwa
python start.py          # Opens browser at http://127.0.0.1:8080
```

Or deploy `dist/RailwayExam_PWA/` to any static host (GitHub Pages, Netlify, etc.).

### Install on phone

| Platform | Steps |
|----------|-------|
| **Android** | Chrome -> menu -> "Add to Home screen" |
| **iOS** | Safari -> Share -> "Add to Home Screen" |
| **HarmonyOS** | Browser -> menu -> "Add to desktop" |

Works **completely offline** after first visit.

---

## Build Android APK (via Capacitor)

This is the mobile equivalent of `PyInstaller --onefile` — it wraps the PWA into a native `.apk`.

### Prerequisites

- Android Studio (with Android SDK)
- Java 17+

### Build

```bash
cd pwa
npm install                    # Install Capacitor (already done)
npm run cap:update             # Sync web assets
npx cap open android           # Open in Android Studio
```

In Android Studio: **Build > Build Bundle(s) / APK(s) > Build APK(s)**

Or use the build script: `build.bat`

Output: `android/app/build/outputs/apk/debug/app-debug.apk`

### App Info

- **App ID**: `com.crsc.railwayexam`
- **App Name**: 铁路技能竞赛模拟考试系统
- **Icon**: Generated from `crsc.ico`

---

## File Structure

```
pwa/
  dist/RailwayExam_PWA_v1.0.zip   <- Distributable package
  index.html                       <- Main app (PWA)
  manifest.json                     <- PWA manifest
  sw.js                             <- Service Worker
  start.py                          <- Dev server
  build.bat                         <- APK build script
  capacitor.config.json             <- Capacitor config
  data/
    信号工.json                      <- 817 questions
    通信工.json                      <- 796 questions
  static/
    icon-192.png, icon-512.png      <- PWA icons
    crsc_china.png, crsc_english.png <- Branding
    splash-*.png                     <- Splash screens
```

## Original Project

All original Python/Flask/PC files are preserved in the parent directory.
