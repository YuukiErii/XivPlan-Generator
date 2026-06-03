# XivPlan Style Guide

本文件冻结 Phase 0 的图面风格基线。目标不是做装饰性好看的图，而是生成接近 KING X 成品的信息密度和可读性：玩家能在几秒内看懂当前判定、自己负责什么、怎么移动、判定后去哪复位。

## 黄金样例

以下 `.xivplan` 文件是 Phase 0 选定的第一批黄金样例。来源目录为 `C:\Users\Mahiru\Desktop\FFXIV\KING X\0523-0524 FRU\Strats_limited`。选择标准是覆盖紧凑规则、多步移动、Light Rampant 类机制、坦克/塔责任分配、复杂分支判定。

| 样例 | 选为黄金样例的原因 | 观察到的结构 |
|---|---|---|
| `P1/P1_thunder_fire_swords.xivplan` | 长流程机制的最佳参考：颜色危险区、重复标点、移动箭头和中文说明密度都比较成熟。 | 14 steps，625 objects，`/arena/e11.svg`，大量 `text`、`circle`、`cone`、`rect`、`arrow`、`party`。 |
| `P1/P1_tankbusters.xivplan` | 紧凑职责图的最佳参考：死刑、塔、黑圈、坦克处理和小步说明很清晰。 | 4 steps，173 objects，`/arena/e11.svg`，角色标签、塔、箭头和短说明块。 |
| `P2/P2_light_rampant_hexagram.xivplan` | Light Rampant 类机制的最佳参考：半场区分、踩塔、职能站位和图文密度都可复用。 | 6 steps，348 objects，`/arena/e8.svg`，半场色块、塔、玩家图标、箭头和标签。 |
| `P2/P2_knockback_four_stacks.xivplan` | 短机制图的最佳参考：击退、移动和分摊三步拆分清楚。 | 3 steps，182 objects，`/arena/e8.svg`，稳定箭头、分摊/散开圆圈和落点职责。 |
| `P4/P4_darklight_dragonsong_line_cases.xivplan` | 复杂分支图的最佳参考：线/连线分支、塔和大量小标签仍保持可读。 | 13 steps，678 objects，无 arena 背景，大量 `text`、`party`、`marker`、`rect`、`circle`、`tower`、`arrow`。 |

需要 polygon 安全区、P3 风格大范围分割或更高密度图面时，可把 `P3/P3UR.xivplan` 与 `P3/P3_apocalypse_carhead.xivplan` 作为二级参考。

## 场地基线

- 默认使用 `600 x 600` 圆形场地，除非机制明确需要方形或矩形场地。
- 坐标以 `(0, 0)` 为中心，`x` 正方向为东，`y` 正方向为北。
- 没有更准确背景时，Eden Promise / FRU P1 类图优先用 `/arena/e11.svg`，Shiva / Light Rampant 类图优先用 `/arena/e8.svg`。
- 标点默认半径约为 `150`，斜点默认约为 `106,106`。
- 除非正在表达击退出界或场外危险，否则对象应保持在场地边界内。

## 默认尺寸

| 元素 | 默认值 | 说明 |
|---|---|---|
| 标点 | `42 x 42` | 黄金样例最常用尺寸。局部小标点可用 `32-38`。 |
| 玩家图标 | `30-36` | 主站位用 `34-36`，复杂分支图可缩到 `25-31`。 |
| Boss / 敌人半径 | `28-36` | 有顺劈、身位、相对方位时必须显示朝向。 |
| 正文标签 | `12-14` | 大多数角色、规则、时间点标签使用该范围。 |
| 密集小字 | `9-11` | 仅用于分支标签或小型补充说明。 |
| 大标题 / 阶段标签 | `23-24` | 只用于 step 标题或非常重要的状态标签。 |
| 移动箭头 | 宽度 `8-13` | 强制移动或击退路径可适度加宽。 |

## 文字样式

- 场内文字默认使用 `style: outline`。
- 描边默认使用深色 `#101318`，这是黄金样例中最稳定的文字描边色。
- 场内文字只写规则、分组、目的地、时间点，不替代攻略正文。
- 长解释放到 `guide_text` 或 Markdown 攻略里，场内只保留可扫读标签。
- 角色标签要贴近玩家图标，但不能遮挡 AoE 边界、塔、箭头头部或关键判定点。
- 新生成的对象标签优先使用 `labelPlacement: "auto"`，并用 `leaderLine: true` 处理被移出机制对象外侧的说明文字。
- 定稿前运行 `audit_label_layout.py`；严重文字互撞、文字压玩家/Boss/标点、文字压箭头或关键机制区域应为 0。

### 文字避让优先级

1. 先避开玩家、Boss/分身、塔、分摊点和机制源，因为这些对象决定职责。
2. 再避开 AoE 边界、安全区边界、箭头头部和路径交叉点，因为这些对象决定行动方向。
3. 最后处理普通说明文字之间的距离；必要时把长句缩成短标签，并把完整解释放入 `guide_text`。
4. 被移动到对象外侧的标签必须加 `leaderLine: true` 或明确 anchor，避免玩家不知道标签对应哪一个机制对象。
5. 如果自动避让后仍有 review 项，优先拆 step，其次缩短标签，最后才降低字体大小。

