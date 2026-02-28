# About Scholium

> *Scholium* (Greek: σχόλιον) — An explanatory note or commentary appended to a text,
> typically to clarify or expand on a point the main text does not fully address.

Scholium is a command-line tool that converts markdown slides with embedded narration into
professional narrated instructional videos. It is designed for educators who want to
produce lecture recordings, flipped-classroom content, and course libraries without
leaving their text editor.

## Project Philosophy

**Simple tool, not a framework.** Scholium does one thing well: converts
markdown + narration into video. It integrates with your existing workflow rather than
replacing it. There is no web UI to learn, no proprietary format to adopt, and no
cloud dependency unless you choose a cloud TTS provider.

**Text-first.** Everything is plain text — markdown slides and YAML configuration — so
your content is:

- **Version controllable** with Git alongside your course materials
- **Searchable and editable** in any text editor
- **Reproducible** across systems and collaborators
- **Easy to maintain** semester after semester

**Pandoc-native.** Scholium uses standard Pandoc/Beamer slide syntax, so the same
source file renders as a PDF presentation with LaTeX/Beamer as well as a narrated video.
You are not locked in.

**Narration as documentation.** The `:::notes:::` block is both the speaker notes in
your slide deck and the narration script for the video. Writing them once produces both
outputs. Metadata lines (`:: like this`) serve as in-file author notes, references, and
TODOs that are never spoken aloud — keeping context close to the content it describes.

## Performance

Generation time scales with the TTS provider and available hardware:

| Hardware | Time per 10-minute lecture |
|---|---|
| NVIDIA GPU | 5–10 minutes |
| Apple Silicon | 10–15 minutes |
| Modern CPU | 30–60 minutes |

First run: models download automatically (~500 MB–1.5 GB) and are cached for future use.

## Name

The word *scholium* (plural: *scholia*) entered English from the Greek σχόλιον, meaning
leisure, study, or commentary. Ancient scholars added scholia as margin notes to
classical texts — the original form of annotated teaching materials. Scholium does the
same for the modern classroom: your narration notes become the commentary that brings
the slides to life.
