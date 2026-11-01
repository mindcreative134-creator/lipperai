import os
import re
import subprocess
from subtitle_engine import generate_ass_subtitles

def sanitize_filename(name: str) -> str:
    """Removes invalid characters for Windows filesystem, keeping clean ASCII."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    clean = re.sub(r'[^\w\s-]', '', clean)
    clean = re.sub(r'\s+', "_", clean).strip("_")
    return clean[:40] if clean else "clip"

def escape_ffmpeg_path(path: str) -> str:
    """Properly escapes Windows file paths for FFmpeg filter arguments."""
    p = os.path.abspath(path).replace('\\', '/')
    p = p.replace(':', '\\:')
    return p

def cut_clip(
    input_video: str,
    start_sec: float,
    end_sec: float,
    output_path: str,
    vertical_crop: bool = False,
    segments: list = None,
    subtitle_template: str = "none"
) -> bool:
    """
    Cuts video between start_sec and end_sec using FFmpeg.
    Burns selected subtitle animation template (Hormozi, Minimal, Neon, Red Box) if enabled.
    """
    duration = end_sec - start_sec
    if duration <= 0:
        return False

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # 1. Generate subtitle file if template selected
    temp_ass = os.path.splitext(output_path)[0] + "_temp.ass"
    has_subtitles = False
    
    if segments and subtitle_template and subtitle_template != "none":
        has_subtitles = generate_ass_subtitles(
            segments, start_sec, end_sec, temp_ass,
            template_key=subtitle_template,
            is_vertical=vertical_crop
        )

    # 2. Build FFmpeg command
    if vertical_crop:
        # Optimized 9:16 vertical conversion (Fast blur on downscaled layer)
        if has_subtitles and os.path.exists(temp_ass):
            sub_filter = escape_ffmpeg_path(temp_ass)
            filter_complex = (
                "[0:v]scale=360:640:force_original_aspect_ratio=increase,crop=360:640,boxblur=12:3,scale=1080:1920[bg];"
                "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,subtitles='{sub_filter}'"
            )
        else:
            filter_complex = (
                "[0:v]scale=360:640:force_original_aspect_ratio=increase,crop=360:640,boxblur=12:3,scale=1080:1920[bg];"
                "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2"
            )

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_sec),
            "-i", input_video,
            "-t", str(duration),
            "-filter_complex", filter_complex,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "128k",
            output_path
        ]
    else:
        # 16:9 Landscape
        if has_subtitles and os.path.exists(temp_ass):
            sub_filter = escape_ffmpeg_path(temp_ass)
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start_sec),
                "-i", input_video,
                "-t", str(duration),
                "-vf", f"subtitles='{sub_filter}'",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "20",
                "-c:a", "aac",
                output_path
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start_sec),
                "-i", input_video,
                "-t", str(duration),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "20",
                "-c:a", "aac",
                output_path
            ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        success = (result.returncode == 0)
    except Exception as e:
        print(f"FFmpeg error: {e}")
        success = False
    finally:
        # Clean up temporary ASS subtitle file
        if os.path.exists(temp_ass):
            try:
                os.remove(temp_ass)
            except Exception:
                pass

    return success

def export_clips(
    video_path: str,
    clips: list,
    output_dir: str = "output_clips",
    vertical: bool = False,
    segments: list = None,
    subtitle_template: str = "hormozi"
) -> list:
    """
    Renders all highlight clips with optional subtitle burning.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated = []
    total = len(clips)
    
    print(f"\n[4/4] Cutting {total} highlight clips (Subtitles: '{subtitle_template}', Vertical: {vertical})...")
    
    for idx, clip in enumerate(clips, start=1):
        start = clip['start']
        end = clip['end']
        duration = round(end - start, 1)
        mins, secs = divmod(int(start), 60)
        
        filename = f"clip_{idx}_{mins:02d}m{secs:02d}s_{int(duration)}s.mp4"
        out_file = os.path.join(output_dir, filename)
        
        print(f"  -> [{idx}/{total}] Cutting: '{clip['title']}' ({duration}s)...")
        success = cut_clip(
            video_path, start, end, out_file,
            vertical_crop=vertical,
            segments=segments,
            subtitle_template=subtitle_template
        )
        
        if success and os.path.exists(out_file):
            print(f"     Saved: {out_file}")
            generated.append(out_file)
        else:
            print(f"     Failed to render clip {idx}")
            
    return generated
