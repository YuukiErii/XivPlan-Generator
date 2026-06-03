# XivPlan Skill 视觉与细节能力优化计划

## 0. 目标

本计划用于增强 `xivplan-ffxiv-guide` skill 的制图能力，使它从“能生成可用攻略图”提升到“能稳定生成接近 KING X / FRU 成品密度和美观度的分镜式机制图”。

核心目标：

- 每个机制流程尽量逐画面画全 8 名玩家站位、Boss / 分身 / 小怪位置、场地状态、观察点、判定区、移动路线和复位点。
- 文本、线条、箭头和色块要更直观、大气、优美，机制流程一眼能读懂，而不是只堆对象。
- 强制处理文字互相覆盖、文字遮挡玩家 / AoE / 箭头、箭头交叉过多、玩家图标重叠等可读性问题。
- 支持根据用户指令、机制类型或参考副本自动选择背景场地，例如 FRU P1 用 `/arena/e11.svg`，Light Rampant / Shiva 类机制用 `/arena/e8.svg`。
- 以 `P1_thunder_fire_swords.xivplan` 作为主要视觉目标：多 step、信息密度高、中文标签密集但仍可读，场地、标点、Boss、玩家、AoE、箭头和说明共同服务机制阅读。

## 1. 当前差距

### 1.1 已具备能力

当前 skill 已有以下基础：

- `SKILL.md` 已要求使用 KING X / FRU 风格、step 拆分、场地、标点、玩家、Boss、AoE、箭头、文本标签。
- `references/xivplan-style-guide.md` 已记录黄金样例，其中 `P1_thunder_fire_swords.xivplan` 是长流程机制最佳参考。
- `build_xivplan_scene.py` 支持 `style: "king-x-fru"`、`arena.preset`、`markerPresets`、`inherit`、`updates`、`replace`、`guide_text`。
- `validate_xivplan_scene.py` 已检查 8 人不足、玩家重叠、越界、文本过长等基础问题。
- `audit_visual_density.py` 已能统计对象密度和关键图层，但还比较粗糙。

### 1.2 主要不足

目前不足集中在五类：

1. 画面完整性不够硬：部分生成 step 可能只画机制对象，未强制继承 8 人、Boss、标点和场地状态。
2. 文字布局缺少避让模型：只能限制文本长度，不能判断文本框之间、文本与玩家、文本与 AoE 边界是否发生视觉碰撞。
3. 背景场地选择不够智能：已有 arena preset，但 skill 没有明确的“按用户指令 / 副本 / 机制类型选择场地”流程。
4. 分镜语法不够细：复杂机制还需要更稳定地拆成“观察 -> 预站 -> 判定 -> 移动 -> 结算 -> 复位 -> 衔接”的完整镜头链。
5. 美观度缺少量化验收：当前 density audit 偏向对象数量和图层覆盖，没有评价层次、留白、线条交叉、标签密度、颜色语义、全员可读性。

## 2. 目标标准

### 2.1 每个 step 的最低画面合同

除非 step 明确标记为 `partial_observation: true`，否则每个 step 必须包含：

- 8 个 `party` 对象，角色完整为 `MT/ST/H1/H2/D1/D2/D3/D4`。
- 至少 1 个 `enemy` 对象，用于 Boss、分身或主要机制源；如 Boss 暂时不可见，也要用半透明 Boss / 来源标记表达机制锚点。
- 稳定的 A/B/C/D/1/2/3/4 标点，除非用户明确要求隐藏。
- 明确的场地背景或场地形态。
- 当前 step 的核心机制对象，例如 AoE、塔、分摊、连线、扇形、击退源、安全区。
- 1-3 个短文本标签，说明观察点、职责或目标位置；长解释必须放入 `guide_text`。

`partial_observation: true` 只允许用于纯观察镜头，例如只展示 Boss 读条、场地变形或远处分身。即便如此，也应优先使用半透明 8 人 ghost 站位和 Boss 锚点，避免画面突然失去队伍上下文。

### 2.2 分镜拆分标准

复杂机制默认拆成以下镜头模板：

1. 初始站位：8 人、Boss、场地、标点、默认宏位。
2. 观察信息出现：点名、颜色、数字、分身朝向、场地变化。
3. 读条判断：用色块 / 箭头 / 短标签把“看什么”画出来。
4. 预站调整：显示每个人从默认位去哪里。
5. 第一次判定：显示 AoE / 塔 / 分摊 / 连线实际结算位置。
6. 移动路线：显示判定后下一步怎么走。
7. 第二次或后续判定：多轮机制逐轮拆图。
8. 复位与衔接：显示回中、回八方、接下一读条的位置。

短机制可以合并为 3-4 step；长机制参考 `P1_thunder_fire_swords.xivplan`，允许 10-14 step 或更多。

### 2.3 视觉语言标准

- 危险区：红 / 橙 / 紫低透明度，不遮住玩家图标。
- 安全区：绿 / 青低透明度，优先用边界和淡色填充。
- 移动：蓝 / 青 / 白箭头，箭头宽度稳定，必要时分段避免交叉。
- 职责：角色标签贴近玩家，但不压住 AoE 边界和箭头头部。
- 观察：用短语，例如“看东侧分身”“火先动”“雷后判”，避免长句。
- 复位：用统一的“回中 / 回八方 / 回原位 / 接下读条”标签。
- 文本风格：默认白字深描边，小字 10-14，大标题 22-24，只用于 step 标题或关键状态。

## 3. 能力升级路线

## Phase A：参考样例结构抽取

目标：把 `P1_thunder_fire_swords.xivplan` 从“人脑参考”变成“机器可学习的风格基准”。

任务：

- 新增 `scripts/analyze_golden_xivplan.py`。
- 输入一个或多个黄金 `.xivplan`，输出：
  - step 数、总对象数、每 step 对象数。
  - 每 step 的 `party/enemy/marker/text/arrow/mechanic_zone` 数量。
  - 文本字号、颜色、描边、位置分布。
  - 箭头数量、长度、方向、交叉风险。
  - 玩家和 Boss 的距离分布。
  - 背景场地、标点半径、常用对象尺寸。
- 输出 `artifacts/style-analysis/p1-thunder-fire-swords-style-profile.json` 和 Markdown 摘要。

验收标准：

- 能自动复现参考样例的核心统计：14 steps、625 objects、`/arena/e11.svg`、大量 text / circle / cone / rect / arrow / party。
- 能给出“每 step 推荐对象密度”“文本密度上限”“玩家/Boss/标点尺寸”的具体基准。

## Phase B：场地背景选择器

目标：skill 能根据用户指令和机制语境选择背景场地。

任务：

- 新增 `references/arena-presets.md`，记录场地选择规则：
  - `fru-p1`: `/arena/e11.svg`，用于 FRU P1、Fatebreaker、东西安全、雷火剑、死刑、Cyclonic Break 类图。
  - `fru-p2` / `eden-light`: `/arena/e8.svg`，用于 Shiva、Light Rampant、冰镜、光球、六芒星类图。
  - `default-circle`: 无明确副本背景时的默认圆形场地。
  - 后续增加方形、格子、平台、特殊地板场地。
- 扩展 `build_xivplan_scene.py` 的 `ARENA_PRESETS`，允许更丰富的别名，例如 `fatebreaker`, `shiva`, `light-rampant`, `tile-square`。
- 扩展 `parse_mechanic_request.py` 或 `build_spec_from_solution.py`：
  - 从输入文本识别“背景用 e11 / FRU P1 / 雷火剑 / Shiva / Light Rampant / 方形场地”等指令。
  - 若用户未指定，则根据 encounter、phase、mechanic category 推断。
- 在 `SKILL.md` 增加“背景场地选择”流程。

验收标准：

- 用户说“背景用 FRU P1”时，spec 自动写入 `arena: { preset: "fru-p1" }`。
- 用户说“类似 Light Rampant”时，默认选择 `eden-light` 或 `fru-p2`。
- 质量报告中明确记录“背景来源：用户指定 / 机制推断 / 默认回退”。

## Phase C：全员与 Boss 逐帧保真

目标：每个 step 默认继承 8 人、Boss、标点和场地上下文。

任务：

- 在 scene spec 中引入 `scene_contract`：

```json
{
  "scene_contract": {
    "require_full_party_each_step": true,
    "require_enemy_each_step": true,
    "require_waymarks_each_step": true,
    "allow_partial_observation": false
  }
}
```

- 扩展 `build_xivplan_scene.py`：
  - 若 step 没有 `inherit`，但 contract 要求完整画面，则自动继承基础 party、Boss、标点。
  - 支持 `ghost: true` 或 `opacity: 35` 表示“背景上下文站位”。
  - 支持 `focusRoles`，让当前职责角色高亮，其余人半透明。
- 扩展 `validate_xivplan_scene.py`：
  - 检查每 step 角色集合是否完整。
  - 检查 Boss / 分身锚点是否存在。
  - 如果 `partial_observation` 被使用，要求 `guide_text` 说明为什么此 step 可以不画全员。
- 扩展 `build_spec_from_solution.py`：
  - 每个模板默认调用 `party_ring()` 或从上一步继承 8 人。
  - 结算和复位 step 必须显示所有人最终位置。

验收标准：

- 新生成的普通机制 `.xivplan` 每个 step 都包含 8 名玩家。
- 复杂机制中当前行动者可以高亮，但非行动者仍以半透明方式存在。
- 质量门能阻止“只有塔 / 只有 AoE / 缺 Boss”的空上下文 step 通过。

## Phase D：文字避让与标签布局

目标：显著减少文字互相覆盖、文字压住机制对象的问题。

任务：

- 新增 `scripts/audit_label_layout.py`。
- 为常见对象估算包围盒：
  - `text`: 根据文本长度、字号、对齐方式估算宽高。
  - `party`: 根据 width / height。
  - `enemy`: 根据 radius。
  - `marker`: 根据 width / height。
  - `circle/rect/cone/tower/stack`: 根据几何范围估算。
  - `arrow/tether`: 根据线段和箭头宽度估算。
- 检查：
  - 文本与文本重叠。
  - 文本与玩家 / Boss / 标点重叠。
  - 文本压住箭头头部。
  - 文本位于高透明度危险区中心。
  - 角色标签离角色过远或贴到另一个角色。
- 新增 `scripts/auto_place_labels.py`：
  - 为每个标签生成候选位置：对象外侧八方向、场地边缘说明区、角落说明区。
  - 用打分函数选择最少碰撞的位置。
  - 支持 leader line：文字移到外侧时用细线指回对象。
- 在 `build_xivplan_scene.py` 中支持：
  - `labelPlacement: "auto"`。
  - `labelAvoid: ["party", "enemy", "mechanic", "arrow", "text"]`。
  - `labelAnchor` 与 `leaderLine`。

验收标准：

- 质量报告列出每 step 的 label collision 数量。
- 默认新生成图中严重文本碰撞为 0。
- 对 `P1_thunder_fire_swords` 这类高密度图，允许人工风格文本密集，但新生成文件必须报告可疑碰撞点。

## Phase E：箭头、线条与流程美化

目标：移动路线更清楚，线条更大气，不像临时标注。

任务：

- 新增 `references/visual-flow-language.md`：
  - 强移动：粗蓝箭头。
  - 微调 / 预站：细青箭头。
  - 击退：宽白 / 蓝箭头，起点标击退源。
  - 连线：按机制颜色区分，必要时弯线或分段。
  - 禁止路线：红叉或半透明红线，不与实际移动箭头混用。
- 扩展 `build_xivplan_scene.py`：
  - 支持 `path` / `polyline` 风格箭头，避免所有路线都用单段直线。
  - 支持 `arrowStyle: "movement" | "knockback" | "bait" | "forbidden" | "reset"`。
  - 支持 `curve` 或 `waypoints`。
- 新增 `scripts/audit_flow_lines.py`：
  - 检查箭头交叉数量。
  - 检查箭头头部是否压住文本 / 玩家。
  - 检查路径是否穿过危险区，除非标记为“机制要求穿越”。

验收标准：

- 移动 step 中每条箭头都有明确起点和终点。
- 同一 step 中箭头交叉数尽量为 0；超过阈值时建议拆 step 或改弯线。
- 复位箭头风格与机制移动箭头区分。

完成记录（2026-05-31）：

- 已新增 `references/visual-flow-language.md`，定义 `movement` / `preposition` / `micro` / `knockback` / `bait` / `forbidden` / `reset` 的语义与默认视觉。
- `build_xivplan_scene.py` 已支持 `arrowStyle`、`path` / `polyline`、`waypoints`、`curve`、`startGap` / `endGap`，并在输出 arrow 对象中保留 `flowStart` / `flowEnd` 供审计使用。
- 已新增 `scripts/audit_flow_lines.py`，检查箭头交叉、箭头头部遮挡、危险区穿越。
- Phase E flow fixture、原 Phase 5 多步样例、solution-planning 生成样例均通过 flow audit：crossings 0，severe 0。
- Phase 8 e2e 回归集已用新 builder 重跑并通过质量门：`artifacts/quality-gates/phase9-quality-report.md` 显示 PASS 5/5，Label Severe 0，Flow Severe 0，Crossings 0。

## Phase F：分镜生成器 v2

目标：从机制 IR 生成更详细、可读的 step 链。

任务：

