# FFXIV XivPlan 自动图文攻略 Codex Skill 完整计划

## 0. 总目标

本项目要构建一个 **本地 Codex Skill + 本地 XivPlan 改造版 + 攻略导出流水线 + 新副本快速攻略生产工作流**，用于把自然语言 FF14 / FFXIV 机制描述、时间轴、开荒观察、队伍约束和参考机制，快速转成优美、可执行、可迭代、可导出的图文攻略。

长期总目标不是只把一个已知机制画出来，而是让 Skill 能参与新副本攻略制作：

1. 用户输入新副本的机制流程、读条顺序、点名规则、场地变化、队伍配置、限制条件和开荒观察。
2. Skill 把输入拆成机制时间轴、机制 IR、未知信息清单、候选机制类别和可类比机制。
3. Skill 检索 4.x+ 零式 / 绝本机制知识库，判断哪些原则可迁移、哪些站位不能照搬。
4. Skill 主动提出多个解法候选，比较安全性、近战 uptime、读条职业移动、记忆成本、容错、图面复杂度和野队可交流性。
5. Skill 生成结构化 scene spec，并拆成多 step XivPlan 图。
6. 本地脚本生成 `.xivplan`、导出 step PNG，并组装 Markdown / DOCX / PDF 攻略包。
7. 每一轮输出都带质量门检查、未知点、版本号和下一轮开荒需要验证的问题。

短期最大目标：支持 **FFXIV 马上要开启的新绝本「绝妖星乱舞」攻略制作**。

在绝妖星乱舞开荒场景中，本项目要优先做到：

- 可以把用户持续补充的机制流程快速整理成阶段化时间轴。
- 可以在信息不完整时先产出“可用草案”，同时明确标出未确认点。
- 可以基于既有绝本 / 零式机制库做类比，例如塔、分摊、散开、连线、Limit Cut、Hello World、Light Rampant、运动会、颜色 / 数字优先级等。
- 可以为同一机制给出至少两个解法候选，并说明推荐理由与风险。
- 可以把推荐解法快速画成 XivPlan，多 step 展示观察点、移动路径、判定站位、复位点。
- 可以随着开荒信息更新，稳定迭代同一机制包，而不是每次重画。

最终效果：

1. 用户输入机制文字，例如“类似 P12S 门神的 Paradeigma + M6S 动物分组，要求近战尽量不离 Boss”。
2. 用户也可以输入新副本流程，例如“P1 00:18 四塔，00:31 双分摊，00:42 Boss 转向后出东西安全区，点名规则暂不确定”。
3. Codex Skill 自动理解机制类型、相似机制、基础站位、职能分工、解法目标和未确认点。
4. Skill 主动提出或选择优化解法，例如减少读条职业移动、降低记忆成本、保证近战可打到、减少交叉线和临场判断。
5. Skill 生成机制 IR、时间轴 IR、候选方案报告和结构化 XivPlan scene spec。
6. 本地脚本生成 `.xivplan`。
7. 本地改造版 XivPlan 打开并可继续编辑该 `.xivplan`。
8. XivPlan 支持导入本地 PNG / image2 生成 PNG 作为攻略素材。
9. XivPlan 或脚本导出每一步图像。
10. Skill 把图像与文字说明整合为 Markdown / DOCX / PDF 攻略包。
11. 质量门脚本检查 `.xivplan`、PNG、图文一致性和攻略包完整性。
12. 对绝妖星乱舞这类新副本，Skill 输出可版本化的开荒攻略包：`v0.1 草案 -> v0.2 实测修正 -> v1.0 稳定打法`。

这个系统不是只写提示词，而是一个可长期扩展的攻略生产工具链。

## 1. 本地现状

### 1.1 工作区

当前项目目录：

```text
.
```

当前 Codex Skill 草案：

```text
xivplan-ffxiv-guide/
```

本地 XivPlan 仓库：

```text
../XivPlan
```

可参考的已有 XivPlan 成品：

```text
external local FRU strategy files, not vendored in this repository
```

### 1.1.1 文件命名规范

本工作区统一使用英文文件名与目录名。

规则：

- 目录名：`kebab-case`，例如 `generated-xivplan`。
- Markdown / JSON / `.xivplan` 文件：`kebab-case`，例如 `tower-cardinals.spec.json`。
- Python 脚本：Python 生态标准 `snake_case`，例如 `build_xivplan_scene.py`。
- Codex 固定入口：保留 `SKILL.md`。
- Codex UI 元数据：保留 `agents/openai.yaml`。
- 不保留 `__pycache__`、`.pyc`、临时 build 缓存等生成缓存。
- 生成样例统一放在顶层 `artifacts/`，不混入 skill 本体。

### 1.2 已有 Skill 能力

已完成：

- `SKILL.md`：基础 Codex Skill 入口。
- `references/style-and-terms.md`：基础国服术语、方向、职能约定。
- `references/xivplan-scene-format.md`：本地 `.xivplan` JSON 结构参考。
- `scripts/validate_xivplan_scene.py`：基础 `.xivplan` 校验。
- `scripts/build_xivplan_scene.py`：从简化 spec JSON 生成 `.xivplan`。
- `assets/specs/*.spec.json`：四塔、分摊散开、击退、连线样例。
- `artifacts/generated-xivplan/*.xivplan`：当前回归生成物。

已验证：

- `quick_validate.py xivplan-ffxiv-guide` 通过。
- 四个生成 `.xivplan` 均通过 `validate_xivplan_scene.py`。

### 1.3 本地 XivPlan 当前能力

从源码观察到：

- `.xivplan` 是普通 JSON，保存时直接写出 scene。
- 对象类型已包含 `party`、`enemy`、`marker`、`tower`、`stack`、`circle`、`cone`、`line`、`rect`、`donut`、`polygon`、`starburst`、`arrow`、`tether`、`text` 等。
- 已有背景图 `backgroundImage` 支持。
- 已有对象 `image` 字段，`party` / `marker` / `icon` 都可加载图片 URL。
- 当前属性面板只有 `Image URL` 文本框，没有友好的本地 PNG 上传按钮。
- 当前截图功能主要是复制当前 step 到剪贴板，缺少“批量导出所有步骤 PNG + 攻略包”的完整流程。

### 1.4 KING X / Strats_limited 风格观察

抽样统计显示：

- FRU 成品通常使用圆形 600x600 场地。
- 常用背景包括 `/arena/e11.svg`、`/arena/e8.svg` 等。
- 复杂攻略文件可达 10+ steps、500+ objects。
- 常见对象组合：
  - `marker` 用于场地标点。
  - `party` 用于玩家和职业图标。
  - `text` 用于中文说明和角色标签。
  - `circle`、`rect`、`cone`、`tower`、`polygon`、`starburst` 表示机制范围。
  - `arrow` 表示移动路线。
