# AI Video Highlight & Clip Maker (100% Free)

Yeh program kisi bhi video (jaise YouTube URL) ko automatically download karke, uske subtitles aur conversation ko read/analyse karta hai aur best **viral / highlight clips** cut karke aapko deta hai.

---

## Features (Khas Baatein)

- **100% Free**: Kisi paid tool (jaise OpusClip ya Klap) ki zaroorat nahi.
- **YouTube Downloader**: `yt-dlp` se best quality (up to 1080p) video download karta hai.
- **Transcript Reader**: `youtube-transcript-api` se video ke captions aur timestamps fetch karta hai (Hindi aur English dono support).
- **Two Analysis Modes**:
  1. **Google Gemini AI (Free)**: Agar aap Gemini free API key daalte hain toh AI best moments select karega.
  2. **Smart Offline Heuristic Mode**: Agar API key nahi hai, tab bhi yeh bina internet ke conversation aur energy analyze karke clips bana dega.
- **Automatic FFmpeg Cutting**: Clips ko exact timestamps ke saath save karta hai.
- **Formats**:
  - **16:9 Landscape**: Normal YouTube videos ke liye.
  - **9:16 Vertical**: Instagram Reels, YouTube Shorts, aur TikTok ke liye (blurred background ke saath).

---

## Kaise Chalayein (How to Run)

Terminal ya PowerShell mein yeh command run karein:

```powershell
python main.py
```

### Steps:
1. **Video URL** daalein (jaise: `https://www.youtube.com/watch?v=...`).
2. Format select karein:
   - `1` = Landscape (16:9)
   - `2` = Vertical Shorts / Reels (9:16)
3. Kitne clips chahiye (default: `3`).
4. Gemini API Key (optional):
   - Agar aapke paas Free Gemini API Key hai toh paste karein (Free key yahan milti hai: [Google AI Studio](https://aistudio.google.com/app/apikey)).
   - Ya sirf **ENTER** daba dein, yeh bina key ke bhi kaam karega!

Clips process hone ke baad seedha `output_clips/` folder mein save ho jayengi aur folder automatically open ho jayega.

---

## Project Structure

```
New folder/
├── main.py            # Main entry point (interactive runner)
├── downloader.py      # Video download handler (yt-dlp)
├── transcriber.py     # Subtitles & timestamps extractor
├── analyzer.py        # AI (Gemini) & Smart Heuristic clip detector
├── cutter.py          # FFmpeg video cutter & 9:16 reel formatter
├── requirements.txt   # Python dependencies
├── .env.example       # API Key template
└── README.md          # Documentation
```