第二轮发布级规则：生成 step 标题和 callout 时，默认避开北侧 A 标、四方标点、箭头头部与玩家图标。标题可以放到场地外圈或安全空白带；机制标签被移到对象外侧时必须保留 `labelAnchor` / `labelAnchorId` 或 `leaderLine: true`。发布前 `text_vs_marker`、`text_vs_party`、`text_vs_enemy`、`text_vs_arrow` 等 severe 项必须为 0。

## 颜色语义

颜色可以随机制微调，但语义必须稳定。

| 语义 | 推荐颜色 | 用法 |
|---|---|---|
| 危险 / 伤害 | 红、橙、紫，低透明度填充 | AoE、诱导范围、爆炸、危险扇区。 |
| 安全 / 目的地 | 绿、青，低透明度填充 | 安全区、最终站位、允许半场。 |
| 移动 / 路径 | 蓝、青、白 | 箭头、移动路线、击退落点。 |
| A 组 / 上半 / 第一轮 | 橙、黄等暖色 | 第一组、第一轮、上半场。 |
| B 组 / 下半 / 第二轮 | 青、蓝等冷色 | 第二组、第二轮、下半场。 |
| 中性说明 | 白、淡黄，深色描边 | 时间点、复位、角色标签。 |

AoE 和区域块优先使用透明度解决遮挡。若某个色块遮住了职责点，先降低透明度或拆成下一步，不要让玩家图标和塔被埋掉。

## 箭头与流程线

- 主移动使用 `arrowStyle: "movement"`，保持蓝色、较粗、方向明确。
- 预站或微调用 `preposition` / `micro`，比主移动更细，避免抢当前判定的视觉焦点。
- 击退用 `knockback`，从击退源指向落点；复位用 `reset`，颜色和主移动区分。
- 诱导用 `bait`，禁止路线用 `forbidden`，不要把禁止路线画成实际移动箭头。
- 长距离路线优先使用 `waypoints`、`curve`、`path` 或 `polyline` 拆成短段，减少箭头交叉和箭头头部遮挡。
- 标记为 `movement_required`、`storyboard_phase: "move"` 或 `storyboard_phase: "reset"` 的 step 必须有明确的 `arrow` 或 `tether`。移动箭头要从起点指向落点，复位箭头要和主移动颜色区分，箭头头部不能压住玩家、Boss、标点或关键说明文字。
- 定稿前运行 `audit_flow_lines.py`；新生成图默认要求严重箭头交叉和箭头头部遮挡为 0。

## 图层顺序

生成或编辑 step 时按以下顺序组织：

1. 场地与大范围安全/危险底色。
2. 大型 AoE：圆形、扇形、矩形、甜甜圈、多边形、星爆。
3. Boss、小怪、塔、分摊、连线等机制锚点。
4. 标点。
5. 玩家图标。
6. 移动箭头。
7. 文字标签。

如果文字或箭头遮住了机制锚点，优先移动标签位置，其次才是缩小字体。

## Step 拆分原则

每个 step 只回答一个主要问题：

- 起始站位在哪里？
- 机制出现了什么？
- 要观察什么？
- 谁去哪里？
- 怎么移动？
- 在哪里判定？
- 判定后怎么复位？

### 教学分镜粒度

第三轮起，分镜的默认目标是“逐帧教学”，不是“事件摘要”。每个 step 应只回答一个 `teaching_question`，并用 `why_this_frame_exists` 说明这一帧为什么值得存在，用 `changed_objects_only` 说明相对上一帧真正变化了什么。

- 简单机制：`3-5` steps，例如单次分摊、单次散开、单次击退。
- 中等机制：`6-10` steps，例如两轮判定、换位、读条加散开。
- 复杂机制：`10-16` steps，例如 Limit Cut、线分支、大运动会、多轮塔/分摊。
- 超长教学流程：`12-20` steps，例如 FRU P1 雷火剑式长流程；允许超过旧 `10-14` 上限，但每帧必须有不同教学价值。

允许使用更细的 `storyboard_phase`：`observe_signal`、`assign_roles`、`preposition`、`first_move`、`first_resolve`、`between_resolves`、`second_move`、`second_resolve`、`reset`、`next_read_setup`。复杂机制至少覆盖 observation / assignment / movement / resolve / reset / next-read 的教学链。

黄金样例的常规密度约为每 step `35-65` 个对象。复杂分支图可以超过这个范围，但前提是重复标点、玩家标签和箭头仍然清楚。

`P1/P1_thunder_fire_swords.xivplan` 是长流程机制密度参考：它证明 10+ steps、数百对象和密集中文标签可以成立，但前提是每一帧都保留场地、Boss、8 人、当前机制层、移动/复位逻辑和可读标签。新生成长流程图宁可多拆 step，也不要追求单帧塞满。

