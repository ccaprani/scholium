# Example Lectures

Complete example lectures demonstrating Scholium's features.

## Computer Science: Binary Search Trees

```markdown
---
title: "Binary Search Trees"
author: "CS 201 - Data Structures"
date: "Week 5"
title_notes: |
  [DUR 3s]
  Welcome to week five. Today: binary search trees.
---

# What is a BST?

A binary tree with ordering property:
- Left subtree < parent
- Right subtree > parent
- Both subtrees are BSTs

::: notes
:: Reference: CLRS Chapter 12

[PRE 1s]

A binary search tree maintains a specific ordering.
Every node's left children are smaller.
Every node's right children are larger.
This property holds recursively for all subtrees.
:::

# Operations

>- Search: O(log n) average
>- Insert: O(log n) average
>- Delete: O(log n) average

::: notes
BSTs support efficient operations.

Search is logarithmic because we eliminate half at each step.

Insertion is also logarithmic as we navigate to correct position.

Deletion is most complex but still logarithmic on average.
:::
```

## Mathematics: Calculus

```markdown
---
title: "The Fundamental Theorem"
author: "Calculus I"
title_notes: |
  Today's topic is the Fundamental Theorem of Calculus.
---

# The Theorem

If $f$ is continuous on $[a,b]$, then:

$$\int_a^b f'(x)\,dx = f(b) - f(a)$$

::: notes
[PRE 3s] [MIN 12s]

The Fundamental Theorem connects differentiation and integration.
Integration and differentiation are inverse operations.
This changed mathematics forever.
Take time to understand both parts.
:::
```

## See Also

- {doc}`user/markdown-format` - Syntax reference
- {doc}`user/narration-format` - Narration guide
- {doc}`user/incremental-lists` - Bullet reveals
