import os
import sys
import uuid
import threading
import time
from flask import Flask, render_template_string, request, jsonify, send_from_directory, send_file
from downloader import download_video
from transcriber import get_video_transcript
from analyzer import (
    analyze_with_heuristics, 
    parse_custom_timestamps, 
    search_topic_moments, 
    split_into_equal_parts
)
from cutter import export_clips
from subtitle_engine import SUBTITLE_STYLES

app = Flask(__name__)

CLIPS_DIR = os.path.abspath("output_clips")
DOWNLOADS_DIR = os.path.abspath("downloads")
os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# In-memory Job Queue (Thread-safe background status tracker)
JOBS = {}

def process_job_background(job_id: str, data: dict):
    """
    Background worker thread:
    Processes video asynchronously so mobile app network calls never timeout.
    """
    url = data.get('url', '').strip()
    mode = data.get('mode', 'auto')
    search_query = data.get('search_query', '').strip()
    custom_timestamps = data.get('custom_timestamps', '').strip()
    subtitle_template = data.get('subtitle_template', 'hormozi')
    fmt = data.get('format', '9:16')
    max_clips = int(data.get('max_clips', 3))

    try:
        # Step 1: Download
        JOBS[job_id]['status'] = 'downloading'
        JOBS[job_id]['progress'] = 20
        JOBS[job_id]['step_message'] = 'Downloading video stream...'
        
        video_info = download_video(url, output_dir=DOWNLOADS_DIR)
        video_path = video_info['file_path']
        video_id = video_info['video_id']
        duration = video_info['duration']

        # Step 2: Transcribe
        JOBS[job_id]['status'] = 'transcribing'
        JOBS[job_id]['progress'] = 40
        JOBS[job_id]['step_message'] = 'Extracting speech dialogue & timestamps...'
        segments = get_video_transcript(video_id)

        # Step 3: Analyze
        JOBS[job_id]['status'] = 'analyzing'
        JOBS[job_id]['progress'] = 60
        JOBS[job_id]['step_message'] = 'Detecting high-engagement viral moments...'

        clips = []
        if mode == 'custom' and custom_timestamps:
            clips = parse_custom_timestamps(custom_timestamps)
        elif mode == 'keyword' and search_query:
            clips = search_topic_moments(segments, search_query, clip_duration=40.0, max_clips=max_clips)
            if not clips:
                clips = analyze_with_heuristics(segments, duration, max_clips=max_clips)
        elif mode == 'splitter':
            clips = split_into_equal_parts(duration, part_seconds=60.0, max_parts=max_clips)
        else:
            clips = analyze_with_heuristics(segments, duration, max_clips=max_clips)

        if not clips:
            JOBS[job_id]['status'] = 'failed'
            JOBS[job_id]['error'] = 'Could not detect clips from this video'
            return

        # Step 4: Cut & Burn Subtitles
        JOBS[job_id]['status'] = 'cutting'
        JOBS[job_id]['progress'] = 80
        JOBS[job_id]['step_message'] = f'Cutting clips & burning {subtitle_template} subtitles...'

        is_vertical = fmt == "9:16"
        saved_files = export_clips(
            video_path, clips,
            output_dir=CLIPS_DIR,
            vertical=is_vertical,
            segments=segments,
            subtitle_template=subtitle_template
        )

        # Step 5: Format Results
        results = []
        for c, fpath in zip(clips, saved_files):
            fname = os.path.basename(fpath)
            results.append({
                'title': c['title'],
                'start': c['start'],
                'end': c['end'],
                'duration': round(c['end'] - c['start'], 1),
                'reason': c.get('reason', ''),
                'filename': fname,
                'stream_url': f'/stream/{fname}',
                'download_url': f'/download/{fname}'
            })

        JOBS[job_id]['status'] = 'completed'
        JOBS[job_id]['progress'] = 100
        JOBS[job_id]['step_message'] = 'All clips generated successfully!'
        JOBS[job_id]['clips'] = results

    except Exception as e:
        JOBS[job_id]['status'] = 'failed'
        JOBS[job_id]['error'] = str(e)


