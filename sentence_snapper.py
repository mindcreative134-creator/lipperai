import os
import re

def snap_to_complete_sentences(segments: list, raw_start: float, raw_end: float, min_dur: float = 25.0, max_dur: float = 60.0) -> tuple:
    """
    CRUCIAL: Prevents cutting off mid-sentence!
    Snaps raw start and end timestamps to the natural start and end of spoken sentences.
    Detects punctuation (., ?, !, ।) and conversational pause gaps (>0.7s).
    """
    if not segments:
        return raw_start, raw_end

    # 1. Find best start (start of a sentence or right after a natural pause)
    snapped_start = raw_start
    best_start_diff = 999.0

    for i, seg in enumerate(segments):
        seg_start = seg['start']
        # If segment is near raw_start
        if abs(seg_start - raw_start) < 8.0:
            # Check if previous segment ended with punctuation or there is a pause
            is_sentence_start = False
            if i == 0:
                is_sentence_start = True
            else:
                prev_text = segments[i - 1]['text'].strip()
                prev_end = segments[i - 1]['end']
                pause = seg_start - prev_end
                if any(prev_text.endswith(p) for p in ('.', '?', '!', '।')) or pause >= 0.7:
                    is_sentence_start = True

            diff = abs(seg_start - raw_start)
            if is_sentence_start and diff < best_start_diff:
                best_start_diff = diff
                snapped_start = seg_start

    # 2. Find best end (must finish complete sentence & thought, not cut off mid-word)
    snapped_end = raw_end
    best_end_diff = 999.0

    for i, seg in enumerate(segments):
        seg_end = seg['end']
        seg_text = seg['text'].strip()
        dur_from_start = seg_end - snapped_start

        if min_dur <= dur_from_start <= max_dur:
            is_sentence_end = False
            # Check if current segment finishes sentence or next has long pause
            if any(seg_text.endswith(p) for p in ('.', '?', '!', '।')):
                is_sentence_end = True
            elif i < len(segments) - 1:
                next_start = segments[i + 1]['start']
                if (next_start - seg_end) >= 0.8:
                    is_sentence_end = True

            diff = abs(seg_end - raw_end)
            if is_sentence_end and diff < best_end_diff:
                best_end_diff = diff
                snapped_end = seg_end

    # Ensure duration is valid
    if snapped_end - snapped_start < min_dur:
        snapped_end = min(snapped_start + min_dur, segments[-1]['end'])

    return round(snapped_start, 2), round(snapped_end, 2)

