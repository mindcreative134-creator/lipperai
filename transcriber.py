import sys
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

def format_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

def get_video_transcript(video_id: str) -> list:
    """
    Fetches transcript segments with start and duration.
    Tries Hindi, English, and auto-generated subtitles.
    Returns list of dicts: [{'start': float, 'duration': float, 'text': str, 'end': float}]
    """
    print(f"[2/4] Fetching transcript for video ID: {video_id}...")
    try:
        api = YouTubeTranscriptApi()
        raw_data = None

        # 1. Try listing all available transcripts and take the first one
        try:
            transcript_list = api.list(video_id)
            for t in transcript_list:
                raw_data = t.fetch()
                break
        except Exception:
            pass

        # 2. Fallback to direct fetch with common languages (Hindi, English)
        if raw_data is None:
            raw_data = api.fetch(video_id, languages=['hi', 'hi-Latn', 'en', 'en-US', 'en-GB'])

        formatted = []
        for item in raw_data:
            start = float(item.start if hasattr(item, 'start') else item['start'])
            dur = float(item.duration if hasattr(item, 'duration') else item['duration'])
            text = str(item.text if hasattr(item, 'text') else item['text']).replace('\n', ' ').strip()
            
            if text:
                formatted.append({
                    'start': round(start, 2),
                    'duration': round(dur, 2),
                    'end': round(start + dur, 2),
                    'text': text
                })
        print(f"  -> Successfully loaded {len(formatted)} dialogue lines from video!")
        return formatted

    except Exception as e:
        print(f"  -> Warning: Could not fetch transcript ({e}).")
        return []

def transcript_to_text_with_timestamps(segments: list) -> str:
    """
    Converts list of segments into a condensed timestamped transcript.
    Combines segments into chunks of ~15-25 seconds to make it concise for AI.
    """
    if not segments:
        return ""
        
    lines = []
    chunk_text = []
    chunk_start = segments[0]['start']
    chunk_end = segments[0]['end']
    
    for seg in segments:
        chunk_text.append(seg['text'])
        chunk_end = seg['end']
        
        # Every ~20 seconds or natural pause, create a timestamp block
        if chunk_end - chunk_start >= 20 or any(seg['text'].endswith(p) for p in ('.', '?', '!', '।')):
            text = " ".join(chunk_text).strip()
            lines.append(f"[{format_timestamp(chunk_start)} - {format_timestamp(chunk_end)}] {text}")
            chunk_text = []
            chunk_start = chunk_end
            
    if chunk_text:
        text = " ".join(chunk_text).strip()
        lines.append(f"[{format_timestamp(chunk_start)} - {format_timestamp(chunk_end)}] {text}")
        
    return "\n".join(lines)