- 成品特点：
  - 每一步图像表达一个明确判定或移动阶段。
  - 图上文字较密，但直接说明判断轴、分工和移动。
  - 大量复用 A/B/C/D/1/2/3/4 标点。
  - 复杂机制会把“观察点”“安全区”“移动路线”“最终站位”拆成多张图。

这些文件应作为本项目的审美和信息密度基准。

## 2. 目标架构

```text
用户自然语言输入
        │
        ▼
Codex Skill: 机制理解与检索
        │
        ├── 基础机制知识库
        ├── 4.x+ 零式 / 绝本机制库
        ├── 站位与国服术语库
        └── 解法优化规则库
        │
        ▼
机制解析 IR
        │
        ▼
解法候选生成 + 优化评分
        │
        ▼
XivPlan scene spec JSON
        │
        ▼
build_xivplan_scene.py
        │
        ▼
.xivplan 文件
        │
        ├── 本地 XivPlan 打开 / 编辑
        ├── 本地 PNG / image2 素材导入
        └── 批量导出步骤图
        │
        ▼
guide_assembler.py
        │
        ├── Markdown 攻略
        ├── DOCX 攻略
        └── PDF 攻略
```

## 3. 核心能力要求拆解

## 3.1 基础机制知识

Skill 需要内置或可检索以下基础机制类型。

### 3.1.1 基础伤害与站位机制

- 分摊：单体分摊、多人分摊、双分摊、连续分摊、小队分摊。
- 分散：八方散开、固定散开、随机点名散开、近远散开。
- 死刑：单T死刑、双T死刑、换T死刑、共享死刑、无敌处理。
- 全屏 AoE：减伤提示、治疗压力、复位窗口。
- 顺劈 / 扇形：Boss 朝向、背后安全、侧面安全。
- 钢铁 / 月环：靠外、靠内、远离、贴近。
- 直线 / 圆形 / 甜甜圈 / 扇形 / 十字 / X 字 AoE。
- 击退 / 拉入：来源、落点、防击退、墙边危险、二段击退。
- 背对 / 看向：眼睛机制、凝视、视线切断。
- 塔：单人塔、多人塔、职能塔、颜色塔、踩塔后移动。
- 连线：远近线、短线、长线、交叉限制、拉断线、传毒线。
- Debuff：颜色、数字、倒计时、先后顺序、同异色、正负极。
- 诱导：地火、扇形、圆圈、点名、最近/最远/仇恨诱导。
- 传递：传毒、传火、交接线、Debuff 交换。
- 旋转：顺逆时针、场地旋转、Boss 旋转、相对方位。
- 复制/镜像：分身、镜像、延迟 AoE、记忆判定。
- 跳舞机制：多轮顺序记忆、多阶段移动、读条前预站。

### 3.1.2 基础站位模板

必须内置：

- 八方固定站位。
- 时钟散开。
- 近远散开。
- TH / DPS 对半。
- MT/ST/H1/H2/D1-D4 固定优先级。
- 灯位 / 颜色 / 数字优先级。
- 东西南北四塔分配。
- 东西南北双人塔分配。
- 小队 4/4 分组。
- 2 人组 / 4 对搭档。
- Boss 北拉 / 中央固定 / 边缘固定。
- 近战内圈、远程外圈。
- 野队宏式位置与固定队自定义位置。

### 3.1.3 基础表达规则

每个机制条目至少记录：

```yaml
mechanic_id:
  cn_names: []
  en_names: []
  category: spread/stack/tower/tether/...
  required_inputs: []
  common_solutions: []
  diagram_patterns: []
  failure_modes: []
  optimization_hooks: []
```

## 3.2 4.x 之后零式 / 绝本机制知识

目标不是让模型凭空背诵，而是建立可检索、可维护、可验证的机制库。

### 3.2.1 覆盖范围

优先级：

1. 绝本：
   - UCOB
   - UWU
   - TEA
   - DSR / DSU
   - TOP
   - FRU
2. 零式：
   - Omega Savage / O 系列
   - Eden Savage / E 系列
   - Pandaemonium Savage / P 系列
   - Arcadion Savage / M 系列
3. 常用类比机制：
   - 光暴 / Light Rampant 类。
   - Hello World 类。
   - Limit Cut 类。
   - Exaflare / 地火类。
   - 大运动会 / 多阶段跳舞机制。
   - 分身延迟 / 镜像复制类。
   - 线与塔组合类。
   - 颜色 / 数字 / 顺逆优先级类。

### 3.2.2 机制库条目格式

每个典型机制建立独立文件，建议路径：

```text
xivplan-ffxiv-guide/references/encounters/
├── ultimates/
│   ├── tea.md
│   ├── dsr.md
│   ├── top.md
│   └── fru.md
├── savage/
│   ├── omega.md
│   ├── eden.md
│   ├── pandaemonium.md
│   └── arcadion.md
└── index.md
```

条目模板：

```markdown
## 机制名

- 副本：
- 阶段：
- 常见别名：
- 机制类别：
- 原理：
- 默认解法：
- 常见优化：
- 常见失误：
- 可类比机制：
- XivPlan 图示拆分：
- 需要确认的信息：
- 参考来源：
- 置信度：
```

### 3.2.3 “类似 XXXX 机制”检索逻辑

当用户说“类似 XXXX 副本中的 XXXX 机制”时：

1. 从机制库按副本名、机制名、别名检索。
2. 若名称模糊，检索同类机制。
3. 输出“我理解你指的是哪类机制”。
4. 抽取它的机制原理，不照搬站位。
5. 根据当前输入重构适配解法。
6. 标注未确认点，例如人数、点名规则、AoE 尺寸、判定顺序。

## 3.3 解法优化能力

Skill 必须主动比较解法，不只把用户文字机械画出来。

### 3.3.1 优化目标

按默认权重：

| 目标 | 说明 | 默认权重 |
|---|---|---|
| 机制安全 | 避免站位冲突、重叠、误判 | 最高 |
| 读条职业移动少 | BLM / PCT / SMN / RDM / Healer 尽量少跑 | 高 |
| 近战可打到 | 近战尽量保持 Boss 目标圈内 | 高 |
| 记忆成本低 | 固定位置、少换位、少临场排序 | 高 |
| 容错高 | 安全区大，路径不交叉，失败可读性强 | 中高 |
| 野队可交流 | 口诀短，宏能描述 | 中 |
| 图面美观 | 图清晰、少遮挡、颜色一致 | 中 |

### 3.3.2 优化输出

对于复杂机制，输出：

```markdown
## 解法选择

### 候选 A：最少移动
- 优点：
- 缺点：

### 候选 B：最低记忆成本
- 优点：
- 缺点：

### 推荐方案
- 推荐理由：
- 牺牲点：
```

### 3.3.3 约束输入

支持用户提供：

