Example Lectures
================

Complete example lectures demonstrating Scholium's features.

Computer Science: Binary Search Trees
--------------------------------------

.. code-block:: markdown

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
    
    # Implementation
    
    ```python
    def search(root, target):
        if not root or root.val == target:
            return root
        if target < root.val:
            return search(root.left, target)
        return search(root.right, target)
    ```
    
    ::: notes
    [PRE 2s] [MIN 15s]
    
    Here's the search implementation.
    Base cases: empty tree or found target.
    If target is less, recurse left.
    Otherwise recurse right.
    :::

Mathematics: Calculus
---------------------

.. code-block:: markdown

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
    
    # Example
    
    Evaluate: $$\int_0^2 x^2\,dx$$
    
    >- Find antiderivative: $F(x) = \frac{x^3}{3}$
    >- Apply FTC: $F(2) - F(0)$
    >- Calculate: $\frac{8}{3} - 0 = \frac{8}{3}$
    
    ::: notes
    Let's work through an example.
    
    First, find the antiderivative using power rule.
    
    Now apply the Fundamental Theorem at endpoints.
    
    Eight thirds minus zero gives us eight thirds.
    :::

Language Learning: Spanish
--------------------------

.. code-block:: markdown

    ---
    title: "Past Tense in Spanish"
    author: "Spanish 202"
    title_notes: |
      Bienvenidos. Today: preterite versus imperfect.
    ---
    
    # Two Past Tenses
    
    **Preterite**: Completed actions
    - Fui al cine ayer
    
    **Imperfect**: Ongoing or habitual
    - Iba al cine cada semana
    
    ::: notes
    Spanish has two past tenses.
    The preterite describes completed actions.
    The imperfect describes ongoing or habitual actions.
    This distinction is challenging for English speakers.
    :::
    
    # When to Use Preterite
    
    >- Specific completed action
    >- Clear beginning and end
    >- Sequence of events
    >- Sudden realization
    
    ::: notes
    Use preterite for specific completed actions.
    
    When there's a clear beginning and end.
    
    When describing a sequence of events.
    
    When describing sudden realizations.
    :::

Physics: Newton's Laws
----------------------

.. code-block:: markdown

    ---
    title: "Newton's Second Law"
    author: "Physics 101"
    title_notes: |
      Today's topic: Newton's Second Law of Motion.
    ---
    
    # The Law
    
    $$\vec{F} = m\vec{a}$$
    
    Force equals mass times acceleration.
    
    **Units:**
    - Force: Newtons (N)
    - Mass: kilograms (kg)
    - Acceleration: m/s²
    
    ::: notes
    [PRE 2s]
    
    Newton's Second Law is foundational.
    Force equals mass times acceleration.
    This describes how objects move when forces act on them.
    :::
    
    # Example
    
    A 10 kg box.
    Push with 50 N.
    What's the acceleration?
    
    $$a = \frac{F}{m} = \frac{50}{10} = 5 \text{ m/s}^2$$
    
    ::: notes
    [MIN 10s]
    
    Let's solve a practical example.
    Ten kilogram box, fifty Newton force.
    Acceleration equals force divided by mass.
    Fifty divided by ten gives five meters per second squared.
    :::

See Also
--------

* :doc:`user/markdown-format` - Syntax reference
* :doc:`user/narration-format` - Narration guide
* :doc:`user/incremental-lists` - Bullet reveals
