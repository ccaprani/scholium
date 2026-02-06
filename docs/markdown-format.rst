Markdown Format
===============

Complete reference for Scholium's unified markdown format with embedded narration.

Document Structure
------------------

Every Scholium document has this structure::

    ---
    title: "Lecture Title"
    author: "Course Name"
    ---
    
    # First Slide
    
    Content
    
    ::: notes
    Narration
    :::
    
    # Second Slide
    
    More content
    
    ::: notes
    More narration
    :::

YAML Frontmatter
----------------

Required Fields
~~~~~~~~~~~~~~~

::

    ---
    title: "Your Lecture Title"
    ---

Only ``title`` is required.

Optional Fields
~~~~~~~~~~~~~~~

::

    ---
    title: "Introduction to Algorithms"
    author: "CS 201"
    date: "2026-02-06"
    subtitle: "Big O Notation"
    institute: "University Name"
    title_notes: |
      [DUR 3s]
      Welcome to the lecture.
    ---

``title_notes``
   Narration for title slide. Without this, title slide is silent.

Creating Slides
---------------

Level-1 headings create slides::

    # First Slide
    
    # Second Slide
    
    # Third Slide

**Only** ``#`` (level-1) creates slides. Level-2 (``##``) and deeper are content within slides.

Slide Content
-------------

Text
~~~~

::

    # Introduction
    
    Plain text paragraph.
    
    **Bold** and *italic* work.
    
    - Regular bullets
    - Second bullet

Code Blocks
~~~~~~~~~~~

::

    # Python Example
    
    ```python
    def factorial(n):
        if n <= 1:
            return 1
        return n * factorial(n - 1)
    ```

Images
~~~~~~

::

    # Architecture
    
    ![Diagram caption](images/architecture.png)

Math Equations
~~~~~~~~~~~~~~

::

    # Quadratic Formula
    
    $$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$

Inline: ``$E = mc^2$``

Tables
~~~~~~

::

    | Algorithm | Time | Space |
    |-----------|------|-------|
    | Bubble    | O(n²)| O(1)  |

Notes Blocks
------------

Basic Syntax
~~~~~~~~~~~~

::

    ::: notes
    Narration text here.
    Multiple lines allowed.
    :::

Must be lowercase ``:::notes:::``.

See :doc:`narration-format` for complete narration syntax.

Lists
-----

Regular Lists
~~~~~~~~~~~~~

All bullets appear at once::

    - Point A
    - Point B
    - Point C

Incremental Lists
~~~~~~~~~~~~~~~~~

Bullets reveal one at a time::

    >- Point A
    >- Point B
    >- Point C

See :doc:`incremental-lists` for complete guide.

Complete Example
----------------

::

    ---
    title: "Binary Search"
    author: "Algorithms 101"
    title_notes: |
      Today we're learning binary search.
    ---
    
    # What is Binary Search?
    
    An efficient search algorithm for sorted arrays.
    
    Time complexity: **O(log n)**
    
    ::: notes
    [PRE 1s]
    
    Binary search is one of the most important algorithms.
    It works by repeatedly dividing the search space in half.
    :::
    
    # How It Works
    
    >- Start with middle element
    >- If target < middle, search left half
    >- If target > middle, search right half
    >- Repeat until found
    
    ::: notes
    Let's understand the algorithm step by step.
    
    First, we examine the middle element of the array.
    
    If our target is less than the middle, we only need to search the left half.
    
    If greater, we search the right half.
    
    We repeat this process, halving the search space each time.
    :::
    
    # Implementation
    
    ```python
    def binary_search(arr, target):
        left, right = 0, len(arr) - 1
        
        while left <= right:
            mid = (left + right) // 2
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        
        return -1
    ```
    
    ::: notes
    [MIN 20s]
    
    Here's a Python implementation.
    We maintain left and right pointers.
    Each iteration, we calculate the midpoint.
    We compare and adjust our search range accordingly.
    Study this code carefully as it's fundamental.
    :::

Next Topics
-----------

* :doc:`narration-format` - Narration syntax
* :doc:`incremental-lists` - Bullet reveals
* :doc:`timing-control` - Timing directives