- 队伍职业组成。
- 哪些职业不想移动。
- 近战是否必须保持身位。
- 国服野队宏习惯。
- 固定队自定义站位。
- 是否允许换位。
- 是否允许防击退。
- 是否优先照搬已有攻略。

## 3.4 XivPlan 图像质量标准

参考 `KING X\0523-0524 FRU\Strats_limited`。

### 3.4.1 图示拆分原则

一张图只表达一个主要信息：

1. 初始站位。
2. 机制出现 / 观察点。
3. 判断规则。
4. 移动路径。
5. 判定站位。
6. 复位或下一机制衔接。

复杂机制必须拆成多 step，不把所有信息塞进一张图。

### 3.4.2 图面元素标准

| 元素 | 标准 |
|---|---|
| 场地 | 使用真实或近似 arena 背景，保持 600x600 基准 |
| 标点 | A/B/C/D/1/2/3/4 清晰固定 |
| 玩家 | 角色标签与职业图标尽量不遮挡机制范围 |
| Boss | 目标圈、朝向、分身名称清楚 |
| 安全区 | 使用绿色或低透明度高亮 |
| 危险区 | 使用红/橙/紫半透明 |
| 移动箭头 | 蓝色或白色，方向明确，避免交叉 |
| 文字 | 简短，不遮挡关键判定点 |
| 图层 | 背景 -> AoE -> Boss/机制 -> 玩家 -> 箭头 -> 文本 |

### 3.4.3 可复用风格模板

应从现有 FRU `.xivplan` 中提取：

- 常用颜色。
- 常用字体大小。
- 标点半径与位置。
- 玩家图标大小。
- 文本描边样式。
- 安全 / 危险区域透明度。
- 复杂机制多 step 命名方式。

## 4. 本地 XivPlan 源码改造计划

这部分属于相邻本地 XivPlan checkout（通常为 `../XivPlan`）的内容；本仓库只保存 skill 与生成流水线。

## 4.1 本地 PNG 导入功能

### 现状

当前 `ImageControl.tsx` 只有 `Image URL` 输入框。

已有对象 `image` 字段可以加载 URL，因此本地 PNG 功能可通过以下方式实现：

1. 选择本地 PNG。
2. 读取为 `data:image/png;base64,...`。
3. 写入对象的 `image` 字段。
4. `.xivplan` 保存时携带 data URL，保证可移植。

### 目标能力

在 XivPlan 中：

- 对 `marker` / `icon` / `party` / 后续自定义 image object，提供 “Choose local PNG” 按钮。
- 支持拖拽 PNG 到画布创建图片对象。
- 支持调整大小、旋转、透明度、命名。
- 支持 image2 生成的 PNG 直接导入。
- 保存 `.xivplan` 后，无需原文件也能显示图片。

### 源码修改点

建议新增：

```text
src/file/image.ts
src/panel/properties/LocalImageButton.tsx
src/prefabs/CustomImage.tsx
src/panel/AssetPanel.tsx
```

修改：

```text
src/panel/properties/ImageControl.tsx
src/scene.ts
src/panel/DrawPanel.tsx 或 MainToolbar.tsx
src/render/ObjectRegistry.ts
```

### 验收

- 能从本地选择 `png`。
- 能嵌入到 `.xivplan`。
- 重启 XivPlan 后图片仍显示。
- 截图导出中图片显示正常。

## 4.2 XivPlan spec 导入功能

### 目标

让本地 XivPlan 能直接打开或导入 Skill 生成的 spec JSON，而不是只能外部脚本生成 `.xivplan`。

### 方案

最小方案：

- 继续由 Codex 脚本生成 `.xivplan`。
- XivPlan 只负责打开 `.xivplan`。

增强方案：

- XivPlan 增加 `Import Guide Spec`。
- 读取 `.xivplan-spec.json`。
- 前端调用同等 TypeScript builder 转成 scene。
- 用户可在 UI 中继续编辑。

建议先做最小方案，再做增强方案。

## 4.3 批量截图导出

### 现状

当前 `StepScreenshotButton.tsx` 支持当前 step 截图到剪贴板。

### 目标

新增：

- 导出当前 step 为 PNG 文件。
- 导出所有 steps 为 PNG zip。
- 生成 `manifest.json`，包含 step 编号、标题、图片文件名。
- 可选导出透明背景 / 带场地背景。
- 可选 1x / 2x / 4x。

### 源码修改点

```text
src/StepScreenshotButton.tsx
src/file/blob.ts
src/render/SceneRenderer.tsx
```

可复用已有 `client-zip` 依赖。

### 验收

- 一个 10 step `.xivplan` 可导出 10 张 PNG。
- 图片命名稳定：`step_01_initial.png`。
- 所有外部图片加载完成后再截图。
- 导出的 PNG 能进入 Markdown / DOCX / PDF。

## 4.4 攻略包导出

XivPlan 内部可先只导出图片；攻略包组装由 Codex Skill 脚本完成。

后续可在 XivPlan 增加：

- `Export Guide Package`
- 选择 `.guide.json`
- 输出 zip：`guide.md` + `images/` + `guide.pdf`

## 5. Skill 目录重构计划

当前 skill 需要从 MVP 升级为可长期维护结构。

建议最终结构：

```text
xivplan-ffxiv-guide/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── style-and-terms.md
│   ├── mechanic-taxonomy.md
│   ├── positioning-patterns.md
│   ├── solution-optimization.md
│   ├── solution-candidate-format.md
│   ├── xivplan-scene-format.md
│   ├── xivplan-style-guide.md
│   ├── guide-output-templates.md
│   ├── image-asset-workflow.md
│   └── encounters/
│       ├── index.md
│       ├── coverage-audit.md
│       ├── savage/
│       │   ├── omega.md
│       │   ├── eden.md
│       │   ├── pandaemonium.md
│       │   └── arcadion.md
│       └── ultimates/
│           ├── ucob.md
│           ├── uwu.md
│           ├── tea.md
│           ├── dsr.md
│           ├── top.md
│           └── fru.md
├── assets/
│   ├── templates/
│   ├── specs/
│   ├── optimization/
│   ├── sample-guides/
│   └── style-examples/
└── scripts/
    ├── build_xivplan_scene.py
    ├── validate_xivplan_scene.py
    ├── score_solution_candidates.py
    ├── test_solution_optimizer.py
    ├── summarize_xivplan_scene.py
    ├── export_xivplan_steps.py
    ├── assemble_guide.py
    ├── build_docx.py
    └── build_pdf.py
```

`SKILL.md` 继续保持短，只导航到这些资源。

## 6. 自然语言理解与中间格式

## 6.1 输入类型

支持：

- 单机制描述。
- 多阶段机制描述。
- “类似某副本某机制”的类比输入。
- 外文攻略片段。
- 现有 `.xivplan`。
- 截图或用户草图。
- 队伍职业配置。
- 输出格式要求。

## 6.2 机制解析 IR

自然语言先转成机制 IR：

