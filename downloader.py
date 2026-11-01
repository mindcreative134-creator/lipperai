import os
import re
import yt_dlp

def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/|v\/|shorts\/)([0-9A-Za-z_-]{11})',
        r'youtu\.be\/([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""

def download_video(url: str, output_dir: str = "downloads") -> dict:
    """
    Downloads the YouTube video in MP4 format (best quality up to 1080p).
    Returns a dict with video path, title, duration, and video_id.
    """
    os.makedirs(output_dir, exist_ok=True)
    video_id = extract_video_id(url)
    
    out_template = os.path.join(output_dir, "%(id)s.%(ext)s")
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': out_template,
        'merge_output_format': 'mp4',
        'quiet': False,
        'no_warnings': True,
    }
    
    print(f"\n[1/4] Downloading video from: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        # Ensure mp4 extension
        base, _ = os.path.splitext(filename)
        final_filename = base + ".mp4"
        
        return {
            'video_id': info.get('id', video_id),
            'title': info.get('title', 'video'),
            'duration': info.get('duration', 0),
            'file_path': final_filename
        }

