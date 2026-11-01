import os
import re

def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS time format: H:MM:SS.cc"""
    if seconds < 0:
        seconds = 0.0
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    centis = int((secs - int(secs)) * 100)
    return f"{int(hours)}:{int(mins):02d}:{int(secs):02d}.{centis:02d}"

SUBTITLE_STYLES = {
    "hormozi": {
        "name": "Viral Hormozi (Word Pop & Yellow Highlight)",
        "fontname": "Impact",
        "fontsize": 44,
        "primary_colour": "&H0000FFFF&",  # Active word Yellow (AABBGGRR)
        "inactive_colour": "&H00FFFFFF&", # Inactive word White
        "outline_colour": "&H00000000&",  # Thick Black Border
        "back_colour": "&H80000000&",
        "bold": 1,
        "outline": 4.5,
        "shadow": 2.0,
        "border_style": 1,
        "alignment": 2
    },
    "clean_white": {
        "name": "Clean Minimalist (Word Flash)",
        "fontname": "Arial",
        "fontsize": 38,
        "primary_colour": "&H00FFFFFF&",
        "inactive_colour": "&H00AAAAAA&",
        "outline_colour": "&H00000000&",
        "back_colour": "&H80000000&",
        "bold": 1,
        "outline": 3.0,
        "shadow": 1.5,
        "border_style": 1,
        "alignment": 2
    },
    "neon_cyan": {
        "name": "Neon Cyber (Cyan Pop & Magenta Glow)",
        "fontname": "Arial",
        "fontsize": 42,
        "primary_colour": "&H00FFFF00&",  # Cyan
        "inactive_colour": "&H00FFFFFF&",
        "outline_colour": "&H00FF00FF&",  # Magenta glow
        "back_colour": "&H80000000&",
        "bold": 1,
        "outline": 4.0,
        "shadow": 2.0,
        "border_style": 1,
        "alignment": 2
    },
    "red_box": {
        "name": "Breaking Red (Highlighted Red Box)",
        "fontname": "Arial",
        "fontsize": 36,
        "primary_colour": "&H00FFFFFF&",
        "inactive_colour": "&H00DDDDDD&",
        "outline_colour": "&H000000CC&",  # Red box
        "back_colour": "&H000000CC&",     # Red box
        "bold": 1,
        "outline": 3.0,
        "shadow": 0.0,
        "border_style": 3,                # Opaque box
        "alignment": 2
    }
}

def split_segment_into_words(seg: dict) -> list:
    """
    Splits a segment into individual words with estimated start & end times.
    Weights duration by word character length.
    """
    text = seg['text'].strip()
    words = text.split()
    if not words:
        return []

    total_chars = sum(max(1, len(w)) for w in words)
    seg_start = seg['start']
    seg_dur = max(0.5, seg['duration'])
    
    word_items = []
    curr_time = seg_start

    for w in words:
        weight = max(1, len(w)) / total_chars
        w_dur = seg_dur * weight
        w_dur = max(0.2, min(w_dur, 1.2))  # Keep natural speech bounds
        
        word_items.append({
            'word': w,
            'start': curr_time,
            'end': curr_time + w_dur
        })
        curr_time += w_dur

    return word_items

def generate_ass_subtitles(
    segments: list,
    clip_start: float,
    clip_end: float,
    output_ass_path: str,
    template_key: str = "hormozi",
    is_vertical: bool = True
) -> bool:
    """
    Generates ASS subtitles with:
      1. Word-by-word animation (voice synchronized).
      2. 2-3 word dynamic bursts (like CapCut & Opus Clip).
      3. Hormozi bouncing pop effect + Active word highlight.
    """
    if template_key == "none" or template_key not in SUBTITLE_STYLES:
        return False

    style = SUBTITLE_STYLES[template_key]
    fontsize = style['fontsize'] + (10 if is_vertical else 0)
    play_res_y = 1920 if is_vertical else 1080
    play_res_x = 1080 if is_vertical else 1920
    # Safe margin for TikTok / Reels: place in lower center (above bottom buttons)
    margin_v = 450 if is_vertical else 100

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style['fontname']},{fontsize},{style['primary_colour']},{style['primary_colour']},{style['outline_colour']},{style['back_colour']},{style['bold']},0,0,0,100,100,0,0,{style['border_style']},{style['outline']},{style['shadow']},{style['alignment']},40,40,{margin_v},1
Style: Inactive,{style['fontname']},{fontsize},{style['inactive_colour']},{style['inactive_colour']},{style['outline_colour']},{style['back_colour']},{style['bold']},0,0,0,100,100,0,0,{style['border_style']},{style['outline']},{style['shadow']},{style['alignment']},40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    # 1. Gather all words inside the clip window
    all_words = []
    for seg in segments:
        if seg['end'] <= clip_start or seg['start'] >= clip_end:
            continue
        all_words.extend(split_segment_into_words(seg))

    # Filter to words strictly within the clip boundary
    clip_words = [
        w for w in all_words 
        if w['end'] > clip_start and w['start'] < clip_end
    ]

    if not clip_words:
        return False

    # 2. Group words into punchy 2-3 word chunks (The Viral Reel Pattern)
    dialogues = []
    chunk_size = 3 if is_vertical else 4
    
    for i in range(0, len(clip_words), chunk_size):
        chunk = clip_words[i:i + chunk_size]
        if not chunk:
            continue

        chunk_start = max(0.0, chunk[0]['start'] - clip_start)
        chunk_end = min(clip_end - clip_start, chunk[-1]['end'] - clip_start)
        
        if chunk_end <= chunk_start:
            continue

        # In this chunk, animate each word as it is spoken!
        for active_idx, active_word in enumerate(chunk):
            w_start = max(0.0, active_word['start'] - clip_start)
            w_end = min(clip_end - clip_start, active_word['end'] - clip_start)
            
            if w_end <= w_start:
                continue

            # Build line: active word is highlighted with POP effect!
            line_parts = []
            for idx, w in enumerate(chunk):
                word_text = w['word'].replace('{', '').replace('}', '').strip()
                if template_key == "hormozi":
                    word_text = word_text.upper()

                if idx == active_idx:
                    # ACTIVE WORD: Bouncing pop animation + Highlight color!
                    # \\t(0,80,\\fscx100\\fscy100) bounces down from 125% scale to 100%
                    pop_tag = r"{\rDefault\fscx125\fscy125\t(0,90,\fscx100\fscy100)\c" + style['primary_colour'] + r"}"
                    line_parts.append(f"{pop_tag}{word_text}")
                else:
                    # Inactive word in chunk: Dimmed white
                    dim_tag = r"{\rInactive\c" + style['inactive_colour'] + r"}"
                    line_parts.append(f"{dim_tag}{word_text}")

            full_line_text = " ".join(line_parts)
            dialogues.append(
                f"Dialogue: 0,{format_ass_time(w_start)},{format_ass_time(w_end)},Default,,0,0,0,,{full_line_text}"
            )

    if not dialogues:
        return False

    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(dialogues))
        f.write("\n")

    return True
