Timing Control
==============

Advanced control over slide duration and narration timing.

Overview
--------

Timing directives control exactly when narration plays and how long slides display.

Available Directives
--------------------

``[PRE Xs]``
   Pause X seconds **before** narration.

``[POST Xs]``
   Pause X seconds **after** narration.

``[MIN Xs]``
   Keep slide visible **minimum** X seconds.

``[DUR Xs]``
   Fixed duration (usually for silent slides).

``[PAUSE Xs]``
   Pause **during** narration.

Syntax
------

Place at beginning of notes block::

    ::: notes
    [PRE 2s] [POST 3s] [MIN 10s]
    
    Your narration here.
    :::

Common Patterns
---------------

Text-Heavy Slide
~~~~~~~~~~~~~~~~

::

    ::: notes
    [PRE 3s]
    
    Give viewers time to read before speaking.
    :::

Key Concept
~~~~~~~~~~~

::

    ::: notes
    [POST 4s]
    
    Important concept.
    Pause after for reflection.
    :::

Complex Diagram
~~~~~~~~~~~~~~~

::

    ::: notes
    [PRE 2s] [MIN 15s]
    
    Allow examination time.
    :::

Silent Transition
~~~~~~~~~~~~~~~~~

::

    ::: notes
    [DUR 3s]
    :::

See :doc:`narration-format` for complete timing syntax.
