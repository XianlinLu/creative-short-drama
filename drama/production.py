"""Compile production notes from the same shot records used for the timeline."""

import hashlib
from html import escape
from urllib.parse import quote


def production_notes(project, timeline):
    look = [f"# 《{project['title']}》视觉与声音设定", project["style"], project["sound"]]
    places = {scene["id"]: scene["place"] for scene in project["scenes"]}
    stills = ["# 分镜静帧提示词草案", "按镜号核对构图和人物身份，再绑定实际可用的参考图。"]
    motion = ["# 视频与声音计划", "以下是按镜规划的节拍。实际生成时按模式组织成段；画布上先完成全员三视图、试音、正式台词及用户确认。每段直连实际用到的角色图、正式台词和本段分镜；续写段另接上一段真实视频，根据实片结尾编写本轮提交词。"]
    edit = ["# 剪辑单草案", "时间码取自分镜。拿到实片后补录素材版本与源入出点，并按实测声音校正字幕。"]
    for scene_id, place in places.items():
        look.append(f"## {scene_id}　{place}")
        for shot in timeline:
            if shot["scene"] == scene_id:
                look.append(f"{shot['id']}　{shot['start']} → {shot['end']}")
    for shot in timeline:
        shot_id = shot["id"]
        place = places[shot["scene"]]
        stills.append(f"## {shot_id} · {place}\n\n{project['style']}\n\n首帧构图：{shot['start']}\n\n收镜构图参考：{shot['end']}")
        motion.append(f"## {shot_id} · {shot['seconds']:g} 秒\n\n{shot['camera']} {shot['start']} {shot['action']} {shot['end']}\n\n声音：{shot['sound']}")
        start = shot["start_frame"] / project["fps"]
        end = shot["end_frame"] / project["fps"]
        edit.append(f"## {shot_id} · 成片 {start:g}–{end:g} 秒\n\n收镜动作：{shot['end']}\n\n声音：{shot['sound']}\n\n字幕：{shot.get('caption') or '无'}")
    sections = {"visual-design.md": look, "image-prompts.md": stills,
                "video-plan.md": motion, "edit-sheet.md": edit}
    return {name: "\n\n".join(lines) + "\n" for name, lines in sections.items()}


def write_delivery_index(folder, title):
    files = sorted(path for path in folder.iterdir() if path.is_file())
    links = "\n".join(f'<li><a href="{quote(p.name)}">{escape(p.name)}</a></li>' for p in files)
    page = (f'<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
            f'<title>{escape(title)} · 本集文件</title><h1>{escape(title)}</h1>'
            f'<ul>{links}</ul><a href="SHA256SUMS">SHA-256 校验清单</a></html>\n')
    index = folder / "index.html"
    index.write_text(page, encoding="utf-8")
    entries = []
    for path in [*files, index]:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        entries.append(f"{digest.hexdigest()}  {path.name}")
    (folder / "SHA256SUMS").write_text("\n".join(entries) + "\n", encoding="utf-8")
