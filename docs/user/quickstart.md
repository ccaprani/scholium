# Quick Start

Get started with Scholium in under 10 minutes.

## Installation

Install Scholium with Piper TTS (recommended for beginners):

```bash
pip install scholium[piper]
```

For other TTS providers, see [TTS Providers](tts-providers.md).

## Your First Video

### Step 1: Create Markdown File

Create `lecture.md`:

````markdown
---
title: "Python Variables"
title_notes: |
  [DUR 3s]
  Welcome to Python Variables.
---

# What are Variables?

Variables store data values.

```python
name = "Alice"
age = 25
```

::: notes
Variables are containers for storing information.
In Python, you create a variable by assigning a value.
:::

# Variable Types

>- Strings (text)
>- Integers (numbers)
>- Floats (decimals)
>- Booleans (True/False)

::: notes
Python has several basic data types.

Strings store text in quotes.

Integers store whole numbers.

Floats store decimal numbers.
:::
````

### Step 2: Generate Video

```bash
scholium generate lecture.md output.mp4
```

### Step 3: Watch

Open `output.mp4` in your video player!

## Key Concepts

### Slides and Notes

Each slide has:

1. **Heading** (`#`) — Creates a new slide
2. **Content** — What appears on the slide
3. **Notes block** (`:::notes:::`) — What gets narrated

### Incremental Bullets

Use `>-` for bullet-by-bullet reveals:

```markdown
>- First point
>- Second point

::: notes
Narration for first.

Narration for second.
:::
```

### Timing Control

Add timing directives:

```markdown
::: notes
[PRE 2s] [POST 3s]

Narration with 2s pre-pause and 3s post-pause.
:::
```

See [Timing Control](timing-control.md) for details.

## Next Steps

- [Markdown Format](markdown-format.md) — Complete syntax guide
- [Narration Format](narration-format.md) — Narration details
- [Incremental Lists](incremental-lists.md) — Bullet-by-bullet reveals
- [Examples](../examples.md) — Full lecture examples