```json
{
  "encounter_context": {
    "fight": "unknown",
    "phase": "unknown",
    "similar_to": ["P12S Paradeigma"]
  },
  "mechanic": {
    "name": "机制名",
    "categories": ["tower", "spread", "stack"],
    "timeline": [],
    "actors": [],
    "debuffs": [],
    "aoes": [],
    "resolution_rules": []
  },
  "party": {
    "roles": ["MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4"],
    "jobs": {},
    "preferences": {}
  },
  "constraints": {
    "minimize_caster_movement": true,
    "keep_melee_uptime": true,
    "reduce_memory_load": true
  },
  "unknowns": []
}
```

## 6.3 XivPlan Scene Spec

IR 再转成 XivPlan scene spec：

```json
{
  "name": "机制名",
  "arena": { "shape": "circle", "size": 600, "backgroundImage": "/arena/e11.svg" },
  "style": "king-x-fru",
  "steps": [
    {
      "title": "图 1：初始站位",
      "guide_text": "这一图说明机制开始前站位。",
      "objects": []
    }
  ]
}
```

每个 step 必须带：

- `title`
- `purpose`
- `objects`
- `guide_text`
- `checks`

## 7. 图文攻略输出

## 7.1 Markdown

默认输出目录：

```text
outputs/<机制名>/
├── guide.md
├── guide.docx
├── guide.pdf
├── scene.xivplan
├── spec.json
└── images/
    ├── step_01.png
    ├── step_02.png
    └── step_03.png
```

Markdown 格式：

```markdown
# 机制名

## 一句话概括

## 推荐解法

## 图 1：初始站位
![图 1](images/step_01.png)

图文说明……

## 图 2：处理过程
![图 2](images/step_02.png)

图文说明……

## 职能分工

## 常见失误

## 队内速记版

## 口诀

## 需要确认的点
```

## 7.2 DOCX

DOCX 需求：

- 标题层级清晰。
- 图片居中。
- 图片下方图注。
- 表格用于职能分工。
- 可插入“队内速记版”灰底文本框。

实现路径：

- `scripts/build_docx.py`
- 输入 `guide.md` 或 `guide.json`
- 输出 `guide.docx`

## 7.3 PDF

PDF 需求：

- 与 Markdown / DOCX 内容一致。
- 图片尺寸稳定。
- 支持中文字体。
- 支持适合分享的 A4 版式。

实现路径：

优先：

- Markdown -> HTML -> Playwright print PDF。

备选：

- DOCX -> PDF。
- Pandoc / wkhtmltopdf，如本机可用。

## 8. image2 素材生成与导入

## 8.1 使用场景

当 XivPlan 内置素材不足时，用 image2 生成 PNG，例如：

- O8S 鬼头。
- M6S 动物。
- 特殊 Boss 分身。
- 特殊机制图标。
- 自定义颜色 / 形态标记。

## 8.2 工作流

```text
机制需要特殊素材
        │
        ▼
Codex 生成素材 brief
        │
        ▼
image2 生成 PNG
        │
        ▼
人工/自动审核：透明背景、可读性、无多余文字
        │
        ▼
保存到 outputs/<机制名>/assets/
        │
        ▼
XivPlan 本地 PNG 导入
        │
        ▼
.xivplan 内嵌 data URL
```

## 8.3 素材标准

- 透明背景优先。
- 单个机制物件居中。
- 轮廓清晰。
- 适合缩放到 32-96 px。
- 不带不必要文字。
- 保持 FF14 攻略图标风格，但不直接复制受版权保护图像。

## 8.4 Skill 侧参考文件

新增：

```text
references/image-asset-workflow.md
assets/image-prompts/
```

## 9. 校验与质量门

## 9.1 机制逻辑校验

必须检查：

- 8 人是否都被分配。
- 塔人数是否匹配。
- 分摊人数是否匹配。
- 散开距离是否足够。
- 连线是否交叉。
- 箭头方向是否与文字一致。
- 安全区与危险区是否冲突。
- 复位点是否明确。

## 9.2 XivPlan 文件校验

扩展 `validate_xivplan_scene.py`：

- 检查 scene-wide id 唯一。
- 检查 tether 端点存在。
- 检查 image data URL 合法。
- 检查每个 step 是否至少有说明标题。
- 检查文本是否超长。
- 检查对象是否明显越界。
- 检查玩家是否重叠。

## 9.3 图像导出校验

新增：

- PNG 文件存在。
- PNG 非空。
- 尺寸符合预期。
- 每个 step 有对应图片。
- 图片中对象加载完成后再导出。

## 9.4 攻略文本校验

检查：

- 图文编号一致。
- 图中位置与文字一致。
- 职能分工表与正文一致。
- 速记版不与完整版冲突。
- 不确定信息明确列出。

## 10. 实施阶段

## Phase 0：需求冻结与样例基线

目标：固定当前需求和参考风格。

任务：

- [x] 重写本计划为完整工程计划。
- [x] 选 3-5 个 `Strats_limited` 文件作为黄金样例。
- [x] 写 `references/xivplan-style-guide.md`。
- [x] 写 `references/solution-optimization.md` 初版。

完成标准：

- 能明确什么叫“像 KING X 成品一样好看”。

## Phase 1：本地 XivPlan PNG 导入

目标：实现本地 PNG 素材导入与内嵌。

任务：

- [x] 修改 `ImageControl.tsx`，增加本地 PNG 选择按钮。
- [x] 新增读取 PNG 为 data URL 的工具。
- [x] 对 `marker` / `icon` / `party` 支持本地图片。
- [x] 可选新增 `customImage` prefab。
- [x] 验证 `.xivplan` 保存后图片仍可显示。

完成标准：

- 用 image2 或任意本地 PNG 生成一个机制物件，并在 XivPlan 中保存、重开、截图正常。

## Phase 2：批量导出步骤图

目标：XivPlan 可导出攻略所需图片。

任务：

- [x] 修改 `StepScreenshotButton.tsx` 或新增导出模块。
- [x] 支持当前 step 保存 PNG。
- [x] 支持所有 steps 打包 zip。
- [x] 输出 `manifest.json`。
- [x] 支持 1x / 2x / 4x。

完成标准：

- 任意多 step `.xivplan` 可导出完整图片序列。

## Phase 3：机制知识库

目标：从“知道基础机制”开始，逐步覆盖 4.x+ 零式与绝本。

任务：

- [x] 写 `mechanic-taxonomy.md`。
- [x] 写 `positioning-patterns.md`。
- [x] 写 `encounters/index.md`。
- [x] 先建立 FRU / TOP / DSR / TEA 机制条目。
- [x] 再建立 Eden / Pandaemonium / Arcadion 条目。
- [x] 补 Omega 典型机制条目。
- [x] 补 UCOB / UWU 机制条目。
- [x] 审计并补齐 Omega / Eden / Pandaemonium / Arcadion 逐楼层典型机制覆盖。

