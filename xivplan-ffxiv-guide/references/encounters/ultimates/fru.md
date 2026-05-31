# FRU Mechanic Cards

## Scope

Use these cards for Futures Rewritten (Ultimate), commonly abbreviated `FRU`. This workspace contains local FRU guide notes and XivPlan scenes under `C:\Users\Mahiru\Desktop\FFXIV\KING X\0523-0524 FRU`. Prefer those artifacts when creating or editing concrete local diagrams.

## Cyclonic Break

- 副本：FRU / Futures Rewritten (Ultimate)
- 阶段：P1 Fatebreaker
- 常见别名：Cyclonic Break、气旋破、暴风破、八方扇形
- 机制类别：`cleave`、`rotation`、`spread`
- 原理：Boss 朝玩家方向释放多组扇形，后续安全缝会旋转变化；玩家先正确引导，再按固定节奏进安全缝。
- 默认解法：先画初始八方引导，再画第一次判定后的左右移动和后续安全缝；远近站位分层。
- 常见优化：近战位在合法安全缝内靠近 Boss，远程与治疗向外让出空间。
- 常见失误：只画最终缝，不画第一下如何引导；把玩家左右移动方向写反。
- 可类比机制：八方扇形、旋转安全缝、诱导后找缝。
- 可迁移部分：初始八方引导、近远分层、旋转节拍。
- 不应照搬：本地限制攻略里的左右移动和远近职业分配属于当前 FRU 配置，换队伍前要确认。
- XivPlan 图示拆分：初始八方；第一下判定；第一次移动；后续安全缝。
- 需要确认的信息：左右移动规则、近远分层、是否叠加火分摊或额外引导。
- 参考来源：本地 `FRU_basic_mechanics_digest.md`；本地 `Strats_limited\P1\P1_cyclonic_break_opening.xivplan`
- 置信度：`local-verified`

## Powder Mark Trail

- 副本：FRU / Futures Rewritten (Ultimate)
- 阶段：P1 Fatebreaker
- 常见别名：Powder Mark Trail、连锁爆印铭刻、连锁爆印、P1 死刑
- 机制类别：`tankbuster`、`debuff`、`sequence`
- 原理：一仇死刑附加连锁爆印和物理易伤，需要换 T；倒计时结束时按持有者与最近队友产生后续爆炸。
- 默认解法：双 T 在预定点处理，其他人避开范围；随后明确观察、换 T 和第二次处理的位置。
- 常见优化：把第一次死刑、观察分身、第二次死刑和回收拆成独立步骤。
- 常见失误：文字写了双 T 处理，但图上其他玩家仍在爆炸圈内；最近玩家选择不稳定。
- 可类比机制：换 T 死刑、最近队友二次爆炸、死刑后分身观察。
- 可迁移部分：死刑圈隔离、最近玩家锁定、换 T 时间轴。
- 不应照搬：本地黑圈半径、塔位置和限制攻略站位只适用于当前 FRU 文件。
- XivPlan 图示拆分：第一次死刑；分身观察；第二次死刑；同半场收尾。
- 需要确认的信息：范围半径、最近玩家规则、换 T 时机、塔组是否固定不动。
- 参考来源：本地 `FRU_basic_mechanics_digest.md`；本地 `Strats_limited\P1\P1_tankbusters.xivplan`
- 置信度：`local-verified`

## Diamond Dust

