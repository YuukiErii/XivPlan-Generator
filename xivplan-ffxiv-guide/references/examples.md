# Examples

## Example 1: Four Towers

Input:

```markdown
Boss 在场中读条后，东西南北出现四个塔。T/H 负责南北，DPS 负责东西。踩完塔后回中集合。
```

Expected guide behavior:

- Draw Boss at center.
- Draw four `tower` objects at north/east/south/west.
- Assign MT/H1 to north, ST/H2 to south, D2/D4 or ranged side to east, D1/D3 or melee side to west if the user has no fixed split.
- State that assignments are an assumption if the input only says "T/H" and "DPS".
- Include "踩塔后回中复位".

Short callout example:

```markdown
四塔：T/H 南北，DPS 东西，踩完回中。默认 MT/H1 北、ST/H2 南、D2/D4 东、D1/D3 西；队内有固定分组则按队内。
```

## Example 2: Spread And Stack

Input:

```markdown
随机四人点名散开，未点名四人中间分摊。散开位按八方固定站位处理。
```

Expected guide behavior:

- Explain that marked players use their assigned clock positions.
- Explain that unmarked players stack at center.
- Do not accidentally make all eight players spread or all eight stack.
- Add a priority note if the source text does not define how random marked players identify themselves.

## Example 3: Knockback

Input:

```markdown
Boss 场中击退全员，随后北侧出现安全区。可以开防击退，也可以从场中靠南位置被击退到北侧安全区。
```

Expected guide behavior:

- Draw knockback source at center.
- Draw north safe zone and danger elsewhere.
- Provide two methods: anti-knockback or manual pre-positioning.
- State exact landing logic and reset.

## Example 4: Tethers

Input:

```markdown
四名玩家被连线，需要拉到东西南北四个方向。连线不能交叉，拉线后原地等待判定。
```

Expected guide behavior:

- Identify tethered players and endpoints if given; otherwise label assignment as an assumption.
- Draw four line/tether objects and arrows to N/E/S/W.
- Explicitly say "不要提前回中，等判定后复位".
- Check that no routes cross unless the mechanic requires crossing.