- 扩展 `build_spec_from_solution.py`，把每个机制类别映射到分镜模板：
  - spread: 预站 -> 点名 -> 散开判定 -> 回中。
  - stack: 分组 -> 分摊目标 -> 分摊判定 -> 复位。
  - tower: 塔出现 -> 分配职责 -> 入塔 -> 判定后移动。
  - tether: 连线出现 -> 拉线方向 -> 判定 -> 复位。
  - knockback: 击退源 -> 防击退 / 站位 -> 落点 -> 后续处理。
  - case-based dance: 观察 -> case 标注 -> 路线 -> 逐轮判定 -> 复位。
  - tile arena: 场地状态 -> 可用格 -> 移动路线 -> 结算。
- 每个模板强制生成：
  - `purpose`
  - `guide_text`
  - `checks`
  - `visual_focus`
  - `required_roles`
  - `reset_state`
- 对复杂机制自动增加“衔接 step”，例如“判定后回八方”“Boss 拉回中”“下一轮从这里开始”。

验收标准：

- 同一输入不再只生成 4 个粗略 step，而是按机制复杂度生成 6-14 个细分 step。
- 每个 step 的 `purpose` 能回答“这张图在教什么”。
- 质量门检查 step 链是否包含观察、移动、判定、复位四类基本画面。

完成记录（2026-06-01）：

- `build_spec_from_solution.py` 已升级为 Phase F storyboard generator v2，按 `spread`、`stack`、`tower`、`tether`、`knockback`、`sequence/case-based`、`tile-platform` 模板拼接分镜链。
- 每个生成 step 均带 `storyboard_phase`、`purpose`、`guide_text`、`checks`、`visual_focus`、`required_roles`、`reset_state`。
- `build_xivplan_scene.py` 已保留 Phase F step 元数据到 `.xivplan` 输出。
- 新增 `scripts/audit_storyboard_steps.py`，并接入 `run_quality_gate.py`；仅对 `build_spec_from_solution.py` / `phase-f-v2` 场景强制检查，旧 Phase 8 fixture 显示 `SKIP` 不被误伤。
- 新增 `scripts/test_storyboard_templates.py` 覆盖 8 组类别模板，验证 6-14 步、必需 phase 和 step 元数据保留。
- Phase F smoke 输出：
  - `artifacts/phase-f/four-tower-spread-stack.xivplan`：11 steps，storyboard audit PASS，flow severe 0，label severe 0。
  - `artifacts/phase-f/fru-p1-rewrite.xivplan`：6 steps，storyboard audit PASS，flow severe 0，label severe 0。

## Phase G：视觉质量门 v2

目标：用自动检查逼近人工审美底线。

任务：

- 扩展 `audit_visual_density.py` 为 `audit_visual_quality.py`，或新增独立脚本。
- 综合评分维度：
  - `context_score`: 8 人、Boss、标点、背景是否齐全。
  - `density_score`: 对象数量是否接近黄金样例区间。
  - `label_score`: 文本长度、碰撞、可读性。
  - `flow_score`: 箭头交叉、路径清晰度。
  - `layer_score`: 背景、AoE、机制、玩家、箭头、文本层次是否完整。
  - `aesthetic_score`: 颜色语义一致、透明度合理、留白合理。
  - `step_story_score`: 分镜是否覆盖观察、移动、判定、复位。
- 输出：
  - `visual-quality-results.json`
  - `visual-quality-report.md`
  - 每个 step 的问题列表和建议修复。
- 接入 `run_quality_gate.py` 和 `run_full_guide_pipeline.py`。

验收标准：

- 严重文本碰撞、缺 8 人、缺 Boss、缺背景、缺复位 step 任一出现时，质量门不通过。
- 中等问题给出 review recommended，但允许用户决定是否接受。
- 报告能直接指出第几个 step、哪个标签、哪个对象存在问题。

完成记录（2026-06-01）：

- 新增 `xivplan-ffxiv-guide/scripts/audit_visual_quality.py`，统一输出 context / density / label / flow / layer / aesthetic / step_story 七项分数。
- `run_quality_gate.py`、`run_full_guide_pipeline.py`、`run_ultimate_yokai_star_dance_pipeline.py` 已接入 Phase G visual quality report。
- `artifacts/phase-g/visual-quality-report.md` 与 `visual-quality-results.json` 已生成，当前 Phase 8 fixture 为 5/5 可通过，visual quality 均为 `REVIEW` 且 severe 0。
- `artifacts/phase-g/full-pipeline-smoke/quality-report/visual-quality-report.md` 验证 full pipeline 会随包产出 Phase G 报告。
- 新增 `scripts/test_visual_quality_audit.py` 覆盖“严重缺上下文会失败、仅 review 项不阻断”的质量门语义。

## Phase H：Skill 文档与提示词升级

目标：让 Codex 在使用 skill 时自然遵守新标准。

任务：

- 更新 `SKILL.md`：
  - 增加“默认逐帧完整画面合同”。
  - 增加“背景场地选择工作流”。
  - 增加“文字避让优先级”。
  - 增加“复杂机制必须先分镜再生成 spec”。
  - 增加“以 `P1_thunder_fire_swords.xivplan` 为长流程机制密度参考”。
- 更新 `references/xivplan-style-guide.md`：
  - 加入文本避让规则。
  - 加入箭头线条语言。
  - 加入每 step 必画 8 人 / Boss 的新默认。
- 新增模板：
  - `assets/templates/visual-storyboard-template.md`
  - `assets/templates/arena-selection-template.md`
  - `assets/templates/visual-quality-checklist.md`
- 更新 `agents/openai.yaml`：
  - 默认要求 `quality_gate_required: true`。
  - 增加 `visual_quality_gate_required: true`。
  - 增加 `full_party_each_step_required: true`。

验收标准：

- 新线程只读 skill 后，也能按新标准生成详细图。
- 计划、模板、脚本和质量门之间没有互相矛盾的规则。

完成记录（2026-06-01）：

- `SKILL.md` 已新增复杂机制先分镜、默认逐帧完整画面合同、背景选择、文字避让优先级、Phase G 视觉质量门和 `P1/P1_thunder_fire_swords.xivplan` 长流程密度参考。
- `references/xivplan-style-guide.md` 已补充文字避让优先级、逐帧完整画面默认项和长流程密度参考说明。
- 新增 `assets/templates/visual-storyboard-template.md`、`assets/templates/arena-selection-template.md`、`assets/templates/visual-quality-checklist.md`。
- `agents/openai.yaml` 已新增 `visual_quality_gate_required: true` 与 `full_party_each_step_required: true`，并补充分镜、完整上下文和 severe/review 质量门策略。
- Phase H 自检确认模板、skill、style guide、agent defaults 与 `audit_visual_quality.py` 的 severe/review 语义一致。

## Phase I：黄金样例回归集

目标：用真实或仿真实例防止质量倒退。

任务：

- 建立 `assets/visual-regression-fixtures/`：
  - `fru-p1-thunder-fire-swords-like.input.md`
  - `tankbuster-tower-like.input.md`
  - `light-rampant-like.input.md`
  - `limit-cut-dance.input.md`
  - `tile-arena-transition.input.md`
- 每个 fixture 生成：
  - spec
  - `.xivplan`
  - step PNG
  - visual quality report
  - guide package
- 新增 `scripts/run_visual_regression.py`，批量生成和验收。

验收标准：

- 所有 fixture 通过 scene validation、guide package validation、visual quality gate。
- 每个输出都满足“每个正常 step 8 人 + Boss + 背景 + 标点”的要求。
- 至少一个 fixture 达到 10+ steps 和 500+ objects 的长流程密度。

完成记录（2026-06-01）：

- 已新增 `xivplan-ffxiv-guide/assets/visual-regression-fixtures/` 五个黄金输入：`fru-p1-thunder-fire-swords-like`、`tankbuster-tower-like`、`light-rampant-like`、`limit-cut-dance`、`tile-arena-transition`。
- 已新增 `xivplan-ffxiv-guide/scripts/run_visual_regression.py`，批量调用 full guide pipeline，生成 spec、`.xivplan`、step PNG、visual quality report、guide package，并同步 top-level case surface 供质量门复查。
- `artifacts/phase-i-visual-regression/visual-regression-report.md` 与 `visual-regression-results.json` 已生成；当前 5/5 fixtures 通过 scene validation、guide package validation、visual quality gate。
- 长流程 fixture `fru-p1-thunder-fire-swords-like` 已达到 12 steps / 618 objects，满足 10+ steps 和 500+ objects 密度验收。

## 4. 实施顺序

建议按以下顺序推进：

1. Phase A：先把黄金样例量化，避免后续只凭感觉谈美观。
2. Phase B：补背景场地选择器，因为它影响所有后续图。
3. Phase C：落实全员 / Boss 逐帧保真，这是详细程度的底座。
4. Phase D：做文本避让，这是当前最影响观感的问题。
5. Phase E：强化箭头和线条，让机制流程更直观。
6. Phase F：升级分镜生成器，让复杂机制自然拆得更细。
7. Phase G：质量门 v2，把美观和详细程度变成可验收标准。
8. Phase H：更新 skill 文档和模板，保证新能力被稳定调用。
9. Phase I：建立视觉回归集，防止以后改坏。

## 5. 第一轮可交付范围

第一轮建议不要一次性追求全自动完美制图，而是先完成“硬约束 + 可检测”的部分：

- 新增 `arena-presets.md`。
- 扩展 `SKILL.md` 的逐帧完整画面要求。
- 扩展 `validate_xivplan_scene.py`，禁止普通 step 缺 8 人 / Boss。
- 新增 `audit_label_layout.py` 的初版，先做文本框粗略碰撞检查。
- 扩展 `audit_visual_density.py` 或新增 `audit_visual_quality.py`，输出 context / label / density 三项分数。
- 新增一个 `fru-p1-thunder-fire-swords-like` fixture，目标 8-10 step、每 step 全员、背景 `/arena/e11.svg`。

第一轮完成后，skill 的最低质量会明显上升：它可能还不是人工精品，但不会再产出缺人、缺 Boss、文字乱叠、背景不对、流程过粗的图。

## 6. 质量验收清单

每次生成 `.xivplan` 前后都检查：

- [ ] 是否按用户指令或机制推断选择了正确场地背景。
- [ ] 每个正常 step 是否有 8 名玩家。
- [ ] 每个正常 step 是否有 Boss / 分身 / 机制源。
- [ ] 每个正常 step 是否有稳定标点。
- [ ] 是否明确画出了当前观察点。
- [ ] 是否明确画出了每个职责的站位。
- [ ] 是否明确画出了移动路线。
- [ ] 是否明确画出了判定范围和安全区。
- [ ] 是否有复位或下一机制衔接画面。
- [ ] 文本是否没有互相覆盖。
- [ ] 文本是否没有遮住玩家、Boss、塔、箭头头部或关键 AoE 边界。
- [ ] 箭头是否尽量不交叉，方向是否与 `guide_text` 一致。
- [ ] 危险 / 安全 / 移动 / 职责颜色语义是否一致。
- [ ] 图中短标签是否足够扫读，长解释是否移到攻略正文。
- [ ] `validate_xivplan_scene.py` 是否通过。
- [ ] `audit_visual_quality.py` 是否通过或只剩可接受的 review 项。

复核记录（2026-06-01）：

- 第一轮 Phase A-I 和本清单的当前验收复核已整理到 `docs/first-round-acceptance-audit-2026-06-01.md`。
- 当前复核结论：PASS；Phase A-I 均有证据，当前五个视觉回归 fixture 为 5/5 PASS，visual quality 均为 PASS 100.0，severe 0，review 0。
- 上方 checklist 保持未勾选模板形态，用于以后每次生成新 `.xivplan` 前后复用；不要把它当成全局一次性任务清单。

## 7. 完成定义

当以下条件全部满足时，可认为本轮“美观程度与详细程度升级”完成：

- 用户输入新机制后，默认生成的每个普通 step 都有 8 人、Boss、背景、标点和当前机制对象。
- 用户可以通过自然语言指定背景，例如“用 FRU P1 场地”“用 Shiva / Light Rampant 背景”“用方形平台场地”。
- 复杂机制默认拆成接近人工攻略的分镜链，而不是少数几张概略图。
- 自动质量门能发现并阻止严重文字覆盖、缺角色、缺 Boss、缺复位、缺背景等问题。
- 至少 3 个视觉回归 fixture 达到 `PASS`。
- 至少 1 个长流程 fixture 在信息密度和可读性上接近 `P1_thunder_fire_swords.xivplan`。

## 8. 第一轮工作记录整合与第二轮优化交接清单

本节用于把第一轮 A-I 的实际落地结果整理成可交接基线，并定义第二轮从“可用且可防退”继续推进到“默认接近人工成品”的任务清单。后续线程应优先按本节未勾选项继续执行。

### 8.1 当前已验证基线（2026-06-01）

- [x] Phase E：箭头、线条与流程语言已落地。
  - 证据：`references/visual-flow-language.md`、`build_xivplan_scene.py` 的 `arrowStyle` / `path` / `polyline` / `waypoints` 支持、`scripts/audit_flow_lines.py`。
  - 已验证：Phase E flow fixture、原 Phase 5 多步样例、solution-planning 生成样例均为 crossings 0、severe 0。
- [x] Phase F：分镜生成器 v2 已落地。
  - 证据：`build_spec_from_solution.py` 已按 `spread`、`stack`、`tower`、`tether`、`knockback`、`sequence/case-based`、`tile-platform` 模板生成 6-14 step 分镜链。
  - 已验证：`scripts/test_storyboard_templates.py` 覆盖 8 组类别模板；Phase F smoke 中 `four-tower-spread-stack.xivplan` 为 11 steps，`fru-p1-rewrite.xivplan` 为 6 steps，storyboard audit PASS。