- 副本：FRU / Futures Rewritten (Ultimate)
- 阶段：P2 Usurper of Frost
- 常见别名：Diamond Dust、钻石星尘、DD、冰花
- 机制类别：`spread`、`knockback`、`in-out`、`sequence`
- 原理：冰花、钢铁/月环、击退和后续站位连续组合，玩家需要先处理个人落点，再完成击退后的分组判定。
- 默认解法：按观察、个人冰花、钢铁/月环、击退落点、后续分组拆图。
- 常见优化：让同组玩家共享稳定 landing lane；把冰花落点与最终分摊位分开。
- 常见失误：击退落点对，但冰花路径穿过队友；钢铁/月环次序没有单独标。
- 可类比机制：E8S Diamond Dust、冰花散开、击退后双分摊。
- 可迁移部分：个人落点、in/out 顺序、击退 landing、分组回收。
- 不应照搬：FRU 的 remix 顺序、冰花数量和后续 stacks 需要针对当前版本确认。
- XivPlan 图示拆分：初始观察；冰花；钢铁/月环；击退；四分摊或复位。
- 需要确认的信息：冰花目标、钢铁/月环顺序、击退距离、分摊人数。
- 参考来源：本地 `FRU_basic_mechanics_digest.md`；本地 `Strats_limited\P2\P2DD.xivplan`；[Icy Veins FRU P2 guide](https://www.icy-veins.com/ffxiv/futures-rewritten-ultimate-guide-for-phase-2-usurper-of-frost)
- 置信度：`local-verified`

## Light Rampant

- 副本：FRU / Futures Rewritten (Ultimate)
- 阶段：P2 Usurper of Frost
- 常见别名：Light Rampant、光之失控、光暴、六芒星
- 机制类别：`tether`、`tower`、`spread`、`sequence`
- 原理：六名连线玩家形成图形并处理塔与 orb，未连线玩家承担额外 AoE；核心是 tether graph、塔职责和最后安全展开。
- 默认解法：全员先八方观察，连线玩家建立六芒星或所选图形，未连线玩家进入专属职责位，再按时间轴踩塔与回收。
- 常见优化：用稳定图形降低线交叉；把观察、换位、塔、orb 和最终收尾拆开。
- 常见失误：只看塔不看线；未连线玩家路径穿过 tether 图形；照搬 E8S 站位而忽略 FRU remix。
- 可类比机制：E8S `Light Rampant`、线塔组合、六边形 tether、自由人补位。
- 可迁移部分：tether graph、free-player 职责、塔与 orb 分阶段。
- 不应照搬：E8S 的塔序、球数和站位不能直接复制到 FRU；FRU 内部也存在不同策略。
- XivPlan 图示拆分：八方观察；tether 图形；塔；orb；最终回收。
- 需要确认的信息：所用策略、tether 换位规则、塔序、orb 职责、最终站位。
- 参考来源：本地 `Strats_limited\P2\P2_light_rampant_hexagram.xivplan`；[Icy Veins FRU P2 guide](https://www.icy-veins.com/ffxiv/futures-rewritten-ultimate-guide-for-phase-2-usurper-of-frost)
- 置信度：`local-verified`

## Ultimate Relativity

- 副本：FRU / Futures Rewritten (Ultimate)
- 阶段：P3 Oracle of Darkness
- 常见别名：Ultimate Relativity、时间压缩绝、UR、相对论
- 机制类别：`debuff`、`sequence`、`rotation`、`bait`
- 原理：多种倒计时 Debuff 按固定时间轴连续结算，玩家需要根据职责在不同 beat 处理火、冰、激光、分摊或等待。
- 默认解法：先做职责时间轴，再为每个 bucket 画起点、移动、判定和回收；每图只展示当前 beat。
- 常见优化：复用固定等待点和旋转方向；让每名玩家只记所属职责线。
- 常见失误：时间轴正确但移动顺序错误；把十拍舞蹈压进一张图。
- 可类比机制：E12S Relativity、Hello World-like 时间桶、长时间 Debuff 舞蹈。
- 可迁移部分：Debuff bucket、时间轴、固定 lane、beat-by-beat 图示。
- 不应照搬：FRU 的 Debuff 集合、时长和 rotation 规则只适用于该机制。
- XivPlan 图示拆分：职责总览；按本地文件拆成 8-10 个 beat；最终复位。
- 需要确认的信息：职责表版本、旋转方向、每个 Debuff 时长、队伍约定 callout。
- 参考来源：本地 `FRU_basic_mechanics_digest.md`；本地 `Strats_limited\P3\P3UR.xivplan`
- 置信度：`local-verified`

## Apocalypse

- 副本：FRU / Futures Rewritten (Ultimate)
- 阶段：P3 Oracle of Darkness
- 常见别名：Apocalypse、启示、车头、地火
- 机制类别：`line-shape`、`rotation`、`bait`、`sequence`
- 原理：场地出现有顺序的 Apocalypse 地火，队伍需要读起点与方向并沿安全路径移动，同时处理后续个人职责。
- 默认解法：先画地火起点和转动方向，再画车头或主移动线；追加职责单独成图。
- 常见优化：用少量关键箭头表达路线，不画所有可能分支；固定一名 callout 玩家读图。
- 常见失误：方向判断正确但进入安全缝过早；箭头遮住地火序号。
- 可类比机制：Exaflare、旋转地火、跟车头、读序列找缝。
- 可迁移部分：起点、旋转方向、主路线、追加职责分图。
- 不应照搬：地火间隔、车头规则和安全路线需要按具体机制确认。
- XivPlan 图示拆分：读起点；第一段路线；中段换位；追加职责；复位。
- 需要确认的信息：地火顺序、转向、队伍路线、追加散开或分摊。
- 参考来源：本地 `FRU_basic_mechanics_digest.md`；本地 `Strats_limited\P3\P3_apocalypse_carhead.xivplan`
- 置信度：`local-verified`

## Darklit Dragonsong

- 副本：FRU / Futures Rewritten (Ultimate)
- 阶段：P4 Usurper of Frost and Oracle of Darkness
- 常见别名：Darklit Dragonsong、光与暗的龙诗、龙诗、P4b
- 机制类别：`tether`、`tower`、`debuff`、`sequence`
- 原理：光暗线、塔和多轮位置判断组合成连续舞蹈，需要先确认 case，再按小队和个人职责处理。
- 默认解法：先画 case 观察，再按 line case 分支画塔、线和回收；每个分支保持同样图例。
- 常见优化：把所有 case 共用的动作写成主线，只为不同线型保留局部分支图。
- 常见失误：把 case 选择和执行步骤混在一起；线看对但塔分组套错。
- 可类比机制：线塔组合、light-party tower、case-based dance。
- 可迁移部分：case 观察、共用主线、局部分支、塔与线分层。
- 不应照搬：FRU 的线型、光暗规则和塔分组必须按所用攻略确认。
- XivPlan 图示拆分：观察 case；共用起点；每个 line case 的塔和线；最终回收。
- 需要确认的信息：采用的 case 分类、线颜色、塔组、光暗状态、队伍宏。
- 参考来源：本地 `FRU_basic_mechanics_digest.md`；本地 `Strats_limited\P4\P4_darklight_dragonsong_line_cases.xivplan`；[Icy Veins FRU P4 guide](https://www.icy-veins.com/ffxiv/futures-rewritten-ultimate-guide-for-phase-4-enter-the-dragon)
- 置信度：`local-verified`

## Crystallize Time

- 副本：FRU / Futures Rewritten (Ultimate)
- 阶段：P4 Usurper of Frost and Oracle of Darkness
- 常见别名：Crystallize Time、时间结晶、P4c
- 机制类别：`debuff`、`sequence`、`clone-memory`、`tower`
- 原理：时间系 Debuff 与来自 E8S、E12S 的 remix 判定叠加，玩家需要按时长与职责进入连续处理位。
- 默认解法：先按 Debuff 与时长分桶，再逐 beat 处理；将观察、移动、判定、回收分开。
- 常见优化：复用 Ultimate Relativity 的 timeline-card 画法；静态队可固定每类职责 lane。
- 常见失误：只按职业记位置，忽略随机 Debuff；跨 beat 回收太早。
- 可类比机制：Advanced Relativity、Wyrm's Lament、时间轴 Debuff 舞蹈。
- 可迁移部分：Debuff bucket、时长、固定 lane、逐 beat 图。
- 不应照搬：E8S 或 E12S 原版站位不能直接覆盖 FRU remix。
- XivPlan 图示拆分：Debuff 总览；每个时长 bucket 的处理；最终回收。
- 需要确认的信息：Debuff 表、时长、塔或线职责、队伍采用的优先级。
- 参考来源：本地 `FRU_basic_mechanics_digest.md`；[Icy Veins FRU P4 guide](https://www.icy-veins.com/ffxiv/futures-rewritten-ultimate-guide-for-phase-4-enter-the-dragon)
- 置信度：`high`

## Fulgent Blade

- 副本：FRU / Futures Rewritten (Ultimate)
- 阶段：P5 Pandora
- 常见别名：Fulgent Blade、光辉锋刃、直线地火
- 机制类别：`line-shape`、`sequence`
- 原理：全屏伤害后生成多向直线地火，玩家需要识别安全路线并按后续机制复位。
- 默认解法：画地火方向、第一安全点、穿越或跟随路线、下一机制集合点。
- 常见优化：箭头只保留主路线；若有近战 uptime 路线，单独标注为可选优化。
- 常见失误：图中只标安全终点，没有标穿越时机。
- 可类比机制：多向直线地火、Exaflare-like 穿越、走廊安全区。
- 可迁移部分：方向读取、路线、穿越节拍、复位。
- 不应照搬：线宽、间隔和后续机制衔接必须重新确认。
- XivPlan 图示拆分：地火出现；第一步；穿越；下一机制复位。
- 需要确认的信息：线宽、生成顺序、是否允许跟线、后续塔或分摊。
- 参考来源：本地 `FRU_basic_mechanics_digest.md`
- 置信度：`high`
