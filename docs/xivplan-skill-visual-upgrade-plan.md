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