# Mobile-Optimized Dashboard & PWA Interface
MOBILE_WEB_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>ClipperAI — 100% Free AI Video Clipper & Viral Reel Maker | OpusClip Alternative</title>
  <meta name="description" content="Turn long YouTube videos into viral 9:16 Shorts & Reels with word-by-word bouncing captions (Alex Hormozi style), AI dialogue excitement detection & sentence snapping. 100% Free, No Watermark.">
  <meta name="keywords" content="ai video clipper, opus clip alternative, viral reels generator, youtube shorts maker, alex hormozi subtitles, auto captions, tiktok editor, free video cutter, ffmpeg 9:16 blur, flutter reels app">
  <meta name="author" content="ClipperAI Team">
  <meta name="robots" content="index, follow">
  
  <!-- OpenGraph / Social Previews -->
  <meta property="og:type" content="website">
  <meta property="og:title" content="ClipperAI — Free AI Video Clipper & Viral Reel Maker">
  <meta property="og:description" content="Auto-convert YouTube videos into 9:16 viral shorts with word-by-word bouncing subtitles and zero mid-sentence cuts. 100% Free & Open Source!">
  <meta property="og:image" content="https://i.ytimg.com/vi/MSA6Pntsi6c/hqdefault.jpg">

  <!-- Schema.org Microdata -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "ClipperAI",
    "operatingSystem": "Android, Windows, Linux, macOS",
    "applicationCategory": "MultimediaApplication",
    "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    "description": "100% Free AI Video Highlight & Reel Maker."
  }
  </script>
  <link rel="manifest" href="/manifest.json">
  <link rel="apple-touch-icon" href="/assets/logo.png">
  <meta name="theme-color" content="#0b0f19">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
  <style>
    body { background-color: #0b0f19; color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .glass { background: rgba(17, 24, 39, 0.92); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); }
    .template-card { cursor: pointer; transition: all 0.2s ease; border: 2px solid transparent; }
    .template-card.active { border-color: #6366f1; background: rgba(99, 102, 241, 0.2); }
    .progress-bar { transition: width 0.4s ease; }
  </style>
</head>
<body class="min-h-screen flex flex-col justify-between pb-6">

  <!-- Mobile Top Bar -->
  <header class="glass sticky top-0 z-50 px-4 py-3.5 flex items-center justify-between border-b border-gray-800">
    <div class="flex items-center gap-2.5">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-pink-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/30">
        <i class="fa-solid fa-scissors text-sm"></i>
      </div>
      <div>
        <h1 class="text-base font-bold text-white tracking-wide">Clipper AI</h1>
        <p class="text-[10px] text-indigo-400 font-medium">Multi-Modal Reel Maker</p>
      </div>
    </div>
    <span class="px-2.5 py-1 rounded-full bg-green-500/10 text-green-400 text-[11px] font-semibold flex items-center gap-1.5 border border-green-500/20">
      <span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span> Free Online
    </span>
  </header>

  <!-- Main Mobile Content -->
  <main class="flex-1 max-w-lg w-full mx-auto p-4 space-y-4">

    <!-- Active Job Progress Card -->
    <div id="jobProgressCard" class="hidden glass rounded-2xl p-4 border border-indigo-500/30 shadow-xl space-y-3">
      <div class="flex items-center justify-between">
        <span class="text-xs font-semibold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
          <i class="fa-solid fa-gear fa-spin text-indigo-400"></i> Processing Video
        </span>
        <span id="percentText" class="text-xs font-bold text-white">0%</span>
      </div>
      
      <div class="w-full bg-gray-800 rounded-full h-2.5 overflow-hidden">
        <div id="progressBar" class="bg-gradient-to-r from-indigo-500 to-pink-500 h-2.5 rounded-full progress-bar w-0"></div>
      </div>
      
      <p id="stepMessage" class="text-xs text-gray-300 text-center font-medium">Starting engine...</p>
    </div>

    <!-- Input Form Card -->
    <div id="createCard" class="glass rounded-2xl p-5 shadow-xl space-y-4">
      
      <!-- Video URL -->
      <div>
        <label class="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-1.5">
          <i class="fa-brands fa-youtube text-red-500 mr-1"></i> YouTube Video Link
        </label>
        <input 
          type="url" 
          id="url" 
          placeholder="https://youtu.be/..." 
          required
          class="w-full px-3.5 py-3 rounded-xl bg-gray-800 border border-gray-700 text-white placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
      </div>

      <!-- Mode Selector -->
      <div>
        <label class="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-1.5">
          <i class="fa-solid fa-sliders text-indigo-400 mr-1"></i> Cutting Option
        </label>
        <select id="mode" class="w-full px-3.5 py-2.5 rounded-xl bg-gray-800 border border-gray-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
          <option value="auto">🤖 Option 1: AI Auto Highlights (Audio + Dialogue)</option>
          <option value="keyword">🔍 Option 2: Search Word/Topic</option>
          <option value="custom">⏱️ Option 3: Exact Timestamps</option>
          <option value="splitter">✂️ Option 4: Split into 60s Reels</option>
        </select>
      </div>

      <!-- Keyword Field -->
      <div id="keywordBox" class="hidden">
        <input 
          type="text" 
          id="searchQuery" 
          placeholder="e.g. fight, joke, intro, win" 
          class="w-full px-3.5 py-2.5 rounded-xl bg-gray-800 border border-purple-500/50 text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
      </div>

      <!-- Custom Timestamps Field -->
      <div id="customBox" class="hidden">
        <input 
          type="text" 
          id="customTimestamps" 
          placeholder="e.g. 01:15-02:00, 05:30-06:15" 
          class="w-full px-3.5 py-2.5 rounded-xl bg-gray-800 border border-green-500/50 text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500"
        >
      </div>

      <!-- Subtitle Animation Templates -->
      <div>
        <label class="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-2">
          <i class="fa-solid fa-closed-captioning text-yellow-400 mr-1"></i> Subtitle Animation Template
        </label>
        <div class="grid grid-cols-2 gap-2.5">
          <div class="template-card active glass rounded-xl p-2.5 text-center" data-template="hormozi">
            <span class="text-xs font-extrabold text-yellow-400 uppercase drop-shadow block mb-0.5">Viral Hormozi</span>
            <span class="text-[10px] text-gray-400">Yellow Bold + Black</span>
          </div>
          <div class="template-card glass rounded-xl p-2.5 text-center" data-template="clean_white">
            <span class="text-xs font-bold text-white block mb-0.5">Clean Minimal</span>
            <span class="text-[10px] text-gray-400">White + Shadow</span>
          </div>
          <div class="template-card glass rounded-xl p-2.5 text-center" data-template="neon_cyan">
            <span class="text-xs font-extrabold text-cyan-400 drop-shadow-[0_0_8px_#ec4899] block mb-0.5">Neon Cyber</span>
            <span class="text-[10px] text-gray-400">Cyan + Magenta Glow</span>
          </div>
          <div class="template-card glass rounded-xl p-2.5 text-center" data-template="red_box">
            <span class="text-xs font-bold bg-red-600 text-white px-1.5 py-0.5 rounded inline-block mb-0.5">Breaking Box</span>
            <span class="text-[10px] text-gray-400">Red Highlight Box</span>
          </div>
        </div>
        <input type="hidden" id="subtitleTemplate" value="hormozi">
      </div>

      <!-- Submit Button -->
      <button 
        id="startBtn" 
        class="w-full py-3.5 px-4 rounded-xl font-bold text-sm text-white bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 shadow-lg shadow-indigo-500/25 active:scale-[0.98] transition flex items-center justify-center gap-2"
      >
        <i class="fa-solid fa-wand-magic-sparkles"></i> Generate Reel Clips
      </button>
    </div>

    <!-- Output Clips Feed -->
    <div id="resultsSection" class="hidden space-y-4">
      <div class="flex items-center justify-between px-1">
        <h2 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
          <i class="fa-solid fa-circle-check text-green-400"></i> Generated Clips
        </h2>
        <button onclick="resetApp()" class="text-xs text-indigo-400 font-semibold hover:underline">
          <i class="fa-solid fa-plus mr-1"></i> New Video
        </button>
      </div>

      <div id="clipsFeed" class="space-y-4"></div>
    </div>

  </main>

  <script>
    const modeSelect = document.getElementById('mode');
    const keywordBox = document.getElementById('keywordBox');
    const customBox = document.getElementById('customBox');
    const templateCards = document.querySelectorAll('.template-card');
    const subtitleInput = document.getElementById('subtitleTemplate');
    const startBtn = document.getElementById('startBtn');
    const jobProgressCard = document.getElementById('jobProgressCard');
    const progressBar = document.getElementById('progressBar');
    const percentText = document.getElementById('percentText');
    const stepMessage = document.getElementById('stepMessage');
    const createCard = document.getElementById('createCard');
    const resultsSection = document.getElementById('resultsSection');
    const clipsFeed = document.getElementById('clipsFeed');

    let currentJobId = null;
    let pollInterval = null;

    // Subtitle card selection
    templateCards.forEach(card => {
      card.addEventListener('click', () => {
        templateCards.forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        subtitleInput.value = card.dataset.template;
      });
    });

    modeSelect.addEventListener('change', () => {
      const mode = modeSelect.value;
      keywordBox.classList.toggle('hidden', mode !== 'keyword');
      customBox.classList.toggle('hidden', mode !== 'custom');
    });

    // Start Video Processing
    startBtn.addEventListener('click', async () => {
      const url = document.getElementById('url').value.trim();
      if (!url) {
        alert('Please enter a YouTube video URL');
        return;
      }

      startBtn.disabled = true;
      startBtn.classList.add('opacity-50');
      jobProgressCard.classList.remove('hidden');
      createCard.classList.add('opacity-40', 'pointer-events-none');

      try {
        // 1. Create Job on Backend
        const res = await fetch('/api/jobs/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            url: url,
            mode: modeSelect.value,
            search_query: document.getElementById('searchQuery').value.trim(),
            custom_timestamps: document.getElementById('customTimestamps').value.trim(),
            subtitle_template: subtitleInput.value,
            format: '9:16',
            max_clips: 3
          })
        });

        const data = await res.json();
        if (!data.success) {
          alert('Error: ' + data.error);
          resetApp();
          return;
        }

        currentJobId = data.job_id;
        // 2. Poll for Progress every 2 seconds
        pollInterval = setInterval(checkJobStatus, 2000);

      } catch (err) {
        alert('Network request failed: ' + err.message);
        resetApp();
      }
    });

    async function checkJobStatus() {
      if (!currentJobId) return;

      try {
        const res = await fetch(`/api/jobs/${currentJobId}`);
        const job = await res.json();

        progressBar.style.width = `${job.progress}%`;
        percentText.innerText = `${job.progress}%`;
        stepMessage.innerText = job.step_message || 'Processing...';

        if (job.status === 'completed') {
          clearInterval(pollInterval);
          jobProgressCard.classList.add('hidden');
          createCard.classList.add('hidden');
          renderClips(job.clips);
        } else if (job.status === 'failed') {
          clearInterval(pollInterval);
          alert('Processing Failed: ' + (job.error || 'Unknown error'));
          resetApp();
        }
      } catch (e) {
        console.error('Polling error:', e);
      }
    }

    function renderClips(clips) {
      clipsFeed.innerHTML = '';
      clips.forEach((clip, i) => {
        const item = document.createElement('div');
        item.className = 'glass rounded-2xl p-4 space-y-3';
        item.innerHTML = `
          <div>
            <div class="text-[11px] font-bold text-indigo-400 uppercase tracking-wider mb-0.5">Reel #${i+1} (${clip.duration}s)</div>
            <h3 class="text-sm font-bold text-white line-clamp-1">${clip.title}</h3>
          </div>

          <div class="rounded-xl overflow-hidden bg-black aspect-[9/16] max-h-[380px] mx-auto flex items-center justify-center border border-gray-800">
            <video controls playsinline preload="metadata" class="w-full h-full object-contain">
              <source src="${clip.stream_url}" type="video/mp4">
            </video>
          </div>

          <a href="${clip.download_url}" download class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-pink-600 text-white font-bold text-xs flex items-center justify-center gap-2 active:scale-[0.98] transition shadow-md shadow-indigo-600/20">
            <i class="fa-solid fa-download"></i> Save to Phone
          </a>
        `;
        clipsFeed.appendChild(item);
      });

      resultsSection.classList.remove('hidden');
    }

    function resetApp() {
      if (pollInterval) clearInterval(pollInterval);
      currentJobId = null;
      startBtn.disabled = false;
      startBtn.classList.remove('opacity-50');
      jobProgressCard.classList.add('hidden');
      createCard.classList.remove('hidden', 'opacity-40', 'pointer-events-none');
      resultsSection.classList.add('hidden');
      progressBar.style.width = '0%';
      percentText.innerText = '0%';
    }
  </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(MOBILE_WEB_TEMPLATE)

