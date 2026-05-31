# UWU Mechanic Cards

## Scope

Use these cards for The Weapon's Refrain (Ultimate), commonly abbreviated `UWU`. UWU requires the three primals to become Woken before Ultima; distinguish the base primal mechanics from their Woken variants.

## Garuda Thermal Low And Mesohigh

- 副本：UWU / The Weapon's Refrain (Ultimate)
- 阶段：Garuda
- 常见别名：Garuda、Thermal Low、低气压、Mesohigh、线
- 机制类别：`debuff`、`tether`、`sequence`
- 原理：Thermal Low 层数与 Mesohigh 线决定谁需要截线和保留状态，正确处理后让 Garuda 进入 Woken。
- 默认解法：先给 Thermal Low 层数分桶，再画 Mesohigh 截线者与等待位。
- 常见优化：预先指定截线角色；把保留一层状态的玩家标出供 Ultima 阶段使用。
- 常见失误：截线过早或过晚；需要保留状态的人被额外清除。
- 可类比机制：状态层数管理、截线、为后续阶段保存资源。
- 可迁移部分：Debuff 层数、固定 interceptor、阶段间状态延续。
- 不应照搬：UWU Woken 条件与 Thermal Low 层数只属于 Garuda。
- XivPlan 图示拆分：层数分桶；Mesohigh 初始线；截线；Woken 检查。
- 需要确认的信息：采用的层数策略、截线优先级、Ultima 阶段保留状态需求。
- 参考来源：[Icy Veins UWU Garuda guide](https://www.icy-veins.com/ffxiv/the-weapons-refrain-ultimate-guides-garuda)
- 置信度：`high`

## Ifrit Nails Charges And Searing Wind

- 副本：UWU / The Weapon's Refrain (Ultimate)
- 阶段：Ifrit
- 常见别名：Ifrit、火神、Nails、火柱、Crimson Cyclone、Searing Wind
- 机制类别：`adds-priority`、`bait`、`sequence`
- 原理：火柱击杀顺序、冲锋安全区和 Searing Wind 隔离共同决定 Woken 条件；点名玩家需要离队避免范围伤害。
- 默认解法：画火柱顺序、冲锋路径和点名隔离点；将输出目标与人物移动分层。
- 常见优化：固定 nail 击杀顺序与安全边；为 Searing Wind 预留独立外侧点。
- 常见失误：火柱顺序错误导致 Woken 失败；Searing Wind 玩家靠近队伍。
- 可类比机制：小怪击杀顺序、冲锋 safe lane、持续范围点名隔离。
- 可迁移部分：adds priority、冲锋观察、点名离队。
- 不应照搬：UWU 的 nail Woken 条件与冲锋顺序只适用于 Ifrit。
- XivPlan 图示拆分：火柱；冲锋观察；冲锋避让；Searing Wind 隔离；Woken 检查。
- 需要确认的信息：火柱击杀顺序、冲锋安全区、点名隔离点、LB 使用。
- 参考来源：[Icy Veins UWU Ifrit guide](https://www.icy-veins.com/ffxiv/the-weapons-refrain-ultimate-guides-ifrit)
- 置信度：`high`

## Titan Granite Gaols

- 副本：UWU / The Weapon's Refrain (Ultimate)
- 阶段：Titan
- 常见别名：Titan、土神、Granite Gaol、石牢、Gaols、三连石牢
- 机制类别：`bait`、`adds-priority`、`sequence`
- 原理：三名玩家需要把 Granite Gaol 放成可连锁爆炸的顺序，同时避免泥潭阻断路线，并让 Titan 获得 Woken。
- 默认解法：按预设优先级确定三人顺序，画出三颗 Gaol 的落点与连锁爆炸方向。
- 常见优化：用自动标记或短优先级减少临场排序；落点沿稳定直线排开。
- 常见失误：石牢距离不足无法连锁；泥潭覆盖 Titan 或队伍逃生线。
- 可类比机制：随机三人排序、连锁爆炸、自动标点、落点距离校验。
- 可迁移部分：优先级排序、链式落点、距离 margin。
- 不应照搬：UWU 石牢距离、Titan Woken 条件和泥潭位置只适用于该阶段。
- XivPlan 图示拆分：点名排序；三颗石牢落点；连锁爆炸；Woken 检查。
- 需要确认的信息：排序方式、自动标记规则、石牢间距、队伍站位。
- 参考来源：[Icy Veins UWU Titan guide](https://www.icy-veins.com/ffxiv/the-weapons-refrain-ultimate-guides-titan)
- 置信度：`high`

## Ultimate Predation

- 副本：UWU / The Weapon's Refrain (Ultimate)
- 阶段：Ultima
- 常见别名：Ultimate Predation、追击、Predation、找安全符文
- 机制类别：`clone-memory`、`line-shape`、`sequence`
- 原理：Garuda、Ifrit、Titan 与 Ultima 出现在不同方位，玩家需要根据四个来源的攻击组合找唯一安全区。
- 默认解法：先找 Garuda 和 Ifrit，再排除 Titan 与 Ultima 覆盖区，进入安全 rune；最后回中 bait Feather Rain。
- 常见优化：把判断压缩为两步排除法；用场边 rune 当稳定落点。
- 常见失误：只看一个 primal；安全点正确但未躲第一次 Landslide。
- 可类比机制：多来源读图找唯一安全区、分身组合、符文安全点。
- 可迁移部分：观察、排除危险象限、落点、回收。
- 不应照搬：UWU primal 组合和 rune 数只属于 Predation。
- XivPlan 图示拆分：四来源观察；排除法；第一次避让；最终 rune；回中。
- 需要确认的信息：callout 方式、安全 rune 编号、队伍回中路径。
- 参考来源：[Icy Veins UWU Ultima guide](https://www.icy-veins.com/ffxiv/the-weapons-refrain-ultimate-guides-ultima)
- 置信度：`high`

## Ultimate Annihilation

- 副本：UWU / The Weapon's Refrain (Ultimate)
- 阶段：Ultima
- 常见别名：Ultimate Annihilation、乱击、Annihilation、3311 球
- 机制类别：`sequence`、`bait`、`tether`、`adds-priority`
- 原理：地火、火分摊、Searing Wind、Mesohigh、冲锋与 Aetheroplasm orb 吸收顺序叠加，球的吸收人数会影响后续 Aetheric Boom。
- 默认解法：固定 orb soak 方案，例如 `3-3-1-1`，再画每轮 puddle bait、截线、Searing Wind 隔离和冲锋避让。
- 常见优化：把 orb 组与队伍组用不同颜色标记；每轮只画当前 AoE 和下一步。
- 常见失误：误吃 orb 改变后续 tether 长度；Searing Wind 回队过早。
- 可类比机制：为后续阶段预设资源、连续 bait、截线、隔离。
- 可迁移部分：orb 资源表、固定 soak 人数、时间轴拆图。
- 不应照搬：UWU `3-3-1-1` 只属于 Aetheroplasm 与 Aetheric Boom 组合。
- XivPlan 图示拆分：起始 bait；第一二球；Searing Wind；冲锋；第三四球；复位。
- 需要确认的信息：orb soak 方案、Searing Wind 角色、Mesohigh 截线者、路线方向。
- 参考来源：[Icy Veins UWU Ultima guide](https://www.icy-veins.com/ffxiv/the-weapons-refrain-ultimate-guides-ultima)
- 置信度：`high`

## Ultimate Suppression

- 副本：UWU / The Weapon's Refrain (Ultimate)
- 阶段：Ultima
- 常见别名：Ultimate Suppression、三运、Suppression、柱子
- 机制类别：`sequence`、`bait`、`tower`、`tether`
- 原理：Eruption、Mistral Song、Gaol、Light Pillar、Laser、Landslide、Mesohigh 与 fire stack 连续分配给不同玩家，核心是快速分类与 process-of-elimination。
- 默认解法：先展开扇形观察职责，再按 Eruption、Song、Gaol 和剩余 Light Pillar 分桶；后半全队集合处理 Landslide 与截线。
- 常见优化：明确 Light Pillar 的排除逻辑；前半与后半拆成两个图组。
- 常见失误：Gaol 玩家位置错误；Light Pillar 未及时识别；后半队伍移动不同步。
- 可类比机制：职责排除、连续随机点名、大运动会、后半集合移动。
- 可迁移部分：职责分桶、剩余玩家排除、前后半拆图。
- 不应照搬：UWU 各职责数量、柱子路线和后半 Landslide 路线属于 Suppression。
- XivPlan 图示拆分：初始扇形；Eruption/Song；Gaol 与 Light Pillar；Laser；后半 Landslide 与 tether；复位。
- 需要确认的信息：职责优先级、Light Pillar 路线、Gaol 打法、后半移动方向。
- 参考来源：[Icy Veins UWU Ultima guide](https://www.icy-veins.com/ffxiv/the-weapons-refrain-ultimate-guides-ultima)
- 置信度：`high`

## Aetheric Boom And Primal Roulette

- 副本：UWU / The Weapon's Refrain (Ultimate)
- 阶段：Ultima endgame
- 常见别名：Aetheric Boom、击退球、Primal Roulette、三神轮盘、终盘
- 机制类别：`knockback`、`sequence`、`raidwide`
- 原理：Aetheric Boom 击退后按此前 orb 状态连续吃球；终盘 Primal Roulette 根据首个 primal 预测后续顺序并处理连续高伤害。
- 默认解法：双组分别被击退进南侧球，治疗后冲刺吃第二组；终盘单独做减伤与 primal 顺序表。
- 常见优化：把 Annihilation 的 orb 方案与 Boom 落点放在同一页；终盘 callout 只报首个 primal。
- 常见失误：提前吃球；治疗未抬满就冲下一组；终盘减伤覆盖错误。
- 可类比机制：击退进球、前置资源影响后续、终盘减伤循环。
- 可迁移部分：资源前后关联、knockback landing、终盘 mit table。
- 不应照搬：UWU orb tether 长度、primal 顺序和终盘伤害轴只属于该副本。
- XivPlan 图示拆分：击退前分组；南侧球；北侧球；终盘顺序；减伤表。
- 需要确认的信息：orb 方案、防击退是否使用、终盘减伤分配、primal callout。
- 参考来源：[Icy Veins UWU Ultima guide](https://www.icy-veins.com/ffxiv/the-weapons-refrain-ultimate-guides-ultima)
- 置信度：`high`