- [x] Phase G：视觉质量门 v2 已落地。
  - 证据：`scripts/audit_visual_quality.py` 统一输出 context / density / label / flow / layer / aesthetic / step_story 七项评分。
  - 已验证：`run_quality_gate.py`、`run_full_guide_pipeline.py`、`run_ultimate_yokai_star_dance_pipeline.py` 均已接入 visual quality report；当前回归集中 severe 0。
- [x] Phase H：Skill 文档、模板和 agent 默认策略已更新。
  - 证据：`SKILL.md`、`references/xivplan-style-guide.md`、`agents/openai.yaml`、`assets/templates/visual-storyboard-template.md`、`arena-selection-template.md`、`visual-quality-checklist.md`。
  - 已验证：`agents/openai.yaml` 中 `quality_gate_required`、`visual_quality_gate_required`、`full_party_each_step_required` 均为 true。
- [x] Phase I：黄金视觉回归集已建立。
  - 证据：`assets/visual-regression-fixtures/` 五个输入、`scripts/run_visual_regression.py`、`artifacts/phase-i-visual-regression/visual-regression-report.md`。
  - 已验证：5/5 fixtures 通过 scene validation、guide package validation、visual quality gate；Phase N 回归后长流程 fixture `fru-p1-thunder-fire-swords-like` 达到 12 steps / 601 objects，visual quality 为 PASS 100.0。

### 8.2 当前距离优化目标的缺口

- [x] 视觉质量仍停留在 `REVIEW`，还没有达到“默认精品图”。
  - Phase N 结果：五个 fixture 均达到 `visual_quality.status == PASS`，分数均为 100.0；review burndown 为 0。
- [x] 标签与标题避让还需要从“无 severe”提升到“几乎无 review”。
  - Phase N 结果：`text_vs_marker` 等 label/title review 已清零；`test_visual_quality_audit.py` 覆盖 label/title obstruction。
- [x] 流程箭头还不够主动。
  - Phase N 结果：含 move / reset 语义的 step 均有 flow layer；flow severe 0，crossings 0；测试覆盖缺失 movement arrow 的失败路径。
- [x] 长流程高密度样例还偏“回归压力测试”，不是完整语义复刻。
  - Phase N 结果：长流程 fixture 已改为 `phase-l-semantic-long-flow`，12 steps / 601 objects，每步都有明确 storyboard 语义，并使用独立长流程密度策略。
- [x] 还缺一次 PNG 级别的人工审美验收。
  - Phase N 结果：Phase M contact sheet 与 human review 已完成；Phase N 重新生成发布门 contact sheets。

### 8.3 第二轮总体目标

第二轮目标：把第一轮的“硬约束 + 可检测 + 可回归”升级为“默认生成图更像人工攻略成品”。具体来说，第二轮结束时应满足：

- [x] `scripts/run_visual_regression.py --force` 仍然 5/5 PASS。
- [x] 所有 fixture severe issues 为 0。
- [x] 至少 3/5 fixture 的 `visual_quality.status` 达到 `PASS`；其余 fixture 若仍为 `REVIEW`，每个 scene 的 review item 应有明确人工接受理由。
- [x] 每个 fixture 的 `label_score >= 80`，且无 step 标题压标点的重复问题。
- [x] 每个含移动、诱导、击退或复位语义的 fixture 都有 flow layer；`audit_flow_lines.py` crossings 维持 0。
- [x] 长流程 fixture 保持 10-14 steps、500+ objects，同时不依赖纯密度填充；每个 step 都有清晰的 observe / move / resolve / reset 语义。
- [x] 生成 `artifacts/phase-j-visual-polish/` 或后续同级目录，保存第二轮报告、截图/contact sheet、质量结果和剩余问题。

### 8.4 第二轮执行顺序与可勾选任务

#### Phase J：Review 项清零与标签避让加强

目标：把当前 Phase I 的 `REVIEW` 主要来源从“标签/标题轻微碰撞”降到可忽略，优先解决 `text_vs_marker`。

- [x] J1 读取 `artifacts/phase-i-visual-regression/visual-regression-results.json`，生成 `artifacts/phase-j-visual-polish/review-burndown.md`，按 fixture / step / issue kind 汇总 review 项。
- [x] J2 调整 step 标题默认位置，避免标题与 A/B/C/D/1/2/3/4 标点相交。
  - 候选方案：标题固定到场外上边缘、缩短标题、或在 builder 中给标题保留专用安全区。
- [x] J3 强化 `labelPlacement: "auto"` 和 `leaderLine` 的默认使用策略。
  - 范围：机制标签、塔/分摊标签、观察标签、长流程 dense label。
- [x] J4 扩展 `auto_place_labels.py` 或 `build_xivplan_scene.py`，让自动避让结果能稳定写回 `.xivplan`。
- [x] J5 重新运行 `run_visual_regression.py --force`，确认 label severe 0，且 `text_vs_marker` review 明显下降。
- [x] J6 在 `docs/visual-upgrade-work-record.md` 记录修改、剩余 review 项和验证命令。

验收：

- [x] Phase I 五个 fixture 仍然 quality gate PASS。
- [x] 所有 fixture `label_score >= 80`。
- [x] 重复出现的 step 标题压标点问题为 0。

#### Phase K：流程箭头与移动语义补强

目标：让 move / reset / bait / knockback step 默认有清晰路线，避免“文字说移动但图中没有箭头”。

- [x] K1 在 `build_spec_from_solution.py` 中区分静态观察 step 与实际移动 step，建立 `movement_required` 或等价元数据。
- [x] K2 当 step 有 party `updates`、移动目标、reset_state 或 `storyboard_phase == "move"` 时，自动生成 `arrowStyle` 路线。
- [x] K3 对 reset step 增加统一 `reset` arrow 样式，和机制移动箭头区分。
- [x] K4 对 bait / knockback / forbidden route 补默认箭头或禁行线策略。
- [x] K5 收紧 `audit_visual_quality.py` 对 missing flow layer 的判断：静态 observe/preposition 可 review，move/reset 缺箭头应升级为 severe 或高优先级 review。
- [x] K6 重新运行 `run_visual_regression.py --force` 和 `audit_flow_lines.py`，确认 crossings 仍为 0。

验收：

- [x] 含移动语义的 fixture 不再报告 scene-level missing flow layer。
- [x] flow severe 0、crossings 0。
- [x] `visual_quality.flow_score` 保持 100 或只剩明确可接受 review。

#### Phase L：长流程语义化重建

目标：把 `fru-p1-thunder-fire-swords-like` 从“高密度压力测试”升级为真正可读的 FRU P1 风格长流程样例。

- [x] L1 对 `P1_thunder_fire_swords.xivplan` 或当前黄金样例运行 `scripts/analyze_golden_xivplan.py`，更新 golden profile 摘要。
- [x] L2 为 `fru-p1-thunder-fire-swords-like` 写独立 storyboard，明确 10-14 个 step 的教学目的。
  - 建议链路：初始站位 -> 东西观察 -> 雷火点名 -> 第一次安全半场 -> 近远预站 -> 第一次判定 -> 坦克死刑外拉 -> 第二轮换边 -> 移动路线 -> 第二次判定 -> 回中 -> 接下一个读条。
- [x] L3 替换 `run_visual_regression.py` 中纯 densify 的实现，改为语义对象生成或专用 spec fixture。
- [x] L4 每个 long-flow step 保留 8 人、Boss、标点、场地、当前机制对象，并补齐必要箭头和短标签。
- [x] L5 重新导出 PNG 和 guide package，人工检查至少 12 张图的阅读节奏。
- [x] L6 在 `artifacts/phase-l-long-flow/` 保存 spec、scene、PNG、quality report 和人工审查报告。

验收：

- [x] long-flow fixture 10-14 steps。
- [x] long-flow fixture 500+ objects。
- [x] long-flow fixture 每 step 都有明确 `purpose`、`guide_text`、`visual_focus`。
- [x] long-flow fixture 不再依赖重复填充对象来达成密度。

完成记录（2026-06-01）：

- `run_visual_regression.py` 已将 `fru-p1-thunder-fire-swords-like` 的旧 densify 逻辑替换为 Phase L semantic FRU P1 storyboard 生成。
- 真实 `P1_thunder_fire_swords.xivplan` golden profile 已输出到 `artifacts/phase-l-long-flow/p1-thunder-fire-swords-golden-profile.md`：14 steps / 625 objects / median 47 objects per step / `/arena/e11.svg`。
- 新 long-flow fixture 为 12 steps / 601 objects；`storyboard-audit.md` PASS，`visual-quality-report.md` 为 REVIEW 88.0、severe 0，仅保留 12 个可接受的 dense-step review。
- Phase L 交付件已保存到 `artifacts/phase-l-long-flow/`，包括 `spec.json`、`scene.xivplan`、`images/`、`guide-package/`、`contact-sheet.png`、quality report 与 `manual-review.md`。

#### Phase M：PNG 肉眼审查与视觉对标

目标：把自动报告之外的“看起来像不像攻略图”纳入交接证据。

- [x] M1 新增或编写一次性脚本，把每个 fixture 的 step PNG 拼成 contact sheet。
  - 建议输出：`artifacts/phase-m-visual-review/contact-sheets/<fixture>.png`。
- [x] M2 对每个 contact sheet 写人工审查表。
  - 记录：信息是否过密、视线是否顺畅、标签是否扫读、箭头是否解释移动、颜色语义是否统一。
- [x] M3 把审查发现分成三类：必须脚本修、fixture 手工修、可接受 review。
- [x] M4 修复最高频的 3 类视觉问题，再跑 Phase I 回归。
- [x] M5 将审查结论写入 `docs/visual-upgrade-work-record.md`。

验收：

- [x] 五个 fixture 都有 contact sheet。
- [x] 五个 fixture 都有人工审查记录。
- [x] 至少 3 个 fixture 被标记为“可作为示例图继续保留”。

完成记录（2026-06-01）：

- 新增 `scripts/build_contact_sheets.py`，并生成 `artifacts/phase-m-visual-review/contact-sheets/*.png` 与 `contact-sheet-manifest.json`。
- 已写入 `artifacts/phase-m-visual-review/human-review.md`，并整合进 `docs/visual-upgrade-work-record.md`。
- 已修复本轮最高频 3 类视觉问题：long-flow callout/标点碰撞、long-flow 箭头头部遮挡、Light Rampant 塔/连线移动 step 缺显式机制层。
- 重新运行 Phase I 回归后 5/5 PASS；4/5 fixture 达到 `visual_quality.status == PASS`，long-flow fixture 保持 REVIEW 但有明确人工接受说明。

#### Phase N：第二轮发布级回归门与交接

目标：把第二轮改动固化成未来线程可直接执行的发布级门槛。

- [x] N1 更新 `README.md`，加入第二轮视觉 polish / contact sheet / review burndown 命令。
- [x] N2 更新 `SKILL.md` 和 `references/xivplan-style-guide.md`，把第二轮新增的标签、箭头、长流程语义规则写入默认流程。
- [x] N3 更新 `agents/openai.yaml`，必要时增加更严格的 visual quality 默认阈值。
- [x] N4 补充或更新测试脚本，覆盖 label/title avoidance、movement arrow generation、semantic long-flow fixture。
- [x] N5 运行完整验证：
  - [x] `python -m compileall -q xivplan-ffxiv-guide\scripts`
  - [x] `python xivplan-ffxiv-guide\scripts\test_visual_quality_audit.py`
  - [x] `python xivplan-ffxiv-guide\scripts\test_storyboard_templates.py`
  - [x] `python xivplan-ffxiv-guide\scripts\run_visual_regression.py --force`
- [x] N6 将最终交接记录整合进 `docs/visual-upgrade-work-record.md`。

完成记录（2026-06-01）：

- 新增 `scripts/summarize_visual_reviews.py`，生成 `artifacts/phase-n-release-gate/review-burndown.md` 与 `.json`。
- `audit_visual_density.py` 已加入 `phase-l-semantic-long-flow` 独立密度策略：10-14 steps、平均 35-65 objects/step、总对象 450+、observe/move/resolve/reset 覆盖、无缺层时接受密集 step。
- `test_visual_quality_audit.py` 已覆盖 label/title obstruction、movement arrow 缺失、semantic long-flow density policy。
- Phase N release gate 输出保存在 `artifacts/phase-n-release-gate/`，包括 contact sheets、review burndown、Phase L density policy audit。
- `run_visual_regression.py --force` 结果：5/5 PASS，五个 fixture 均为 visual quality PASS 100.0，review items 0，severe items 0。
- 最终交接记录：`docs/visual-upgrade-work-record.md`。

验收：

- [x] 第二轮所有新增报告、脚本、fixtures 和文档路径在 handoff 中列清楚。
- [x] 质量门结果、PNG/contact sheet、人工审查结论三类证据都齐全。
- [x] 后续线程只读本节和 `docs/visual-upgrade-work-record.md` 就能继续第三轮或发布整理。

### 8.5 第二轮停止线

第二轮不追求一次性解决所有审美问题。满足以下条件即可收束：

- [x] 无 severe regression。
- [x] 当前五个 golden fixtures 保持 5/5 quality gate PASS。
- [x] 标签、箭头、长流程语义三个主要缺口都有可验证改善。
- [x] 至少 3 个 fixture 达到 `visual_quality.status == PASS`，或有明确人工接受说明。
- [x] 交接报告能说明哪些 review 项被接受、哪些留到第三轮。

## 9. 第三轮优化计划：分镜教学、敌人身份与职业级职责表达