完成标准：

- 用户说“类似某机制”时，Skill 能定位原理、常用解法、可迁移部分和不应照搬的部分。

## Phase 4：解法优化器

目标：从用户输入生成多个可行方案并推荐一个。

任务：

- [x] 定义 `solution_score`。
- [x] 实现移动成本估计。
- [x] 实现近战 uptime 检查。
- [x] 实现读条职业移动惩罚。
- [x] 实现记忆成本评分。
- [x] 实现图面复杂度评分。

完成标准：

- 同一机制可输出至少两个候选方案，并说明推荐理由。

## Phase 5：XivPlan scene spec 生成增强

目标：从机制 IR 生成高质量多 step XivPlan。

任务：

- [x] 扩展 `build_xivplan_scene.py` 支持更多对象。
- [x] 支持 marker presets。
- [x] 支持 arena presets。
- [x] 支持 image object。
- [x] 支持每 step 的 guide text。
- [x] 支持复制上一 step 并局部修改。
- [x] 支持从 `Strats_limited` 风格模板继承默认样式。

完成标准：

- 对基础机制能直接生成 3-6 step 美观图。

当前验收样例：

- `xivplan-ffxiv-guide/assets/specs/phase5-multistep-style.spec.json`
- `artifacts/generated-xivplan/phase5-multistep-style.xivplan`
- 验证结果：4 steps，102 objects，包含 `marker` / `tower` / `circle` / `rect` / `polygon` / `donut` / `starburst` / `arrow` / `guide_text`。

## Phase 6：攻略包组装

目标：图片和文字整合为 Markdown / DOCX / PDF。

任务：

- [x] 设计 `guide.json`。
- [x] 实现 `assemble_guide.py`。
- [x] 实现 Markdown 输出。
- [x] 实现 DOCX 输出。
- [x] 实现 PDF 输出。
- [x] 支持只输出速记版。

完成标准：

- 一个输入机制生成完整攻略包。

当前验收样例：

- `xivplan-ffxiv-guide/references/guide-json-format.md`
- `xivplan-ffxiv-guide/assets/sample-guides/phase5-multistep-guide.json`
- `xivplan-ffxiv-guide/scripts/assemble_guide.py`
- `xivplan-ffxiv-guide/scripts/build_docx.py`
- `xivplan-ffxiv-guide/scripts/build_pdf.py`
- 完整包输出：`artifacts/guide-packages/phase5-multistep-guide/`
- 速记版输出：`artifacts/guide-packages/phase5-short/`
- 验证结果：完整包包含 `guide.md`、`short-guide.md`、`guide.docx`、`guide.pdf`、`scene.xivplan`、`spec.json` 和 4 张 step PNG；速记版可通过 `--short-only` 单独输出。

## Phase 7：image2 素材闭环

目标：缺素材时自动生成并纳入 XivPlan。

任务：

- [x] 写 `image-asset-workflow.md`。
- [x] 定义素材 prompt 模板。
- [x] 调用 image2 生成 PNG。
- [x] 检查透明背景 / 可读性。
- [x] 自动写入 spec 并导入 XivPlan。

完成标准：

- 能为“鬼头”“动物”等特殊对象生成 PNG，并进入 `.xivplan`。

当前验收样例：

- `xivplan-ffxiv-guide/references/image-asset-workflow.md`
- `xivplan-ffxiv-guide/assets/image-prompts/ffxiv-mechanic-icon.prompt.md`
- `xivplan-ffxiv-guide/assets/image-prompts/animal-icon.example.prompt.md`
- `xivplan-ffxiv-guide/assets/image-assets/samples/m6s-animal-icon-256.png`
- `xivplan-ffxiv-guide/assets/image-assets/sample-asset-manifest.json`
- `xivplan-ffxiv-guide/assets/specs/image-asset-base.spec.json`
- `xivplan-ffxiv-guide/scripts/validate_image_assets.py`
- `xivplan-ffxiv-guide/scripts/inject_image_assets.py`
- 注入后 spec：`artifacts/generated-specs/image-asset-injected.spec.json`
- 注入后 `.xivplan`：`artifacts/generated-xivplan/image-asset-injected.xivplan`
- 验证结果：PNG 为 256x256 透明图，subject ratio 0.3414；注入后 `.xivplan` 为 2 steps / 25 objects，包含 4 个 `image` 对象且通过 `validate_xivplan_scene.py`。

## Phase 8：端到端联调

目标：跑通真实复杂机制。

测试样例：

1. [x] 四塔 + 分摊散开。
2. [x] Light Rampant 类机制。
3. [x] Hello World / Limit Cut 类机制。
4. [x] FRU P1 或 P2 已有机制改写。
5. [x] 一个需要 image2 特殊素材的机制。

完成标准：

- [x] 输入文字。
- [x] 生成方案。
- [x] 生成 `.xivplan`。
- [x] 打开本地 XivPlan 正常显示。
- [x] 导出 PNG。
- [x] 生成 Markdown / DOCX / PDF。

当前验收证据：

- 一键联调脚本：`xivplan-ffxiv-guide/scripts/run_phase8_e2e.py`
- step PNG 导出脚本：`xivplan-ffxiv-guide/scripts/export_xivplan_steps.py`
- 联调报告：`artifacts/phase8-e2e/phase8-e2e-report.md`
- 结构化结果：`artifacts/phase8-e2e/phase8-e2e-results.json`
- 本地 XivPlan UI 检查：`artifacts/phase8-e2e/xivplan-ui-check.md`
- 本地 XivPlan 截图：`artifacts/phase8-e2e/xivplan-ui-screenshot.png`

## Phase 9：质量门与验收自动化

目标：把 Phase 8 已跑通的链路变成可重复验收的质量门，避免“能生成但不可用”。

任务：

- [x] 扩展 `validate_xivplan_scene.py`。
  - [x] 检查 `image` / `icon` / `party.image` 中的 data URL 是否合法。
  - [x] 检查每个 step 是否有 `title` 与 `guide_text`。
  - [x] 检查文本是否过长，避免图中文字遮挡。
  - [x] 检查对象是否明显越界。
  - [x] 检查同一步玩家是否明显重叠。
  - [x] 检查每一步是否至少包含 8 名玩家，或明确标记为观察图 / 局部图。
- [x] 新增 `scripts/validate_guide_package.py`。
  - [x] 检查 `guide.json`、`guide.md`、`guide.docx`、`guide.pdf` 是否存在。
  - [x] 检查 figure 编号与 `manifest.json` 一致。
  - [x] 检查每个 figure 的图片存在、非空、尺寸符合预期。
  - [x] 检查 role assignments 是否覆盖 MT / ST / H1 / H2 / D1-D4，或明确使用组覆盖。
  - [x] 检查 `unknowns` 字段存在，信息不完整时不能静默省略。