# ----------------- MOBILE REST API ENDPOINTS -----------------

@app.route('/api/jobs/create', methods=['POST'])
def api_create_job():
    """
    Called by Mobile App to start a new clipping task.
    Returns immediately with a job_id (No connection timeout!).
    """
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'success': False, 'error': 'No video URL provided'}), 400

    job_id = str(uuid.uuid4())[:8]
    JOBS[job_id] = {
        'job_id': job_id,
        'status': 'queued',
        'progress': 5,
        'step_message': 'Job placed in queue...',
        'created_at': time.time(),
        'clips': []
    }

    # Run in background daemon thread
    thread = threading.Thread(target=process_job_background, args=(job_id, data), daemon=True)
    thread.start()

    return jsonify({'success': True, 'job_id': job_id, 'status': 'queued'})

@app.route('/api/jobs/<job_id>', methods=['GET'])
def api_get_job(job_id):
    """
    Polled by Mobile App every 2 seconds to get real-time progress.
    """
    job = JOBS.get(job_id)
    if not job:
        return jsonify({'success': False, 'error': 'Job not found'}), 404
    return jsonify(job)

@app.route('/manifest.json')
def manifest_json():
    manifest_path = os.path.abspath('mobile_app/assets/manifest.json')
    return send_file(manifest_path, mimetype='application/json')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    assets_dir = os.path.abspath('mobile_app/assets')
    return send_from_directory(assets_dir, filename)

@app.route('/stream/<path:filename>')
def stream_file(filename):
    return send_from_directory(CLIPS_DIR, filename)

@app.route('/download/<path:filename>')
def download_file(filename):
    file_path = os.path.join(CLIPS_DIR, filename)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n=============================================================")
    print(f" Mobile API & PWA App running at: http://localhost:{port}")
    print(f"=============================================================\n")
    app.run(host='0.0.0.0', port=port, debug=False)