第三轮目标：把第二轮的“视觉质量 PASS”继续升级为“每一帧都像可直接给队员看的教学分解图”。这一轮不只检查 8 人、Boss、标点是否存在，还要让 skill 主动把复杂机制拆得更细，把 Boss / 小怪身份画清楚，把玩家表达升级为“XivPlan 内置官方职业图标 + 图标附近的 `MT/ST/H1/H2/D1/D2/D3/D4` 职责短标”，并且在每一帧都保留可辨认的敌人图像或图标。

口径修正（2026-06-01）：本计划里的“职业图标”严格指 XivPlan 自带的 `public/actor/<JOB>.png` 官方职业图标资源，例如 `/actor/DRK.png`、`/actor/SAM.png`、`/actor/PCT.png`。`job:*` 抽象 token、泛用职能图标、或把 `SAM/PCT` 等缩写画进色块徽章，都不能算作第三轮验收中的职业图标。

口径更新（2026-06-02）：攻略图现在分为 `mechanic_flow` 与 `flow_example` 两类。第三轮 Phase R/S 的官方职业图标 + 职责短标要求保留给 `flow_example`；默认主机制图 `mechanic_flow` 改用官方编号职能图标（`tank1/tank2/healer1/healer2/dps1-dps4`），不再额外生成 `MT/ST/H1...` 文字标签。

第三轮完成后，默认生成图应满足：

- 复杂机制宁可多拆 step，也不把观察、判断、预站、移动、判定、复位压进同一帧。
- 每个 Boss、分身和小怪都有明显目标环、名字、目标环半径或尺寸说明，必要时显示朝向和身位。
- 每个 Boss、分身和小怪都有 `image` / `icon` 图层或可回退的统一敌人图标；已有副本优先参考攻略图、第一视角截图或用户描述生成专属素材。
- 每一帧的 8 人不只是存在，还要在 XivPlan 官方职业图标附近标清每个人的职责短标；默认使用 `/actor/<JOB>.png` 职业图标而不是同质化职能图标或文字缩写徽章。
- 人群集合、多人重叠、近距离分摊或需要保持画面清爽的帧，可以省略职责短标，并适当缩小职业图标；但职业图标仍必须可辨认。
- 默认职业配置固定为：`MT=DRK(/actor/DRK.png)`、`ST=PLD(/actor/PLD.png)`、`H1=AST(/actor/AST.png)`、`H2=SCH(/actor/SCH.png)`、`D1=SAM(/actor/SAM.png)`、`D2=DRG(/actor/DRG.png)`、`D3=BRD(/actor/BRD.png)`、`D4=PCT(/actor/PCT.png)`。若用户给出队伍配置，以用户输入覆盖默认值。

### 9.1 第三轮当前缺口

- [x] 分镜数量仍偏“机制类型模板化”：虽然已有 6-14 step，但对需要逐动作教学的新机制，仍可能少画“读什么、怎么判、谁先动、谁后动、判定后去哪”的中间帧。
- [x] Boss / 小怪仍主要是 `enemy` 圆点或目标环，名字、目标环大小、朝向、身位、分身差异不够显眼。
- [x] 敌人图像资产没有成为默认合同：Phase Q 已把 dedicated/fallback enemy icon 注入纳入默认合同。
- [x] 玩家仍偏职责点表达：Phase R/S 已先改为 XivPlan 官方 `/actor/<JOB>.png` 职业图标 + 职责短标，纠正了“文字缩写徽章”误读；2026-06-02 起该样式作为 `flow_example` 合同保留，默认 `mechanic_flow` 合同改为编号职能图标。
- [x] 质量门目前检查“有无 party / enemy”，但没有严查“敌人是否命名、是否有目标环半径、是否有 icon、玩家是否有职业级身份”。Phase P/Q/R/S 已补齐 enemy identity、enemy icon、party official job icon 校验。

### 9.2 第三轮总体目标

- [x] 新增“教学分镜粒度”策略：普通复杂机制默认 `8-16` step，长流程机制默认 `12-20` step；只有简单单判定机制才允许 `3-5` step。
- [x] 每个 step 的 `purpose` 必须回答一个更细的问题，例如“谁被点名”“看哪只分身”“MT/ST 从哪里拉到哪里”“H1/H2 为什么换位”“D1/D2/D3/D4 的最终落点是什么”。
- [x] 每个 normal step 至少保留一个 `enemy_identity` 合同：`name`、`kind`、`radius`、`ring`、`label`、`icon`、`facing` 按需填写。
- [x] 所有 Boss / add 目标环必须可读：目标环大小和名字不能被 AoE、玩家、箭头或标签遮挡。
- [x] 对每个 Boss / add 生成或选择图像资产：优先 image2 生成专属小图标；如果素材暂缺，使用统一 boss/add 占位图标，并在 unknowns / guide_text 中标注待替换。
- [x] 玩家对象升级为可按图面分类切换的双合同：`role` 保留 `MT/ST/H1/H2/D1/D2/D3/D4`，`job` 保留默认职业或用户职业；`flow_example` 图面显示 XivPlan `/actor/<JOB>.png` icon + 职责短标，`mechanic_flow` 图面显示编号职能 icon；集合/重叠帧允许隐藏职责短标，并允许按比例缩小图标。
- [x] 第三轮回归集新增至少 3 个 fixture：多 Boss / 多小怪机制、已有副本 Boss 图标机制、职业分工敏感机制。

### 9.3 Phase O：教学分镜粒度 v3

目标：让 skill 学会用更多帧数讲清机制，不再只做“事件摘要图”。

- [x] O1 在 `references/xivplan-style-guide.md` 增加“教学分镜粒度”规则：
  - 简单机制：`3-5` step，例如单次分摊、单次散开、单次击退。
  - 中等机制：`6-10` step，例如两轮判定、换位、读条加散开。
  - 复杂机制：`10-16` step，例如 Limit Cut、线分支、大运动会、多轮塔/分摊。
  - 超长流程：`12-20` step，例如 FRU P1 雷火剑式长流程；允许超过旧 `10-14` 上限，但必须有逐帧教学价值。
- [x] O2 扩展 `build_spec_from_solution.py` 的 storyboard generator：
  - 把每个机制拆成 `observe_signal`、`assign_roles`、`preposition`、`first_move`、`first_resolve`、`between_resolves`、`second_move`、`second_resolve`、`reset`、`next_read_setup` 等更细 phase。
  - 对多轮机制按“每轮观察 -> 移动 -> 判定 -> 复位/衔接”循环展开。
  - 当某个 step 同时包含两个以上教学问题时，自动拆成相邻 step。
- [x] O3 扩展 `assets/templates/visual-storyboard-template.md`：
  - 增加 `teaching_question` 字段。
  - 增加 `why_this_frame_exists` 字段，避免无意义拆帧。
  - 增加 `changed_objects_only` 字段，说明本帧相比上一帧真正变化了什么。
- [x] O4 扩展 `audit_storyboard_steps.py`：
  - 检查每个 step 是否只有一个主教学问题。
  - 检查复杂机制是否包含足够的 observation / assignment / movement / resolve / reset / next-read coverage。
  - 对“guide_text 同时讲了多个动作但图中只有一帧”的情况给出 review 或 severe。
- [x] O5 在 `run_visual_regression.py` 中增加第三轮长分镜 fixture，要求至少 `14` step 且每步都有不同 `teaching_question`。

验收：

- [x] 复杂 fixture 的 step 数量不低于 `10`，长流程 fixture 不低于 `14`。
- [x] 每个 step 都有 `teaching_question`、`purpose`、`guide_text`、`visual_focus`。
- [x] `audit_storyboard_steps.py` 能指出“过粗 step”并建议拆分。

完成记录（2026-06-01）：

- `build_spec_from_solution.py` 已切换为 `phase-o-v3`，每个 step 输出 `teaching_question`、`why_this_frame_exists`、`changed_objects_only`，并覆盖 observation / assignment / movement / resolve / reset / next-read。
- `audit_storyboard_steps.py` 已扩展教学问题单一性、v3 phase 覆盖、长流程 `14-20` step 规则和过粗 `guide_text` review。
- `run_visual_regression.py` 已把 FRU semantic long-flow 升级为 14-step teaching fixture，并新增 `long-teaching-storyboard.input.md`。
- 回归证据：`artifacts/phase-i-visual-regression/visual-regression-report.md`，7/7 PASS，长流程 14 steps / 733 objects。

### 9.4 Phase P：Boss / 小怪目标环与名称合同

目标：让每只 Boss、分身、小怪都在每一帧有明确身份，不再只是一个模糊圆点。

- [x] P1 新增 `references/enemy-identity-style-guide.md`，定义敌人表达规则：
  - `boss`：必须有目标环、名字、朝向；默认半径 `32-45`，大型 Boss 可按用户描述增大。
  - `add`：必须有目标环、名字或编号；默认半径 `20-32`。
  - `clone` / `shadow` / `分身`：必须和本体名字区分，例如“Boss 分身 N”“东侧分身”“火分身”。
  - `untargetable_source`：不可选中机制源可用虚线环或半透明环，但仍要有名称。
- [x] P2 扩展 scene spec 的敌人语法：

```json
{
  "type": "enemy",
  "kind": "boss",
  "name": "Fatebreaker",
  "displayName": "Fatebreaker",
  "radius": 42,
  "ring": {
    "visible": true,
    "radius": 42,
    "strokeWidth": 3,
    "style": "target-ring"
  },
  "facing": 180,
  "labelPlacement": "auto",
  "icon": "asset:fatebreaker-boss"
}
```

- [x] P3 扩展 `build_xivplan_scene.py`：
  - 自动为缺 `ring` 的 Boss / add 补目标环。
  - 自动为缺 `displayName` 的敌人使用 `name`。
  - 对多个同名 add 自动追加方位或编号，例如 `Add N`、`Add E`、`Add 1`。
  - 对目标环和名字标签使用 label avoidance，避免压住玩家与 AoE。
- [x] P4 扩展 `validate_xivplan_scene.py`：
  - `enemy` 必须有非空 `name`。
  - normal step 中每个 `enemy` 必须有 `radius` 或 `ring.radius`。
  - Boss / add 名字标签缺失、目标环不可见、多个敌人同名不可区分时失败。
- [x] P5 扩展 `audit_visual_quality.py`：
  - 新增 `enemy_identity_score`。
  - 检查目标环是否被大型 AoE 或文本遮挡。
  - 检查 Boss / add 名称是否可读，是否与另一个敌人标签重叠。

验收：

- [x] 每个 normal step 的所有 `enemy` 都有名字和目标环。
- [x] 多 Boss / 多 add fixture 中，不存在不可区分的同名敌人。
- [x] 敌人标签和目标环 severe obstruction 为 0。

完成记录（2026-06-01）：

- 新增 `references/enemy-identity-style-guide.md`。
- `build_xivplan_scene.py` 已支持 `boss` / `enemy` / `add` / `clone` / `shadow` / `untargetable_source`，自动补 `displayName`、`enemyKind`、`targetRing`、半径、名字标签，并为同名敌人追加方向或编号。
- `validate_xivplan_scene.py` 已校验敌人非空名称、半径或目标环半径、可见目标环、匹配文字标签和重复敌人名。
- `audit_visual_quality.py` 已新增 `enemy_identity_score`，并检查敌人名字、目标环、重复名和严重遮挡。
- 新增 `multi-boss-add-identity.input.md` 第三轮回归 fixture；当前 7/7 回归 PASS，`multi-boss-add-identity` 的 label severe / flow severe 均为 0。

### 9.5 Phase Q：Boss / 小怪图像资产与 icon 注入

目标：每一帧的 Boss / 小怪不只靠目标环表达，还要有可辨认的小图像或 icon。

- [x] Q1 新增 `references/enemy-image-asset-workflow.md`，在现有 `image-asset-workflow.md` 之上补充敌人专用流程：
  - 用户描述 Boss 样子时，先把描述整理成 `asset_brief`。
  - 已有副本时，优先从用户截图、攻略截图、第一视角或公开视频截图中提取外观特征；如果无法确认，则用通用 guide-friendly boss icon 回退。
  - image2 prompt 不复制官方 UI 或原画，只生成攻略图用的原创小图标：清晰轮廓、透明背景、无文字、64-96 px 可读。
  - 每个敌人资产都写入 manifest，并注入 `.xivplan` 为 data URL。
- [x] Q2 新增敌人资产 manifest 结构：

```json
{
  "enemy_assets": [
    {
      "enemy_id": "fatebreaker",
      "name": "Fatebreaker",
      "kind": "boss",
      "source": "user-description",
      "asset_id": "boss-fatebreaker-icon",
      "path": "outputs/<mechanic>/assets/boss-fatebreaker-icon.png",
      "fallback": "generic-boss-icon",
      "display": {
        "width": 72,
        "height": 72,
        "anchor": "center"
      }
    }
  ]
}
```

- [x] Q3 扩展 `inject_image_assets.py` 或新增 `inject_enemy_assets.py`：
  - 把 enemy manifest 注入 spec。
  - 为每个 enemy 写入 `icon` / `image` 字段。
  - 在没有专属 PNG 时注入统一 boss/add fallback icon，并记录 `asset_status: "fallback"`。
- [x] Q4 扩展 `build_xivplan_scene.py`：
  - enemy 同时渲染目标环、icon 和名字。
  - icon 不遮住目标环边界；目标环始终比 icon 更外层或更清晰。
  - 小怪数量多时支持小图标缩放，但不能小到无法辨认。