- [x] 新增 `scripts/audit_visual_density.py`。
  - [x] 输出每个 `.xivplan` 的 step 数、object 数、每 step 平均对象数。
  - [x] 检查是否包含 marker / party / enemy / text / mechanic zone / arrow 等关键图层。
  - [x] 检查是否遵守“单 step 单主要信息”的拆图原则。
  - [x] 给出接近 KING X 风格的信息密度与可读性摘要。
- [x] 新增 `scripts/run_quality_gate.py`。
  - [x] 批量检查 Phase 8 五个 case。
  - [x] 输出 `artifacts/quality-gates/phase9-quality-report.md`。
  - [x] 输出 `artifacts/quality-gates/phase9-quality-results.json`。

完成标准：

- [x] `run_quality_gate.py artifacts/phase8-e2e` 一条命令可检查 `.xivplan`、PNG、manifest、Markdown、DOCX、PDF 和图文一致性。
- [x] Phase 8 五个 case 全部通过质量门。
- [x] 最终验收标准中“批量导出 step 图片”“生成 Markdown / DOCX / PDF”“检查图文一致性”可以有脚本证据支撑。

当前验收证据：

- 质量门脚本：`xivplan-ffxiv-guide/scripts/run_quality_gate.py`
- 攻略包校验：`xivplan-ffxiv-guide/scripts/validate_guide_package.py`
- 视觉密度审计：`xivplan-ffxiv-guide/scripts/audit_visual_density.py`
- 质量门报告：`artifacts/quality-gates/phase9-quality-report.md`
- 结构化结果：`artifacts/quality-gates/phase9-quality-results.json`

## Phase 10：自然语言机制流程解析与 IR

目标：让用户输入新副本机制流程后，Skill 能生成可追踪的机制 IR 和时间轴 IR，而不是只靠手写 spec。

输入形态：

```text
P1 00:18 四塔，T/H 南北，DPS 东西。
00:31 双分摊后散开，近战尽量不离 Boss。
00:42 Boss 转向，东西半场一边安全，点名规则暂不确定。
```

目标输出：

```text
artifacts/parsed-mechanics/<case>/
├── input.md
├── mechanic-ir.json
├── timeline-ir.json
├── unknowns.md
├── candidate-categories.json
└── parse-report.md
```

任务：

- [x] 定义 `references/mechanic-ir-format.md`。
  - [x] `encounter_context`：副本名、阶段、版本、来源、置信度。
  - [x] `timeline`：时间点、读条、判定、移动窗口、复位窗口。
  - [x] `mechanics`：机制类别、参与对象、点名规则、站位要求、失败条件。
  - [x] `party_constraints`：队伍配置、近战 uptime、读条职业移动、固定队自定义站位。
  - [x] `unknowns`：缺失信息、待验证假设、需要用户确认的问题。
- [x] 新增 `scripts/parse_mechanic_request.py`。
  - [x] 支持中文自然语言机制描述。
  - [x] 支持按时间点 / 阶段 / 步骤解析。
  - [x] 能识别塔、分摊、散开、连线、击退、顺劈、月环、钢铁、Limit Cut、Hello World、Light Rampant 等基础类别。
  - [x] 输出 `mechanic-ir.json` 与 `timeline-ir.json`。
- [x] 新增解析测试集 `assets/parser-fixtures/`。
  - [x] Phase 8 五个输入样例。
  - [x] 一个绝妖星乱舞占位样例：`ultimate-yokai-star-dance-p1-draft.input.md`。
  - [x] 一个信息不完整样例，用于验证 unknowns 输出。
- [x] 新增 `scripts/test_mechanic_parser.py`。
  - [x] 验证基础机制类别识别。
  - [x] 验证时间轴顺序。
  - [x] 验证 unknowns 不丢失。

完成标准：

- [x] 用户输入一段新副本机制流程后，能生成 IR、候选类别和未知点报告。
- [x] Phase 8 五个 case 可以从输入文本生成 IR，再进入后续 spec / guide 流水线。
- [x] 最终验收标准中“能解析自然语言机制描述”“能识别基础 FF14 机制类型”有自动测试支撑。

当前验收证据：

- IR 格式：`xivplan-ffxiv-guide/references/mechanic-ir-format.md`
- 解析器：`xivplan-ffxiv-guide/scripts/parse_mechanic_request.py`
- 回归测试：`xivplan-ffxiv-guide/scripts/test_mechanic_parser.py`
- 解析测试集：`xivplan-ffxiv-guide/assets/parser-fixtures/`
- 解析产物：`artifacts/parsed-mechanics/`

## Phase 11：机制知识检索与类比迁移

目标：用户说“类似 XXXX 机制”时，Skill 能检索知识库，解释类比对象，并输出可迁移 / 不可照搬的部分。

任务：

- [x] 新增 `references/mechanic-aliases.md`。
  - [x] 收录国服常用简称、英文名、机制别名、层数简称。
  - [x] 覆盖 Light Rampant、Hello World、Limit Cut、Paradeigma、Exaflare、运动会、颜色 / 数字优先级等常见类比入口。
- [x] 新增 `scripts/search_mechanic_knowledge.py`。
  - [x] 检索 `mechanic-taxonomy.md`。
  - [x] 检索 `positioning-patterns.md`。
  - [x] 检索 `references/encounters/**/*.md`。
  - [x] 输出候选条目、类别、置信度、可迁移点和风险提示。
- [x] 新增 `scripts/adapt_similar_mechanic.py`。
  - [x] 输入：用户机制描述 + 检索结果 + 当前队伍约束。
  - [x] 输出：`similarity-report.md`。
  - [x] 报告必须包含“我理解你指的是哪类机制”“可迁移部分”“不能照搬部分”“当前缺失信息”“推荐改写方向”。
- [x] 新增检索验收样例。
  - [x] “类似 Light Rampant 但塔在正点，光球在斜角”。
  - [x] “类似 Hello World / Limit Cut，1-8 号顺序处理”。
  - [x] “类似 P12S Paradeigma + 动物分组”。
  - [x] “FRU P1 风格的东西安全区 + 近远散开”。

完成标准：

- [x] 用户输入“类似 XXXX”时，Skill 能定位至少 1-3 个候选机制，并说明为什么匹配。
- [x] 类比报告明确区分机制原理与原攻略站位，避免照搬错误站位。
- [x] 最终验收标准中“能检索 4.x+ 零式 / 绝本典型机制”“能处理类似 XXXX 机制”有脚本证据支撑。

当前验收证据：

- 别名表：`xivplan-ffxiv-guide/references/mechanic-aliases.md`
- 知识检索：`xivplan-ffxiv-guide/scripts/search_mechanic_knowledge.py`
- 类比迁移报告：`xivplan-ffxiv-guide/scripts/adapt_similar_mechanic.py`
- 回归测试：`xivplan-ffxiv-guide/scripts/test_mechanic_knowledge_search.py`
- 检索样例：`xivplan-ffxiv-guide/assets/knowledge-fixtures/`
- 检索与类比报告产物：`artifacts/knowledge-search/`

