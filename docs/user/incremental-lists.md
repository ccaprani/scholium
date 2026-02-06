# Incremental Lists (Bullet-by-Bullet Reveals)

Incremental lists reveal bullet points one at a time, with synchronized narration for each bullet. This is one of Scholium's most powerful features for instructional videos.

## Basic Syntax

Use `>-` for incremental bullets (standard Pandoc/Beamer syntax):

```markdown
# Key Concepts

>- First point
>- Second point
>- Third point

::: notes
First paragraph narrates while first bullet shows.

Second paragraph narrates while second bullet appears.

Third paragraph narrates while third bullet appears.
:::
```

**How It Works**:
1. Pandoc generates multiple PDF pages - one per bullet
2. Previous bullets remain visible (cumulative reveal)
3. Blank lines in `:::notes:::` separate narration segments
4. Each narration paragraph plays during its corresponding bullet reveal

## Regular vs Incremental

### Regular Bullets (All at Once)

Using `-` shows all bullets immediately:

```markdown
# Points

- Point A
- Point B
- Point C

::: notes
All three points are visible from the start.
This narration plays while viewing all bullets.
:::
```

**Result**: 1 PDF page, 1 narration segment

### Incremental Bullets (One by One)

Using `>-` reveals bullets progressively:

```markdown
# Points

>- Point A
>- Point B
>- Point C

::: notes
Narration for point A.

Narration for point B.

Narration for point C.
:::
```

**Result**: 3 PDF pages, 3 narration segments
- Page 1: Shows bullet A only
- Page 2: Shows bullets A and B
- Page 3: Shows bullets A, B, and C

## Narration Structure

### Separating Narration

Use **blank lines** to separate narration for each bullet:

```markdown
>- First bullet
>- Second bullet

::: notes
Narration for first bullet.
Can be multiple lines.
But no blank lines within this segment.

Narration for second bullet.
Starts after blank line.
:::
```

:::{important}
Number of blank-line-separated segments must match number of bullets.
:::

### Single-Line Narration

Each segment can be brief:

```markdown
>- Quick point
>- Another quick point

::: notes
First explanation.

Second explanation.
:::
```

### Multi-Line Narration

Segments can be detailed:

```markdown
>- Complex concept

::: notes
This concept requires detailed explanation.
We need to cover several aspects.
The first aspect is the theoretical foundation.
Then we'll discuss practical applications.
:::
```

## Common Patterns

### Step-by-Step Instructions

```markdown
# Installation Steps

>- Install Python 3.11+
>- Install Pandoc and LaTeX
>- Run pip install scholium[piper]
>- Verify with scholium --version

::: notes
First, ensure you have Python 3.11 or higher installed.

Next, install Pandoc and LaTeX for slide generation.

Now install Scholium with your chosen TTS provider.

Finally, verify the installation by checking the version.
:::
```

### Advantages or Features

```markdown
# Benefits of BSTs

>- Logarithmic search time
>- Efficient insertion
>- Efficient deletion
>- Maintains sorted order

::: notes
The first major benefit is logarithmic search time on average.

Second, insertion is also logarithmic as we navigate to the correct position.

Third, deletion is efficient, though slightly more complex.

Finally, BSTs automatically maintain sorted order of elements.
:::
```

### Concept Breakdown

```markdown
# What is Recursion?

>- Function calls itself
>- Has a base case
>- Makes progress toward base case
>- Elegant solutions to complex problems

::: notes
Recursion means a function calls itself during execution.

Critically, it must have a base case to stop recursion.

Each recursive call must make progress toward the base case.

When used correctly, recursion provides elegant solutions to problems like tree traversal.
:::
```

## Nested Lists

### Basic Nesting

Indent sub-items with spaces (Pandoc standard):

```markdown
# Hierarchical Structure

>- Main point A
>    - Sub-point A1
>    - Sub-point A2
>- Main point B

::: notes
The first main point has two sub-components.

Now we move to the second main point.
:::
```

:::{note}
Pandoc treats nested items as part of parent reveal. Both sub-items appear with parent.
:::

### Complex Nesting

Multiple levels:

```markdown
# Data Structure Classification

>- Linear structures
>    - Arrays
>    - Linked lists
>    - Stacks and queues
>- Non-linear structures
>    - Trees
>    - Graphs

::: notes
Linear structures store data in sequence.
This includes arrays, linked lists, stacks, and queues.

Non-linear structures have hierarchical or network relationships.
Trees and graphs are the primary examples.
:::
```