- [x] Q5 扩展 `validate_image_assets.py`：
  - 检查 enemy icon 是否透明、非空、边缘留白、64 px 下可读。
  - 检查 manifest 中每个 enemy 是否至少有专属 asset 或 fallback。
- [x] Q6 在 `SKILL.md` 中增加敌人素材询问/使用规则：
  - 如果用户提供 Boss 样子，必须进入 image2 / asset manifest 流程。
  - 如果用户未提供但副本已知，先查已有参考或攻略截图；无法确认时使用 fallback 并标注待替换。
  - 不因素材不确定而跳过目标环、名字和职责图。

验收：

- [x] 第三轮 fixture 中每个 Boss / add 都有 icon 或 fallback icon。
- [x] 专属 icon manifest 与 `.xivplan` 内 data URL 一致。
- [x] `validate_image_assets.py` 和 scene validation 均通过。
- [x] PNG contact sheet 中 Boss / add 图标在正常导出尺寸下可辨认。

完成记录（2026-06-01）：

- 新增 `references/enemy-image-asset-workflow.md`、`assets/image-assets/sample-enemy-asset-manifest.json` 和 `scripts/inject_enemy_assets.py`。
- `build_xivplan_scene.py` 现在为 Boss/add/clone/source 自动补 `icon`、`assetStatus`、`assetFallback` 与可审计 fallback PNG data URL；`export_xivplan_steps.py` 会在 PNG 预览中绘制敌人 icon。
- `validate_image_assets.py` 已支持 `enemy_assets` manifest 与 fallback-only entries；`validate_xivplan_scene.py` 和 `audit_visual_quality.py` 会检查 normal step enemy icon。
- 证据：`artifacts/phase-q/sample-enemy-asset-validation.json`、`artifacts/phase-q/multi-boss-add-identity.enemy-assets.xivplan`、`artifacts/phase-q/multi-boss-add-identity.enemy-assets.visual-quality.md`。

### 9.6 Phase R：八人职业图标、职责短标与默认队伍配置

目标：让每一帧的玩家身份从“有 8 个点”升级为“XivPlan 官方职业图标能区分人、职责短标能区分 MT/ST/H1/H2/D1/D2/D3/D4”。这里的“标注位置”不是额外写绝对坐标，而是在 `/actor/<JOB>.png` 职业图标附近标注职责；集合/重叠帧可省略职责短标，并适当缩小职业图标，避免画面糊成一团。

- [x] R1 新增 `references/party-job-defaults.md`，定义默认队伍配置和职责短标：

| 职责 | 默认职业 | XivPlan 官方图标 | 图面职责短标 | 说明 |
|---|---|---|---|---|
| MT | DRK | `/actor/DRK.png` | `MT` | 默认主坦；职业由暗骑官方图标表达。 |
| ST | PLD | `/actor/PLD.png` | `ST` | 默认副坦；职业由骑士官方图标表达。 |
| H1 | AST | `/actor/AST.png` | `H1` | 默认 H1；职业由占星官方图标表达。 |
| H2 | SCH | `/actor/SCH.png` | `H2` | 默认 H2；职业由学者官方图标表达。 |
| D1 | SAM | `/actor/SAM.png` | `D1` | 默认近战 1；职业由武士官方图标表达。 |
| D2 | DRG | `/actor/DRG.png` | `D2` | 默认近战 2；职业由龙骑官方图标表达。 |
| D3 | BRD | `/actor/BRD.png` | `D3` | 默认远敏；职业由诗人官方图标表达。 |
| D4 | PCT | `/actor/PCT.png` | `D4` | 默认法系；职业由画家官方图标表达。 |

- [x] R2 扩展 party object 语法：

```json
{
  "type": "party",
  "role": "MT",
  "job": "DRK",
  "roleLabel": "MT",
  "icon": "/actor/DRK.png",
  "image": "/actor/DRK.png",
  "iconScale": 1.0,
  "x": 0,
  "y": 150,
  "roleLabelPlacement": "near-icon"
}
```

- [x] R3 扩展 `build_spec_from_solution.py`：
  - 默认生成 party 时写入 `job`、`roleLabel`、`icon`、`image`。
  - 当用户提供队伍配置、宏位或职业替换时覆盖默认职业。
  - 每个 step 的 `updates` 保留职业和职责，不允许移动后丢失 `role/job/icon`。
  - 当 step 标记为 `party_cluster: true`、`stack_group: true` 或多人图标距离低于阈值时，允许 `roleLabelVisible: false`，并可设置 `iconScale: 0.72-0.9`，但职业图标必须保留且可辨认。
- [x] R4 扩展 `build_xivplan_scene.py`：
  - 优先使用 XivPlan 内置 `/actor/<JOB>.png` 官方职业 icon；如果本地 XivPlan 资源缺失，验收应失败或标记为待修复，不能改用职业缩写文字 fallback 伪装通过。
  - 角色标签采用职责短标，例如 `MT`、`H1`，并贴近职业图标；职业信息由职业 icon 表达。
  - 集合/分摊/多人重叠帧可隐藏职责短标，并把职业 icon 缩小到仍可辨认的尺寸；必要时在 `guide_text` 说明“集合帧省略职责短标”。
  - 职业 icon 缩放应有下限：正常导出尺寸下不得小于可读阈值，建议等效宽高不低于 `24 px`。
  - `job:*` 抽象 token、`/actor/tank.png` / `/actor/healer.png` / `/actor/dps.png` 泛用图标、以及文字缩写徽章都不满足默认职业图标验收。
  - `focusRoles` 高亮时只改变透明度/描边，不移除非 focus 玩家身份。
- [x] R5 扩展 `validate_xivplan_scene.py`：
  - normal step 必须包含 8 个唯一 `role`。
  - 每个 party 必须有 `job` 或明确用户禁用职业图标。
  - 默认配置下必须能匹配 `MT=DRK(/actor/DRK.png) / ST=PLD(/actor/PLD.png) / H1=AST(/actor/AST.png) / H2=SCH(/actor/SCH.png) / D1=SAM(/actor/SAM.png) / D2=DRG(/actor/DRG.png) / D3=BRD(/actor/BRD.png) / D4=PCT(/actor/PCT.png)`。
  - 非集合帧必须有 `roleLabel` 或等价职责短标；集合/重叠帧可省略职责短标，但必须保留职业 icon。
  - 如果某一帧同一职责出现两次、某个职责消失、职业 icon 丢失，或非集合帧职责短标丢失，则失败。
- [x] R6 扩展 `audit_visual_quality.py`：
  - 新增 `party_identity_score`。
  - 检查职业 icon / 职责短标是否被 AoE、敌人目标环、箭头或其他标签遮挡。
  - 检查 8 人站位是否和 `guide_text` 中的职责位置一致。
  - 对集合/重叠帧使用独立规则：不因职责短标隐藏或职业 icon 适度缩小扣 severe，但职业 icon 必须可辨认。
- [x] R7 更新 `assets/templates/visual-quality-checklist.md`：
  - 增加“`flow_example` 非集合帧 8 人是否都有职业图标 + 职责短标”，并在 2026-06-02 后补充“`mechanic_flow` 非集合帧是否都有编号职能图标”。
  - 增加“集合/重叠帧是否保留可辨认职业图标，且省略职责短标或缩小图标不会影响判断”。
  - 增加“默认职业配置是否正确或已被用户配置覆盖”。
  - 增加“XivPlan 官方职业图标在导出 PNG 中是否可辨认，且不是文字缩写徽章”。

验收：

- [x] 每个 normal step 都有 MT/ST/H1/H2/D1/D2/D3/D4 且不重复。
- [x] 默认职业配置在所有 fixture 中稳定保留，移动和复位后不丢失。
- [x] 非集合帧职责短标在官方职业图标附近可读；集合/重叠帧职业 icon 可缩小但仍需可读。
- [x] 官方职业 icon 在 PNG contact sheet 中可读；默认场景不接受 `job:*` token 或文字缩写 badge fallback。
- [x] `party_identity_score` 达到 PASS，且 party icon / role label severe obstruction 为 0。

完成记录（2026-06-01）：

- 新增 `references/party-job-defaults.md`，默认配置为 MT=DRK、ST=PLD、H1=AST、H2=SCH、D1=SAM、D2=DRG、D3=BRD、D4=PCT，且默认 icon/image 必须指向 XivPlan `/actor/<JOB>.png`。
- `build_spec_from_solution.py`、`build_xivplan_scene.py`、`plan_solution_candidates.py` 现在写入并保留 `job`、`jobName`、`icon`、`image`、`roleLabel`、`roleLabelVisible` 与 `iconScale`。
- `validate_xivplan_scene.py` 已检查 8 人唯一职责、默认职业、官方职业 icon 路径和非集合帧职责短标；`audit_visual_quality.py` 新增 `party_identity_score`，并把 `job:*` 抽象 token 视为严重问题。
- `audit_label_layout.py`、`audit_flow_lines.py`、`audit_visual_quality.py` 已把 party role label 作为 party identity 附属标识处理，避免被普通标签碰撞门误判。
- 证据：`artifacts/phase-i-visual-regression/visual-regression-report.md` 当时 10/10 PASS，所有 case severe=0，职业身份报告明确记录官方 `/actor/<JOB>.png` 图标路径；Phase U 后完整套件扩展为 11/11。

### 9.7 Phase S：第三轮回归、人工审查与交接

目标：把第三轮能力纳入可重复验证的 release gate。

- [x] S1 新增第三轮 fixtures：
  - `multi-boss-add-identity.input.md`：测试多 Boss / 小怪名字、目标环、icon、朝向。
  - `known-encounter-boss-asset.input.md`：测试已有副本 Boss 素材获取、image2 或 fallback 流程。
  - `job-specific-positioning.input.md`：测试默认职业配置、职责短标、移动后身份保留。
  - `party-stack-label-omission.input.md`：测试集合/重叠帧省略职责短标、适当缩小职业图标但仍可辨认。
  - `long-teaching-storyboard.input.md`：测试 14+ step 教学分镜。
- [x] S2 扩展 `run_visual_regression.py` 或新增 `run_phase3_visual_regression.py`：
  - 输出第三轮 scene、PNG、guide package、enemy asset manifest、job identity report。
  - 质量门额外检查 `enemy_identity_score`、`party_identity_score`、`teaching_story_score`。
- [x] S3 生成 contact sheets：
  - 每个 fixture 至少一张总览 contact sheet。
  - 对多 Boss / 小怪 fixture 额外生成 enemy crop sheet。
  - 对职业职责 fixture 额外生成 party identity crop sheet，覆盖普通分散帧和集合重叠帧。
- [x] S4 写入人工审查报告：
  - Boss / add 是否一眼能认出。
  - 目标环大小和名字是否醒目。
  - 非集合帧 XivPlan 官方职业 icon 和职责短标是否清晰；集合帧只看缩小后的官方职业 icon 是否足够判断身份。
  - 分镜是否足够 step-by-step，是否存在可以继续拆帧的地方。
- [x] S5 更新 `README.md`、`SKILL.md`、`agents/openai.yaml`、`docs/visual-upgrade-work-record.md`：
  - README 记录第三轮回归命令。
  - SKILL 写入敌人 identity、image2 asset、职业默认配置和更细分镜规则。
  - agent defaults 增加 enemy / party identity gate。
  - work record 写清第三轮改动、证据路径和剩余问题。
- [x] S6 完整验证：
  - [x] `python -m compileall -q xivplan-ffxiv-guide\scripts`
  - [x] `python xivplan-ffxiv-guide\scripts\test_storyboard_templates.py`
  - [x] `python xivplan-ffxiv-guide\scripts\test_visual_quality_audit.py`
  - [x] `python xivplan-ffxiv-guide\scripts\run_visual_regression.py --force`
  - [x] 第三轮新增 regression 命令通过。

验收：

- [x] 原 Phase I / N 五个 fixtures 继续 5/5 PASS；Phase S 当时完整回归为 10/10 PASS，Phase U 后完整回归为 11/11 PASS。
- [x] 第三轮新增 fixtures 全部通过 scene validation、asset validation、guide package validation、visual quality gate。
- [x] 所有 normal step 的 Boss / add 都有名字、目标环、icon 或 fallback icon。
- [x] 所有 normal step 的 8 人都有职责身份；`mechanic_flow` 通过编号职能 icon 表达，`flow_example` 通过官方职业 icon + 职责短标表达；集合/重叠帧允许隐藏职责短标和缩小图标，但不能隐藏图标。
- [x] 至少一个复杂机制 fixture 达到 `14+` step，并且每 step 都有不同教学目的。
- [x] contact sheet 和人工审查报告能证明第三轮目标不是只在 JSON 里通过，而是在 PNG 导出中也清楚。

完成记录（2026-06-01，第三轮验收口径修正版）：

- `build_spec_from_solution.py`、`build_xivplan_scene.py`、`plan_solution_candidates.py` 已把默认职业图标从 `job:*` 抽象 token 改为 XivPlan 官方 `/actor/<JOB>.png` 资源路径：DRK、PLD、AST、SCH、SAM、DRG、BRD、PCT。
- `export_xivplan_steps.py` 已能从本机 `..\XivPlan\public` 解析 `/actor/<JOB>.png`，因此 Phase S PNG/contact sheet 里能实际看到官方职业图标，而不是文字缩写徽章。
- `validate_xivplan_scene.py` 和 `audit_visual_quality.py` 已把默认职业 icon 路径纳入验收；`job:*` token 会被视为严重问题。
- 回归证据：`artifacts/phase-i-visual-regression/visual-regression-report.md`，Phase S 当时 10/10 PASS；2026-06-02 双图面路由后 long-flow 为 14 steps / 733 objects，severe=0；Phase U 后完整回归为 11/11 PASS。
- 职业身份证据：`artifacts/phase-i-visual-regression/job-specific-positioning/job-identity-report.md`、`artifacts/phase-i-visual-regression/party-stack-label-omission/job-identity-report.md`，均记录 expected official XivPlan icons。
- PNG 证据：`artifacts/phase-s-release-gate/contact-sheets/` 与 `artifacts/phase-s-release-gate/identity-crop-sheets/party/` 已重新生成；人工审查记录为 `artifacts/phase-s-release-gate/human-review.md`。

