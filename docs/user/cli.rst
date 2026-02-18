Command Line Interface
======================

Main Command
------------

.. code-block:: bash

    scholium generate <slides.md> <output.mp4> [OPTIONS]

Generate an instructional video from markdown slides with embedded narration.

Arguments
~~~~~~~~~

``slides.md``
   Path to markdown file with embedded ``:::notes:::`` blocks.

``output.mp4``
   Path for output video file.

Options
~~~~~~~

``--provider``, ``-p``
   TTS provider to use. Options: ``piper``, ``elevenlabs``, ``coqui``, ``openai``, ``bark``.
   Default: ``piper``

``--voice``, ``-v``
   Voice name or ID. Default from config file.

``--config``, ``-c``
   Path to configuration file. Default: ``config.yaml``

``--verbose``
   Show detailed progress output.

``--keep-temp``
   Keep temporary files for debugging.

``--help``, ``-h``
   Show help message.

Examples
~~~~~~~~

Basic generation::

    scholium generate lecture.md output.mp4

Custom voice::

    scholium generate lecture.md output.mp4 --voice en_US-amy-medium

Different provider::

    scholium generate lecture.md output.mp4 --provider elevenlabs

Verbose with temp files::

    scholium generate lecture.md output.mp4 --verbose --keep-temp

Voice Commands
--------------

List Voices
~~~~~~~~~~~

.. code-block:: bash

    scholium list-voices [OPTIONS]

List all available trained voices.

Options:
  ``--config PATH`` - Configuration file

Example::

    scholium list-voices

Train Voice
~~~~~~~~~~~

.. code-block:: bash

    scholium train-voice --name NAME --provider PROVIDER --sample AUDIO [OPTIONS]

Train a new voice from audio sample (Coqui only).

Required Options:
  ``--name`` - Name for the voice
  ``--provider`` - TTS provider (currently only ``coqui``)
  ``--sample`` - Path to audio sample file

Optional:
  ``--description`` - Description of the voice
  ``--language`` - Language code (default: ``en``)
  ``--config`` - Configuration file

Example::

    scholium train-voice \
      --name my_voice \
      --provider coqui \
      --sample recording.wav \
      --description "My teaching voice"

Regenerate Embeddings
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    scholium regenerate-embeddings --voice NAME

Pre-compute speaker embeddings for faster generation (Coqui only).

Example::

    scholium regenerate-embeddings --voice my_voice

Provider Commands
-----------------

List Providers
~~~~~~~~~~~~~~

.. code-block:: bash

    scholium providers list

Show all available TTS providers and their installation status.

Provider Info
~~~~~~~~~~~~~

.. code-block:: bash

    scholium providers info PROVIDER

Show detailed information about a specific provider.

Arguments:
  ``PROVIDER`` - Provider name (piper, elevenlabs, coqui, openai, bark)

Example::

    scholium providers info piper

Configuration
-------------

Configuration File
~~~~~~~~~~~~~~~~~~

Create ``config.yaml`` in your project directory:

.. code-block:: yaml

    # TTS settings
    tts_provider: "piper"
    voice: "en_US-lessac-medium"
    
    # Provider-specific settings
    piper:
      quality: "medium"
    
    elevenlabs:
      api_key: ""
      model: "eleven_multilingual_v2"
    
    coqui:
      model: "tts_models/multilingual/multi-dataset/xtts_v2"
    
    openai:
      api_key: ""
      model: "tts-1"
    
    bark:
      model: "small"
    
    # Timing defaults
    timing:
      default_pre_delay: 0.0
      default_post_delay: 0.0
      min_slide_duration: 3.0
    
    # Video settings
    resolution: [1920, 1080]
    fps: 30
    
    # Paths
    voices_dir: "~/.local/share/scholium/voices"
    temp_dir: "./temp"
    output_dir: "./output"
    
    # Options
    keep_temp_files: false
    verbose: true

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

API Keys::

    export ELEVENLABS_API_KEY="your_key"
    export OPENAI_API_KEY="your_key"

Exit Codes
----------

:0: Success
:1: General error
:2: Command-line usage error
:3: File not found
:4: Provider not installed
:5: TTS generation failed
:6: Video generation failed
