"""
make_gif.py — Generate an animated terminal GIF showing `scholium generate`.

Run from the project root:
    python docs/demo/make_gif.py

Output: docs/demo/demo.gif
Requires: Pillow  (pip install pillow)
"""

from PIL import Image, ImageDraw, ImageFont
import os

# ── Palette ──────────────────────────────────────────────────────────────────
BG     = (20,  24,  30)    # #14181e  dark background
FG     = (220, 220, 220)   # default text
PROMPT = ( 80, 210, 120)   # green prompt / $ sign
CMD    = (200, 220, 255)   # command text
TEAL   = ( 69, 157, 185)   # #459DB9  brand teal
GREEN  = (100, 220, 100)   # ✓ success lines
DIM    = (120, 120, 140)   # dimmed / secondary
TITLE  = (255, 255, 255)   # bright white for section headers

# ── Layout ───────────────────────────────────────────────────────────────────
W, H    = 860, 460
PAD     = 20
FONT_SZ = 15
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

font  = ImageFont.truetype(FONT_PATH, FONT_SZ)
LINE_H = FONT_SZ + 5

BAR_H  = 28   # top title-bar height

def blank():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    # top title bar
    draw.rectangle([0, 0, W, BAR_H], fill=(35, 40, 50))
    draw.text((PAD, 7), "  terminal — scholium demo", font=font, fill=DIM)
    return img, draw

def txt(draw, x, y, s, color=FG):
    draw.text((x, y), s, font=font, fill=color)
    return y + LINE_H

# ── Script ───────────────────────────────────────────────────────────────────
# Each entry: (text, colour, hold_ms)
SCRIPT = [
    # show the lecture source
    ("$ cat docs/demo/lecture.md",                            PROMPT,  700),
    ("",                                                       FG,       50),
    ("---",                                                    DIM,      50),
    ('title: "Scholium"',                                      DIM,      50),
    ("title_notes: |",                                         DIM,      50),
    ("  [PRE 1s] Scholium converts markdown slides into ...",  DIM,      50),
    ("---",                                                    DIM,      50),
    ("",                                                       FG,       50),
    ("# One Command",                                          TITLE,    50),
    ("",                                                       FG,       50),
    (">- Parses slides and narration from your markdown",      FG,       50),
    (">- Synthesises speech with your chosen TTS voice",       FG,       50),
    (">- Combines slides and audio into a finished video",     FG,       50),
    ("",                                                       FG,       50),
    ("::: notes",                                              DIM,      50),
    ("Narration for bullet 1.",                                DIM,      50),
    ("",                                                       FG,       50),
    ("Narration for bullet 2.",                                DIM,      50),
    ("",                                                       FG,       50),
    ("Narration for bullet 3.",                                DIM,     700),
    (":::",                                                    DIM,      50),
    ("",                                                       FG,       50),
    # generate command
    ("$ scholium generate docs/demo/lecture.md \\",           PROMPT,  600),
    ("      docs/demo/demo.mp4 --provider piper",              CMD,     700),
    ("",                                                       FG,       50),
    ("🔄  Slides:    docs/demo/lecture.md",                    FG,      150),
    ("🎬  Output:    docs/demo/demo.mp4",                      FG,      150),
    ("🎤  Voice:     en_US-lessac-medium",                     FG,      150),
    ("📊  Provider:  piper",                                   FG,      400),
    ("",                                                       FG,       50),
    ("🔨  Processing slides...",                               TEAL,    500),
    ("    ✔  Generated 6 slides",                             GREEN,   250),
    ("",                                                       FG,       50),
    ("📖  Parsing narration...",                               TEAL,    350),
    ("    ✔  Parsed 6 slides with narration",                 GREEN,   250),
    ("",                                                       FG,       50),
    ("🎤  Generating audio...",                                TEAL,    300),
    ("    Generating:  13% |█▎        | 1/8",                 DIM,     350),
    ("    Generating:  25% |██▌       | 2/8",                 DIM,     350),
    ("    Generating:  38% |███▊      | 3/8",                 DIM,     350),
    ("    Generating:  50% |█████     | 4/8",                 DIM,     350),
    ("    Generating:  63% |██████▎   | 5/8",                 DIM,     350),
    ("    Generating:  75% |███████▌  | 6/8",                 DIM,     350),
    ("    Generating:  88% |████████▊ | 7/8",                 DIM,     350),
    ("    Generating: 100% |██████████| 8/8",                 DIM,     300),
    ("    ✔  Generated 8 audio segments",                     GREEN,   350),
    ("",                                                       FG,       50),
    ("🎬  Generating video...",                                TEAL,    600),
    ("    ✔  Video saved to docs/demo/demo.mp4",              GREEN,   300),
    ("",                                                       FG,       50),
    ("✅  Success! — generated in 30 seconds",                 GREEN, 3000),
]

def build_frames(script):
    frames = []
    visible = []
    max_lines = (H - BAR_H - PAD * 2) // LINE_H

    for (s, col, delay) in script:
        visible.append((s, col))
        img, draw = blank()
        start = max(0, len(visible) - max_lines)
        y = BAR_H + PAD
        for (line, lc) in visible[start:]:
            txt(draw, PAD, y, line, lc)
            y += LINE_H
        frames.append((img.copy(), delay))
    return frames

frames = build_frames(SCRIPT)

images    = [f[0] for f in frames]
durations = [f[1] for f in frames]

out = os.path.join(os.path.dirname(__file__), "demo.gif")
images[0].save(
    out,
    save_all=True,
    append_images=images[1:],
    duration=durations,
    loop=0,
    optimize=False,
)

size_kb = os.path.getsize(out) // 1024
print(f"Written: {out}  ({size_kb} KB, {len(frames)} frames)")
