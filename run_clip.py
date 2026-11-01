import os
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import transcriber
import analyzer
import cutter

def process_existing():
    video_id = '4m58nVDpoY8'
    video_file = os.path.abspath('downloads/4m58nVDpoY8.mp4')
    
    if not os.path.exists(video_file):
        print(f"Error: {video_file} not found")
        return
        
    print("[1/3] Reading Hindi & English Dialogue Transcript...")
    segments = transcriber.get_video_transcript(video_id)
    print(f"Loaded {len(segments)} dialogue segments!")

    print("\n[2/3] Analyzing Conversation & Finding Real Highlights...")
    clips = analyzer.analyze_with_heuristics(segments, 1150.0, max_clips=3)

    print("\nSelected Real Moments:")
    for idx, c in enumerate(clips, 1):
        dur = round(c['end'] - c['start'], 1)
        mins_start, secs_start = divmod(int(c['start']), 60)
        mins_end, secs_end = divmod(int(c['end']), 60)
        time_str = f"{mins_start:02d}:{secs_start:02d} to {mins_end:02d}:{secs_end:02d}"
        print(f"  Clip #{idx}: [{time_str}] ({dur}s)")
        print(f"    Topic/Dialogue: {c['title']}")
        print(f"    Detail: {c['reason']}\n")

    print("[3/3] Cutting Highlight Clips with FFmpeg...")
    saved_files = cutter.export_clips(video_file, clips, output_dir="output_clips", vertical=False)
    
    print("\n=======================================================")
    print(f"SUCCESS! All {len(saved_files)} clips generated perfectly:")
    for f in saved_files:
        print(f" -> {os.path.abspath(f)}")
    print("=======================================================")

if __name__ == "__main__":
    process_existing()
