TTS Providers
=============

Scholium supports five text-to-speech providers.

Provider Comparison
-------------------

=============== ====== ========= ====== ============= ======= ====
Provider        Type   Quality   Speed  Voice Cloning API Key Cost
=============== ====== ========= ====== ============= ======= ====
**Piper**       Local  ⭐⭐⭐⭐    Fast   ❌            ❌      Free
**ElevenLabs**  Cloud  ⭐⭐⭐⭐⭐  Fast   ✅            ✅      Paid
**Coqui**       Local  ⭐⭐⭐⭐    Medium ✅            ❌      Free
**OpenAI**      Cloud  ⭐⭐⭐⭐    Fast   ❌            ✅      Paid
**Bark**        Local  ⭐⭐⭐⭐⭐  Slow   ⚠️            ❌      Free
=============== ====== ========= ====== ============= ======= ====

Piper (Recommended)
-------------------

Installation::

    pip install scholium[piper]

Usage::

    scholium generate slides.md output.mp4 --provider piper

**Pros:** Fast, local, no API key

**Cons:** Limited voices, not as natural as ElevenLabs

ElevenLabs
----------

Installation::

    pip install scholium[elevenlabs]

Setup::

    export ELEVENLABS_API_KEY="your_key"

Usage::

    scholium generate slides.md output.mp4 --provider elevenlabs

**Pros:** Highest quality, fast

**Cons:** Requires API key, costs money

Coqui
-----

Installation::

    pip install scholium[coqui]

Train voice::

    scholium train-voice --name my_voice --provider coqui --sample audio.wav

Usage::

    scholium generate slides.md output.mp4 --provider coqui --voice my_voice

**Pros:** Voice cloning, free, local

**Cons:** Dependency conflicts, slower

OpenAI
------

Installation::

    pip install scholium[openai]

Setup::

    export OPENAI_API_KEY="your_key"

Usage::

    scholium generate slides.md output.mp4 --provider openai

**Pros:** Latest models, affordable

**Cons:** Requires API key

Bark
----

Installation::

    pip install scholium[bark]

Usage::

    scholium generate slides.md output.mp4 --provider bark

**Pros:** Highest quality local

**Cons:** Very slow

Choosing a Provider
-------------------

**For beginners**: Start with Piper

**For production**: Use ElevenLabs

**For your voice**: Use Coqui

**For variety**: Use OpenAI

**For offline**: Use Piper or Bark
