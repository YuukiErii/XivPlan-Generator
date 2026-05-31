# Eden Savage Mechanic Cards

## Scope

Use these cards for Eden Savage (`E1S-E12S`). Eden contains several high-value templates reused by FRU.

## Light Rampant

- 副本：Eden Savage / E8S Shiva
- 阶段：Shiva
- 常见别名：Light Rampant、光之失控、光暴、LR
- 机制类别：`tether`、`tower`、`spread`、`sequence`
- 原理：连线玩家、自由人、塔与 orb 按时间轴组合；解法核心是 tether 图形和职责分桶。
- 默认解法：先观察谁有线，再按所选策略建立图形与塔组；自由人进入补位；每轮 orb 与塔单独画。
- 常见优化：选择线少交叉、记忆成本低的稳定图形；用固定 waymark 帮助站位。
- 常见失误：把 tether 图形摆对但漏掉 tower 或 orb；不同攻略流派混用。
- 可类比机制：FRU `Light Rampant`、线塔组合、自由人补位。
- 可迁移部分：tether graph、自由人职责、塔与 orb 分阶段。
- 不应照搬：E8S 的塔序、orb 数量和具体站位不能直接套用到 FRU remix。
- XivPlan 图示拆分：观察；图形建立；塔；orb；收尾。
- 需要确认的信息：采用的 LR 策略、塔序、自由人职责、最终收尾。
- 参考来源：[Icy Veins FRU P2 guide comparison context](https://www.icy-veins.com/ffxiv/futures-rewritten-ultimate-guide-for-phase-2-usurper-of-frost)
- 置信度：`high`

## Wyrms Lament

- 副本：Eden Savage / E8S Shiva
- 阶段：Shiva
- 常见别名：Wyrm's Lament、龙诗、红蓝镜、冰火
- 机制类别：`debuff`、`bait`、`sequence`
- 原理：玩家按颜色或状态分组，在多轮龙头或场地判定中轮换职责。
- 默认解法：先按状态分桶，再画每轮谁处理、谁等待、谁复位。
- 常见优化：让两组沿稳定 lane 轮换，避免穿越。
- 常见失误：颜色识别正确但处理轮次颠倒；等待组过早进入。
- 可类比机制：颜色分组轮换、龙头 bait、FRU 时间结晶 remix。
- 可迁移部分：状态分桶、两组轮换、等待区。
- 不应照搬：E8S 龙头位置、颜色含义和判定轮数需要重新确认。
- XivPlan 图示拆分：状态分组；第一轮；第二轮；复位。
- 需要确认的信息：颜色、轮次、bait 目标、等待点。
- 参考来源：[Final Fantasy XIV Wiki E8S](https://ffxiv.consolegameswiki.com/wiki/Eden%27s_Verse:_Refulgence_(Savage))
- 置信度：`medium`

## Basic And Advanced Relativity

- 副本：Eden Savage / E12S Oracle of Darkness
- 阶段：Oracle of Darkness
- 常见别名：Basic Relativity、Advanced Relativity、相对论、时间压缩
- 机制类别：`debuff`、`sequence`、`rotation`
- 原理：多种带时长 Debuff 按时间轴连续结算，玩家按职责和方向进入不同处理点。
- 默认解法：先做 Debuff 时长表，再为每个 bucket 画起点、移动、判定与回收。
- 常见优化：固定旋转方向和等待点；将每人的职责压缩为一条个人时间线。
- 常见失误：只记位置不记时长；不同攻略旋转方向混用。
- 可类比机制：FRU `Ultimate Relativity`、FRU `Crystallize Time`、Hello World-like 时间桶。
- 可迁移部分：Debuff bucket、时长、旋转、beat-by-beat 图示。
- 不应照搬：E12S 的火、冰、激光和 return 规则不能直接复制到 FRU。
- XivPlan 图示拆分：Debuff 表；每个主要 beat；最终回收。
- 需要确认的信息：Debuff 类型、时长、旋转方向、队伍攻略版本。
- 参考来源：[Final Fantasy XIV Wiki E12S](https://ffxiv.consolegameswiki.com/wiki/Eden%27s_Promise:_Eternity_(Savage))
- 置信度：`high`

## Lions Rampant

- 副本：Eden Savage / E12S Eden's Promise
- 阶段：Eden's Promise
- 常见别名：Lions Rampant、狮子、大小狮、狮子诱导
- 机制类别：`bait`、`line-shape`、`sequence`
- 原理：大小狮子按固定顺序喷吐或诱导，玩家需要在规定位置分组并按节拍交换。
- 默认解法：先分大狮与小狮职责，再画每次诱导与换位；保持 lane 清晰。
- 常见优化：用固定顺序和简短 callout；箭头只显示当前换位。
- 常见失误：喷吐顺序正确但换位提前；线路交叉。
- 可类比机制：多源 bait、固定顺序喷吐、双 lane 交换。
- 可迁移部分：职责分桶、喷吐节拍、lane 交换。
- 不应照搬：狮子位置、喷吐次数、距离与具体 swap 方案需要按新机制确认。
- XivPlan 图示拆分：分组；第一次诱导；交换；第二次诱导；复位。
- 需要确认的信息：大小狮分配、喷吐顺序、交换时机、场地朝向。
- 参考来源：[Final Fantasy XIV Wiki E12S](https://ffxiv.consolegameswiki.com/wiki/Eden%27s_Promise:_Eternity_(Savage))
- 置信度：`medium`

## E1S Delta Attack And Pure Light

- 副本：Eden Savage / E1S Eden Prime
- 阶段：Eden Prime
- 常见别名：E1S、Eden Prime、Delta Attack、Pure Light、激光
- 机制类别：`line-shape`、`spread`、`sequence`
- 原理：多方向直线、圆形 AoE 与散开组合，玩家要根据 Boss 朝向进入安全缝并保持个人间距。
- 默认解法：先画 Pure Light 朝向和安全背侧，再画 Delta Attack 的范围与八方散开。
- 常见优化：将 Boss-relative safe side 与散开 clock 合并为短移动。
- 常见失误：只躲直线，散开圈重叠；Boss 朝向未标。
- 可类比机制：多方向激光、Boss-relative safe side、八方散开。
- 可迁移部分：朝向、直线 safe lane、个人圈。
- 不应照搬：E1S 的激光宽度和攻击顺序只属于 Eden Prime。
- XivPlan 图示拆分：朝向；Pure Light；Delta Attack；复位。
- 需要确认的信息：Boss 面向、个人圈半径、散开 clock。
- 参考来源：[Final Fantasy XIV Wiki E1S](https://ffxiv.consolegameswiki.com/wiki/Eden%27s_Gate:_Resurrection_%28Savage%29)
- 置信度：`high`

## E2S Spell In Waiting

- 副本：Eden Savage / E2S Voidwalker
- 阶段：Voidwalker
- 常见别名：E2S、Voidwalker、Spell-in-Waiting、延迟 Buff、Quietus
- 机制类别：`debuff`、`sequence`、`spread`、`stack`
- 原理：分摊、散开、凝视与圈会先获得延迟状态，再按各自倒计时结算。
- 默认解法：先建立延迟技能时间轴，再按到期顺序画 stack、spread、gaze 和 reset。
- 常见优化：将倒计时作为主键，不按技能获得顺序记忆。
- 常见失误：看见技能图标就立即处理；倒计时相同的人没有提前分散。
- 可类比机制：延迟魔法、倒计时 Debuff、Relativity-like 时间桶。
- 可迁移部分：timer bucket、延迟结算、逐 beat 图示。
- 不应照搬：E2S 的延迟技能集合与 Quietus 顺序只属于 Voidwalker。
- XivPlan 图示拆分：Debuff 总览；每个倒计时 bucket；复位。
- 需要确认的信息：倒计时、技能类型、分摊人数、散开位。
- 参考来源：[Final Fantasy XIV Wiki E2S](https://ffxiv.consolegameswiki.com/wiki/Eden%27s_Gate:_Descent_%28Savage%29)
- 置信度：`high`

## E3S Temporary Current And Tsunami

- 副本：Eden Savage / E3S Leviathan
- 阶段：Leviathan
- 常见别名：E3S、Leviathan、Temporary Current、Tsunami、平台切割
- 机制类别：`tile-platform`、`line-shape`、`knockback`
- 原理：平台不断被切割，斜向 Current 与 Tsunami 击退要求玩家在有限区域内预站并落到安全块。
- 默认解法：每一步画当前平台边界、斜线覆盖和击退落点。
- 常见优化：把平台状态做成背景；路线箭头保持短且不交叉。
- 常见失误：人物落点正确但平台已不存在；击退预站偏离。
- 可类比机制：平台切割、斜线、击退 landing、狭窄场地。
- 可迁移部分：arena state、斜线 safe lane、landing zone。
- 不应照搬：E3S 平台形状与 Tsunami 方向组合只属于 Leviathan。
- XivPlan 图示拆分：平台；Current；Tsunami 前；落点；复位。
- 需要确认的信息：当前平台、斜线方向、击退来源、防击退规则。
- 参考来源：[Final Fantasy XIV Wiki E3S](https://ffxiv.consolegameswiki.com/wiki/Eden%27s_Gate:_Inundation_%28Savage%29)
- 置信度：`high`

## E4S Uplift Gaols And Landslides

- 副本：Eden Savage / E4S Titan
- 阶段：Titan
- 常见别名：E4S、Titan、Uplift、Gaol、石牢、Landslide、车
- 机制类别：`tile-platform`、`bait`、`sequence`
- 原理：Titan 通过平台隆起、石牢、冲拳和 Landslide 改变安全区，玩家需要在 arena state 变化中保持分组。
- 默认解法：画 Uplift 后平台状态、石牢职责与 Landslide 路线；转车阶段单独成图。
- 常见优化：分组固定在稳定平台；近战位优先保留 Boss 接触。
- 常见失误：平台状态漏画；石牢或冲拳方向读反。
- 可类比机制：Titan 石牢、平台变化、击退或冲拳、tile arena。
- 可迁移部分：arena-state snapshot、固定平台组、路线分图。
- 不应照搬：E4S 平台布局和车形态攻击只属于 Titan。
- XivPlan 图示拆分：Uplift；石牢；Landslide；转车；复位。
- 需要确认的信息：平台 case、石牢点名、分组、冲拳方向。
- 参考来源：[Final Fantasy XIV Wiki E4S](https://ffxiv.consolegameswiki.com/wiki/Eden%27s_Gate:_Sepulture_%28Savage%29)
- 置信度：`high`

## E5S Fury's Fourteen

- 副本：Eden Savage / E5S Ramuh
- 阶段：Ramuh
- 常见别名：E5S、Ramuh、Fury's Fourteen、Stepped Leader、雷枪、雷云
- 机制类别：`bait`、`tower`、`line-shape`
- 原理：雷云、雷枪、冲锋和 Stepped Leader 需要按雷球状态、站位与移动时机处理。
- 默认解法：先标雷球需求与云位置，再画雷枪 lane 和冲锋 safe side。
- 常见优化：固定云与枪职责；图上明确谁需要或不需要雷球。
- 常见失误：雷球层数错误；枪 lane 与队伍移动交叉。
- 可类比机制：状态资源、枪线、云 bait、冲锋。
- 可迁移部分：资源标签、固定 lane、bait 与 non-bait 分离。
- 不应照搬：E5S 雷球层数和 Fury's Fourteen 阵型只属于 Ramuh。
- XivPlan 图示拆分：雷球；云；枪；冲锋；复位。
- 需要确认的信息：雷球层数、枪分配、云职责、冲锋方向。
- 参考来源：[Final Fantasy XIV Wiki E5S](https://ffxiv.consolegameswiki.com/wiki/Eden%27s_Verse:_Fulmination_%28Savage%29)
- 置信度：`high`

## E6S Conflag Strike And Hands Of Hell

- 副本：Eden Savage / E6S Ifrit and Garuda
- 阶段：Garuda, Ifrit, and Raktapaksa
- 常见别名：E6S、Conflag Strike、Hands of Hell、火风、线
- 机制类别：`tether`、`line-shape`、`sequence`
- 原理：风火 Boss 的线、冲锋、扇形和 Conflag Strike 连续叠加，玩家要按 tether 身份进入固定 lane。
- 默认解法：先画 tether 分组与 lane，再画冲锋、扇形和融合后安全区。
- 常见优化：左右组固定；减少跨场交换。
- 常见失误：线拉错侧；融合后仍沿用单 Boss 安全区。
- 可类比机制：线分组、双 Boss 融合、冲锋 lane。
- 可迁移部分：tether lanes、Boss 状态变化、分阶段图。
- 不应照搬：E6S 的线身份和融合顺序只属于该副本。
- XivPlan 图示拆分：线分配；冲锋；Conflag；融合；复位。
- 需要确认的信息：线颜色、左右组、冲锋方向、融合时机。
- 参考来源：[Final Fantasy XIV Wiki E6S](https://ffxiv.consolegameswiki.com/wiki/Eden%27s_Verse:_Furor_%28Savage%29)
- 置信度：`high`

## E7S Portals And Color Stacks

- 副本：Eden Savage / E7S Idol of Darkness
- 阶段：Idol of Darkness
- 常见别名：E7S、Idol of Darkness、Portal、传送门、颜色、鸟
- 机制类别：`clone-memory`、`debuff`、`line-shape`
- 原理：传送门颜色和入口方向决定延迟激光出口，玩家还要按光暗颜色处理分组与 adds。
- 默认解法：先画入口到出口映射，再画颜色分组和最终 safe lane。
- 常见优化：为每种 portal 路径使用同色箭头；adds 阶段独立成图。
- 常见失误：只看入口不推出口；颜色组在激光 lane 上集合。
- 可类比机制：Portal 激光、延迟映射、颜色分组。
- 可迁移部分：入口出口映射、颜色标签、观察与执行。
- 不应照搬：E7S portal 布局和光暗颜色规则只属于 Idol of Darkness。
- XivPlan 图示拆分：portal 入口；出口预测；颜色组；adds；复位。
- 需要确认的信息：portal 颜色、出口方向、颜色组、adds 优先级。
- 参考来源：[Final Fantasy XIV Wiki E7S](https://ffxiv.consolegameswiki.com/wiki/Eden%27s_Verse:_Iconoclasm_%28Savage%29)
- 置信度：`high`

## E9S Tiles And Wide Angle

- 副本：Eden Savage / E9S Cloud of Darkness
- 阶段：Cloud of Darkness
- 常见别名：E9S、Cloud of Darkness、Anti-Air、Wide-Angle、地板、放云
- 机制类别：`tile-platform`、`bait`、`cleave`
- 原理：场地 tiles、Anti-Air/Wide-Angle 范围与放云 bait 组合，玩家需要在有效地板内保留分散空间。
- 默认解法：画 tile 状态，再画前后或左右安全区和云落点。
- 常见优化：固定放云路线；近战位在 tile 内贴目标圈。
- 常见失误：云放在回收路线；地板状态过期后仍按旧图移动。
- 可类比机制：tile arena、云 bait、前后刀、平台安全区。
- 可迁移部分：arena-state snapshot、bait 路线、Boss-relative cleave。
- 不应照搬：E9S tile 消失规则和云持续时间只属于该副本。
- XivPlan 图示拆分：tile；范围；放云；回收。
- 需要确认的信息：tile 状态、范围类型、云职责、回收点。
- 参考来源：[Final Fantasy XIV Wiki E9S](https://ffxiv.consolegameswiki.com/wiki/Eden%27s_Promise:_Umbra_%28Savage%29)
- 置信度：`high`

## E10S Shadows And Umbral Orbs

- 副本：Eden Savage / E10S Shadowkeeper
- 阶段：Shadowkeeper
- 常见别名：E10S、Shadowkeeper、影子、Shadow、Umbral Orb、狗
- 机制类别：`clone-memory`、`line-shape`、`sequence`
- 原理：Boss 的影子方向决定延迟攻击朝向，Umbral Orb 与 clone-like 读图进一步限制安全区。
- 默认解法：先画 Boss 本体与 shadow 投影，再画延迟攻击和 orb 安全位。
- 常见优化：图上明确区分 Boss facing 与 shadow facing。
- 常见失误：按本体而不是影子躲攻击；观察图与执行图混在一起。
- 可类比机制：影子延迟、镜像方向、clone-memory。
- 可迁移部分：双朝向、延迟执行、观察分图。
- 不应照搬：E10S shadow 映射和 orb 顺序只属于 Shadowkeeper。
- XivPlan 图示拆分：影子观察；攻击预测；orb；执行；复位。
- 需要确认的信息：影子方向、攻击类型、orb 规则、最终站位。
- 参考来源：[Final Fantasy XIV Wiki E10S](https://ffxiv.consolegameswiki.com/wiki/Eden%27s_Promise:_Litany_%28Savage%29)
- 置信度：`high`

## E11S Elemental Break And Cycles

- 副本：Eden Savage / E11S Fatebreaker
- 阶段：Fatebreaker
- 常见别名：E11S、Fatebreaker、Elemental Break、Cycles、雷火光、Turn of the Heavens
- 机制类别：`clone-memory`、`spread`、`stack`、`sequence`
- 原理：技能与元素属性组合决定散开、分摊、击退或额外范围，玩家要先读属性再套处理模板。
- 默认解法：建立雷、火、光属性字典，再为 Break、Burnt Strike 和 Cycles 画对应落点。
- 常见优化：同一属性使用稳定颜色和短 callout；重复模板只保留差异。
- 常见失误：技能名对但元素看错；击退与分摊顺序混淆。
- 可类比机制：FRU Fatebreaker、属性 remix、技能名加元素后缀。
- 可迁移部分：属性字典、模板复用、差异化画图。
- 不应照搬：E11S 与 FRU 的攻击顺序和数值不同，不能直接复制站位。
- XivPlan 图示拆分：元素图例；Break；Strike；Cycles；复位。
- 需要确认的信息：属性、技能、击退规则、散开或分摊。
- 参考来源：[Final Fantasy XIV Wiki E11S](https://ffxiv.consolegameswiki.com/wiki/Eden%27s_Promise:_Anamorphosis_%28Savage%29)
- 置信度：`high`
