# TEA Mechanic Cards

## Scope

Use these cards for The Epic of Alexander (Ultimate), commonly abbreviated `TEA`. They capture transferable mechanic structures, not one region's exact waymarks or party-finder macro.

## Limit Cut

- 副本：TEA / The Epic of Alexander (Ultimate)
- 阶段：Brute Justice and Cruise Chaser transition
- 常见别名：Limit Cut、限制切、麻将数字、数字点名
- 机制类别：`debuff`、`sequence`、`bait`
- 原理：玩家获得有顺序的数字标记，并按固定节拍依次处理冲锋或范围判定；未轮到的玩家需要在等待区保持队形。
- 默认解法：先按数字分组，再把每组的等待位、处理位和回收位固定下来；用节拍而不是临场追着标记移动。
- 常见优化：让同一侧的玩家共享等待路线，减少横穿；把下一组预站与上一组回收分开。
- 常见失误：只写数字顺序，没有写等待位和何时离开处理位。
- 可类比机制：TEA `Wormhole Formation`、TOP 有序世界状态、任何数字依次冲锋或踩塔机制。
- 可迁移部分：数字分桶、固定节拍、等待区与处理区分离。
- 不应照搬：具体左右分配、每个数字的落点和 waymark，需要按当前机制的冲锋方向与场地重新确认。
- XivPlan 图示拆分：数字分组总览；前半组处理；后半组处理；全员复位。
- 需要确认的信息：数字获得方式、每轮判定对象、是否有冲锋、塔、分摊或地板限制。
- 参考来源：[Icy Veins TEA guide index](https://www.icy-veins.com/ffxiv/the-epic-of-alexander-ultimate-guides-introduction)
- 置信度：`high`

## Judgment Nisi And Gavel

- 副本：TEA / The Epic of Alexander (Ultimate)
- 阶段：Brute Justice and Cruise Chaser
- 常见别名：Nisi、判决、Gavel、传毒
- 机制类别：`debuff`、`pass`、`sequence`
- 原理：多种 Nisi 状态需要在指定玩家之间通过接触传递，并在后续 Gavel 条件检查前维持正确持有人；不同 Nisi 不应错误相撞。
- 默认解法：先定义每种 Nisi 的传递链，再把每次交接放入时间轴；交接点应与 Boss、分摊和其他机制路径错开。
- 常见优化：使用固定 relay 点和固定传递顺序，避免自由追人；把交接动作画成单独步骤。
- 常见失误：只标最终持有人，没有画传递路径；两个不同 Nisi 持有人交叉。
- 可类比机制：Hello World-like 传递、传火、传毒、接触交换机制。
- 可迁移部分：状态家族不可混合、固定 relay 顺序、交接时间轴。
- 不应照搬：TEA 的具体 Nisi 种类、Gavel 检查条件和交接人数不能直接套用到新机制。
- XivPlan 图示拆分：初始 Nisi；第一次交接；第二次交接；Gavel 前最终检查。
- 需要确认的信息：状态种类、合法接收者、接触规则、持续时间、最终检查条件。
- 参考来源：[Icy Veins TEA Brute Justice and Cruise Chaser guide](https://www.icy-veins.com/ffxiv/the-epic-of-alexander-ultimate-guides-brute-justice-and-cruise-chaser)
- 置信度：`high`

## Wormhole Formation

- 副本：TEA / The Epic of Alexander (Ultimate)
- 阶段：Alexander Prime
- 常见别名：Wormhole、虫洞、虫洞 Formation
- 机制类别：`sequence`、`debuff`、`bait`、`tower`
- 原理：数字顺序与多种场地判定叠加，玩家要按编号处理冲锋、跳跃或引导，同时避开场地 AoE 并完成 puddle soak。
- 默认解法：数字先分左右和前后等待位，再为每组画出唯一处理窗口；把中场穿越和 puddle 责任拆开。
- 常见优化：给每组预留独立等待位；让箭头只展示当前节拍，避免一张图塞入所有数字路径。
- 常见失误：数字处理顺序正确，但等待玩家挡住 Chakram 或踩错 puddle。
- 可类比机制：Limit Cut-like 大运动会、数字踩塔、顺序诱导地火。
- 可迁移部分：按数字分桶、节拍处理、等待玩家静止、每 beat 单独成图。
- 不应照搬：TEA 的具体数字站位、Chakram 线、Super Jump 和 puddle 布局只属于 Wormhole。
- XivPlan 图示拆分：数字观察；初始分侧；每两组一个处理图；最终回中。
- 需要确认的信息：数字数量、每轮判定、场地危险线、塔或 puddle 的人数要求。
- 参考来源：[Icy Veins TEA Alexander Prime guide](https://www.icy-veins.com/ffxiv/the-epic-of-alexander-ultimate-guides-alexander-prime)
- 置信度：`high`

## Fate Calibration Alpha And Beta

- 副本：TEA / The Epic of Alexander (Ultimate)
- 阶段：Perfect Alexander
- 常见别名：Fate Calibration、命运校准、未来观测、Alpha、Beta
- 机制类别：`clone-memory`、`debuff`、`sequence`
- 原理：玩家先观察自己的未来分身会承受或执行什么，再在正式判定时复现正确动作；观察阶段与执行阶段分离。
- 默认解法：先标自己的 clone，再记录个人职责和全团动作；把 Motion/Stillness、个人 Debuff、安全区和最终站位按顺序拆成检查表。
- 常见优化：指定一名可靠玩家报全团观察项，同时每人只记自己的职责；图上用编号明确观察顺序。
- 常见失误：把 clone 位置当成最终位置；忘记全团动作与个人 debuff 的先后关系。
- 可类比机制：分身延迟、镜像复制、FRU 时间系机制、任何先看录像再执行的机制。
- 可迁移部分：观察和执行分图、个人职责卡、全团 callout 与个人记忆分离。
- 不应照搬：TEA 的 clone 标识、Enigma Codex 前置和 Alpha/Beta 具体判定不能套到一般镜像机制。
- XivPlan 图示拆分：观察 clone；记录个人任务；正式第一次判定；正式第二次判定；复位。
- 需要确认的信息：观察窗口、clone 与玩家映射、全团动作顺序、个人状态数量。
- 参考来源：[Icy Veins TEA Perfect Alexander guide](https://www.icy-veins.com/ffxiv/the-epic-of-alexander-ultimate-guides-perfect-alexander)
- 置信度：`high`
