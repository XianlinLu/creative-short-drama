# 运行短剧工作流

仓库提供两条运行路径。Lumina 路径将创作 Skill、剧本与定时分镜打成一个可导入的 ZIP，由画布里的 Canvas Agent 调用宿主能力生成视频。本地路径按同一份分镜合成二维动画，适合逐镜核对故事、灯光、音效和时间码。

## 一、编译项目

从仓库根目录执行，准备步骤只需 Python 3.9 或更高版本。

```bash
python3 -m drama prepare examples/leave-a-light/project.json --out build/leave-a-light/plan
```

输出包括剧本 `screenplay.md`、定时分镜 `storyboard.md`、逐帧时间线 `timeline.json`、字幕 `subtitles.srt`、制作草案和 `lumina-workflow.zip`。ZIP 根目录的 `SKILL.md` 提供画布执行入口，同层的 `memory-pawnshop.md` 收录《记忆典当行》精剪范例与完整中文剧本。`references/` 包含导演总流程、三份阶段手册、人物与对白连线手册和 13 份专项参考。`project/` 装入同一版剧本、定时分镜、视觉设定、静帧提示词、视频与声音计划和剪辑单草案。后四项根据分镜编译，真实视频回执、素材入出点和声音校时在制作时填写。打开输出目录的 `index.html` 可浏览本次构建产物，在该目录运行 `shasum -a 256 -c SHA256SUMS` 可逐文件复验。

[《留灯》项目源文件](../examples/leave-a-light/project.json)维护故事、场次和镜头之间的映射。每镜写明所属场、时长、镜头、起点、事件、终点和声音。编译器检查场次引用、镜号唯一性、全场覆盖和帧对齐，再由镜头顺序累计全片时间码。脚本和镜头由创作者或宿主创作 Skill 编写，改稿时重新编译同一份项目。可以只准备剧本、分镜和执行包，无需先绘制本地动画素材。

## 二、在 Lumina 执行生成

1. 进入目标画布的 Canvas Agent。打开 **Skill → Create Skill → Import Local Skills → Upload zip archive**，选择上一步的 ZIP。新建草稿自带空白 SKILL.md 时，用包内入口替换。名称填写 **Creative Short Drama Director**。将[英文预设](preset-prompts.txt)填入 Preset Prompts，补上简介后保存到 My Skills。
2. 在该 Skill 的详情中点 **Use Skills**，确认输入框出现 Skill 标签。仅制作方案可用 Manual mode；要提交实际生成，选择 **Auto mode**。
3. 对《留灯》，可发送“运行随包《留灯》七镜 70 秒版本。先保存剧本和分镜 Note，读取 ba-canvas 与 lumina-canvas-quality，核对 Seedance 2.5。按 16:9、纯效果音、无配乐无人声、中文后期字幕制作一条片。”同时给出自己的执行与费用范围。
4. 画布先读取两项宿主依赖，发现当前模型能力，建立同版 Note，逐人制备三视图、试音和剧本实际用到的对白；整套获得确认后才连接本段分镜、角色与素材并建立首段视频任务。实际尺寸、可选时长和延长输出以本次画布返回为准。记录返回的任务号。手动模式只建好节点时，可在切换 Auto mode 后要求运行已有节点。
5. 按宿主交接规则恢复原任务。要求“查询当前任务；已就绪则读取实片边界，并继续下一段”。每次使用真实上游延长，直到所需素材齐备。若宿主不可延长，按实际能力与授权决定是否调整路线。网络中断时先查原任务，避免重复提交。
6. 核对延长结果是否包含前段，使用完整来源加字幕、复核时长并导出。项目分镜页、任务提交回执、可播放视频和最终导出文件各自代表不同阶段。

画布通过宿主内部的 Skill 名称加载依赖，执行口是 Canvas Agent。个人库里的 Skill 可复用。更换项目时重新导入该项目的执行包或替换其中同一版本的项目文档。请在自己有权使用的画布内运行，仓库不保存登录态、任务编号或临时媒体地址。

## 三、本地渲染并复验

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m drama render examples/leave-a-light/project.json --out build/leave-a-light/local
```

得到带中文字幕和音效的 `film.mp4`、七镜取样图 `storyboard.jpg` 及同版的制作文件。示例自带原创剪纸图层和 70 秒 WAV 混音。本地合成使用图层透明度、位移、镜头缩放和定时字幕。自定义本地项目时，每镜的 `base` 和可选的 `layers[].file` 指向与项目尺寸一致的图片。透明度关键帧是 `[镜内秒数, 0到1的值]`，位移关键帧是 `[镜内秒数, x像素, y像素]`。音轨可选，提供时使用与项目时长一致的 PCM WAV。可用 `--font /path/to/font.ttc` 指定中文字体。

## 四、已有完整画布源片时收尾

如果画布已导出含字幕的合成结果，直接检验该文件。若拿到的是**覆盖全片的无字幕累计源片**，也可以本地收尾。此命令保留源片声音，按项目帧率和画幅编码，写入默认启用、可关闭的字幕轨。短于目标的源片会被拒绝。

```bash
python -m drama finish examples/leave-a-light/project.json \
  --source /path/to/cumulative-film.mp4 --out build/leave-a-light/final
ffprobe -v error -count_frames -show_entries \
  stream=codec_name,width,height,r_frame_rate,nb_read_frames,duration \
  -of json build/leave-a-light/final/film.mp4
```

`finish` 需要 FFprobe 与 FFmpeg。可在 PATH 安装，或用 `FFPROBE`、`FFMPEG` 指定可执行文件。示例目标为 1280 × 720、24 fps、1680 帧、70 秒。使用不同输出目录，便于对照画布生成版与本地动画版。
