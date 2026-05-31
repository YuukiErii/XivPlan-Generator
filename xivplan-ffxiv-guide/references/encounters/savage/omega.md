# Omega Savage Mechanic Cards

## Scope

Use these cards for Omega Savage (`O1S-O12S`). The goal is to retrieve high-value analogy patterns from the 4.x raid series. Confirm the exact floor and strategy before drawing.

## Grand Cross

- 副本：Omega Savage / O4S Exdeath and Neo Exdeath
- 阶段：Neo Exdeath
- 常见别名：Grand Cross、Delta、Alpha、Omega、大十字
- 机制类别：`debuff`、`sequence`、`spread`
- 原理：玩家获得不同 Debuff 与职责，需要按状态进入预定区域并依次处理，核心是先分类再执行。
- 默认解法：把 Debuff 映射到固定 lane 或 quadrant；先画职责表，再按每轮判定拆图。
- 常见优化：让同一职责家族共享等待点，减少跨场；把随机状态翻译为短 callout。
- 常见失误：只按职业站位，不先识别随机状态；把多轮 Grand Cross 塞进一张图。
- 可类比机制：Hello World-like 分类、Relativity-like 时间轴、复杂 Debuff 大运动会。
- 可迁移部分：Debuff 分类、固定 lane、分 beat 处理。
- 不应照搬：O4S 的 Debuff 集合、持续时间和具体安全区不适用于后续机制。
- XivPlan 图示拆分：状态表；初始分 lane；每轮判定；复位。
- 需要确认的信息：Grand Cross 变体、Debuff 名称、持续时间、lane 分配。
- 参考来源：[Final Fantasy XIV Wiki O4S](https://ffxiv.consolegameswiki.com/wiki/Deltascape_V4.0_(Savage))
- 置信度：`medium`

## Forsaken

- 副本：Omega Savage / O8S Kefka
- 阶段：God Kefka
- 常见别名：Forsaken、神々の像、塔、鬼头、Skull
- 机制类别：`tower`、`bait`、`spread`、`sequence`
- 原理：塔、头部/骷髅素材、分摊和散开连续组合，需要先按职责分配塔，再处理移动素材与后续个人位置。
- 默认解法：先画 tower assignment，再画鬼头或 Skull 路线与安全区；素材较特殊时使用本地 PNG 或自定义 image object。
- 常见优化：把素材移动与 tower soak 分开成图；保留稳定塔组。
- 常见失误：图上缺少特殊素材，玩家无法快速读懂危险来源；tower 人数与分组不一致。
- 可类比机制：塔加移动素材、特殊图标安全区、需要 image2 的机制对象。
- 可迁移部分：塔组、移动素材、素材图像工作流、分阶段图示。
- 不应照搬：O8S 的具体 Skull 轨迹、塔序和 Knockback 处理需要按原机制确认。
- XivPlan 图示拆分：塔分配；特殊素材出现；移动与避让；后续散开或分摊。
- 需要确认的信息：Forsaken 轮次、塔人数、素材轨迹、是否需要自定义 PNG。
- 参考来源：[Final Fantasy XIV Wiki O8S](https://ffxiv.consolegameswiki.com/wiki/Sigmascape_V4.0_(Savage))
- 置信度：`medium`

## Hello World

- 副本：Omega Savage / O12S Omega
- 阶段：Omega-M and Omega-F / Final Omega
- 常见别名：Hello World、HW、补丁、Rot、世界状态
- 机制类别：`debuff`、`pass`、`bait`、`sequence`
- 原理：多种带时长的 Debuff 按规则传递、爆炸或清除，玩家需要在固定时间轴上完成 relay。
- 默认解法：先建立状态桶与时长表，再为每个 relay 画等待点、交接点、bait 点和清除点。
- 常见优化：固定传递路线，减少自由追人；让 callout 只报当前轮。
- 常见失误：传错目标；状态持有人路径交叉；最终清除条件遗漏。
- 可类比机制：TOP `Hello World`、TEA Nisi、传毒、长时间 Debuff 舞蹈。
- 可迁移部分：状态分类、时长、relay 路径、beat-by-beat 图示。
- 不应照搬：O12S 的 Patch、Rot 和 tower 规则不能直接套到 TOP 或其他传毒机制。
- XivPlan 图示拆分：Debuff 总览；第一次 relay；第二次 relay；清除；复位。
- 需要确认的信息：状态种类、时长、交接条件、清除条件、采用的地区攻略。
- 参考来源：[Icy Veins O12S Blue Mage guide](https://www.icy-veins.com/ffxiv/alphascape-v4-0-savage-blue-mage-guide)
- 置信度：`high`

## Archive All And Patch

- 副本：Omega Savage / O12S Omega
- 阶段：Omega-M and Omega-F
- 常见别名：Archive All、Patch、男女组合技、远近线
- 机制类别：`clone-memory`、`tether`、`spread`
- 原理：玩家根据 Patch 线和 Boss 动作进入正确距离与安全区，并避开多方向攻击。
- 默认解法：先画 Patch 配对和近远条件，再画 Boss 动作与最终安全区。
- 常见优化：将 pair lineup 固定；观察与执行分图。
- 常见失误：只处理线长，不看 Boss 动作；pair 交叉。
- 可类比机制：TOP `Party Synergy`、PlayStation pair、近远线、观察分身动作。
- 可迁移部分：pair lineup、距离条件、观察后执行。
- 不应照搬：O12S 的动作组合、Patch 颜色和具体 safe spot 不能直接复制。
- XivPlan 图示拆分：Patch pair；距离站位；Boss 动作；最终安全区。
- 需要确认的信息：Patch 类型、近远阈值、Boss 动作、最终散开。
- 参考来源：[Icy Veins O12S Blue Mage guide](https://www.icy-veins.com/ffxiv/alphascape-v4-0-savage-blue-mage-guide)
- 置信度：`medium`

## O1S Clamp And Downburst

- 副本：Omega Savage / O1S Alte Roite
- 阶段：Alte Roite
- 常见别名：O1S、Alte Roite、Clamp、Downburst、击退
- 机制类别：`knockback`、`line-shape`、`sequence`
- 原理：直线冲锋、场地击退与基础 AoE 连续出现，玩家需要读 Boss 位置并预站到合法 landing zone。
- 默认解法：先画 Clamp 路径，再画 Downburst 来源、预站点和落点。
- 常见优化：把防击退与手动 landing 两种合法方案分开写。
- 常见失误：只标起点，没有标击退后的落点；Boss 冲锋方向读反。
- 可类比机制：基础冲锋、场中击退、击退后复位。
- 可迁移部分：line telegraph、landing zone、anti-knockback 分支。
- 不应照搬：O1S 的场地边界与击退距离不能直接用于其他副本。
- XivPlan 图示拆分：Clamp；击退前；击退落点；回中。
- 需要确认的信息：是否允许防击退、落点、安全边。
- 参考来源：[Final Fantasy XIV Wiki O1S](https://ffxiv.consolegameswiki.com/wiki/Deltascape_V1.0_%28Savage%29)
- 置信度：`high`

## O2S Gravity And Levitation

- 副本：Omega Savage / O2S Catastrophe
- 阶段：Catastrophe
- 常见别名：O2S、Catastrophe、Levitation、Gravity、上下层
- 机制类别：`debuff`、`tile-platform`、`sequence`
- 原理：玩家通过 Levitation 改变高度，躲避只命中地面或空中的攻击；站位不仅有平面坐标，还有高度状态。
- 默认解法：每一步标明地面组与浮空组，随后画对应安全区。
- 常见优化：用不同边框或文字标签区分高度，不依赖图标颜色。
- 常见失误：人物位置正确但高度状态错误；Levitation 切换过晚。
- 可类比机制：高度切换、浮空、双层场地、状态决定安全区。
- 可迁移部分：arena state、状态标签、切换时机。
- 不应照搬：O2S 的高度技能和重力攻击组合只属于 Catastrophe。
- XivPlan 图示拆分：高度观察；浮空组；地面组；切换；复位。
- 需要确认的信息：当前攻击命中层、Levitation 获取方式、切换时机。
- 参考来源：[Final Fantasy XIV Wiki O2S](https://ffxiv.consolegameswiki.com/wiki/Deltascape_V2.0_%28Savage%29)
- 置信度：`high`

## O3S Spellblade Panels And Queens Waltz

- 副本：Omega Savage / O3S Halicarnassus
- 阶段：Halicarnassus
- 常见别名：O3S、Halicarnassus、Spellblade、Queen's Waltz、地板、书
- 机制类别：`tile-platform`、`clone-memory`、`sequence`
- 原理：场地面板与 Spellblade 属性决定攻击变化，Queen's Waltz 会按当前地板主题复现对应机制。
- 默认解法：先画地板主题，再画 Spellblade 属性与 Waltz 对应安全区。
- 常见优化：为不同主题使用稳定图例；观察与执行分图。
- 常见失误：只记 Waltz 名称，不记当前地板主题；图面缺少 arena state。
- 可类比机制：地板主题、旧机制复现、属性读招。
- 可迁移部分：arena-state snapshot、属性标签、复现机制。
- 不应照搬：O3S 的面板主题、书本与青蛙变化只属于 Halicarnassus。
- XivPlan 图示拆分：地板主题；Spellblade；Waltz；复位。
- 需要确认的信息：当前主题、属性、队伍分组、追加 AoE。
- 参考来源：[Final Fantasy XIV Wiki O3S](https://ffxiv.consolegameswiki.com/wiki/Deltascape_V3.0_%28Savage%29)
- 置信度：`high`

## O5S Phantom Train Platforms And Ghosts

- 副本：Omega Savage / O5S Phantom Train
- 阶段：Phantom Train
- 常见别名：O5S、Phantom Train、幽灵列车、车厢、Ghost
- 机制类别：`tile-platform`、`adds-priority`、`sequence`
- 原理：列车平台、车厢幽灵和转场小怪改变可站立区域与转火目标。
- 默认解法：每一步画清车厢、平台边界、幽灵路径与转火目标。
- 常见优化：将车厢状态作为背景图层，人物路线单独用箭头表达。
- 常见失误：只画人物站位，不画平台边界；漏掉转火或进入车厢的职责。
- 可类比机制：移动平台、车厢、幽灵穿越、adds priority。
- 可迁移部分：arena-state snapshot、平台边界、转火标签。
- 不应照搬：O5S 列车长度、幽灵路径与车厢机制属于 Phantom Train。
- XivPlan 图示拆分：平台；幽灵；车厢；转火；回收。
- 需要确认的信息：车厢职责、幽灵方向、转火顺序、场地边界。
- 参考来源：[Final Fantasy XIV Wiki O5S](https://ffxiv.consolegameswiki.com/wiki/Sigmascape_V1.0_%28Savage%29)
- 置信度：`high`

## O6S Paintings And Demonic Howl

- 副本：Omega Savage / O6S Chadarnook
- 阶段：Chadarnook
- 常见别名：O6S、Chadarnook、画、Paintings、Demonic Howl
- 机制类别：`clone-memory`、`tile-platform`、`sequence`
- 原理：场地画作与 Boss 附身对象决定下一组攻击，玩家要在画作生效前进入正确区域。
- 默认解法：先画画作位置与生效范围，再画 Boss 附身结果和安全区。
- 常见优化：为每幅画使用固定图标；让观察步骤单独成图。
- 常见失误：画作选对但进入时机错误；场地对象未显示导致攻略难读。
- 可类比机制：素材激活、场地机关、观察后进入安全区。
- 可迁移部分：特殊素材图标、观察与执行、arena state。
- 不应照搬：O6S 画作种类和附身顺序只属于 Chadarnook。
- XivPlan 图示拆分：画作图例；附身观察；进入画作；判定；复位。
- 需要确认的信息：画作种类、触发时间、队伍集合点。
- 参考来源：[Final Fantasy XIV Wiki O6S](https://ffxiv.consolegameswiki.com/wiki/Sigmascape_V2.0_%28Savage%29)
- 置信度：`high`

## O7S Programs And Virus

- 副本：Omega Savage / O7S Guardian
- 阶段：Guardian
- 常见别名：O7S、Guardian、Program、Virus、病毒、面板
- 机制类别：`clone-memory`、`debuff`、`adds-priority`
- 原理：Guardian 加载多个程序与病毒状态，玩家需要根据程序类型处理场地 AoE、转火和隔离。
- 默认解法：先标加载的 Program，再画对应安全区与转火目标；Virus 持有者单独标隔离或传递。
- 常见优化：用程序图标和文字双重标识；不同 program 保持统一配色。
- 常见失误：程序识别正确但转火目标遗漏；Virus 玩家与队伍接触。
- 可类比机制：模块加载、旧机制 remix、病毒隔离、程序化读招。
- 可迁移部分：Program 字典、特殊素材、隔离、adds priority。
- 不应照搬：O7S 的具体程序序列和病毒效果只属于 Guardian。
- XivPlan 图示拆分：Program 观察；场地处理；Virus；转火；复位。
- 需要确认的信息：Program 类型、病毒规则、转火目标、场地安全区。
- 参考来源：[Final Fantasy XIV Wiki O7S](https://ffxiv.consolegameswiki.com/wiki/Sigmascape_V3.0_%28Savage%29)
- 置信度：`high`

## O9S Elemental Orbs And Damning Edict

- 副本：Omega Savage / O9S Chaos
- 阶段：Chaos
- 常见别名：O9S、Chaos、元素球、Earthquake、Tsunami、Damning Edict
- 机制类别：`rotation`、`line-shape`、`sequence`
- 原理：Chaos 以不同元素进入攻击循环，玩家根据属性处理击退、靠近、远离或直线安全区。
- 默认解法：建立元素字典，再按当前 orb 属性画对应预站与落点。
- 常见优化：把四种元素做成可复用小卡；主图只标当前属性。
- 常见失误：元素读对但套错移动模板；直线 Edict 朝向读反。
- 可类比机制：元素轮盘、属性决定安全区、in/out 与击退组合。
- 可迁移部分：属性字典、模板复用、预站点。
- 不应照搬：O9S 元素顺序和 Edict 方向只属于 Chaos。
- XivPlan 图示拆分：元素图例；当前属性；预站；判定；复位。
- 需要确认的信息：元素、顺序、Boss 朝向、防击退规则。
- 参考来源：[Final Fantasy XIV Wiki O9S](https://ffxiv.consolegameswiki.com/wiki/Alphascape_V1.0_%28Savage%29)
- 置信度：`high`

## O10S Spins And Akh Morn

- 副本：Omega Savage / O10S Midgardsormr
- 阶段：Midgardsormr
- 常见别名：O10S、Midgardsormr、旋转、spin、Akh Morn、尾巴
- 机制类别：`clone-memory`、`stack`、`line-shape`
- 原理：龙的旋转动画决定尾扫、吐息或俯冲方向，同时队伍要处理 Akh Morn 连续分摊。
- 默认解法：先画 Boss 动画与攻击方向，再画队伍集合点和移动箭头。
- 常见优化：将动画识别转成短 callout；近战用目标圈边缘微调。
- 常见失误：只看 Boss 朝向不看旋转动画；分摊后回位过早。
- 可类比机制：动画读招、龙类吐息、连续分摊。
- 可迁移部分：动画字典、攻击方向、stack reset。
- 不应照搬：O10S 的动画与攻击映射只属于 Midgardsormr。
- XivPlan 图示拆分：动画观察；攻击范围；Akh Morn；复位。
- 需要确认的信息：动画、朝向、分摊次数、目标圈路线。
- 参考来源：[Final Fantasy XIV Wiki O10S](https://ffxiv.consolegameswiki.com/wiki/Alphascape_V2.0_%28Savage%29)
- 置信度：`high`

## O11S Starboard Larboard And Pantokrator

- 副本：Omega Savage / O11S Omega
- 阶段：Omega
- 常见别名：O11S、Starboard、Larboard、左右舷、Pantokrator、全能之主
- 机制类别：`cleave`、`bait`、`rotation`、`sequence`
- 原理：左右舷要求根据 Boss 面向判断安全侧；Pantokrator 则把连续 bait、导弹与旋转移动组合在一起。
- 默认解法：左右舷先明确 Boss-relative 左右；Pantokrator 固定起点、旋转方向和每拍移动。
- 常见优化：将左右舷 callout 转换为安全边；全团统一旋转节奏。
- 常见失误：用玩家视角而不是 Boss 视角判断左右；转圈速度不一致。
- 可类比机制：Boss-relative 左右刀、TOP Pantokrator、旋转 bait。
- 可迁移部分：relative facing、统一旋转、节拍移动。
- 不应照搬：O11S Pantokrator 的导弹与圈序不能直接套用 TOP。
- XivPlan 图示拆分：左右舷；Pantokrator 起点；逐拍旋转；复位。
- 需要确认的信息：Boss 面向、旋转方向、bait 次数、远近分层。
- 参考来源：[Final Fantasy XIV Wiki O11S](https://ffxiv.consolegameswiki.com/wiki/Alphascape_V3.0_%28Savage%29)
- 置信度：`high`
