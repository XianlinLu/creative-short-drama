import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


from .production import production_notes, write_delivery_index


SKILL = Path(__file__).resolve().parents[1] / "skills" / "seedance-2-5"


def load(path):
    project = json.loads(path.read_text(encoding="utf-8"))
    for key in ("title", "logline", "style", "sound"):
        if not isinstance(project.get(key), str) or not project[key].strip():
            raise ValueError(f"缺少项目文本 {key}")
    width, height = project["size"]
    if any(type(n) is not int or n < 2 or n % 2 for n in (width, height)):
        raise ValueError("画面宽高须为正偶数")
    fps = project["fps"]
    if type(fps) is not int or not 1 <= fps <= 120:
        raise ValueError("帧率须在 1–120 之间")
    ids = set()
    for scene in project["scenes"]:
        if scene["id"] in ids or not all(scene.get(k) for k in ("id", "place", "action")):
            raise ValueError("剧本场次缺字段或编号重复")
        ids.add(scene["id"])
    used, shots = set(), set()
    for s in project["shots"]:
        if s["scene"] not in ids or s["id"] in shots:
            raise ValueError(f"无效镜号或场次 {s['id']}")
        for k in ("id", "camera", "start", "action", "end", "sound"):
            if not isinstance(s.get(k), str) or not s[k].strip():
                raise ValueError(f"{s['id']} 缺少 {k}")
        shots.add(s["id"])
        used.add(s["scene"])
        frames = s["seconds"] * fps
        if frames < 1 or not math.isfinite(frames) or not math.isclose(frames, round(frames), abs_tol=1e-6):
            raise ValueError("镜头时长必须对齐到帧")
    if not shots or used != ids:
        raise ValueError("每场剧本至少需要一个镜头")
    return project


def compile_plan(p):
    elapsed = 0
    timeline = []
    for shot in p["shots"]:
        frames = round(shot["seconds"] * p["fps"])
        timeline.append(dict(shot, start_frame=elapsed, end_frame=elapsed + frames))
        elapsed += frames
    return timeline


def texts(p, timeline):
    script = [f"# {p['title']}", p["logline"]]
    script += [f"## {s['id']}　{s['place']}\n\n{s['action']}" for s in p["scenes"]]
    frames = timeline[-1]["end_frame"]
    board = [f"# 《{p['title']}》定时分镜",
             f"{p['size'][0]} × {p['size'][1]} · {p['fps']} fps · {frames/p['fps']:g} 秒",
             p["style"], p["sound"]]
    for s in timeline:
        board.extend([f"## {s['id']} · 场 {s['scene']} · {s['start_frame']/p['fps']:g}–{s['end_frame']/p['fps']:g} 秒",
                      f"{s['camera']} {s['start']} {s['action']} {s['end']}",
                      f"声音：{s['sound']}\n\n后期字幕：{s.get('caption', '')}"])
    return "\n\n".join(script)+"\n", "\n\n".join(board)+"\n"


HOST = """## 在 Lumina 使用导演工作流

先按[导演工作流](references/director-workflow.md)选择入口。正式单集可将剧本、设定、分镜、图片提示词、视频计划和剪辑单分节保存到画布 Note，沿用同一组场号和镜号。

当用户点名《记忆典当行》或要求学习精剪范例时，读取 memory-pawnshop.md。用户要求运行当前打包项目（如《留灯》）时，读取 project/screenplay.md 和 project/storyboard.md。同目录的 visual-design.md、image-prompts.md、video-plan.md 和 edit-sheet.md 是同版制作草案；在投入生成或剪辑前结合真实素材校正。其他创作任务沿用下文的通用流程。

进入画布后，先用宿主已注册的 ba-canvas 核对当前画布、资源、Seedance 2.5 可用模式、规格与真实提交能力。读取宿主 lumina-canvas-quality 的视频、声音、镜头一致性及需要的剪辑规则，据此复核分镜。若缺少其中任一依赖，报告缺失项和受影响的步骤。不得虚报调用或替换模型。

将剧本和分镜保存到同一份画布 Note。按用户本轮授权和实际报价决定执行范围。若实时模式能一次覆盖全部镜头，优先提交一个含定时分镜的视频任务；若需多轮，按 references/sequential-extension-chain.md 从首段开始，每次只从已就绪的真实上游延长一段。字幕是后期层，使用准确文案。记录真实任务编号和资源状态，按宿主约定交接。输出为累计成片时直接使用；仅在精确字幕、时长或导出需要时进入后期。最终说明实际模型、两项依赖的可用情况、实测时长及真实成片所在节点或导出位置。
"""


def package(path, documents):
    original = (SKILL / "SKILL.md").read_text()
    front, body = original.split("---\n", 2)[1:]
    front = front.replace("name: 'seedance-2-5'", "name: 'creative-short-drama-director'")
    with ZipFile(path, "w", ZIP_DEFLATED) as z:
        z.writestr("SKILL.md", "---\n"+front+"---\n\n"+HOST+"\n"+body)
        z.write(SKILL / "memory-pawnshop.md", "memory-pawnshop.md")
        for ref in sorted((SKILL / "references").glob("*.md")):
            z.write(ref, "references/"+ref.name)
        for name, content in documents.items():
            z.writestr("project/" + name, content)


def main():
    parser = argparse.ArgumentParser(description="生成 Lumina 执行包与定时分镜，或渲染本地动画")
    parser.add_argument("command", choices=["prepare", "render", "finish"])
    parser.add_argument("project", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--font", help="本地渲染中文字幕所用字体")
    parser.add_argument("--source", type=Path, help="finish 使用的完整、无字幕累计源片")
    args = parser.parse_args()
    if (args.command == "finish") != bool(args.source):
        parser.error("finish 命令必须传 --source，其他命令不接受 --source")
    try:
        p = load(args.project)
        timeline = compile_plan(p)
        script, board = texts(p, timeline)
        args.out.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=args.out) as tmp:
            tmp = Path(tmp)
            documents = {"screenplay.md": script, "storyboard.md": board, **production_notes(p, timeline)}
            for name, content in documents.items():
                (tmp / name).write_text(content, encoding="utf-8")
            (tmp/"timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
            from .finish import finish, subtitles
            (tmp/"subtitles.srt").write_text(subtitles(timeline, p["fps"]), encoding="utf-8")
            package(tmp/"lumina-workflow.zip", documents)
            if args.command == "finish":
                finish(p, timeline, args.source, tmp)
            if args.command == "render":
                from .render import render
                render(p, timeline, args.project.resolve().parent, tmp, args.font)
            write_delivery_index(tmp, p["title"])
            files = list(tmp.iterdir())
            for file in files:
                file.replace(args.out / file.name)
        print(f"{p['title']} · {len(timeline)} 镜 · {timeline[-1]['end_frame']} 帧 → {args.out}")
    except (OSError, KeyError, TypeError, ValueError, ImportError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"工作流中止：{exc}\n")


if __name__ == "__main__":
    main()
