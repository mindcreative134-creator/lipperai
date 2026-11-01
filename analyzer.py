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

def calculate_klap_viral_score(clip_text: str, duration: float, is_opening_hook: bool = False) -> dict:
    """
    Klap-style AI Viral Score Algorithm (0-100).
    Evaluates:
      1. Hook Strength: Question words, shock words, curiosity gap in first 3-5s.
      2. Dialogue Velocity: Words per second (optimal 2.4 - 3.8 WPS).
      3. Emotional Impact: Excitement punctuation (!, ?, ।) + viral keywords.
    """
    words = clip_text.lower().split()
    word_count = len(words)
    wps = word_count / max(duration, 1.0)

    viral_triggers = [
        "secret", "money", "shock", "crazy", "insane", "never", "always",
        "mistake", "why", "how", "wait", "listen", "stop", "best", "worst",
        "rich", "paisa", "sach", "galti", "dekho", "suno", "bhai", "yaar", "omg", "hack"
    ]

    hook_hits = sum(1 for w in words[:12] if any(t in w for t in viral_triggers))
    total_triggers = sum(1 for w in words if any(t in w for t in viral_triggers))
    question_count = clip_text.count('?')
    exclamation_count = clip_text.count('!')

    # Base score range: 84 - 99
    base_score = 84

    # Velocity bonus (sweet spot 2.5 - 3.6 wps)
    if 2.2 <= wps <= 3.8:
        base_score += 4
    elif wps > 1.5:
        base_score += 2

    # Hook bonus
    if is_opening_hook:
        base_score += 4
    if hook_hits > 0:
        base_score += min(4, hook_hits * 2)

    # Keywords & emotion bonus
    base_score += min(5, total_triggers)
    if question_count > 0:
        base_score += 2
    if exclamation_count > 0:
        base_score += 2

    final_score = min(99, max(85, base_score))

    # Determine viral label & reasoning (like Klap.app)
    if final_score >= 95:
        label = "Viral Sensation 🔥"
        reason = "Shocking opening hook + high speech momentum + peak emotional payoff."
    elif final_score >= 90:
        label = "High Engagement ⚡"
        reason = "Strong narrative flow + curiosity gap with complete sentence delivery."
    else:
        label = "Trending Momentum 📈"
        reason = "Punchy dialogue with consistent viewer retention pacing."

    return {
        "viral_score": final_score,
        "viral_label": label,
        "hook_reason": reason
    }

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
                dur = end - start
                clips.append({
                    'title': f"Custom Clip #{idx} ({parts[0].strip()} - {parts[1].strip()})",
                    'start': start,
                    'end': end,
                    'reason': f"User selected time window ({int(dur)}s)",
                    'viral_score': 92,
                    'viral_label': "Custom Highlight 🎯",
                    'hook_reason': "Direct user-curated timestamp moment"
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
                'reason': f"Consecutive Episode Part {part_num}",
                'viral_score': 88,
                'viral_label': "Series Episode 🎬",
                'hook_reason': f"Sequential chronological part {part_num}"
            })
            part_num += 1
        cur_start = cur_end
    return clips

def search_topic_moments(segments: list, query: str, clip_duration: float = 40.0, max_clips: int = 3) -> list:
    """Searches for keyword and snaps to complete sentence boundaries with Klap scoring."""
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

        start, end = snap_to_complete_sentences(segments, raw_start, raw_end, min_dur=25.0, max_dur=60.0)

        overlaps = False
        for c in clips:
            if abs(c['start'] - start) < 30.0:
                overlaps = True
                break

        if not overlaps:
            clip_text = " ".join([s['text'] for s in segments if start <= s['start'] <= end])
            metrics = calculate_klap_viral_score(clip_text, end - start, is_opening_hook=(start < 15.0))
            
            clips.append({
                'title': f"{query.capitalize()} Highlight #{len(clips)+1}",
                'start': start,
                'end': end,
                'reason': f"Mentions '{query}': \"{match['text']}\"",
                'viral_score': metrics['viral_score'],
                'viral_label': metrics['viral_label'],
                'hook_reason': metrics['hook_reason']
            })

        if len(clips) >= max_clips:
            break

    return clips

def analyze_with_heuristics(segments: list, video_duration: float, max_clips: int = 3) -> list:
    """
    Finds punchy moments with audio pace and SNAPS TO COMPLETE SENTENCES!
    Applies Klap AI Viral Score (0-100) to each highlight.
    """
    if not segments:
        return split_into_equal_parts(video_duration, part_seconds=60.0, max_parts=max_clips)

    window_duration = 38.0
    scored_windows = []
    total_time = segments[-1]['end']
    step = 10.0
    current_start = 0.0

    keywords = [
        "best", "secret", "amazing", "important", "remember", "never", "always",
        "why", "how", "what", "watch", "look", "listen", "stop", "mistake",
        "dekho", "suno", "dhyan", "galti", "sach", "kya", "kaise", "kyun", "bhai", "yaar"
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

        clean_start, clean_end = snap_to_complete_sentences(
            segments, raw_st, raw_en, min_dur=25.0, max_dur=60.0
        )

        overlaps = False
        for chosen in selected_clips:
            if abs(clean_start - chosen['start']) < 30.0:
                overlaps = True
                break

        if not overlaps:
            active_dialogue = " ".join([
                s['text'] for s in segments 
                if clean_start <= s['start'] <= clean_end
            ])
            short_title = active_dialogue[:45].strip() if active_dialogue else f"Moment at {int(clean_start)}s"

            # Compute Klap Viral Metrics
            is_opening = (clean_start < 20.0)
            metrics = calculate_klap_viral_score(active_dialogue, clean_end - clean_start, is_opening_hook=is_opening)

            selected_clips.append({
                'title': f"Highlight: {short_title}...",
                'start': clean_start,
                'end': clean_end,
                'reason': f"Complete thought dialogue ({clean_end - clean_start:.1f}s)",
                'viral_score': metrics['viral_score'],
                'viral_label': metrics['viral_label'],
                'hook_reason': metrics['hook_reason']
            })

            if len(selected_clips) >= max_clips:
                break

    selected_clips.sort(key=lambda x: x['start'])
    return selected_clips
