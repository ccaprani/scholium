# Timing Control

Advanced control over slide duration and narration timing.

## Overview

Timing directives are placed inside `:::notes:::` blocks and control exactly when narration plays and how long slides remain visible.

## Available Directives

| Directive | Description |
|-----------|-------------|
| `[PRE Xs]` | Pause X seconds **before** narration begins |
| `[POST Xs]` | Pause X seconds **after** narration ends |
| `[MIN Xs]` | Keep slide visible **at least** X seconds |
| `[DUR Xs]` | Fixed duration — slide shows for **exactly** X seconds |
| `[PAUSE Xs]` | Pause **during** narration (splits into a silent segment) |

## Syntax

Place slide-level directives (`PRE`, `POST`, `MIN`, `DUR`) at the beginning of the notes block:

```markdown
::: notes
[PRE 2s] [POST 3s] [MIN 10s]

Your narration here.
:::
```

`[PAUSE]` can appear anywhere inside the narration text:

```markdown
::: notes
The answer is.
[PAUSE 2s]
Forty-two!
:::
```

Time values support seconds (`2s`, `2.5s`) and milliseconds (`500ms`).

## Common Patterns

### Text-Heavy Slide

Give viewers time to read before speaking:

```markdown
::: notes
[PRE 3s]

Now let's break down this definition.
:::
```

### Key Concept with Reflection Time

```markdown
::: notes
[POST 4s]

This is the fundamental theorem.
It changes everything.
:::
```

### Complex Diagram

Ensure adequate viewing time:

```markdown
::: notes
[PRE 2s] [MIN 15s]

Take a moment to examine this architecture.
Notice the three-tier structure.
:::
```

### Silent Section Slide

```markdown
::: notes
[DUR 3s]
:::
```

### Dramatic Pause

```markdown
::: notes
And the winner is.
[PAUSE 3s]
Team Blue! Congratulations!
:::
```

## Directive Interaction

When multiple directives are combined:

```
Slide appears → [PRE] pause → narration → [POST] pause
```

`[MIN]` ensures the total duration (including all delays and narration) is at least the specified value.

`[DUR]` overrides everything — the slide shows for exactly that duration regardless of audio length.

## See Also

- [Narration Format](narration-format.md) — Complete narration syntax
- [Incremental Lists](incremental-lists.md) — Per-bullet timing
