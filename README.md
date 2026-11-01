<div align="center">

# 🎬 ClipperAI — Viral Reel Maker & AI Video Clipper

<p align="center">
  <b>Transform any long-form video into high-engagement 9:16 viral shorts with word-by-word bouncing captions, audio excitement analysis, and zero mid-sentence cuts — 100% Free & Open Source!</b>
</p>

[![Flutter](https://img.shields.io/badge/Flutter-3.24.0-02569B?logo=flutter&logoColor=white)](https://flutter.dev)
[![Android](https://img.shields.io/badge/Platform-Android-3DDC84?logo=android&logoColor=white)](https://www.android.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Optimized%20Pipeline-007808?logo=ffmpeg&logoColor=white)](https://ffmpeg.org)
[![SQLite](https://img.shields.io/badge/Database-SQLite%20Offline-003B57?logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![GitHub Release](https://img.shields.io/github/v/release/mindcreative134-creator/lipperai?color=brightgreen&label=APK%20Release)](https://github.com/mindcreative134-creator/lipperai/releases)

<br/>

<a href="https://github.com/mindcreative134-creator/lipperai/releases/latest">
  <img src="https://img.shields.io/badge/⬇️_DOWNLOAD_OFFICIAL_APK-v1.0.1-success?style=for-the-badge&logo=android" alt="Download APK" height="42">
</a>
<a href="http://localhost:5000">
  <img src="https://img.shields.io/badge/🌐_OPEN_WEB_STUDIO-PORT_5000-blueviolet?style=for-the-badge" alt="Web Studio" height="42">
</a>

</div>

---

## 🌟 Why ClipperAI?

Most viral clip creators (like OpusClip, Klap, or Submagic) charge heavy monthly subscriptions, enforce watermark restrictions, or cut speakers off mid-thought. 

**ClipperAI** solves all of this with a completely free, local-first multi-modal pipeline:

| Feature | ❌ Typical Paid SaaS | ✨ ClipperAI (Free & Open Source) |
| :--- | :--- | :--- |
| **Price** | $29 – $99 / month | **100% Free Forever** |
| **Speaker Cuts** | Cuts randomly at fixed 30s/60s mark | **Sentence Boundary Snapper** (Zero mid-sentence cuts) |
| **Subtitles** | Static lines or paid add-on | **Dynamic Word-by-Word Bouncing Pop** (Hormozi style) |
| **Rendering Speed** | Queued on congested cloud servers | **Ultra-Fast FFmpeg Blur Pipeline** (~10s per clip) |
| **Mobile App** | Web-only or restricted | **Native Flutter App (`com.clipperai.reels`) + SQLite** |
| **Data Privacy** | All your videos sent to 3rd party servers | **Runs locally on your own machine & home network** |

---

## ✨ Key Features

```
                                      ┌──────────────┐
                                      │ YouTube URL  │
                                      └──────┬───────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
             [ Audio Energy Track ]                     [ Full Transcript ]
             (Pitch / Volume / RMS)                     (Hindi, English, Auto)
                       │                                           │
                       └─────────────────────┬─────────────────────┘
                                             ▼
                                  ┌────────────────────┐
                                  │ Multi-Modal Fusion │
                                  │  Excitement Engine │
                                  └──────────┬─────────┘
                                             ▼
                                  ┌────────────────────┐
                                  │  Sentence Snapper  │ ──► Zero mid-sentence cuts
                                  └──────────┬─────────┘
                                             ▼
                                  ┌────────────────────┐
                                  │ Bouncing Pop ASS   │ ──► Word-by-word synced highlight
                                  └──────────┬─────────┘
                                             ▼
                                  ┌────────────────────┐
                                  │ Fast 9:16 Renderer │ ──► Dynamic blurred vertical format
                                  └──────────┬─────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
              [ Local Web Studio ]                       [ Flutter Mobile App ]
             (Live on Port 5000)                        (Saved to Local SQLite)
```

### 🎯 1. Smart Sentence Boundary Snapping
Never suffer from a clip that cuts off mid-word. Our intelligent sentence boundary engine inspects punctuation (`.`, `?`, `!`, `।`) and speech pauses (>0.7s) to ensure every clip begins and ends on a finished, punchy thought.

### ⚡ 2. Word-by-Word Voice-Synced Subtitles (Hormozi Style)
Subtitles are generated directly into high-fidelity ASS (Advanced SubStation Alpha) format:
- **Active Word Pop Animation**: Spoken words bounce with `\fscx125\fscy125\t(0,90,\fscx100\fscy100)` scaling.
- **Viral Color Accents**: Spoken words highlight in vibrant electric yellow (`&H0000FFFF&`) with thick black borders and neon drop-shadows.
- **Multiple Visual Styles**: Supports *Viral Yellow (Hormozi)*, *Minimal Clean White*, and *Cyber Neon Cyan*.

### 📱 3. Native Flutter Mobile App
- **Package ID**: `com.clipperai.reels`
- **Offline SQLite Storage (`sqflite`)**: Saves all rendered clips locally with duration, timestamps, and thumbnail data.
- **One-Tap Share & Download**: Instantly export to your phone gallery for Instagram Reels, YouTube Shorts, or TikTok.
- **Dark Neon Cyberpunk Theme**: Styled with neon green/purple accents and smooth animations.

### 🚀 4. 10x Turbo 9:16 Vertical Blur Pipeline
Converting 16:9 widescreen to 9:16 vertical reels often chokes CPU power. ClipperAI uses a 2-stage FFmpeg pipeline that downscales background frames before applying Gaussian box-blur, delivering full-HD 60fps renders in just **10-15 seconds per reel**.

---

## 📱 Mobile App (Android APK)

The Flutter mobile app connects seamlessly to your local server over Wi-Fi, allowing you to trigger clip generation from your sofa and manage your clips offline in SQLite.

### 📥 Download & Install
1. Head over to [GitHub Releases](https://github.com/mindcreative134-creator/lipperai/releases/latest).
2. Download **`ClipperAI-v1.0.0.apk`**.
3. Tap on the downloaded APK to install on any Android device (Android 5.0+ supported).

---

## 💻 Quick Start (Web & Local Server)

### 1. Clone & Setup
```bash
# Clone the repository
git clone https://github.com/mindcreative134-creator/lipperai.git
cd lipperai

# Install Python requirements
pip install -r requirements.txt
```

### 2. Launch the Web Studio
```bash
python app.py
```
Open **`http://localhost:5000`** in your browser, or visit `http://<YOUR_LOCAL_IP>:5000` on your mobile phone connected to the same Wi-Fi.

### 3. Command Line Runner (CLI Mode)
Prefer running directly in the terminal? Run:
```bash
python main.py
```
Paste any YouTube link, choose your subtitle style, and let ClipperAI do the magic!

---

## 📁 Project Architecture

```
lipperai/
├── 🌐 Web & API Engine
│   ├── app.py                   # Flask server, REST API, & Mobile PWA interface
│   ├── main.py                  # Interactive CLI runner
│   └── templates/
│       └── index.html           # Modern glassmorphism web dashboard
│
├── 🧠 Multi-Modal AI Pipeline
│   ├── multimodal_engine.py     # Audio RMS energy & scene dynamic analyzer
│   ├── sentence_snapper.py      # Complete sentence boundary algorithm
│   ├── subtitle_engine.py       # Word-by-word bouncing ASS subtitle compiler
│   ├── transcriber.py           # Multi-lingual transcript & timestamp extractor
│   ├── analyzer.py              # Dialogue excitement & keyword scorer
│   ├── downloader.py            # High-speed yt-dlp video fetcher
│   └── cutter.py                # Accelerated FFmpeg 9:16 vertical rendering engine
│
├── 📱 Flutter Mobile App (mobile_app/)
│   ├── lib/
│   │   ├── main.dart            # Two-tab navigation & live server job monitor
│   │   ├── database/
│   │   │   └── db_helper.dart   # SQLite database CRUD operations
│   │   ├── models/
│   │   │   └── clip_item.dart   # Local clip metadata schema
│   │   ├── screens/
│   │   │   └── saved_clips_screen.dart # Offline saved clips viewer
│   │   └── widgets/
│   │       └── app_logo.dart    # Custom vector neon branding
│   └── android/                 # Production Android configuration
│
└── ⚙️ CI/CD Automation
    └── .github/workflows/
        └── build_apk.yml        # GitHub Actions automated release pipeline
```

---

## 🎨 Subtitle Styles Showcase

| Style | Accent Color | Animation | Recommended For |
| :--- | :--- | :--- | :--- |
| **Viral Yellow** | `#FFEA00` (Electric Yellow) | Word Pop Zoom (`\fscx125`) | Podcasts, Finance, Alex Hormozi style |
| **Minimal White** | `#FFFFFF` (Pure White) | Smooth Fade & Glow | Storytelling, Documentaries, Calm discussions |
| **Cyber Neon** | `#00F0FF` (Neon Cyan) | Glitch Pop Glow | Tech reviews, Gaming, High-energy commentary |

---

## 🛠️ Tech Stack & Requirements

- **Backend**: Python 3.10+, Flask, `yt-dlp`, `youtube-transcript-api`
- **Processing**: FFmpeg (with `ass` and `scale` filter support)
- **Mobile App**: Flutter 3.24+, Dart 3.5+, SQLite (`sqflite`)
- **Cloud Build**: GitHub Actions CI/CD (Zulu OpenJDK 17 + Ubuntu Runner)

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to check [issues page](https://github.com/mindcreative134-creator/lipperai/issues).

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

<div align="center">
  <sub>Built with ❤️ for creators, podcasters, and video editors worldwide.</sub>
</div>