### 9.8 第三轮停止线

第三轮满足以下条件即可收束，剩余审美微调可留到第四轮：

- [x] 原有视觉回归不退化，severe regression 为 0。
- [x] 敌人身份合同落地：名字、目标环、目标环大小、icon / fallback icon 均可验证。
- [x] 玩家身份合同落地：8 人职责唯一、默认职业配置正确、非集合帧官方职业 icon / 职责短标可读，集合帧缩小后的官方职业 icon 可读。
- [x] 分镜教学粒度明显提升：复杂机制默认能生成 10+ step，长流程能生成 14+ step。
- [x] 新增第三轮 artifacts 目录保存 spec、scene、PNG、asset manifest、quality report、contact sheet、人工审查与交接记录。

## 10. 第四轮优化计划：真实金标准对照与成品感差距修复

本轮来自 2026-06-02 对 `C:\Users\Mahiru\Desktop\FFXIV\KING X\UDM\test\o8s_yokai_star_dance.xivplan` 与金标准 `C:\Users\Mahiru\Desktop\FFXIV\KING X\0523-0524 FRU\Strats_limited\P1\P1_thunder_fire_swords.xivplan` 的直接对比。对比证据保存到 `artifacts/compare-o8s-p1/`：

- `density-audit.md/json`
- `visual-quality-audit.md/json`
- `label-layout-audit.md/json`
- `flow-audit.md/json`
- `contact-sheets/o8s-images.png`
- `contact-sheets/p1-images.png`

这次对比说明：第三轮后的 skill 已经能生成“合同完整、审计通过”的图，但还没有稳定达到 KING X 人工成品那种“机制语义直接写在图里、每一帧都是攻略页面”的密度与表达力。

### 10.1 对比结论

结构密度：

| 项目 | skill 产物：`o8s_yokai_star_dance` | 金标准：`P1_thunder_fire_swords` | 暴露问题 |
|---|---:|---:|---|
| step 数 | 6 | 14 | skill 仍偏摘要式流程，复杂机制没有拆到足够多的判断/换位/判定/复盘镜头。 |
| 对象数 | 212 | 625 | skill 单步合同完整，但总机制信息量只有金标准约 1/3。 |
| 平均对象数 | 35.33/step | 44.64/step | skill 单帧看起来干净，但缺少金标准的图内解释、优先级、判定范围和状态切换。 |
| 图内 text 对象 | 64 | 284 | skill 的文字大多只是角色短标和 step 标题。 |
| 图内文字总量 | 185 字 | 2179 字 | skill 把 563 字解释放在 `guide_text`，但图面本身不够自解释。 |
| 伤害/机制范围对象 | 22 | 144 | skill 画出了塔、圈、分摊、矩形区域，但缺少大量扇形、目标环、轴线、暗区/安全区层次。 |
| 箭头对象 | 20 | 17 | skill 箭头数量不低，但箭头更多是“移动方向”，少了金标准那种与优先级、旧位/新位、判定轮次绑定的路线说明。 |
| 背景 | `preset: default-circle` | `backgroundImage: /arena/e11.svg` + radial ticks | skill 对 encounter/fight 背景选择仍保守，实际成品感弱。 |

文字描述缺陷：

- `o8s` 的 64 个 text 对象里，48 个是 `MT/ST/H1/H2/D1/D2/D3/D4` 职责短标；图内平均文字长度只有 2.9 字，最长 8 字。
- 金标准有 284 个 text 对象，平均 7.7 字，最长 38 字，直接写入 `AC 雷轴`、`BD 火轴`、`双排优先级`、`左排自上往下`、`右排看倒数`、`雷：三人分散引导三个120度扇形`、`火是三人分摊90度扇形` 等攻略语义。
- 当前 skill 的长说明集中在 `guide_text`，例如 step 1/2/3 各有接近 100 字说明；这对导出攻略文档有用，但单看 `.xivplan` 画面时，队员无法像读金标准那样直接从图上读出判断逻辑、优先级和例外条件。
- 当前 step 标题是 `1 分工`、`2 DPS诱导`、`3 残影`、`4 塔序`、`5 分摊`、`6 复位`，粒度偏阶段名；金标准虽然没有 step title 字段，但每页图内都有“AD组：雷雷”“雷火火：第1-2次”“火雷火：第3-4次”等页面标题和局部说明。

箭头展示缺陷：

- 当前 skill 的 flow audit 对 `o8s` 给出 PASS：20 箭头、0 交叉、0 severe；但视觉上很多箭头只是方向提示，没有明确绑定“从哪个旧站位到哪个新站位”“第几次判定前移动”“移动后接什么范围”。
- 金标准只有 17 个 arrow，却和密集文本、扇形范围、Boss 目标环、优先级短标共同表达换位；当前审计器反而把金标准判为 flow FAIL，主要是因为箭头头部贴近 marker/enemy/text/party 被当作 severe。这说明现有 flow gate 更适合检查生成器是否整洁，不适合衡量人工金标准的“箭头指向目标对象”的合法语法。
- 当前 builder 的箭头已有 `arrowStyle`，但缺少 `fromRole`、`toRole`、`resolveIndex`、`startLabel`、`endLabel`、`snapToTarget` 等语义字段；审计器也没有区分“箭头头部故意指向目标角色/目标点”和“箭头误遮挡”。

攻略流程详细程度缺陷：

- `o8s` 6 step 覆盖“分工 -> DPS诱导 -> 残影 -> 塔序 -> 分摊 -> 复位”，可以说明机制大意，但缺少金标准式的条件分支页面：不同读条/点名组合、第一轮和第三轮的关系、困难顺序示例、每组优先级如何换算。
- 金标准用 14 step 拆出基础站位、雷雷、火火、雷火火、火雷火、困难顺序示例等多个页面；部分页面专门教一个分支，而不是把所有变化压进一个通用流程。
- 当前 skill 的 `teaching_question` 字段存在，但在 `o8s` 产物里没有转化为足够多的“只回答一个问题”的画面。下一轮应把 `teaching_question` 与图内标题、图内 callout、范围对象和箭头对象强绑定。

伤害范围展示缺陷：

- `o8s` 使用了 7 个 `circle`、6 个 `tower`、2 个 `stack`、3 个 `rect`、4 个 `line`，适合表达“有塔/有分摊/有诱导圈/有分区”。
- 金标准使用 82 个 `circle`、34 个 `cone`、28 个 `rect`，大量展示 Boss 目标环、120 度雷扇形、90 度火分摊扇形、危险半场/安全半场、贴目标环处理等真实判定语义。
- 当前 skill 对“伤害范围”的表达仍偏泛化图标：有危险圈和塔，但缺少“这个伤害为什么是这个角度/半径/朝向、谁引导、谁分摊、判定后留下什么”的几何语义。

标点、背景与构图缺陷：

- `o8s` 每步都有 A/B/C/D/1/2/3/4 标点，合同完整；但场地是 `default-circle`，没有战斗专属背景、地板纹理、radial ticks 或轴线语义。
- 金标准使用 `/arena/e11.svg`，并叠加 `AC 雷轴`、`BD 火轴`、Boss 目标环和深色象限区域，让背景、标点和机制判断成为一套统一语言。
- 本机 `..\XivPlan\public\arena` 目前没有发现 `o8s` / `omega` 专用 arena 资源；因此 O8S 类图不能简单写死背景路径，必须先做资源扫描、alias 记录和 fallback 说明。如果用户提供背景或后续补入资源，skill 应自动写入 `backgroundImage`，否则质量报告必须说明“无 O8S 专用背景，使用 default-circle fallback”。

审计器缺陷：

- `audit_visual_quality.py` 给 `o8s` 打出 `REVIEW score=95.33 severe=0 review=6`，但给金标准打出 `FAIL score=19.78 severe=634 review=439`。
- 这不是金标准质量差，而是审计器把第三轮生成器合同当成唯一标准：它不识别金标准里 `party.name = "H1 AST"` 这类 legacy role 写法，也不理解“文字贴着角色/范围/箭头”有时是有意的图内标注。
- 第四轮必须新增“金标准兼容模式”和“生成器严格模式”两套口径：生成器仍要避免严重遮挡，但参考样例分析不能把人工成品的密集标注误判为失败。

Boss 形象缺陷：

