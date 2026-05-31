# Arcadion Savage Mechanic Cards

## Scope

Use these cards for Arcadion Savage (`M1S+`). Arcadion is the live raid series as of May 31, 2026. Before drawing a concrete live-tier strategy, refresh the source guide or use the user's macro as authoritative.

## Witch Hunt

- 副本：Arcadion Savage / M4S Wicked Thunder
- 阶段：Wicked Thunder
- 常见别名：Witch Hunt、近远、巫术、雷圈
- 机制类别：`bait`、`spread`、`sequence`
- 原理：多轮近远 bait 与个人圈按固定顺序交替，玩家需要按职责进入稳定半径并保持可读间距。
- 默认解法：先画近 bait 与远 bait 的半径，再按轮次标谁进谁出；每轮结束明确复位。
- 常见优化：将角色分成稳定内外组，减少反复交换；近战优先使用内圈合法点。
- 常见失误：只记近远，不记轮次；非 bait 玩家站进锁定半径。
- 可类比机制：近远 bait、内外圈轮换、closest/farthest targeting。
- 可迁移部分：同心半径、bait 与 non-bait 分离、轮次。
- 不应照搬：M4S 的目标数量、轮次与 arena half 规则需要按具体机制确认。
- XivPlan 图示拆分：内外组；第一轮；交换；第二轮；复位。
- 需要确认的信息：近远目标数、轮次、锁定时机、内外组。
- 参考来源：[Icy Veins M4S guide](https://www.icy-veins.com/ffxiv/aac-light-heavyweight-m4-savage-raid-guide)
- 置信度：`high`

## Sunrise Sabbath

- 副本：Arcadion Savage / M4S Wicked Thunder
- 阶段：Wicked Thunder
- 常见别名：Sunrise Sabbath、日出、炮台塔、长短 Buff
- 机制类别：`debuff`、`tower`、`line-shape`、`sequence`
- 原理：玩家根据长短状态和极性处理 cannon line 与 tower soak，职责在不同轮次切换。
- 默认解法：先画 Debuff 表，再按第一轮 cannon/tower、第二轮 cannon/tower 拆图。
- 常见优化：固定每种状态的等待 lane；用颜色和文字同时标极性。
- 常见失误：长短状态混淆；炮台方向对但踩错塔。
- 可类比机制：长短 Debuff 踩塔、炮台线、极性 tower。
- 可迁移部分：Debuff bucket、长短轮次、line 与 tower 分层。
- 不应照搬：M4S 的 cannon 朝向、塔位置和极性规则需要重新确认。
- XivPlan 图示拆分：状态表；第一轮炮台与塔；换位；第二轮；复位。
- 需要确认的信息：长短时长、炮台方向、极性、塔分组。
- 参考来源：[Icy Veins M4S guide](https://www.icy-veins.com/ffxiv/aac-light-heavyweight-m4-savage-raid-guide)
- 置信度：`high`

## Sugar Riot Animals And Adds

- 副本：Arcadion Savage / M6S Sugar Riot
- 阶段：Sugar Riot
- 常见别名：M6S、Sugar Riot、糖画、动物、小怪、猫、蛇、蜂
- 机制类别：`adds-priority`、`tile-platform`、`bait`、`sequence`
- 原理：场地画作与动物小怪改变安全区、移动路线和转火优先级；攻略图需要把素材身份和 arena state 画清楚。
- 默认解法：先识别本轮动物或画作，再画出现位置、安全区、移动路线和转火优先级；复杂素材使用本地 PNG 或 image2 生成的透明图标。
- 常见优化：为每种动物建立一致图标和颜色；把素材说明与人物站位分层。
- 常见失误：用纯文字代替动物素材，导致图难以扫读；只画安全区不写转火目标。
- 可类比机制：特殊素材机制、adds priority、tile arena、图标驱动的安全区变化。
- 可迁移部分：custom image 工作流、素材图例、arena-state snapshot、转火标签。
- 不应照搬：M6S 每种动物的具体攻击、出现顺序和 tile 变化必须按所画步骤确认。
- XivPlan 图示拆分：素材图例；动物出现；安全区；移动或转火；复位。
- 需要确认的信息：动物种类、画作轮次、攻击范围、转火顺序、是否需要 image2 素材。
- 参考来源：[Icy Veins M6S guide](https://www.icy-veins.com/ffxiv/aac-cruiserweight-m2-savage-raid-guide)
- 置信度：`high`

## Lone Wolf's Lament

- 副本：Arcadion Savage / M8S Howling Blade
- 阶段：Lone Wolf's Lament
- 常见别名：M8S、Howling Blade、Lone Wolf、近远线、平台
- 机制类别：`tile-platform`、`tether`、`sequence`
- 原理：玩家分散到不同平台后，根据近线或远线条件调整位置；处理必须先满足 tether 条件，再考虑后续共享伤害和平台移动。
- 默认解法：先画平台状态与初始分组，再画近线和远线玩家的调整路线；将多段平台移动拆开。
- 常见优化：让固定职责尽量留在原平台；为近线和远线使用不同颜色与文字标签。
- 常见失误：只画最终平台，没有画初始分组；线长条件满足但下一轮平台路线冲突。
- 可类比机制：近远线、平台转移、Lone Wolf、tile arena。
- 可迁移部分：arena-state snapshot、近远线、平台分组、逐段复位。
- 不应照搬：M8S 的平台分组、近远线人数和传送顺序需要按具体攻略确认。
- XivPlan 图示拆分：平台与初始分组；线类型；第一次调整；后续平台；复位。
- 需要确认的信息：平台布局、近远线条件、职责组、传送时机、后续共享伤害。
- 参考来源：[Icy Veins M8S guide](https://www.icy-veins.com/ffxiv/aac-cruiserweight-m4-savage-raid-guide)
- 置信度：`high`

## Trophy Weapons And Meteorain

- 副本：Arcadion Savage / M11S The Tyrant
- 阶段：The Tyrant
- 常见别名：M11S、The Tyrant、Trophy Weapons、Meteorain、武器、陨石
- 机制类别：`clone-memory`、`bait`、`line-shape`、`sequence`
- 原理：Boss 根据武器或 portal 顺序组合不同安全区、分摊、散开与陨石落点；玩家要先读序列，再按固定节拍移动。
- 默认解法：先画武器与 portal 顺序，再画每次 jump 或 bait 的安全点；陨石阶段单独画落点、保护区和回收路线。
- 常见优化：把稳定的 full-uptime 路线标为可选方案，同时保留容错更高的默认路线。
- 常见失误：武器读对但 jump 顺序记错；陨石落点距离不够；只画路线不画 portal line。
- 可类比机制：武器读图、portal 顺序、陨石 bait、保护区、Exaflare-like 安全路线。
- 可迁移部分：观察序列、分阶段路线、bait 落点、默认与 uptime 路线分离。
- 不应照搬：Heavyweight live-tier 的具体技能组合和优化路线在使用前必须刷新，并以用户宏为准。
- XivPlan 图示拆分：武器或 portal 观察；逐次安全区；陨石 bait；保护区；复位。
- 需要确认的信息：技能组合、序列、陨石落点、portal line、默认或 uptime 路线。
- 参考来源：[Icy Veins M11S guide](https://www.icy-veins.com/ffxiv/aac-heavyweight-m3-savage-raid-guide)
- 置信度：`refresh-before-use`

## M1S Mouser And Nine Lives

- 副本：Arcadion Savage / M1S Black Cat
- 阶段：Black Cat
- 常见别名：M1S、Black Cat、Mouser、地板、Nine Lives、Soulshade
- 机制类别：`tile-platform`、`clone-memory`、`sequence`
- 原理：Mouser 破坏场地 tile，Nine Lives 与 Soulshade 记录并复现 Boss 动作；玩家要同时记忆 arena state 与 replay 顺序。
- 默认解法：先画破坏后的 tile，再画记录动作与分身复现的先后。
- 常见优化：用深色压暗已破坏 tile；观察和执行严格分图。
- 常见失误：人物站位正确但 tile 已破坏；分身动作顺序记反。
- 可类比机制：地板破坏、分身重放、clone-memory。
- 可迁移部分：arena-state snapshot、record/replay、执行顺序。
- 不应照搬：M1S tile 图案和 Soulshade 顺序只属于 Black Cat。
- XivPlan 图示拆分：Mouser；tile 状态；Nine Lives 观察；Soulshade 执行；复位。
- 需要确认的信息：tile 图案、动作顺序、分散或分摊、静态路线。
- 参考来源：[Icy Veins M1S guide](https://www.icy-veins.com/ffxiv/aac-light-heavyweight-m1-savage-raid-guide)
- 置信度：`high`

## M2S Beats And Alarm Pheromones

- 副本：Arcadion Savage / M2S Honey B. Lovely
- 阶段：Honey B. Lovely
- 常见别名：M2S、Honey B、Beat、爱心、Alarm Pheromones、蜜蜂
- 机制类别：`debuff`、`bait`、`sequence`
- 原理：Beat 爱心层数、舞台 AoE 与 Alarm Pheromones 蜂群路线组合，玩家需要避免额外叠层并沿安全 lane 移动。
- 默认解法：先标爱心层数与禁止接触区，再画蜂群路径、安全缝和回收点。
- 常见优化：蜂群阶段只画关键安全路线；不同 Beat 使用一致配色。
- 常见失误：层数接近上限仍吃额外爱心；蜂群箭头过多导致图难读。
- 可类比机制：魅惑层数、蜂群跑圈、移动安全缝。
- 可迁移部分：Debuff 层数、路线、接触禁区。
- 不应照搬：M2S Beat 层数和蜂群 pattern 只属于 Honey B. Lovely。
- XivPlan 图示拆分：爱心层数；蜂群；安全路线；复位。
- 需要确认的信息：当前 Beat、蜂群 pattern、层数上限、队伍路线。
- 参考来源：[Icy Veins M2S guide](https://www.icy-veins.com/ffxiv/aac-light-heavyweight-m2-savage-raid-guide)
- 置信度：`high`

## M3S Chain Deathmatch Fusefield And Fusedown

- 副本：Arcadion Savage / M3S Brute Bomber
- 阶段：Brute Bomber
- 常见别名：M3S、Brute Bomber、Chain Deathmatch、Final Fusedown、Fusefield、炸弹
- 机制类别：`debuff`、`sequence`、`knockback`
- 原理：长短引线、炸弹、冲击与场边击退连续组合，玩家要按 fuse 时长进入对应处理点。
- 默认解法：先做长短 fuse 表，再画每轮炸弹、击退来源和 landing zone。
- 常见优化：把 fuse 时长作为主键；边缘击退单独画落点。
- 常见失误：只看炸弹位置，不看自己的引线；击退方向读反。
- 可类比机制：长短 Debuff、炸弹时间轴、击退 landing。
- 可迁移部分：timer bucket、bomb order、knockback。
- 不应照搬：M3S fuse 时长和 bomb 图案只属于 Brute Bomber。
- XivPlan 图示拆分：fuse 表；Chain Deathmatch；Fusedown；Fusefield；复位。
- 需要确认的信息：时长、炸弹顺序、击退来源、防击退规则。
- 参考来源：[Icy Veins M3S guide](https://www.icy-veins.com/ffxiv/aac-light-heavyweight-m3-savage-raid-guide)
- 置信度：`high`

## M5S Arcady Night Fever And Ride The Waves

- 副本：Arcadion Savage / M5S Dancing Green
- 阶段：Dancing Green
- 常见别名：M5S、Dancing Green、Arcady Night Fever、节拍、Ride the Waves、跳舞
- 机制类别：`sequence`、`tile-platform`、`rotation`
- 原理：舞台灯、节拍与波浪路线按音乐节奏连续切换，玩家需要按固定 lane 和 timing 移动。
- 默认解法：画舞台格、节拍序号、每拍落点与最终回收。
- 常见优化：将路线压缩为可数拍的短口诀；图中只保留当前和下一拍箭头。
- 常见失误：路线正确但节拍错一拍；舞台 tile 状态没有更新。
- 可类比机制：跳舞机制、按拍移动、tile arena。
- 可迁移部分：节拍、固定 lane、逐拍图、口诀。
- 不应照搬：M5S 舞步、波浪方向和灯位只属于 Dancing Green。
- XivPlan 图示拆分：舞台；每拍路线；Ride the Waves；复位。
- 需要确认的信息：节拍、波浪方向、固定 lane、队伍口诀。
- 参考来源：[Icy Veins M5S guide](https://www.icy-veins.com/ffxiv/aac-cruiserweight-m1-savage-raid-guide)
- 置信度：`high`

## M7S Stoneringer And Demolition Deathmatch

- 副本：Arcadion Savage / M7S Brute Abombinator
- 阶段：Brute Abombinator
- 常见别名：M7S、Brute Abombinator、Stoneringer、Demolition Deathmatch、种子、藤蔓
- 机制类别：`clone-memory`、`tether`、`bait`、`adds-priority`
- 原理：Boss 手中武器决定钢铁或月环，建筑 tether 与种子落点形成持续藤蔓路线；Deathmatch 要在拉线压力下按固定点放种。
- 默认解法：先画武器字典，再画 tether 接取者、种子落点和藤蔓安全区。
- 常见优化：使用固定 waymark 的 Bilibili 式落种路线；武器图标与 in/out 标签并用。
- 常见失误：武器看错；拉线玩家距离不足；种子覆盖回收路线。
- 可类比机制：武器读招、线压、固定落种、adds interrupt。
- 可迁移部分：动作字典、tether lane、bait spots、adds priority。
- 不应照搬：M7S 建筑位置、武器规则和落种 waymark 只属于 Brute Abombinator。
- XivPlan 图示拆分：武器；线手；落种；藤蔓；Slaminator；复位。
- 需要确认的信息：武器、tether 接取者、落种策略、interrupt 顺序。
- 参考来源：[Icy Veins M7S guide](https://www.icy-veins.com/ffxiv/aac-cruiserweight-m3-savage-raid-guide)
- 置信度：`high`

## M9S Vamp Stomp And Coffinmaker

- 副本：Arcadion Savage / M9S Vamp Fatale
- 阶段：Vamp Fatale
- 常见别名：M9S、Vamp Fatale、Vamp Stomp、Coffinmaker、蝙蝠、棺材
- 机制类别：`tile-platform`、`bait`、`sequence`
- 原理：Vamp Stomp 生成旋转蝙蝠与扩散冲击，Coffinmaker 则在缩窄平台上按列推进并叠加 Half Moon 半场刀。
- 默认解法：先画蝙蝠旋转方向与冲击传播，再画棺材列、Half Moon 安全侧和逐行移动。
- 常见优化：棺材阶段用网格背景；蝙蝠只画传播路径和最终安全区。
- 常见失误：只躲蝙蝠，不躲冲击扩散；棺材安全列与 Half Moon 安全半场冲突。
- 可类比机制：传播 AoE、推进墙、半场刀、狭窄平台。
- 可迁移部分：arena state、传播路径、网格移动、复合 safe spot。
- 不应照搬：M9S 蝙蝠、棺材列与满足度强化只属于 Vamp Fatale。
- XivPlan 图示拆分：Vamp Stomp；蝙蝠传播；棺材网格；Half Moon；回收。
- 需要确认的信息：旋转方向、棺材列、Half Moon、队伍路线。
- 参考来源：[Icy Veins M9S guide](https://www.icy-veins.com/ffxiv/aac-heavyweight-m1-savage-raid-guide)
- 置信度：`refresh-before-use`

## M10S Insane Air And Snaking

- 副本：Arcadion Savage / M10S The Xtremes
- 阶段：Red Hot and Deep Blue
- 常见别名：M10S、The Xtremes、Insane Air、Snaking、冲浪、红蓝
- 机制类别：`clone-memory`、`debuff`、`bait`、`sequence`
- 原理：冲浪板方向决定 closest tankbuster、分摊锥或散开锥；火水 puddle、Snaking 状态和双 Boss 攻击进一步限制路线。
- 默认解法：先画双 Boss 与 surfboard 图例，再按 light party 处理 Insane Air；Snaking 阶段标火水状态与保持中场干净的路线。
- 常见优化：固定 LP1/LP2 初始 Boss；每次 surfboard 只画本轮锥形；火 puddle 尽量压边。
- 常见失误：冲浪板方向看错；火水状态套错 Boss；puddle 污染中场。
- 可类比机制：图标读招、双 Boss 小队分工、状态定向、场地资源管理。
- 可迁移部分：动作字典、light parties、puddle route、Debuff 分桶。
- 不应照搬：M10S surfboard 映射、火水交互和净化顺序只属于 The Xtremes。
- XivPlan 图示拆分：surfboard 图例；Insane Air；Snaking 状态；puddle 路线；Xtreme Snaking。
- 需要确认的信息：surfboard、light party、火水状态、puddle 路线、uptime 策略。
- 参考来源：[Icy Veins M10S guide](https://www.icy-veins.com/ffxiv/aac-heavyweight-m2-savage-raid-guide)
- 置信度：`refresh-before-use`

## M12S Mortal Slayer Grotesquerie And Replication

- 副本：Arcadion Savage / M12S Lindwurm
- 阶段：Lindwurm door boss and final boss
- 常见别名：M12S、Lindwurm、Mortal Slayer、Grotesquerie、Replication、分身
- 机制类别：`clone-memory`、`debuff`、`bait`、`sequence`
- 原理：门神 Mortal Slayer 按手与球的生成顺序处理最近目标 AoE，Grotesquerie 按职责状态展开；本体 Replication 则记录并复现多个分身组合。
- 默认解法：门神先画球的左右生成序与角色 lane，再画每个 Grotesquerie Act；本体为每轮 Replication 建观察图和执行图。
- 常见优化：使用固定 lane 和清晰序号；门神、本体分成独立图组。
- 常见失误：球顺序看对但站错左右；Grotesquerie 状态漏读；Replication 观察与执行混淆。
- 可类比机制：顺序 bait、Act 舞台、clone replay、终层多阶段机制。
- 可迁移部分：观察序列、职责分桶、Act 分图、record/replay。
- 不应照搬：M12S live-tier 的球序、Grotesquerie 状态和 Replication 组合使用前必须刷新并以用户宏为准。
- XivPlan 图示拆分：Mortal Slayer；每个 Grotesquerie Act；门神收尾；Replication 观察；Replication 执行。
- 需要确认的信息：门神或本体、Act、球序、职责状态、Replication 轮次、用户宏。
- 参考来源：[Icy Veins M12S door boss guide](https://www.icy-veins.com/ffxiv/aac-heavyweight-m4-door-boss-savage-raid-guide)、[Icy Veins M12S final boss guide](https://www.icy-veins.com/ffxiv/aac-heavyweight-m4-final-boss-savage-raid-guide)
- 置信度：`refresh-before-use`
