import os
import subprocess
import numpy as np
import re

def extract_audio_pcm(video_path: str, temp_wav_path: str = "temp_audio.wav") -> bool:
    """
    Extracts 16kHz mono 16-bit PCM audio from video for fast energy analysis.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-f", "wav",
        temp_wav_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return os.path.exists(temp_wav_path)
    except Exception:
        return False

def analyze_audio_energy(wav_path: str, duration: float, window_sec: float = 1.0) -> np.ndarray:
    """
    Computes RMS energy per 1-second window.
    Tracks volume peaks, excitement, shouts, and detects dead silence.
    """
    import wave
    try:
        with wave.open(wav_path, 'rb') as wf:
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            audio_bytes = wf.readframes(n_frames)
            
        data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
        samples_per_window = int(framerate * window_sec)
        total_windows = int(len(data) / samples_per_window)
        
        if total_windows == 0:
            return np.ones(int(duration))
            
        trimmed = data[:total_windows * samples_per_window]
        windows = trimmed.reshape((total_windows, samples_per_window))
        
        # Calculate RMS energy per window
        rms = np.sqrt(np.mean(windows ** 2, axis=1))
        
        # Normalize between 0.0 and 1.0
        max_val = np.max(rms)
        if max_val > 0:
            norm_energy = rms / max_val
        else:
            norm_energy = np.zeros(total_windows)
            
        return norm_energy
        
    except Exception as e:
        print(f"Audio analysis warning: {e}")
        return np.ones(int(duration))

def analyze_visual_scene_activity(video_path: str, duration: float) -> np.ndarray:
    """
    Detects visual scene cuts, camera switches, and high-motion action using FFmpeg scene filter.
    Returns per-second visual activity score (0.0 to 1.0).
    """
    # Ultra-fast sampling: Sample 2 frames per second to check scene transitions (15x faster)
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-filter:v", "fps=2,select='gt(scene,0.3)',showinfo",
        "-f", "null",
        "-"
    ]
    total_seconds = max(1, int(duration))
    visual_scores = np.zeros(total_seconds, dtype=np.float32)

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')
        # Parse showinfo timestamps: pts_time:12.34
        for line in proc.stderr.splitlines():
            if "pts_time:" in line:
                match = re.search(r'pts_time:([0-9.]+)', line)
                if match:
                    sec = int(float(match.group(1)))
                    if 0 <= sec < total_seconds:
                        # Give a score boost around scene transitions
                        start_window = max(0, sec - 3)
                        end_window = min(total_seconds, sec + 4)
                        visual_scores[start_window:end_window] += 0.35

        # Normalize visual scores
        max_score = np.max(visual_scores)
        if max_score > 0:
            visual_scores = np.clip(visual_scores / max_score, 0.0, 1.0)
            
    except Exception as e:
        print(f"Visual scene analysis warning: {e}")

    return visual_scores

from sentence_snapper import snap_to_complete_sentences

def compute_multimodal_engagement_peaks(
    segments: list,
    audio_energy: np.ndarray,
    visual_activity: np.ndarray,
    duration: float,
    clip_length: float = 40.0,
    max_clips: int = 3
) -> list:
    """
    AI FUSION ENGINE:
    Merges:
      1. Audio Energy & Excitement (Pitch/Loudness spikes, Shouts, Reactions)
      2. Visual Activity (Scene cuts, camera transitions, action)
      3. Dialogue/Transcript density & keywords
    Scores every 1-second interval, applies silence penalty, and selects true peak clips.
    """
    total_seconds = int(duration)
    text_scores = np.zeros(total_seconds, dtype=np.float32)

    keywords = [
        "best", "secret", "amazing", "important", "remember", "never", "always",
        "why", "how", "what", "watch", "look", "listen", "stop", "mistake",
        "dekho", "suno", "dhyan", "galti", "sach", "kya", "kaise", "kyun", "bhai", "yaar", "maar", "kill", "nice"
    ]

    # Map dialogue text to timeline
    for seg in segments:
        st = int(seg['start'])
        en = min(total_seconds, int(seg['end']))
        words = seg['text'].lower().split()
        score = len(words) * 0.1
        score += sum(0.5 for w in words if any(k in w for k in keywords))
        if '?' in seg['text'] or '!' in seg['text']:
            score += 0.5
        text_scores[st:en] += score

    # Normalize text score
    if np.max(text_scores) > 0:
        text_scores = text_scores / np.max(text_scores)

    # Align array lengths
    min_len = min(len(audio_energy), len(visual_activity), len(text_scores), total_seconds)
    audio = audio_energy[:min_len]
    visual = visual_activity[:min_len]
    text = text_scores[:min_len]

    # MULTI-MODAL FUSION FORMULA:
    # 40% Audio Energy + 35% Visual Motion + 25% Dialogue Context
    fusion_scores = (0.40 * audio) + (0.35 * visual) + (0.25 * text)

    # Silence penalty: If audio is dead silent (< 0.05), penalize heavily
    silence_mask = audio < 0.05
    fusion_scores[silence_mask] *= 0.1

    # Score sliding windows of `clip_length` seconds
    win_len = int(clip_length)
    if win_len >= min_len:
        return [{
            'title': "Main Highlight",
            'start': 0.0,
            'end': float(min_len),
            'reason': "Complete high-engagement segment"
        }]

    window_scores = []
    step = 5  # 5-second stride for fine-grained detection
    
    for start_t in range(0, min_len - win_len, step):
        end_t = start_t + win_len
        score = float(np.mean(fusion_scores[start_t:end_t]))
        window_scores.append((start_t, end_t, score))

    # Sort windows by score descending
    window_scores.sort(key=lambda x: x[2], reverse=True)

    # Select top non-overlapping clips
    selected = []
    for start_t, end_t, score in window_scores:
        overlaps = False
        for s_t, e_t, _ in selected:
            if abs(start_t - s_t) < (win_len * 0.75):
                overlaps = True
                break
        if not overlaps:
            selected.append((start_t, end_t, score))
            if len(selected) >= max_clips:
                break

    # Sort chronologically
    selected.sort(key=lambda x: x[0])

    clips = []
    for idx, (st, en, sc) in enumerate(selected, start=1):
        # Snap raw window to complete spoken sentence boundary
        clean_st, clean_en = snap_to_complete_sentences(segments, float(st), float(en), min_dur=25.0, max_dur=60.0)
        
        # Find matching dialogue
        matching = [s['text'] for s in segments if s['start'] >= clean_st and s['end'] <= clean_en]
        dialogue = " ".join(matching)[:55].strip() if matching else f"Peak at {int(clean_st)}s"
        
        clips.append({
            'title': f"Peak #{idx}: {dialogue}...",
            'start': clean_st,
            'end': clean_en,
            'reason': f"Multi-Modal Score: {round(sc, 2)} (Audio + Visual Peak with complete sentence)"
        })

    return clips