## Phase 12：解法规划器 v2 与新副本打法生成

目标：从机制 IR / 时间轴 IR 自动生成多个解法候选，并选择推荐打法，进入 XivPlan spec。

任务：

- [x] 扩展 `references/solution-optimization.md`。
  - [x] 增加“新副本未知信息下的保守假设”。
  - [x] 增加“开荒优先解”和“竞速 / 熟练优化解”的权重差异。
  - [x] 增加“固定队策略”和“野队可交流策略”的权重差异。
- [x] 新增 `scripts/plan_solution_candidates.py`。
  - [x] 输入 `mechanic-ir.json`、`timeline-ir.json`、知识检索结果和队伍约束。
  - [x] 生成至少两个候选方案：低记忆成本、少移动 / 保 uptime、高容错。
  - [x] 输出 `solution-candidates.json`。
- [x] 扩展 `score_solution_candidates.py`。
  - [x] 纳入时间轴移动距离。
  - [x] 纳入连续机制复位成本。
  - [x] 纳入读条职业移动窗口。
  - [x] 纳入安全区面积 / 交叉路径 / 塔人数 / 分摊人数。
- [x] 新增 `scripts/build_spec_from_solution.py`。
  - [x] 将推荐候选方案转成 scene spec。
  - [x] 按“观察 -> 预站 -> 判定 -> 移动 -> 结算 -> 复位”自动拆 step。
  - [x] 每个 step 必须带 `purpose`、`guide_text`、`checks`。
- [x] 新增 `artifacts/solution-planning/` 验收输出。
  - [x] 方案对比表。
  - [x] 推荐理由。
  - [x] 风险与待验证点。
  - [x] 生成的 `.xivplan` 与攻略包。

完成标准：

- 对 Phase 8 五个 case，可从 IR 生成候选方案、评分、推荐方案和 XivPlan spec。
- 对绝妖星乱舞占位样例，可生成开荒版 v0.1 草案，并明确列出假设和未知点。
- 最终验收标准中“能主动提出优化解法”“能生成优美、多 step、可编辑的 `.xivplan`”有新副本路径证据支撑。

当前验收证据：

- `scripts/run_phase12_planning.py` 批量生成 6 个 case：Phase 8 五个 case + `ultimate-yokai-star-dance-p1-draft`。
- `artifacts/solution-planning/phase12-solution-planning-report.md` 记录每个 case 的 3 个候选、推荐方案、6-step spec 和未知点数量。
- 每个 case 输出 `solution-candidates.json`、`solution-scores.json`、`solution-report.md`、`risks-and-assumptions.md`、`spec.json`、`scene.xivplan` 和 `guide-package/`。
- 绝妖星占位样例输出 `artifacts/solution-planning/ultimate-yokai-star-dance-p1-draft/`，风险文件明确保留“点名规则暂不确定”等 v0.1 未知点。
- 初次生成命令（同版本重跑需显式加 `--force`，平时应使用新 version 以保留旧输出）：
  - `C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe xivplan-ffxiv-guide\scripts\test_solution_optimizer.py`
  - `C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe xivplan-ffxiv-guide\scripts\run_phase12_planning.py`
  - `C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe xivplan-ffxiv-guide\scripts\run_quality_gate.py artifacts\solution-planning --out-dir artifacts\solution-planning\quality-gates`
- 最新质量门：`artifacts/solution-planning/quality-gates/phase9-quality-report.md`，`PASS (6/6 cases)`。

## Phase 13：绝妖星乱舞短期开荒攻略工作流

目标：为马上开启的新绝本「绝妖星乱舞」建立专门的快速攻略制作工作流，使本项目能在开荒信息持续变化时快速迭代。

工作目录建议：

```text
artifacts/ultimate-yokai-star-dance/
├── raw-notes/
├── parsed-ir/
├── knowledge-matches/
├── solution-candidates/
├── generated-specs/
├── generated-xivplan/
├── guide-packages/
├── quality-reports/
└── change-log.md
```

任务：

- [x] 建立 `artifacts/ultimate-yokai-star-dance/README.md`。
  - [x] 说明当前信息来源、版本号、阶段状态、置信度。
  - [x] 说明所有输出都是开荒草案，必须等待实测修正。
- [x] 建立 `raw-notes/p1-draft-notes.md`。
  - [x] 用于记录用户输入的绝妖星乱舞 P1 机制流程。
  - [x] 支持未确认信息、截图描述、时间轴、口述 call。
- [x] 建立 `scripts/run_ultimate_yokai_star_dance_pipeline.py`。
  - [x] 输入 raw notes。
  - [x] 运行自然语言解析。
  - [x] 运行知识检索与类比报告。
  - [x] 运行候选解法生成与评分。
  - [x] 生成 XivPlan spec、`.xivplan`、PNG 和攻略包。
  - [x] 运行质量门。
- [x] 建立版本化输出约定。
  - [x] `v0.1-draft`：基于口述 / 初见信息的草案。
  - [x] `v0.2-observed`：加入实测点名规则与判定顺序。
  - [x] `v0.3-stabilized`：站位和移动路线稳定。
  - [x] `v1.0-release`：可公开分享的攻略包。
- [x] 建立绝妖星乱舞机制模板库。
  - [x] `references/future-ultimate-workflow.md`。
  - [x] `assets/templates/ultimate-phase-notes-template.md`。
  - [x] `assets/templates/ultimate-change-log-template.md`。
  - [x] `assets/templates/ultimate-guide-release-checklist.md`。
- [x] 建立开荒迭代规则。
  - [x] 每次用户补充新机制信息，先更新 raw notes。
  - [x] 每次生成新版本，必须保留上一版本，不覆盖。
  - [x] 每个版本必须列出“新增确认”“推翻假设”“仍待确认”。
  - [x] 攻略正文不得把未确认信息写成确定结论。

完成标准：

- 给定一份绝妖星乱舞 P1 草案输入，能生成 `v0.1-draft` 攻略包。
- 攻略包包含 `.xivplan`、PNG、Markdown、DOCX、PDF、候选方案报告、类比报告、质量门报告和未知点清单。
- 用户补充新信息后，可以生成 `v0.2-observed`，并在 `change-log.md` 中记录差异。

当前验收证据：

