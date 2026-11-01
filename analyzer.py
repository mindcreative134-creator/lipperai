import os
import json
import re
from sentence_snapper import snap_to_complete_sentences

def parse_time_to_seconds(time_val) -> float:
    """Converts seconds or MM:SS / HH:MM:SS string to float seconds."""
    if isinstance(time_val, (int, float)):
        return float(time_val)
    if isinstance(time_val, str):
        val = time_val.strip()
        parts = val.split(':')
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        try:
            return float(val)
        except ValueError:
            return 0.0
    return 0.0

def parse_custom_timestamps(timestamps_input: str) -> list:
    """Parses exact user timestamps like '01:15-02:00, 05:30-06:15'."""
    clips = []
    entries = re.split(r'[,;\n]+', timestamps_input)
    for idx, entry in enumerate(entries, start=1):
        entry = entry.strip()
        if not entry:
            continue
        parts = re.split(r'[-–—to]+', entry)
        if len(parts) >= 2:
            start = parse_time_to_seconds(parts[0])
            end = parse_time_to_seconds(parts[1])
            if end > start:
                clips.append({
                    'title': f"Custom Clip #{idx} ({parts[0].strip()} - {parts[1].strip()})",
                    'start': start,
                    'end': end,
                    'reason': f"User selected time window"
                })
    return clips

def split_into_equal_parts(duration: float, part_seconds: float = 60.0, max_parts: int = 5) -> list:
    """Splits video into consecutive 60s Reel parts."""
    clips = []
    cur_start = 0.0
    part_num = 1
    while cur_start < duration and len(clips) < max_parts:
        cur_end = min(cur_start + part_seconds, duration)
        if cur_end - cur_start >= 15:
            clips.append({
                'title': f"Part {part_num} (Reel)",
                'start': round(cur_start, 1),
                'end': round(cur_end, 1),
                'reason': f"Consecutive Episode Part {part_num}"
            })
            part_num += 1
        cur_start = cur_end
    return clips

def search_topic_moments(segments: list, query: str, clip_duration: float = 40.0, max_clips: int = 3) -> list:
    """Searches for keyword and snaps to complete sentence boundaries."""
    if not segments or not query:
        return []

    query_lower = query.strip().lower()
    matches = [s for s in segments if query_lower in s['text'].lower()]
    if not matches:
        return []

    clips = []
    half_window = clip_duration / 2.0

    for idx, match in enumerate(matches, start=1):
        center_time = match['start'] + (match['duration'] / 2.0)
        raw_start = max(0.0, center_time - half_window)
        raw_end = center_time + half_window

        # Complete thought snapping!
        start, end = snap_to_complete_sentences(segments, raw_start, raw_end, min_dur=25.0, max_dur=60.0)

        overlaps = False
        for c in clips:
            if abs(c['start'] - start) < 30.0:
                overlaps = True
                break

        if not overlaps:
            clips.append({
                'title': f"{query.capitalize()} Highlight #{len(clips)+1}",
                'start': start,
                'end': end,
                'reason': f"Mentions '{query}' with complete thought: \"{match['text']}\""
            })

        if len(clips) >= max_clips:
            break

    return clips

def analyze_with_heuristics(segments: list, video_duration: float, max_clips: int = 3) -> list:
    """
    Finds punchy moments with audio pace and SNAPS TO COMPLETE SENTENCES!
    Zero mid-sentence cutoff.
    """
    if not segments:
        return split_into_equal_parts(video_duration, part_seconds=60.0, max_parts=max_clips)

    window_duration = 35.0
    scored_windows = []
    total_time = segments[-1]['end']
    step = 10.0
    current_start = 0.0

    keywords = [
        "best", "secret", "amazing", "important", "remember", "never", "always",
        "why", "how", "what", "watch", "look", "listen", "stop", "mistake",
        "dekho", "suno", "dhyan", "galti", "sach", "kya", "kaise", "kyun", "bhai", "yaar", "maar", "kill"
    ]

    while current_start + window_duration <= total_time:
        current_end = current_start + window_duration
        matching_segs = [
            s for s in segments 
            if s['start'] >= current_start and s['end'] <= current_end
        ]
        window_text = " ".join([s['text'] for s in matching_segs])
        words = window_text.lower().split()

        word_count = len(words)
        keyword_hits = sum(1 for w in words if any(k in w for k in keywords))
        punctuations = window_text.count('?') + window_text.count('!') + window_text.count('।')

        score = (word_count * 0.4) + (keyword_hits * 3.5) + (punctuations * 2.5)

        scored_windows.append({
            'raw_start': current_start,
            'raw_end': current_end,
            'score': score,
            'text': window_text
        })
        current_start += step

    scored_windows.sort(key=lambda x: x['score'], reverse=True)

    selected_clips = []
    for win in scored_windows:
        raw_st = win['raw_start']
        raw_en = win['raw_end']

        # Snap to complete sentence
        clean_start, clean_end = snap_to_complete_sentences(
            segments, raw_st, raw_en, min_dur=25.0, max_dur=60.0
        )

        overlaps = False
        for chosen in selected_clips:
            if abs(clean_start - chosen['start']) < 30.0:
                overlaps = True
                break

        if not overlaps:
            # Extract sentence snippet for title
            active_dialogue = " ".join([
                s['text'] for s in segments 
                if clean_start <= s['start'] <= clean_end
            ])
            short_title = active_dialogue[:45].strip() if active_dialogue else f"Moment at {int(clean_start)}s"

            selected_clips.append({
                'title': f"Highlight: {short_title}...",
                'start': clean_start,
                'end': clean_end,
                'reason': f"Complete thought dialogue ({clean_end - clean_start:.1f}s)"
            })

            if len(selected_clips) >= max_clips:
                break

    selected_clips.sort(key=lambda x: x['start'])
    return selected_clips
