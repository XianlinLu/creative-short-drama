"""Local 2-D edit using a timed script, full-frame artwork, opacity cues and a sound mix."""
import bisect
import math
import os
import shutil
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def encoder():
    binary = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if not binary:
        import imageio_ffmpeg
        binary = imageio_ffmpeg.get_ffmpeg_exe()
    return binary


def font_path(explicit):
    for path in (explicit, os.environ.get("DRAMA_FONT"),
                 "/System/Library/Fonts/Supplemental/Songti.ttc",
                 "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
                 r"C:\Windows\Fonts\simsun.ttc"):
        if path and Path(path).is_file():
            return path
    raise ValueError("请用 --font 指定支持片中文字的 TTF/OTF/TTC 字体")


def curve(keys, duration, opacity=True):
    if not keys or any(len(pair) != 2 for pair in keys):
        raise ValueError("透明度曲线须含 [镜内秒数, 透明度] 关键帧")
    times, values = zip(*keys)
    if (any(not 0 <= t <= duration for t in times)
            or any(b <= a for a, b in zip(times, times[1:]))
            or any(not math.isfinite(v) or (opacity and not 0 <= v <= 1) for v in values)):
        raise ValueError("透明度关键帧时间须递增且位于镜内，透明度范围 0–1")

    def sample(t):
        i = bisect.bisect_right(times, t)
        if i == 0:
            return values[0]
        if i == len(times):
            return values[-1]
        a, b = times[i-1:i+1]
        return values[i-1] + (values[i]-values[i-1]) * (t-a) / (b-a)

    return sample


def artwork(path, size):
    with Image.open(path) as im:
        if im.size != size:
            raise ValueError(f"{path.name} 尺寸 {im.size} 与项目 {size} 不一致")
        return im.convert("RGBA")


def render(p, timeline, root, tmp, font):
    size = tuple(p["size"])
    w, h = size
    fps = p["fps"]
    total = timeline[-1]["end_frame"] / fps
    font = font_path(font)
    subtitle = ImageFont.truetype(font, max(14, round(h*.044)))
    title = ImageFont.truetype(font, max(20, round(h*.106)))
    cmd = [encoder(), "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
           "-pixel_format", "rgb24", "-video_size", f"{w}x{h}", "-framerate", str(fps),
           "-i", "pipe:0"]
    if p.get("audio"):
        audio = root / p["audio"]
        with wave.open(str(audio)) as wav:
            if abs(wav.getnframes()/wav.getframerate()-total) > 1/fps:
                raise ValueError("音轨时长须与时间线对齐到一帧内")
        cmd += ["-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", "128k"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-preset", "veryfast", "-movflags", "+faststart", str(tmp/"film.mp4")]
    sheet = Image.new("RGB", (320*3, 202*math.ceil(len(timeline)/3)), "#182635")
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as proc:
        try:
            for n, shot in enumerate(timeline):
                base = artwork(root / shot["base"], size)
                layers = []
                for layer in shot.get("layers", []):
                    offsets = layer.get("offset", [[0, 0, 0]])
                    x = curve([(t, x) for t, x, y in offsets], shot["seconds"], False)
                    y = curve([(t, y) for t, x, y in offsets], shot["seconds"], False)
                    alpha = curve(layer["opacity"], shot["seconds"])
                    layers.append((artwork(root / layer["file"], size), alpha, x, y))
                z0, z1 = shot.get("zoom", [1, 1])
                if not all(math.isfinite(z) and z >= 1 for z in (z0, z1)):
                    raise ValueError("镜头缩放值须为有限数且至少为 1")
                count = shot["end_frame"] - shot["start_frame"]
                previous, source = None, None
                for i in range(count):
                    t = i/fps
                    amounts = tuple((round(a(t)*255), round(x(t)), round(y(t))) for _, a, x, y in layers)
                    if amounts != previous:
                        composed = base.copy()
                        for (layer, *_), (amount, x, y) in zip(layers, amounts):
                            if amount == 255:
                                composed.alpha_composite(layer, dest=(x, y))
                            elif amount:
                                adjusted = layer.copy()
                                adjusted.putalpha(layer.getchannel("A").point(lambda a: a*amount/255))
                                composed.alpha_composite(adjusted, dest=(x, y))
                        source = composed.convert("RGB")
                        previous = amounts
                    pos = i/max(1, count-1)
                    zoom = z0+(z1-z0)*pos*pos*(3-2*pos)
                    dx, dy = (w-w/zoom)/2, (h-h/zoom)/2
                    img = source.resize(size, Image.Resampling.BICUBIC, box=(dx,dy,w-dx,h-dy))
                    d = ImageDraw.Draw(img)
                    if n == 0 and .4 <= t < 3.8:
                        d.text((w*.49,h*.30),p["title"],font=title,anchor="mm",fill="#f3e8d0",
                               stroke_width=1,stroke_fill="#354454")
                    if shot.get("caption") and .7 <= t < shot["seconds"]-.45:
                        d.text((w*.5,h*.921),shot["caption"],font=subtitle,anchor="mm",
                               fill="#fff4db",stroke_width=2,stroke_fill="#172532")
                    if i == count//2:
                        x,y = n%3*320,n//3*202
                        sheet.paste(img.resize((320,180),Image.Resampling.LANCZOS),(x,y))
                        ImageDraw.Draw(sheet).text((x+7,y+183),f"{shot['id']}   {shot['start_frame']/fps:g} - {shot['end_frame']/fps:g} s",fill="white")
                    proc.stdin.write(img.tobytes())
            proc.stdin.close()
            if proc.wait():
                raise OSError("FFmpeg 编码失败")
        except BaseException:
            proc.kill()
            raise
    sheet.save(tmp/"storyboard.jpg",quality=90)