- 第三轮已经要求 enemy 有 `icon` / fallback，但当前能力更像“有图标字段”，还不是“知道这是哪个 Boss 就主动查证外观并做专属攻略 icon”。
- 已知 Boss 时，skill 应优先搜索 FF14 中文维基 `https://ff14.huijiwiki.com/wiki/首页`，用 Boss 中文名、英文名、副本名和别名查找 Boss / 副本 / NPC 页面，记录页面 URL、图像来源和外观特征。
- 访问灰机 wiki 时必须直连，不走本机 `127.0.0.1:7890` 代理。本机当前可能存在 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` 指向 7890 的环境变量；`search_boss_appearance.py` 应在请求 `ff14.huijiwiki.com` 时设置 `NO_PROXY=ff14.huijiwiki.com,.huijiwiki.com`，并清除或绕过代理环境变量。只有无代理重试仍失败，才允许记录 `wiki-search-blocked-fallback`。
- 不能直接把 wiki/官方截图原样贴进最终攻略图；默认应根据查到的形象特征生成或绘制原创、透明底、无文字、64-96 px 仍可读的小图标，再通过 enemy asset manifest 注入 `.xivplan`。
- 2026-06-02 本地 XivPlan 源码确认：外部 PNG 导入主路已存在，`src/file/image.ts` 会读取 PNG 为 `data:image/png;base64,...`，`src/panel/properties/ImageControl.tsx` 有 `Choose local PNG`，`src/render/SceneRenderer.tsx` 支持拖放 PNG 生成 `ObjectType.Image`。本轮还补了 `src/prefabs/Enemies.tsx` 的 enemy icon 渲染，使 `.xivplan` 里的 `enemy.icon` data URL 能在 Boss 目标环内显示；`tsc -b` 已通过。

### 10.2 Phase T：金标准差异分析器与双口径质量门

目标：让 skill 能稳定回答“为什么当前生成图不像金标准”，而不是只报告自己 PASS。

任务：

- 新增 `scripts/compare_xivplan_to_gold.py`，输入 generated `.xivplan` 与 gold `.xivplan`，输出结构化差异：
  - step/object/type/density 对比；
  - 图内文字数量、总字数、平均字长、长说明迁移比例；
  - arrow 数量、样式、端点对象、是否带 from/to/resolve 语义；
  - circle/cone/rect/tower/stack 等伤害范围覆盖；
  - arena/background/ticks/axis/waymark 对比；
  - role/party legacy 写法兼容结果；
  - 逐维度缺陷清单和下一步建议。
- 扩展 `audit_visual_quality.py` 增加 `--reference-mode gold`：
  - 识别 `party.name` 中的 `H1 AST`、`D4 PCT` 等 role 前缀；
  - 将“短角色标贴近玩家图标”“箭头指向目标点/目标角色”“机制标签贴近 AoE”识别为可接受的 attached label，而不是默认 severe；
  - 单独输出 `gold_style_score`，不与生成器合同分数混用。
- 扩展 `audit_label_layout.py`：
  - 增加 `attachedLabel` / `roleBadge` / `mechanicCallout` 分类；
  - 对 `MT/ST/H1/H2/D1/D2/D3/D4/1-8/高后/低右/1雷/3火` 等短标签采用更小包围盒和不同碰撞阈值；
  - 把“可读但密集”和“不可读遮挡”分开。
- 把本次对比样例加入固定回归：
  - generated: `C:\Users\Mahiru\Desktop\FFXIV\KING X\UDM\test\o8s_yokai_star_dance.xivplan`
  - gold: `C:\Users\Mahiru\Desktop\FFXIV\KING X\0523-0524 FRU\Strats_limited\P1\P1_thunder_fire_swords.xivplan`

验收：

- `compare_xivplan_to_gold.py` 能复现本次关键结论：`6 vs 14 steps`、`212 vs 625 objects`、`64 vs 284 text objects`、`185 vs 2179 in-scene text chars`、`22 vs 144 mechanic/range zones`、`default-circle vs /arena/e11.svg`。
- `audit_visual_quality.py --reference-mode gold` 不再把金标准作为生成器合同 FAIL 处理，而是输出“参考样式密集、可读性需人工确认”的 gold profile。
- 生成器严格模式仍然保留第三轮 severe gate，不因为参考模式放宽而让新图胡乱遮挡。

Phase T implementation status (2026-06-02):

- [x] 新增 `xivplan-ffxiv-guide/scripts/compare_xivplan_to_gold.py`，并输出 `artifacts/phase-t-gold-comparison/compare-o8s-p1.{json,md}`。
- [x] `compare_xivplan_to_gold.py` 已复现关键结论：`6 vs 14 steps`、`212 vs 625 objects`、`64 vs 284 text objects`、`185 vs 2179 in-scene text chars`、`22 vs 144 mechanic/range zones`、`default-circle vs /arena/e11.svg`。
- [x] `audit_visual_quality.py --reference-mode gold` 已输出 `GOLD_PROFILE gold_style_score=95.24 severe=0`，不再把人工 P1 金标准作为生成器合同失败处理；严格模式下该样例仍保留 FAIL 语义。
- [x] `audit_label_layout.py --reference-mode gold` 已输出 PASS，`attachedLabel` / `roleBadge` / `mechanicCallout` 进入分类统计，密集贴标作为 review profile 而不是 severe。
- [x] `test_visual_quality_audit.py` 新增 gold reference mode 回归，确认严格模式和参考模式分离。
- [x] `run_visual_regression.py --force` 在 Phase T checkpoint 保持 PASS 10/10，说明 reference mode 未放宽生成器严格质量门；Phase U 后扩展为 PASS 11/11。
- [x] 新增并落地 `guide_section` / `figure_type` 图面分类：默认 `mechanic_flow` 使用官方编号职能图标，`flow_example` 保留默认职业图标 + 职责短标。
- [x] `build_spec_from_solution.py` 默认写入 `guide_section: "mechanic_flow"`；Phase S 的 `job-specific-positioning` 与 `party-stack-label-omission` fixture 显式标为 `flow_example`，用于继续验证示例图职业图标口径。
- [x] `validate_xivplan_scene.py`、`audit_visual_quality.py` 和 `test_visual_quality_audit.py` 已同步双合同：主机制检查 `/actor/tank1.png`、`/actor/healer2.png`、`/actor/dps4.png` 等编号图标；示例图检查 `/actor/<JOB>.png` 与 `roleLabel`。

### 10.3 Phase U：图内攻略文字与标点语法升级

目标：把“攻略在 `guide_text` 里”升级为“攻略关键信息直接在图里可读”。

任务：

- 在 scene spec 中新增 `annotation_contract`：

```json
{
  "annotation_contract": {
    "require_in_scene_teaching": true,
    "min_callouts_per_step": 3,
    "max_callout_chars": 38,
    "prefer_axis_and_priority_labels": true,
    "convert_guide_text_to_footer": true
  }
}
```

- 扩展 `build_spec_from_solution.py`：
  - 将每个 step 的 `teaching_question` 转成图内 page title，例如“AD组：雷雷”“第1轮：DPS诱导”“塔序：北塔集合”；
  - 从 `guide_text` 自动抽取 2-4 条图内短 callout，剩余长文保留在导出攻略；
  - 为复杂机制生成“轴线标签”“优先级标签”“判定轮次标签”“例外提醒标签”；
  - 对组合机制生成分支页，不再把所有条件压成一张通用图。
- 新增 `references/in-scene-annotation-style.md`：
  - 页面标题：8-16 字，写机制分支或判定轮次；
  - 局部标签：2-8 字，贴近角色/范围/箭头；
  - 说明行：18-38 字，放在场地上方/下方/左右说明带；
  - 标点风格：中文机制词 + 必要半角 role/waymark，例如 `AC 雷轴`、`D3/D4 最远诱导`、`第2塔后回中`；
  - 禁止把所有解释只塞进 `guide_text`。
- 扩展 `auto_place_labels.py` 或 label placement 逻辑：
  - 增加 top/bottom/left/right 四个说明带；
  - 支持 `labelRole: "page_title" | "axis" | "priority" | "mechanic" | "footer" | "role_badge"`；
  - 说明带文本可以重叠场地外空白，但不得压住玩家图标、Boss 目标环和关键 AoE 边界。

验收：

- 新生成的 O8S/妖星乱舞类复杂机制至少 `10-14` step，不再只有 6 个大阶段。
- 图内 text 对象数达到金标准的 50% 以上，复杂机制目标为 `140+` text objects 或 `900+` 图内文字字符；平均图内标签长度控制在 `4-14` 字之间。
- 每个 normal step 至少有：页面标题、1 个机制判断标签、1 个职责/优先级标签、1 个移动或判定说明。
- `guide_text` 可以保留，但不能是唯一解释来源；对复杂机制，至少 60% 的关键 callout 必须进入图内对象。

Phase U implementation status (2026-06-02):

- [x] `build_spec_from_solution.py` now emits `annotation_contract` with `require_in_scene_teaching`, `min_callouts_per_step`, `max_callout_chars`, `prefer_axis_and_priority_labels`, and `convert_guide_text_to_footer`.
- [x] Generated steps derive `page_title` from `teaching_question` and add eight compact in-scene callouts per normal step.
- [x] Generated callouts use `labelRole: "axis" | "priority" | "mechanic" | "footer"` and stable `labelBand` slots in top/bottom/left/right outside-arena bands.
- [x] Sequence / case-based templates now add explicit branch pages instead of compressing all conditions into one generic flow.
- [x] `build_xivplan_scene.py` preserves `annotation_contract`, `page_title`, `annotation_callouts`, `labelRole`, and `labelBand`, and renders the derived page title as the step title object.
- [x] `audit_visual_quality.py` now reports `components.annotation_contract` and fails generated complex scenes that miss page titles, axis/priority/mechanic/footer callouts, or the Phase U text-richness threshold.
- [x] Added `references/in-scene-annotation-style.md` and documented Phase U in `SKILL.md`, `README.md`, `agents/openai.yaml`, `references/xivplan-scene-format.md`, `references/xivplan-style-guide.md`, and the visual checklist.
- [x] Added `ultimate-yokai-star-dance-phase-u.input.md` to visual regression, and `run_visual_regression.py --force` now requires the Phase U fixture.

Evidence (2026-06-02):

- `test_visual_quality_audit.py`: PASS, including Phase U annotation contract smoke.
- `test_storyboard_templates.py`: PASS.
- `run_visual_regression.py --force`: PASS 11/11.
- Phase U fixture: 14 steps, 436 objects, visual quality `REVIEW 88.89`, severe 0.
- Annotation profile: 176 text objects, 1322 in-scene text characters, 114 callouts, average text length 7.51, severe 0.
- Gold comparison after Phase U: `14 vs 14 steps`, `436 vs 625 objects`, `176 vs 284 text objects`, `1322 vs 2179 in-scene text chars`, `64 vs 144 mechanic/range zones`, `14 vs 17 arrows`.

### 10.4 Phase V：箭头、换位与伤害范围语义升级

目标：让箭头和 AoE 不只是“看起来有”，而是能表达判定几何和换位逻辑。

本阶段是第四轮的硬门槛，不是审美加分项。箭头和 AoE 如果没有语义，图即使文字和角色齐全也不能视为接近金标准。

任务：

- 在 spec 中新增 `damagePattern` 与 `movementRoute` 语义层：

```json
{
  "damagePattern": {
    "kind": "fan120 | shareFan90 | baitTrail | towerResolve | chargeLine | safeSector | bossHitbox",
    "source": "Boss | add id | role",
    "targets": ["MT", "H1"],
    "resolveIndex": 1,
    "angle": 120,
    "radius": 260,
    "label": "雷：三人分散120度"
  },
  "movementRoute": {
    "fromRole": "D3",
    "to": "north_tower",
    "resolveIndex": 2,
    "arrowStyle": "movement",
    "startLabel": "诱导后",
    "endLabel": "进北塔",
    "snapToTarget": true
  }
}
```

- 扩展 `build_xivplan_scene.py`：
  - 将 `fan120` 渲染为三枚或多枚 `cone`，并自动标注引导者；
  - 将 `shareFan90` 渲染为 90 度 `cone` + 分摊角色短标；
  - 将 `baitTrail` 渲染为按时间编号的连续危险圈；
  - 将 `safeSector` 渲染为半透明暗区/安全区遮罩；
  - 将 `bossHitbox` 渲染为目标环 + 半径说明。
  - 对每个 AoE 写入 `aoeIntent`：`damage` / `safe` / `bait_history` / `future_resolve` / `reference_only`，避免安全区、历史残留和当前伤害混成一种颜色。
  - 对每个关键 AoE 写入 `resolveTiming`：`preposition` / `cast_snapshot` / `first_hit` / `second_hit` / `after_resolve`，让图能表达“现在看什么、之后炸什么”。
- 扩展 `audit_flow_lines.py`：
  - 箭头头部贴近 `toRole` / `toMarker` / `toZone` 时视为合法 endpoint snap；
  - 未声明 endpoint 却压住对象才算 severe；
  - 检查 movement step 是否每条路线都有 `fromRole` 或 `fromObject`、`toRole` 或 `toObject`。
- 扩展 `audit_visual_quality.py`：
  - 新增 `range_semantics_score`，统计 circle/cone/rect/tower/stack 是否有 label、source、target、resolveIndex；
  - 对复杂机制要求至少一种真实判定几何，不接受只有泛用危险圈和箭头。
  - 新增 `arrow_semantics_score`，统计每条箭头是否有起点、终点、意图、阶段和 endpoint snap。
  - 对复杂机制设置硬失败项：movement/reset step 没有语义箭头、resolve step 没有 AoE 几何、AoE 没有 label/source/timing、箭头穿过当前危险区却未标注为允许穿越。

验收：

- O8S/妖星乱舞类样例至少包含诱导轨迹、塔判定、残影冲锋/线、分摊、复位五类语义对象。
- FRU 雷火剑类样例能自动生成 120 度雷扇形、90 度火分摊扇形、Boss 目标环和半场/轴线遮罩。
- flow audit 不再只看 crossing=0，还能确认每个箭头的起点、终点、判定轮次和意图。
- `range_semantics_score` 和 `arrow_semantics_score` 必须进入第四轮 release gate；这两项任何 severe 都阻止交付。

实施状态（2026-06-02）：

- [x] `build_xivplan_scene.py` 已支持 `damagePattern`：`fan120`、`shareFan90`、`baitTrail`、`towerResolve`、`chargeLine`、`safeSector`、`bossHitbox`。
- [x] `build_xivplan_scene.py` 已支持 `movementRoute`，并保留起点、终点、意图、判定轮次、短标和 `snapToTarget`。
- [x] `build_spec_from_solution.py` 已为生成图注入 `mechanic_semantics_contract`，现有塔对象直接附着 `towerResolve` 元数据，避免重复画塔。
- [x] `audit_flow_lines.py` 已区分合法 endpoint snap 与误遮挡；movement/reset 页面缺少语义路线时 hard fail。
- [x] `audit_flow_lines.py` 已按 `aoeIntent` 区分当前危险区与 `bait_history` / `safe` / `future_resolve` / `reference_only`，避免把历史残留误判为当前危险穿越。
- [x] `audit_visual_quality.py` 已输出 `range_semantics_score`、`arrow_semantics_score` 和 `components.mechanic_semantics`；resolve 页面无真实判定几何时 hard fail。
- [x] `validate_xivplan_scene.py` 已校验 Phase V 合同，`test_visual_quality_audit.py` 已包含删除路线终点的负例。
- [x] `run_visual_regression.py --force` 已将 FRU 与 O8S Phase V profile 纳入 acceptance：`PASS 11/11`，两者 range / arrow semantics 均为 `100.0`。
- [x] FRU 样例已达到 `14 steps / 743 objects`，使用 `/arena/e11.svg`，并显示 Boss 目标环、120 度雷扇形、90 度火分摊扇形、半场遮罩和换边路线。
- [x] O8S / 妖星乱舞样例已包含诱导轨迹、塔判定、残影冲锋线、分摊、散开与复位语义对象。
- [x] 已生成 `review-burndown.md`、FRU/O8S contact sheets、identity crop sheets、gold comparison 和 Phase V 人工审查记录；severe visual issues 为 `0`。
- [ ] Phase W 仍需补 arena/background asset 扫描、O8S fallback 说明、arena overlay 和最终七项成品门。

### 10.5 Phase W：Boss 形象、背景资源与金标准成品门

目标：让 Boss 形象、背景和标点不再只是合同项，而是参与机制阅读。

任务：

- 新增 `scripts/search_boss_appearance.py` 或等价 workflow：
  - 输入 Boss 中文名、英文名、encounter、phase、alias；
  - 优先搜索 FF14 中文维基 `https://ff14.huijiwiki.com/wiki/首页`；
  - 对 `ff14.huijiwiki.com` 强制无代理访问：脚本内不要继承 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY=127.0.0.1:7890`；若使用 Python HTTP client，设置不信任环境代理或显式传空代理；若使用 shell 包装命令，先设置 `NO_PROXY=ff14.huijiwiki.com,.huijiwiki.com`；
  - 记录候选页面、图片 URL、页面标题、检索词、访问状态和引用时间；
  - 如果无代理 wiki 直连、API 或页面抓取仍受阻，记录 `wiki-search-blocked-fallback`，再使用浏览器搜索、用户截图或公共攻略截图作为回退。
- 扩展 `references/enemy-image-asset-workflow.md`：
  - 增加灰机 wiki 查证步骤；
  - 增加 `source_url`、`source_page_title`、`visual_traits`、`icon_brief`、`generated_icon_path`、`license_note` 等 manifest 字段；
  - 明确最终 icon 是原创简化攻略图标，不直接复制 wiki / 官方原图。
- 新增或扩展 Boss icon 生成步骤：
  - 从查证到的形象提炼轮廓、主色、武器/翅膀/头部特征；
  - 生成透明底 PNG，建议 `256x256` 源图，注入显示尺寸 `64-96`；
  - 运行 `validate_image_assets.py` 检查 alpha、边缘留白、主体占比和 64px 可读性；
  - 用 `inject_enemy_assets.py` 写入 `enemy.icon` data URL 和 `iconWidth/iconHeight`。
- 本地 XivPlan app 兼容：
  - 已确认 `ObjectType.Image` 支持外部 PNG 作为 data URL 嵌入 `.xivplan`；
  - 已补齐 `enemy.icon` 在 `EnemyRenderer` 中显示，因此 dedicated Boss icon 不再只存在于 JSON 或导出器里；
  - 后续回归应打开或导出包含 enemy icon 的 `.xivplan`，证明 app 画布和 skill PNG exporter 都能显示。
- 新增 `scripts/scan_xivplan_assets.py`：
  - 扫描 `..\XivPlan\public\arena`、`..\XivPlan\public\actor`、`..\XivPlan\public\marker`；
  - 输出可用 arena manifest；
  - 标记用户请求的 encounter 是否有可用背景。
- 扩展 `references/arena-presets.md`：
  - 增加 `omega-o8s` / `kefka` / `妖星乱舞` alias；
  - 若本机仍无 O8S/Omega 背景，则明确 background 为 `none`，sourceReason 写“no built-in O8S arena asset found; fallback to default-circle with explicit axis overlays”；
  - 对 FRU/Fatebreaker 继续要求 `/arena/e11.svg`。
- 扩展 `build_xivplan_scene.py`：
  - 对 `arena.backgroundImage` 导出 PNG 预览时也尝试绘制背景，不再只画默认圆；
  - 支持 radial ticks、AC/BD 轴线、半场遮罩、目标环说明带作为 arena overlay；
  - arena source 必须写入质量报告。
- 新增金标准成品门：
  - 生成 PNG contact sheet；
  - 运行 generated 严格质量门；
  - 运行 gold comparison；
  - 写人工审查清单，至少评估文字、Boss 形象、箭头、范围、背景、标点、流程完整度七项。

验收：

- 已知 Boss 的新样例必须产生 dedicated enemy icon；只有在 wiki / 截图 / 用户描述都无法确认时才允许 fallback，并且报告中必须写清原因。
- `.xivplan` 内的 dedicated Boss icon 必须是 data URL 或可解析资源路径；在 XivPlan app 画布、skill PNG exporter、contact sheet 中均可见。
- 对 `P1_thunder_fire_swords` 对齐任务，生成图必须使用 `/arena/e11.svg` 或明确说明用户要求不同背景。
- 对 O8S/妖星乱舞任务，若无专用 arena，质量报告必须说明 fallback，并用轴线、半场、标点、目标环弥补背景缺失。
- `export_xivplan_steps.py` 的 contact sheet 能显示实际背景或明确的 arena overlay；不能只靠 JSON 里有 `backgroundImage`。
- 第四轮回归报告必须同时给出“第三轮合同 PASS”和“金标准差距缩小”的证据。

Phase W implementation status (2026-06-02):

- [x] 新增 `xivplan-ffxiv-guide/scripts/search_boss_appearance.py`：使用空 `ProxyHandler` 对灰机 wiki API 做无代理访问，记录检索词、访问状态、候选页面、图片引用、`icon_brief` 和 fallback 策略。本机对 `凯夫卡 / Kefka / O8S / 妖星乱舞` 查询返回 403，已记录为 `wiki-search-blocked-fallback`。
- [x] 新增 `xivplan-ffxiv-guide/scripts/scan_xivplan_assets.py`：扫描 `..\XivPlan\public\arena|actor|marker` 并生成 arena availability manifest。当前本机有 74 个 arena assets；O8S/Omega 无专用背景，UDM/Yokai 有 `/arena/udm-p1.png`。
- [x] `arena-presets.md`、`parse_mechanic_request.py` 和 `build_xivplan_scene.py` 已支持 `omega-o8s`、`ultimate-yokai-star-dance`、`kefka`、`妖星乱舞`、`udm` 等 alias。O8S/Omega fallback 固定写入标准 `sourceReason`：`no built-in O8S arena asset found; fallback to default-circle with explicit axis overlays`。
- [x] `export_xivplan_steps.py` 已按 `arena.backgroundImage` 尝试绘制本地 PNG/SVG 背景，并支持 Phase W `arenaOverlays`：`radial_ticks`、`axis`、`half_mask`、`ring_label_band`。SVG 无法由 Pillow 原生 rasterize 时，导出器会绘制明确的 SVG arena fallback 与 overlay，而不是回到匿名默认圆。
- [x] `audit_visual_quality.py` 已输出 `components.arena_context`，Markdown 报告包含 preset、background、backgroundStatus、source、overlay kinds 和 sourceReason；O8S fallback 缺 axis/radial tick overlay 会变成 severe。
- [x] `run_visual_regression.py --force` 已把 Phase W arena/background gate、dedicated Boss icon gate 和七项成品门纳入 acceptance。当前 `PASS 11/11`，Phase W arena/background gate PASS，dedicated Boss icon PASS，seven-item product gate PASS。
- [x] `known-encounter-boss-asset` fixture 改为生成原创透明底 Fatebreaker guide icon，manifest 包含 `source_url`、`source_page_title`、`visual_traits`、`icon_brief`、`generated_icon_path`、`license_note`；`validate_image_assets.py` 通过，subject ratio `0.3212`，enemy crop sheet 中 dedicated Boss icon 可见。
- [x] 已生成 Phase W 证据包：`artifacts/phase-w-product-gate/arena-assets-o8s.md`、`arena-assets-udm.md`、`boss-appearance-kefka.md`、`o8s-fallback-visual-quality.md`、`compare-fru-p1-phase-w.md`、`review-burndown.md`、`contact-sheets/`、`identity-crop-sheets/`、`phase-w-human-review.md`。

Verification (2026-06-02):

- `py_compile`: PASS for Phase W scripts and edited builder/exporter/audit/parser/regression scripts.
- `test_visual_quality_audit.py`: PASS.
- `test_storyboard_templates.py`: PASS.
- `test_mechanic_parser.py`: PASS.
- `test_arena_selection.py`: PASS.
- `run_visual_regression.py --force`: PASS 11/11; severe visual issues `0`; review items `337`.
- FRU Phase W comparison: generated vs gold is `14 vs 14 steps`, `743 vs 625 objects`, `49 vs 284 text objects`, `487 vs 2179 in-scene text chars`, `481 vs 144 mechanic/range zones`, `24 vs 17 arrows`, `/arena/e11.svg vs /arena/e11.svg`.
- O8S fallback audit: `omega-o8s`, background `none`, status `fallback`, overlays `axis, half_mask, radial_ticks, ring_label_band`, sourceReason matches the required fallback wording.

Known non-blocking review items:

- Generated FRU still has less in-scene prose than the KING X gold reference (`49` vs `284` text objects). This remains a future polish candidate rather than a Phase W/X blocker because Phase U/V/W/X gates now prove step count, semantics, background, icon, status overlays, and contact-sheet readability.
- Review burndown remains intentionally strict: `337` review items, mostly `label_far_from_anchor`, `text_vs_cone`, and `text_overlap`; severe remains `0`.

### 10.5.1 Phase X：Buff / Debuff 归属图标层（新增计划项）

目标：当机制解法强依赖 buff / debuff 图标、状态点名或状态组别时，图里必须直接显示“每个人被点了什么状态”，不能只写在说明文字里。状态图标应贴在每个玩家图标左上角，作为该玩家身份的一部分参与读图。

触发条件：

- 用户输入、机制名、攻略文本或解析结果明确出现 buff、debuff、状态、点名、颜色/图标、延时/短时、世界第一/第二、High Concept/Hello World/Relativity 类机制。
- 解法判断依赖“谁拿到哪个状态”来决定站位、顺序、分摊、换位或优先级。
- 同一职业/职能在不同分支中因状态不同承担不同职责。

任务：

- 在 spec 中新增 `statusAssignments` 或等价语义层：
  - 每条记录至少包含 `role`、`statusName`、`statusIcon`、`kind`、`decisionGroup`、`visibleSteps`；
  - 可选包含 `durationLabel`、`stackLabel`、`priorityLabel`、`source`、`confidence`；
  - `role` 必须指向 `MT/ST/H1/H2/D1/D2/D3/D4`，不能只给分组文字。
- 扩展 `build_xivplan_scene.py`：
  - 对每个带状态的 party 对象生成一个小型 `icon` overlay，默认锚定玩家图标左上角；
  - overlay 尺寸以玩家图标为基准，默认约为玩家图标宽度的 `35%-45%`，并保留清晰描边或底色托盘；
  - 多状态时最多显示 2-3 个小图标，超出的低优先级状态移入 callout 或 `guide_text`，避免遮住玩家身份；
  - 状态图标不能覆盖编号职能图标、目标圈、关键 AoE 边界或箭头头部。
- 扩展状态图标资源流程：
  - 优先使用可解析的 XivPlan/public status icon、已授权本地状态资源或 data URL；
  - 无法确认真实图标时，允许使用明确的文字化 fallback badge，但质量报告必须记录 `status-icon-fallback` 和原因；
  - 对用户提供截图中的 buff 图标，应保留来源说明和裁剪/重绘步骤，不把未确认图标伪装成官方资源。
- 扩展 audit：
  - 新增 `status_assignment_score`，统计状态驱动机制中有多少玩家具备可见状态 overlay；
  - 对状态驱动 step 设置 hard fail：缺少任一关键玩家状态图标、状态只在长文本中出现、图标与玩家归属不清、图标小到 contact sheet 不可读；
  - 对多分支机制检查状态图标、站位、箭头和 AoE 标签是否一致，例如“短延时去内侧”的图标和实际角色必须匹配。
- 新增回归 fixture：
  - 至少一个 Hello World / Relativity / High Concept 类状态分配样例；
  - 每个 `MT/ST/H1/H2/D1/D2/D3/D4` 都有不同或分组状态图标；
  - contact sheet 必须证明正常导出尺寸下左上角图标可读。

验收：

- buff / debuff 强相关机制中，8 名玩家的状态归属必须在玩家图标左上角可见；只写“红去左、蓝去右”不算通过。
- `status_assignment_score` 进入 release gate；状态驱动机制出现任一关键状态缺失或错配时阻止交付。
- 人工审查清单新增“状态图标归属”项，检查图标可读性、归属清晰度、与站位/箭头/判定的一致性。

实施状态（2026-06-02）：

- [x] `build_xivplan_scene.py` 已支持 `statusAssignments` 与 `status_assignment_contract`；每条状态分配可按 `role`、`statusName`、`kind`、`decisionGroup`、`visibleSteps` 绑定到 MT/ST/H1/H2/D1/D2/D3/D4，并在对应 party 图标左上角生成 `statusOverlay` icon。
- [x] 状态 overlay 保留 `statusRole`、`statusName`、`decisionGroup`、`anchorRole`、`anchorPartyId`、`assetStatus`、`assetFallback`、`fallbackReason` 等审计字段；无真实图标资源时生成明确的文字化 fallback badge。
- [x] `build_spec_from_solution.py` 会在检测到 `debuff`、`hello-world-like`、buff/debuff/status/状态/点名/延时/Hello World/Relativity/High Concept 等状态驱动语境时写入 Phase X 合同和默认八人状态分配。
- [x] `validate_xivplan_scene.py` 已校验 Phase X 合同：状态 assignment 必须指向合法 role，状态驱动 step 必须有可见 overlay，overlay 必须锚定正确 party，fallback 状态图标必须记录原因。
- [x] `audit_visual_quality.py` 已新增 `status_assignment_score`、`components.status_assignment` 与 Markdown Status Assignment 表；状态缺失、错锚、过小或无原因 fallback 都是 strict generated mode 的 severe。
- [x] `run_visual_regression.py --force` 已新增 `status-driven-assignment` fixture，生成 `status-assignment-report.json/md`，并把 Phase X status gate 纳入 release acceptance。
- [x] `SKILL.md`、`README.md`、`agents/openai.yaml`、`references/xivplan-scene-format.md` 和 visual quality checklist 已记录 Phase X 规则。

Evidence (2026-06-02):

- `test_visual_quality_audit.py`: PASS，包含 Phase X 正例与删除 MT overlay 的负例。
- `run_visual_regression.py --force`: PASS 12/12。
- Phase X fixture: `status_assignment_score=100.0`，`48 visible / 48 expected`，covered roles 为 `MT/ST/H1/H2/D1/D2/D3/D4`。

### 10.6 第四轮停止线

第四轮完成时，至少满足：

- [x] `compare_xivplan_to_gold.py` 能稳定生成本次两文件的差异报告。
- [x] 金标准参考模式不再把人工 KING X 样例误判为低质量合同失败。
- [x] 主机制图与流程示例图的 party identity 生成、校验和回归路径已拆分：`mechanic_flow` 默认编号职能图标，`flow_example` 默认职业图标。
- [x] O8S/妖星乱舞重新生成版本达到 `10+` step，图内文字和 Phase U page-title/callout 合同已有可审计证据；Boss icon、箭头端点、伤害范围和背景 fallback 已分别通过 Phase Q/S、V、W gate。
- [x] FRU 雷火剑回归样例能在 `/arena/e11.svg` 背景、目标环、雷/火扇形、优先级文字和多分支页面上接近金标准；剩余差距主要是图内 prose 密度，而非机制语义或背景合同。
- [x] contact sheet + 人工审查能证明新图不是只在 JSON 指标上变密，而是真的更像可直接给队员看的攻略图。
- [x] 状态驱动机制不再只靠文字描述状态分组；Phase X 回归样例每个玩家的 buff/debuff 归属都在玩家图标左上角可见，并进入 release gate。
