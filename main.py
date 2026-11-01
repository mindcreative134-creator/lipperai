import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from downloader import download_video
from transcriber import get_video_transcript, transcript_to_text_with_timestamps
from analyzer import (
    analyze_with_gemini, 
    analyze_with_heuristics, 
    parse_custom_timestamps, 
    search_topic_moments, 
    split_into_equal_parts
)
from cutter import export_clips

def print_banner():
    banner = """
=============================================================
      AI VIDEO CLIPPER & ANIMATED SUBTITLE STUDIO
=============================================================
  - YouTube Video Download (yt-dlp)
  - Full Hindi & English Transcript Extraction
  - Multi-Modal Audio & Dialogue Engagement Analysis
  - Viral Subtitle Animation Templates (Hormozi, Neon, Minimal)
  - 9:16 Shorts / 16:9 Landscape Video Cutting
=============================================================
"""
    print(banner)

def main():
    print_banner()

    # 1. Ask for Video URL
    url = input("Enter YouTube Video URL: ").strip()
    if not url:
        print("Error: Video URL cannot be empty.")
        return

    # 2. Cutting Mode
    print("\n--- Choose Cutting Mode ---")
    print("  [1] 🤖 Smart Auto Highlights (Audio energy & conversation peaks)")
    print("  [2] 🔍 Search By Topic / Keyword (Cut moments where a specific word was spoken)")
    print("  [3] ⏱️ Custom Timestamps (Give exact start & end times, e.g. 01:30-02:15)")
    print("  [4] ✂️ Consecutive Splitter (Cut video into 60s Part 1, Part 2, Part 3 Reels)")
    mode_choice = input("Enter Mode [1, 2, 3, or 4 - default: 1]: ").strip()
    if not mode_choice:
        mode_choice = "1"

    # Specific mode inputs
    search_query = ""
    custom_timestamps_input = ""
    if mode_choice == "2":
        search_query = input("Enter word/topic to search in video (e.g. fight, intro, game): ").strip()
    elif mode_choice == "3":
        print("Enter timestamps separated by comma (e.g. 01:15-02:00, 05:30-06:15):")
        custom_timestamps_input = input("Timestamps: ").strip()

    # 3. Subtitle Template Choice (User Requested Feature)
    print("\n--- Choose Subtitle Animation Template ---")
    print("  [1] 🟡 Viral Hormozi (Bold Yellow Text + Black Border - Most Viral)")
    print("  [2] ⚪ Clean Minimalist (Crisp White Text + Soft Shadow)")
    print("  [3] 🟢 Neon Cyber (Electric Cyan + Magenta Outline Glow)")
    print("  [4] 🔴 Breaking Red Box (White Text with Red Highlight Box)")
    print("  [5] 🚫 No Subtitles (Clean Video Only)")
    sub_choice = input("Enter Subtitle Template [1 to 5, default: 1]: ").strip()
    template_map = {
        "1": "hormozi",
        "2": "clean_white",
        "3": "neon_cyan",
        "4": "red_box",
        "5": "none"
    }
    subtitle_template = template_map.get(sub_choice, "hormozi")

    # 4. Ask for Clip format
    print("\nSelect Output Format:")
    print("  [1] Vertical Reel/Shorts (9:16) - For Instagram / YouTube Shorts (Default)")
    print("  [2] Original Landscape (16:9) - Standard video")
    fmt_choice = input("Enter choice [1 or 2, default: 1]: ").strip()
    is_vertical = fmt_choice != "2"

    # 5. Number of clips
    clips_count_input = input("\nHow many clips do you want? [default: 3]: ").strip()
    max_clips = int(clips_count_input) if clips_count_input.isdigit() else 3

    # Execute Pipeline
    try:
        # Step 1: Download Video
        video_info = download_video(url, output_dir="downloads")
        video_path = video_info['file_path']
        video_id = video_info['video_id']
        duration = video_info['duration']
        print(f"Downloaded: {video_info['title']} ({round(duration, 1)} seconds)")

        # Step 2: Fetch Transcript
        segments = get_video_transcript(video_id)
        transcript_text = transcript_to_text_with_timestamps(segments)

        # Step 3: Determine Clips
        clips = []
        if mode_choice == "3" and custom_timestamps_input:
            clips = parse_custom_timestamps(custom_timestamps_input)
        elif mode_choice == "2" and search_query:
            clips = search_topic_moments(segments, search_query, clip_duration=40.0, max_clips=max_clips)
            if not clips:
                clips = analyze_with_heuristics(segments, duration, max_clips=max_clips)
        elif mode_choice == "4":
            clips = split_into_equal_parts(duration, part_seconds=60.0, max_parts=max_clips)
        else:
            clips = analyze_with_heuristics(segments, duration, max_clips=max_clips)

        if not clips:
            print("Error: Could not determine clips to cut.")
            return

        print("\n=== CLIPS TO BE GENERATED ===")
        for idx, c in enumerate(clips, start=1):
            dur = round(c['end'] - c['start'], 1)
            print(f"  [{idx}] {c['title']} ({dur}s: {c['start']}s -> {c['end']}s)")

        # Step 4: Cut and Export Clips with Subtitles
        output_dir = "output_clips"
        saved_files = export_clips(
            video_path, clips,
            output_dir=output_dir,
            vertical=is_vertical,
            segments=segments,
            subtitle_template=subtitle_template
        )

        print("\n=============================================================")
        print(f" SUCCESS! Generated {len(saved_files)} clips with '{subtitle_template}' subtitles:")
        print(f" Folder: '{os.path.abspath(output_dir)}'")
        print("=============================================================")
        for f in saved_files:
            print(f"  * {os.path.basename(f)}")

        if sys.platform == "win32":
            os.system(f'explorer "{os.path.abspath(output_dir)}"')

    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