- 专用工作区：`artifacts/ultimate-yokai-star-dance/`，含 `raw-notes/`、`parsed-ir/`、`knowledge-matches/`、`solution-candidates/`、`generated-specs/`、`generated-xivplan/`、`guide-packages/`、`quality-reports/`。
- `v0.1-draft` 已由 `raw-notes/p1-draft-notes.md` 生成，输出在 `guide-packages/v0.1-draft/`、`generated-xivplan/v0.1-draft/` 等目录。
- `v0.2-observed` 已由 `raw-notes/p1-observed-notes.md` 生成，并在 `change-log.md` 记录“新增确认”“推翻假设”“仍待确认”。
- 两个版本均生成 Markdown / DOCX / PDF、`.xivplan`、step PNG、候选方案报告、类比报告、未知点清单和质量门报告。
- 验证命令：
  - `C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe xivplan-ffxiv-guide\scripts\run_ultimate_yokai_star_dance_pipeline.py --version v0.1-draft`
  - `C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe xivplan-ffxiv-guide\scripts\run_ultimate_yokai_star_dance_pipeline.py --notes artifacts\ultimate-yokai-star-dance\raw-notes\p1-observed-notes.md --version v0.2-observed --previous-version v0.1-draft`
- 最新质量门：
  - `artifacts/ultimate-yokai-star-dance/quality-reports/v0.1-draft/quality-report.md`：`PASS`
  - `artifacts/ultimate-yokai-star-dance/quality-reports/v0.2-observed/quality-report.md`：`PASS`

## Phase 14：Skill 集成与一键使用体验

目标：把上述脚本和参考文档整合到 Codex Skill 的固定入口，让用户不需要记脚本名。

任务：

- [x] 更新 `xivplan-ffxiv-guide/SKILL.md`。
  - [x] 增加“新副本机制流程输入”工作流。
  - [x] 增加“类似机制检索与改写”工作流。
  - [x] 增加“绝妖星乱舞开荒攻略生成”工作流。
  - [x] 增加“质量门检查与版本发布”工作流。
- [x] 更新 `agents/openai.yaml`。
  - [x] 固定默认输出目录。
  - [x] 固定质量门必须运行。
  - [x] 固定未知信息必须显式列出。
- [x] 新增 `scripts/run_full_guide_pipeline.py`。
  - [x] 通用入口：输入 `input.md`，输出完整攻略包。
  - [x] 支持 `--encounter-name`、`--phase`、`--version`、`--output-dir`。
  - [x] 支持 `--ultimate-yokai-star-dance` 快捷模式。
- [x] 更新 README。
  - [x] 写明普通机制生成命令。
  - [x] 写明绝妖星乱舞开荒命令。
  - [x] 写明质量门命令。

完成标准：

- 用户只需要提供一个机制流程 Markdown，就能通过一条命令生成完整攻略包。
- Skill 文档能指导另一个 Codex 线程直接接手绝妖星乱舞攻略制作。

当前验收证据：

- 通用入口：`scripts/run_full_guide_pipeline.py`。
- 普通机制 smoke：`run_full_guide_pipeline.py` 可从单个 Markdown 生成完整攻略包，质量门 `PASS`。
- 绝妖星快捷 smoke：`--ultimate-yokai-star-dance` 可生成版本化攻略包，质量门 `PASS`。
- Skill 入口已写入 `xivplan-ffxiv-guide/SKILL.md` 的 One-Command、New Encounter、Similar-Mechanic、Ultimate Yokai、Quality/Release 工作流。
- README 已写明普通机制、绝妖星乱舞和质量门命令。
- `agents/openai.yaml` 固定默认输出目录、质量门必跑、unknowns 必列和版本输出保留策略。
- 验证命令：
  - `python xivplan-ffxiv-guide\scripts\run_full_guide_pipeline.py artifacts\ultimate-yokai-star-dance\raw-notes\p1-draft-notes.md --encounter-name "Ultimate Yokai Star Dance" --phase P1 --version v0.1-smoke --output-dir artifacts\full-guide-pipeline\ultimate-yokai-smoke --force`
  - `python xivplan-ffxiv-guide\scripts\run_full_guide_pipeline.py artifacts\ultimate-yokai-star-dance\raw-notes\p1-observed-notes.md --ultimate-yokai-star-dance --version v0.2-observed-smoke --previous-version v0.2-observed --force`

## 11. 风险与处理策略

| 风险 | 处理 |
|---|---|
| “熟知所有机制”范围过大 | 用可维护知识库逐步覆盖，条目标注置信度 |
| 用户机制描述缺信息 | 先输出可用草案，再列需要确认点 |
| 类比机制名称模糊 | 先复述理解，再给候选匹配 |
| 生成图太乱 | 强制多 step 拆图 |
| image2 素材风格不稳定 | 设置素材规范，必要时人工挑选 |
| 本地 PNG 外链失效 | 使用 data URL 嵌入 `.xivplan` |
| PDF 中文字体问题 | 使用 HTML/PDF 路径并固定中文字体 |
| XivPlan 源码改动破坏原功能 | 每阶段保留 smoke test 和示例 `.xivplan` 回归 |
| 新绝本开荒信息不完整 | 输出草案时必须列 unknowns、假设和待验证点，不把猜测写成事实 |
| 新机制与旧机制类比过度 | 类比报告必须区分“机制原理可迁移”和“原站位不可照搬” |
| 用户持续补充信息导致版本混乱 | 绝妖星乱舞工作流必须版本化输出，并保留 change-log |
| 方案优化过早追求极限 | 开荒阶段默认优先安全、低记忆成本、高容错，再给熟练优化方案 |
| 攻略正文与图不一致 | Phase 9 质量门必须检查 manifest、figure 编号、图片存在、职责表和 unknowns |

## 12. 验收标准

最终系统完成时，必须满足：

- [x] 能解析自然语言机制描述。
- [x] 能识别基础 FF14 机制类型。
- [x] 能检索 4.x+ 零式 / 绝本典型机制。
- [x] 能处理“类似 XXXX 机制”的类比输入。
- [x] 能主动提出优化解法。
- [x] 能生成优美、多 step、可编辑的 `.xivplan`。
- [x] 能导入本地 PNG / image2 PNG。
- [x] 能批量导出 XivPlan step 图片。
- [x] 能生成 Markdown 攻略。
- [x] 能生成 DOCX 攻略。
- [x] 能生成 PDF 攻略。
- [x] 能检查图文一致性。
- [x] 复杂机制输出接近 `KING X\Strats_limited` 的信息密度与可读性。
- [x] 能把新副本机制流程解析为 timeline IR 与 mechanic IR。
- [x] 能在信息不完整时输出 unknowns、假设和需要验证的问题。
- [x] 能从机制 IR 自动生成多个候选解法并评分。
- [x] 能从推荐解法自动生成 scene spec。
- [x] 能为绝妖星乱舞生成版本化开荒攻略包。
- [x] 能在用户补充新信息后生成新版本并记录 change-log。

## 13. 当前下一步

建议立即执行：

1. 根据真实开荒信息继续更新 `artifacts/ultimate-yokai-star-dance/raw-notes/`。
2. 用 `run_full_guide_pipeline.py --ultimate-yokai-star-dance --version <new-version>` 生成下一版。
3. 发布前检查 `change-log.md`、质量门报告、unknowns 和攻略正文措辞。