语义化长流程使用独立密度策略，不再按普通单帧清爽阈值误判。只有同时满足以下条件时，密集 step 才能被接受：`metadata.storyboard_generator == "phase-l-semantic-long-flow"` 或 `phase-o-teaching-long-flow`，总步数在对应策略范围内，平均对象数接近黄金样例的 `35-65 / step`，包含 observe / move / resolve / reset 覆盖，且 label、flow、context severe 均为 0。否则仍按普通 `single_step_focus` 阈值拆图。

第四轮 Phase U 起，复杂机制还要启用 `annotation_contract`：每个 normal step 必须有图内 page title，并用 `labelRole: "axis" | "priority" | "mechanic" | "footer"` 把关键读法、优先级、行动和例外提醒写进图内。`guide_text` 可以保留完整解释，但不能成为唯一攻略来源。O8S / 妖星乱舞类组合机制目标是 10-14 steps，并达到 `140+` text objects 或 `900+` 图内文字字符。

## 对象语法

- `marker` 用于 A/B/C/D/1/2/3/4，所有 steps 中位置要稳定。
- `party` 用于玩家；主机制图默认用 XivPlan 内置编号职能图标（`/actor/tank1.png`、`/actor/healer2.png`、`/actor/dps4.png` 等）表达职责槽位，不再额外堆 `MT/ST/H1...` 文字。流程示例图使用 `guide_section: "flow_example"`，沿用 `/actor/<JOB>.png` 官方职业图标加附近职责短标。
- `enemy` 用于 Boss、小怪、分身和不可选中机制源；每个 normal step 中的敌人都必须有非空 `name` / `displayName`、可见目标环、半径或 `targetRing.radius`、方向或 `facing`（需要身位时），以及可读名字标签。
- `circle`、`cone`、`rect`、`donut`、`polygon`、`starburst` 用于 AoE、安全区或危险区。
- `tower` 只用于真实需要踩塔的机制，并在攻略文字说明踩塔人数。
- `stack` 或带标签的圆形用于分摊点，并在攻略文字说明分摊人数。
- `arrow` 用于移动；除非机制要求交叉，否则避免箭头交叉。
- `tether` / `line` 用于连线，并标注拉线方向或目标点。
- `text` 用于 page title、轴线、优先级、机制短句和 footer 提醒；生成文本优先使用 `labelRole` 和 `labelBand`，避免把长句直接塞进场地中央。

## Phase V 判定与路线语义

复杂生成图必须声明 `mechanic_semantics_contract`。箭头不再只是视觉线条：使用 `movementRoute` 写明起点、终点、意图、判定轮次、起终点短标和 `snapToTarget`。只有箭头确实需要贴住声明目标时才设 `snapToTarget: true`。

AoE 不再只靠颜色区分：使用 `damagePattern` 写明 `kind`、`source`、`targets`、`resolveIndex`、`resolveTiming`、`aoeIntent` 和短标签。`aoeIntent` 至少区分 `damage`、`safe`、`bait_history`、`future_resolve`、`reference_only`，避免把安全区、诱导残留和当前爆炸画成同一种红圈。

第四轮 release gate 要求 FRU 与 O8S 语义样例同时达到 `range_semantics_score=100.0` 和 `arrow_semantics_score=100.0`，且 resolve 页面必须有真实判定几何。

## 逐帧完整画面合同

新生成的常规机制图默认使用 `scene_contract`，要求每个 normal step 都保留 8 名玩家、至少一个 Boss/分身/机制源、稳定标点和场地背景。即使当前 step 只讲塔、AoE 或箭头，也不能让队伍上下文突然消失。

- `scene_contract.require_full_party_each_step`、`require_enemy_each_step`、`require_waymarks_each_step` 默认为 true。
- 缺少 `inherit` 的 step 会由构建器自动补齐基础八方站位、Boss 和标点。
- 当前行动者可用 `focusRoles` 高亮；非行动者用 `ghost: true` 或较低 `opacity` 保留在图中。
- 只有纯观察、素材预览或局部读条帧才允许 `partial_observation: true`，并且必须在 `guide_text` 说明为什么这一帧可以不画完整上下文。
- 验证器会拦截缺 8 人、缺 Boss/机制源、缺 A/B/C/D 标点的普通 step。

## 生成图检查表

定稿 `.xivplan` 或攻略图之前检查：

- 场地形状、标点位置、东西南北文字一致。
- 每个普通 step 都有 MT/ST/H1/H2/D1/D2/D3/D4、Boss/机制源和稳定标点。
- 当前 step 中每个玩家只有一个明确职责。
- 塔、分摊、散开、连线的人数和位置不冲突。
- 箭头方向与文字说明一致。
- 安全色和危险色没有互相矛盾。
- 正常截图尺寸下文字可读。
- 复杂机制已经拆成多 step，而不是塞成一张不可读的大图。
- 最后一步说明或暗示了下一机制前的复位位置。
