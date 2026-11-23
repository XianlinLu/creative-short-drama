# Creative Short Drama · 短剧创作流程

Creative Short Drama Director 从小说、参考片、故事点子或已有分集稿进入制作，支持逐集交接、镜头投产和剪辑验收。新增的四份中文导演手册、工作流入口及本地制作文档编译代码由本项目独立创作。

| 你要做什么 | 从哪里开始 |
| --- | --- |
| 按手上的素材选择环节，查看 12 个环节的输入与交付 | [短剧与漫剧导演工作流](skills/seedance-2-5/references/director-workflow.md) |
| 编译剧本和分镜、导入 Lumina、生成和导出成片 | [运行工作流与复验示例](docs/run.md) |
| 学习如何把约九分钟的故事精剪成 116 秒 | [《记忆典当行》七场精剪范例与完整台词](skills/seedance-2-5/memory-pawnshop.md) · [英文预设提示词](docs/preset-prompts.txt) |
| 查看《留灯》的七镜时间线与本地动画 | [70 秒短剧示例](examples/leave-a-light/) |
| 通读全流程，查每一步的输入、产出和回退条件 | [完整链路分析](docs/workflow.md) |
| 使用或移植这套创作 Skill | [Skill 入口与参考文件读取顺序](skills/seedance-2-5/SKILL.md) |
| 从一句话故事写到可拍的短剧分镜 | [影视与叙事](skills/seedance-2-5/references/narrative-film.md) |
| 分镜后制作全员三视图、试音和正式对白，检查每段连线 | [画布人物与对白流程](skills/seedance-2-5/references/cast-and-dialogue.md) |
| 在火山引擎 Lumi 或 BytePlus Lumina 创建、核对与补齐画布连线 | [双画布连线与验收](skills/seedance-2-5/references/canvas-connections.md) |
| 让多个场景沿同一条真实视频逐段延长 | [串行延长与任务恢复](skills/seedance-2-5/references/sequential-extension-chain.md) |

**短剧的典型路径**是先明确人物想得到什么、遇到什么阻碍，再写出行动、对白和结局。创作分镜为每次切镜给出理由，按表演和声音估时。制作阶段才决定哪些镜头能放进同一次生成，哪些需要接着上一段实片延长。

**运行环境**分三层。本仓库提供创作方法与场景规则。原包中的画布执行依赖宿主提供的 `ba-canvas`（资源、节点、提交与恢复）和 `lumina-canvas-quality`（图像、视频与剪辑质量方法）。直接阅读或编写方案只需这些 Markdown 文档。实际生成还需在具备对应能力的环境中核验参数、绑定素材并提交任务。
