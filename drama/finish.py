"""Finish one cumulative source returned by the host with a switchable subtitle track."""
import json
import os
import shutil
import subprocess
from fractions import Fraction


def stamp(frame, fps):
    ms = round(frame*1000/fps)
    hours, tail = divmod(ms, 3600000)
    minutes, tail = divmod(tail, 60000)
    seconds, ms = divmod(tail, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"


def subtitles(shots, fps):
    cues = []
    for s in shots:
        if s.get("caption"):
            cues.append(f"{len(cues)+1}\n{stamp(s['start_frame'], fps)} --> "
                        f"{stamp(s['end_frame'], fps)}\n{s['caption']}\n")
    return "\n".join(cues)


def finish(p, shots, source, tmp):
    probe = os.environ.get("FFPROBE") or shutil.which("ffprobe")
    if not probe:
        raise ValueError("请在 PATH 安装 ffprobe，或用 FFPROBE 指定路径")
    ffmpeg = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if not ffmpeg:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    info = subprocess.run([probe, "-v", "error", "-show_streams", "-of", "json", str(source)],
                          check=True, capture_output=True, text=True)
    streams = json.loads(info.stdout)["streams"]
    video = next((s for s in streams if s["codec_type"] == "video"
                  and not s.get("disposition", {}).get("attached_pic")), None)
    if p.get("audio") and not any(s["codec_type"] == "audio" for s in streams):
        raise ValueError("项目含声音，但源片缺少音轨，请先补齐混音")
    if not video:
        raise ValueError("没有可读取的视频流")
    w, h = p["size"]
    if video["width"]*h != video["height"]*w:
        raise ValueError("源片比例与项目不同，请先确定重新构图方案")
    duration = shots[-1]["end_frame"]/p["fps"]
    video_seconds = float(video.get("duration") or
                          int(video["duration_ts"]) * Fraction(video["time_base"]))
    if video_seconds < duration-0.5/p["fps"]:
        raise ValueError(f"源片只有 {video_seconds:g} 秒，成片需 {duration:g} 秒。请提供完整累计结果")
    cmd = [ffmpeg, "-y", "-v", "error", "-i", str(source)]
    captions = (tmp/"subtitles.srt").stat().st_size > 0
    if captions:
        cmd.extend(["-i", str(tmp/"subtitles.srt")])
    cmd.extend(["-map", f"0:{video['index']}", "-map", "0:a:0?"])
    if captions:
        cmd.extend(["-map", "1:s:0", "-c:s", "mov_text", "-disposition:s:0", "default"])
    cmd += ["-t", str(duration), "-vf", f"fps={p['fps']},scale={w}:{h},setsar=1",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
            "-c:a", "aac", "-movflags", "+faststart", str(tmp/"film.mp4")]
    subprocess.run(cmd, check=True)
