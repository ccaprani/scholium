# Narration Format

The `:::notes:::` block is where you write what will be spoken during each slide. This guide explains the complete narration syntax.

## Basic Syntax

### Notes Block Structure

Every slide can have an associated narration block:

```markdown
# Slide Title

Slide content here

::: notes
This is what gets narrated.
Can be multiple lines.
:::
```

**Important**: Must be lowercase `:::notes:::` not `:::NOTES:::`.

### Multi-Paragraph Narration

Use blank lines to separate paragraphs:

```markdown
::: notes
First paragraph of narration.
Continues on multiple lines.

Second paragraph after blank line.

Third paragraph.
:::
```

All paragraphs play continuously unless you have incremental reveals (see [Incremental Lists](incremental-lists.md)).

## Metadata Lines

Lines starting with `::` are metadata - they are **not narrated**:

```markdown
::: notes
:: Reference: Chapter 3, pages 45-52
:: Author: Remember to emphasize this clearly
:: Note: This is a key concept

This text WILL be narrated.
The lines above will NOT.
:::
```

**Use metadata for**:
- Source references
- Author notes to yourself
- Reminders about presentation
- Documentation that shouldn't be spoken

:::{important}
Timing directives should **not** be in metadata lines - put them directly in the narration text.
:::

## Timing Directives

Control slide display duration and pauses by adding directives at the **beginning** of notes:

```markdown
::: notes
[PRE 2s] [POST 3s] [MIN 10s]

Your narration here.
:::
```

### Slide-Level Directives

These affect the entire slide:

**`[PRE Xs]`**
: Pause X seconds **before** narration begins.

Example:
```markdown
::: notes
[PRE 2s]

After a 2-second pause, narration begins.
:::
```

**`[POST Xs]`**
: Pause X seconds **after** narration ends.

Example:
```markdown
::: notes
[POST 3s]

Narration plays, then 3-second pause.
:::
```

**`[MIN Xs]`**
: Keep slide visible for **minimum** X seconds.

Example:
```markdown
::: notes
[MIN 15s]

Even if narration is shorter, slide stays for 15s.
:::
```

**`[DUR Xs]`**
: Fixed duration - slide shows for **exactly** X seconds (usually silent).

Example:
```markdown
::: notes
[DUR 5s]
:::
```
Shows slide silently for 5 seconds.

### Combining Directives

Multiple directives work together:

```markdown
::: notes
[PRE 2s] [POST 3s] [MIN 15s]

2s pause → narration → 3s pause, minimum 15s total.
:::
```

**Timeline**:
1. Slide appears
2. 2-second pause (PRE)
3. Narration plays
4. 3-second pause (POST)
5. Total time at least 15 seconds (MIN)

### Mid-Narration Pauses

**`[PAUSE Xs]`**
: Pause **during** narration for emphasis.

Example:
```markdown
::: notes
And the result is.
[PAUSE 2s]
Ninety-nine point nine percent uptime!
:::
```

Use sparingly for dramatic effect.

### Directive Syntax Rules

**Correct**:
```markdown
[PRE 2s]      # Space between directive and value
[POST 3.5s]   # Decimals allowed
[MIN 10s]     # Lowercase 's' for seconds
[PAUSE 500ms] # Milliseconds also supported
```

**Incorrect**:
```markdown
[PRE:2s]      # No colon
[PRE=2s]      # No equals sign
[PRE 2]       # Missing unit (though will assume seconds)
[ PRE 2s]     # No space after opening bracket
```

## Title Slide Narration

Add narration to the title slide via YAML frontmatter:

```yaml
---
title: "Introduction to Algorithms"
author: "CS 201"
title_notes: |
  [DUR 3s]
  
  Welcome to Introduction to Algorithms.
  Today we'll learn about Big O notation.
---
```

**Without** `title_notes`: Title slide is silent

**With** `title_notes`: Title slide has narration

## Common Patterns

### Simple Slide

```markdown
# Introduction

Welcome to the course.

::: notes
Today we're going to learn about data structures.
We'll start with linked lists and work our way up.
:::
```

### Text-Heavy Slide

Give viewers time to read before speaking:

```markdown
# Complex Definition

**Algorithm**: A finite sequence of well-defined instructions...
[Long text on slide]

::: notes
[PRE 3s]

Now let's break down this definition.
An algorithm must have a finite number of steps.
:::
```

### Key Concept

Pause after for reflection:

```markdown
# The Fundamental Theorem

$$E = mc^2$$

::: notes
[POST 4s]

This is Einstein's famous equation.
It fundamentally changed physics.
:::
```

### Complex Diagram

Ensure adequate viewing time:

```markdown
# System Architecture

![Complex architecture diagram](images/arch.png)

::: notes
[PRE 2s] [MIN 15s]

Take a moment to examine this architecture.
Notice the three-tier structure.
:::
```

### Silent Transition

Section breaks or title slides:

```markdown
# Section 2: Advanced Topics

::: notes
[DUR 3s]
:::
```

### Dramatic Reveal

Mid-narration pause for effect:

```markdown
# The Winner

And the winner is...

::: notes
And the winner is.
[PAUSE 3s]
Team Blue!
Congratulations!
:::
```

## Best Practices

### DO ✓

- Write how you speak naturally
- Use complete sentences
- Explain what's on the slide, don't just read it
- Add context and examples
- Use timing directives purposefully

### DON'T ✗

- Read bullet points word-for-word
- Write in bullet form in notes
- Leave complex slides without adequate time
- Overuse timing directives
- Put narration outside `:::notes:::` blocks

## Troubleshooting

### Narration Not Playing

**Check**:
- Lowercase `:::notes:::` (not `:::NOTES:::`)
- Three colons on each side
- Notes block has actual content
- Notes block is inside slide (after heading)

### Timing Not Working

**Check**:
- Directives at **beginning** of notes
- Correct syntax: `[PRE 2s]` not `[PRE:2s]`
- Unit specified: `[PRE 2s]` not `[PRE 2]`
- Not in metadata lines (no `::` prefix)

### Unexpected Pauses

**Check**:
- Blank lines in notes (separate paragraphs for incremental reveals)
- Accidental `[PAUSE]` directives
- `[PRE]` or `[POST]` too long

## Examples

### Complete Slide Example

```markdown
# Binary Search Trees

A tree structure where:
- Left subtree < parent
- Right subtree > parent

::: notes
:: Reference: CLRS Chapter 12
:: Author: Emphasize the ordering property

[PRE 1s] [MIN 12s]

A binary search tree maintains a specific ordering.
All left children are less than the parent node.
All right children are greater than the parent.
This property enables efficient searching.
:::
```

See [Examples](../examples.md) for complete lecture examples.

## Related Topics

- [Markdown Format](markdown-format.md) - Overall slide structure
- [Incremental Lists](incremental-lists.md) - Bullet-by-bullet reveals
- [Timing Control](timing-control.md) - Detailed timing guide