## Mixing Regular and Incremental

You can use both in same slide:

```markdown
# Overview

Background (all at once):
- Context point 1
- Context point 2

Key takeaways (incremental):
>- First key insight
>- Second key insight

::: notes
The background points provide context.
Now let's focus on the key insights.

First, this fundamental insight.

Second, this important implication.
:::
```

## Timing with Incremental Lists

### Per-Bullet Timing

Apply timing to each narration segment:

```markdown
>- Important point 1
>- Important point 2

::: notes
[PRE 1s]
First point requires emphasis.

[POST 2s]
Second point even more critical - let it sink in.
:::
```

:::{note}
Timing directives at start of segment only apply to that segment.
:::

### Slide-Level Timing

Apply timing to entire slide:

```markdown
>- Point 1
>- Point 2

::: notes
[MIN 15s]

Narration for point 1.

Narration for point 2.
:::
```

Total slide time (both bullets) will be at least 15 seconds.

## Validation

Scholium validates incremental lists during generation:

**Correct Match**:
```markdown
>- Bullet 1
>- Bullet 2
>- Bullet 3

::: notes
Segment 1.

Segment 2.

Segment 3.
:::
```
✓ 3 bullets, 3 segments - perfect!

**Mismatch Warning**:
```markdown
>- Bullet 1
>- Bullet 2

::: notes
Only one segment.
:::
```
⚠️ Warning: 2 bullets but only 1 narration segment

**What Happens**:
- If too few segments: Later bullets are silent
- If too many segments: Extra segments ignored
- Always shown in `--verbose` output

## Best Practices

### DO ✓

- Match narration segments to bullet count
- Use blank lines to separate segments clearly
- Keep bullets concise (details in narration)
- Use for step-by-step processes
- Use for lists with distinct explanations

### DON'T ✗

- Don't mix `-` and `>-` for same list
- Don't forget blank lines between segments
- Don't make bullets too long (use narration)
- Don't use for simple lists without explanations
- Don't create too many bullets (3-5 optimal)

## Troubleshooting

### Bullets Appear All at Once

**Problem**: Used `-` instead of `>-`

**Solution**: Change to `>-`:
```markdown
# Wrong
- Bullet

# Correct
>- Bullet
```

### Wrong Number of Pages

**Problem**: Pandoc generating unexpected page count

**Check**:
- Each `>-` creates a new page
- Nested items count as parent's reveal
- Slide content might trigger extra pages

**Solution**: Use `--verbose` to see page count warnings

### Narration Misaligned

**Problem**: Narration doesn't match visible bullets

**Check**:
- Count bullets (each `>-`)
- Count narration segments (separated by blank lines)
- They must match exactly

**Solution**: Add or remove narration segments

### Silent Bullets

**Problem**: Some bullets have no narration

**Cause**: Fewer narration segments than bullets

**Solution**: Add narration segments:
```markdown
>- Bullet 1
>- Bullet 2

::: notes
Narration for bullet 1.

Narration for bullet 2.  ← Add this
:::
```

## Examples

### Computer Science Lecture

```markdown
# Algorithm Properties

>- Correctness - produces right output
>- Efficiency - runs in reasonable time
>- Clarity - easy to understand and verify
>- Robustness - handles edge cases

::: notes
First, correctness is fundamental.
The algorithm must produce the correct output for all valid inputs.

Second, efficiency matters.
An algorithm that takes years to run isn't practical.

Third, clarity is essential for maintenance.
Other developers must be able to understand your algorithm.

Finally, robustness means handling edge cases gracefully.
What happens with empty input or extreme values?
:::
```

### Mathematics Proof

```markdown
# Proof Steps

>- Assume P(k) is true
>- Show P(k) implies P(k+1)
>- P(1) is true (base case)
>- Therefore P(n) true for all n

::: notes
[PRE 1s]
We begin with the inductive hypothesis.
Assume the statement is true for some arbitrary k.

Next, we must prove that P of k implies P of k plus one.
This is the inductive step.

We verify the base case: P of one is true.

By the principle of mathematical induction,
the statement holds for all natural numbers n.
:::
```

## Related Topics

- {doc}`narration-format` - Notes block syntax
- {doc}`markdown-format` - Overall slide structure
- {doc}`timing-control` - Detailed timing directives
- {doc}`/examples` - Complete lecture examples
