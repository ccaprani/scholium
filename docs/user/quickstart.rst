Quick Start
===========

Get started with Scholium in under 10 minutes.

Installation
------------

Install Scholium with Piper TTS (recommended for beginners)::

    pip install scholium[piper]

For other TTS providers, see :doc:`tts-providers`.

Your First Video
----------------

**Step 1: Create Markdown File**

Create ``lecture.md``::

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

**Step 2: Generate Video**

::

    scholium generate lecture.md output.mp4

**Step 3: Watch**

Open ``output.mp4`` in your video player!

Key Concepts
------------

Slides and Notes
~~~~~~~~~~~~~~~~

Each slide has:

1. **Heading** (``#``) - Creates new slide
2. **Content** - What appears on slide
3. **Notes block** (``:::notes:::``) - What gets narrated

Incremental Bullets
~~~~~~~~~~~~~~~~~~~

Use ``>-`` for bullet-by-bullet reveals::

    >- First point
    >- Second point
    
    ::: notes
    Narration for first.
    
    Narration for second.
    :::

Timing Control
~~~~~~~~~~~~~~

Add timing directives::

    ::: notes
    [PRE 2s] [POST 3s]
    
    Narration with 2s pre-pause and 3s post-pause.
    :::

See :doc:`timing-control` for details.

Next Steps
----------

* :doc:`markdown-format` - Complete syntax guide
* :doc:`narration-format` - Narration details
* :doc:`incremental-lists` - Bullet-by-bullet reveals
* :doc:`../examples` - Full lecture examples
