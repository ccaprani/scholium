"""Unit tests for the slide-backend registry and the Slidev translator.

These tests exercise pure-Python logic only — no pandoc, ffmpeg, Node, or
Chromium is required.  The Slidev export step is exercised separately in
``tests/test_integration.py`` if/when a real Slidev install is available.
"""

from __future__ import annotations

import os
import stat
import textwrap
from pathlib import Path

import pytest
from PIL import Image

from click.testing import CliRunner

from scholium.config import Config
from scholium.slides import (
    MarpBackend,
    PandocBackend,
    Probe,
    SlidevBackend,
    VALID_BACKENDS,
    get_available_backends,
    get_backend,
    is_backend_available,
)
from scholium.slide_processor import SlideProcessor


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSlideBackendRegistry:
    """The slide-backend registry mirrors the TTS provider registry."""

    def test_valid_backends(self):
        """All shipping backends are advertised in VALID_BACKENDS."""
        assert "pandoc" in VALID_BACKENDS
        assert "slidev" in VALID_BACKENDS
        assert "marp" in VALID_BACKENDS

    def test_get_available_backends(self):
        """get_available_backends returns the names → classes mapping."""
        available = get_available_backends()
        assert available["pandoc"] is PandocBackend
        assert available["slidev"] is SlidevBackend
        assert available["marp"] is MarpBackend

    def test_is_backend_available(self):
        assert is_backend_available("pandoc") is True
        assert is_backend_available("slidev") is True
        assert is_backend_available("marp") is True
        assert is_backend_available("nope") is False

    def test_get_backend_pandoc(self):
        backend = get_backend("pandoc", resolution=(1024, 768))
        assert isinstance(backend, PandocBackend)
        assert backend.resolution == (1024, 768)
        assert backend.pandoc_template == "beamer"

    def test_get_backend_pandoc_template_override(self):
        backend = get_backend(
            "pandoc",
            resolution=(1920, 1080),
            backend_config={"template": "revealjs"},
        )
        assert backend.pandoc_template == "revealjs"

    def test_get_backend_slidev(self):
        backend = get_backend(
            "slidev",
            resolution=(1920, 1080),
            backend_config={"theme": "seriph"},
        )
        assert isinstance(backend, SlidevBackend)
        assert backend.theme == "seriph"

    def test_get_backend_marp(self):
        backend = get_backend(
            "marp",
            resolution=(1920, 1080),
            backend_config={"theme": "gaia", "paginate": True},
        )
        assert isinstance(backend, MarpBackend)
        assert backend.theme == "gaia"
        assert backend.paginate is True

    def test_get_backend_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown slide backend"):
            get_backend("not-a-thing")

    def test_slide_processor_backward_compat(self):
        """The legacy SlideProcessor name is now a subclass of PandocBackend."""
        sp = SlideProcessor(pandoc_template="beamer", resolution=(800, 600))
        assert isinstance(sp, PandocBackend)
        assert sp.pandoc_template == "beamer"
        assert sp.resolution == (800, 600)


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSlideBackendConfig:
    """Config has a slide_backend key with validation."""

    def test_default_is_pandoc(self):
        cfg = Config(config_path="nonexistent.yaml")
        assert cfg.get("slide_backend") == "pandoc"

    def test_pandoc_section_defaults(self):
        """The ``pandoc:`` section ships with an empty frontmatter overlay.
        ``Config._migrate_legacy`` also lifts the default top-level
        ``pandoc_template: "beamer"`` into ``pandoc.template`` so the
        downstream pipeline sees one schema regardless of which key the
        user set."""
        cfg = Config(config_path="nonexistent.yaml")
        pandoc = cfg.get("pandoc")
        assert pandoc == {"frontmatter": {}, "template": "beamer"}

    def test_legacy_pandoc_template_still_honoured(self, tmp_path):
        """A user config that only sets the legacy top-level
        ``pandoc_template`` key still drives the Pandoc backend."""
        from scholium.cli.generate import _build_backend_config

        config_file = tmp_path / "config.yaml"
        config_file.write_text("pandoc_template: revealjs\n")
        cfg = Config(str(config_file))

        backend_cfg = _build_backend_config(cfg, "pandoc")
        assert backend_cfg["template"] == "revealjs"

    def test_explicit_pandoc_template_wins_over_legacy(self, tmp_path):
        """If both keys are set, the new ``pandoc.template`` takes
        precedence over the legacy top-level key."""
        from scholium.cli.generate import _build_backend_config

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "pandoc_template: revealjs\npandoc:\n  template: beamer\n"
        )
        cfg = Config(str(config_file))

        backend_cfg = _build_backend_config(cfg, "pandoc")
        assert backend_cfg["template"] == "beamer"

    def test_slidev_section_defaults(self):
        cfg = Config(config_path="nonexistent.yaml")
        slidev = cfg.get("slidev")
        assert slidev["theme"] == "default"
        assert slidev["command"] == ["npx", "@slidev/cli"]
        assert slidev["timeout"] == 600

    def test_marp_section_defaults(self):
        cfg = Config(config_path="nonexistent.yaml")
        marp = cfg.get("marp")
        assert marp["theme"] == "default"
        assert marp["command"] == ["npx", "@marp-team/marp-cli"]
        assert marp["no_sandbox"] is True
        assert marp["paginate"] is False

    def test_invalid_backend_rejected(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("slide_backend: not-real\n")
        with pytest.raises(ValueError, match="Invalid slide_backend"):
            Config(str(config_file))

    def test_valid_backend_accepted(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("slide_backend: slidev\n")
        cfg = Config(str(config_file))
        assert cfg.get("slide_backend") == "slidev"


# ---------------------------------------------------------------------------
# Slidev translator
# ---------------------------------------------------------------------------


_SAMPLE_SOURCE = textwrap.dedent(
    """\
    ---
    title: "Newton's Laws"
    author: "Physics 101"
    slide-level: 2
    ---

    # Section One

    ## First Slide

    Body content.

    ::: notes
    Narration goes here.
    :: Reference: textbook page 47
    [MIN 5s] [PRE 1s]
    :::

    ## Second Slide

    >- Bullet one
    >- Bullet two

    ::: notes
    First paragraph.

    Second paragraph.
    :::

    # Another Section

    ## Third Slide

    Content here.
    """
)


@pytest.mark.unit
class TestSlidevTranslation:
    """The Slidev translator emits valid, well-structured slidev markdown."""

    @pytest.fixture
    def backend(self):
        return SlidevBackend(
            resolution=(1920, 1080),
            backend_config={"theme": "seriph"},
        )

    def test_translation_strips_notes_block(self, backend):
        out = backend._translate(_SAMPLE_SOURCE)
        assert "::: notes" not in out
        assert "Narration goes here" not in out

    def test_translation_strips_metadata_lines(self, backend):
        out = backend._translate(_SAMPLE_SOURCE)
        assert ":: Reference" not in out

    def test_translation_strips_timing_directives(self, backend):
        out = backend._translate(_SAMPLE_SOURCE)
        assert "[MIN 5s]" not in out
        assert "[PRE 1s]" not in out

    def test_translation_converts_incremental_bullets(self, backend):
        out = backend._translate(_SAMPLE_SOURCE)
        assert ">-" not in out
        assert "- Bullet one" in out

    def test_translation_preserves_title_and_author(self, backend):
        out = backend._translate(_SAMPLE_SOURCE)
        # Frontmatter should include both
        assert "title: Newton's Laws" in out
        assert "author: Physics 101" in out
        assert "theme: seriph" in out

    def test_translation_default_theme_becomes_none(self):
        """`theme: default` is mapped to `theme: none` to avoid the
        @slidev/theme-default package being required on every install."""
        b = SlidevBackend(resolution=(1920, 1080), backend_config={"theme": "default"})
        out = b._translate(_SAMPLE_SOURCE)
        assert "theme: none" in out

    def test_translation_sets_canvas_dimensions(self):
        """`canvasWidth` + `aspectRatio` are derived from the configured
        resolution (the Slidev CLI doesn't accept --width/--height)."""
        b = SlidevBackend(resolution=(1600, 900), backend_config={})
        out = b._translate(_SAMPLE_SOURCE)
        assert "canvasWidth: 1600" in out
        assert "aspectRatio: 1600/900" in out

    def test_translation_uses_slide_separators(self, backend):
        """Each heading becomes a Slidev `---` slide separator."""
        out = backend._translate(_SAMPLE_SOURCE)
        # 5 slides → 5 frontmatter+content blocks → 4 separators between
        # them, plus the closing of the deck frontmatter.  Counting the
        # number of `\n---\n` occurrences gives 5 (1 frontmatter close +
        # 4 inter-slide separators).
        assert out.count("\n---\n") == 5

    def test_translation_slide_level_one(self, backend):
        """slide-level: 1 splits on `#` only, not `##`."""
        src = textwrap.dedent(
            """\
            ---
            title: x
            slide-level: 1
            ---

            # Slide One

            Some content.

            ## A subheading inside Slide One

            More content.

            # Slide Two

            Body.
            """
        )
        out = backend._translate(src)
        # 2 slides → 1 inter-slide separator + 1 frontmatter close
        assert out.count("\n---\n") == 2

    def test_translation_rejects_invalid_slide_level(self, backend):
        src = "---\nslide-level: 5\n---\n\n# A\n"
        with pytest.raises(ValueError, match="slide-level must be 1 or 2"):
            backend._translate(src)


# ---------------------------------------------------------------------------
# Marp translator
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMarpTranslation:
    """The Marp translator emits valid, well-structured Marp markdown."""

    @pytest.fixture
    def backend(self):
        return MarpBackend(
            resolution=(1920, 1080),
            backend_config={"theme": "default"},
        )

    def test_translation_adds_marp_true(self, backend):
        out = backend._translate(_SAMPLE_SOURCE)
        # `marp: true` is required for the CLI to recognise the file.
        assert "marp: true" in out

    def test_translation_preserves_theme(self, backend):
        out = backend._translate(_SAMPLE_SOURCE)
        assert "theme: default" in out

    def test_translation_strips_notes_metadata_timing(self, backend):
        out = backend._translate(_SAMPLE_SOURCE)
        assert "::: notes" not in out
        assert "Narration goes here" not in out
        assert ":: Reference" not in out
        assert "[MIN 5s]" not in out

    def test_translation_converts_incremental_bullets(self, backend):
        out = backend._translate(_SAMPLE_SOURCE)
        assert ">-" not in out
        assert "- Bullet one" in out

    def test_translation_uses_slide_separators(self, backend):
        """Each heading becomes a Marp `---` slide separator."""
        out = backend._translate(_SAMPLE_SOURCE)
        # 5 slides → 1 frontmatter close + 4 inter-slide separators.
        assert out.count("\n---\n") == 5

    def test_translation_paginate_flag(self):
        b = MarpBackend(
            resolution=(1920, 1080),
            backend_config={"theme": "default", "paginate": True},
        )
        out = b._translate(_SAMPLE_SOURCE)
        assert "paginate: true" in out

    def test_translation_rejects_invalid_slide_level(self, backend):
        src = "---\nslide-level: 5\n---\n\n# A\n"
        with pytest.raises(ValueError, match="slide-level must be 1 or 2"):
            backend._translate(src)


# ---------------------------------------------------------------------------
# Slidev export — end-to-end with a fake CLI
# ---------------------------------------------------------------------------


def _make_fake_slidev(path: Path) -> None:
    """Write a stub script that creates two PNGs at --output and exits 0."""
    path.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import sys
            from pathlib import Path
            from PIL import Image
            args = sys.argv[1:]
            for i, a in enumerate(args):
                if a == '--output':
                    out_dir = Path(args[i+1])
                    break
            out_dir.mkdir(parents=True, exist_ok=True)
            for n in (1, 2):
                img = Image.new('RGB', (640, 480), color=(n*100, n*50, 50))
                img.save(out_dir / f'fake-{n:02d}.png')
            """
        )
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _make_fake_marp(path: Path) -> None:
    """Write a stub Marp script that mimics ``marp --images png -o <out>.png``.

    Marp writes ``<basename>.001.png``, ``<basename>.002.png``, … next to
    the ``-o`` path.  The stub emits two such files and exits 0.
    """
    path.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import sys
            from pathlib import Path
            from PIL import Image
            args = sys.argv[1:]
            out_template = None
            for i, a in enumerate(args):
                if a == '-o':
                    out_template = Path(args[i+1])
                    break
            assert out_template is not None, "no -o argument"
            out_template.parent.mkdir(parents=True, exist_ok=True)
            stem = out_template.stem
            for n in (1, 2):
                img = Image.new('RGB', (640, 480), color=(50, n*80, n*120))
                img.save(out_template.parent / f'{stem}.{n:03d}.png')
            """
        )
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


@pytest.mark.unit
class TestSlidevExportEndToEnd:
    """Run the full process() path against a stub CLI script."""

    def test_export_collects_pngs(self, tmp_path):
        fake = tmp_path / "fake-slidev"
        _make_fake_slidev(fake)

        src = tmp_path / "lecture.md"
        src.write_text(
            textwrap.dedent(
                """\
                ---
                title: Demo
                slide-level: 2
                ---

                # Section

                ## Slide

                Body.

                ::: notes
                Spoken.
                :::
                """
            )
        )

        backend = SlidevBackend(
            resolution=(1920, 1080),
            backend_config={"command": [str(fake)], "timeout": 5},
        )
        images = backend.process(str(src), str(tmp_path / "out"))

        assert len(images) == 2
        for path in images:
            assert Path(path).name.startswith("slide_")
            with Image.open(path) as img:
                assert img.size == (1920, 1080)

    def test_export_missing_cli_raises(self, tmp_path):
        src = tmp_path / "x.md"
        src.write_text("---\ntitle: x\n---\n\n# A\n")

        backend = SlidevBackend(
            resolution=(640, 480),
            backend_config={"command": ["definitely-not-a-real-binary-xyz-abc"]},
        )
        with pytest.raises(RuntimeError, match="requires Node.js and the Slidev CLI"):
            backend.process(str(src), str(tmp_path / "out"))


# ---------------------------------------------------------------------------
# Marp export — end-to-end with a fake CLI
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMarpExportEndToEnd:
    """Run the full Marp process() path against a stub CLI script."""

    def test_export_collects_pngs(self, tmp_path):
        fake = tmp_path / "fake-marp"
        _make_fake_marp(fake)

        src = tmp_path / "lecture.md"
        src.write_text(
            textwrap.dedent(
                """\
                ---
                title: Demo
                slide-level: 2
                ---

                # Section

                ## Slide

                Body.

                ::: notes
                Spoken.
                :::
                """
            )
        )

        backend = MarpBackend(
            resolution=(1920, 1080),
            backend_config={"command": [str(fake)]},
        )
        images = backend.process(str(src), str(tmp_path / "out"))

        assert len(images) == 2
        for path in images:
            assert Path(path).name.startswith("slide_")
            with Image.open(path) as img:
                assert img.size == (1920, 1080)

    def test_export_missing_cli_raises(self, tmp_path):
        src = tmp_path / "x.md"
        src.write_text("---\ntitle: x\n---\n\n# A\n")

        backend = MarpBackend(
            resolution=(640, 480),
            backend_config={"command": ["definitely-not-a-real-binary-xyz-abc"]},
        )
        with pytest.raises(RuntimeError, match="requires Node.js and the Marp CLI"):
            backend.process(str(src), str(tmp_path / "out"))


# ---------------------------------------------------------------------------
# Pandoc frontmatter overlay
# ---------------------------------------------------------------------------


def _make_fake_pandoc(path: Path) -> None:
    """Stub for ``pandoc`` that records its argv to a sibling file and exits 0.

    The real pandoc would produce a PDF; for the overlay test we only need
    to confirm the right CLI flags + metadata file are passed.
    """
    path.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import sys
            from pathlib import Path
            args = sys.argv[1:]
            # Find the -o argument and write a dummy file so the caller's
            # "output exists" expectation holds.
            for i, a in enumerate(args):
                if a == '-o':
                    Path(args[i+1]).write_bytes(b'%PDF-1.4 (stub)\\n')
                    break
            # Record argv next to ourselves for inspection.
            (Path(__file__).parent / 'pandoc-argv.txt').write_text('\\n'.join(args))
            """
        )
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


@pytest.mark.unit
class TestPandocFrontmatterOverlay:
    """The Pandoc backend gains a `frontmatter:` overlay, symmetric with
    the Slidev and Marp backends.  The overlay is written to a YAML file
    and passed to pandoc via ``--metadata-file``."""

    def test_frontmatter_stored_on_backend(self):
        b = PandocBackend(
            resolution=(1920, 1080),
            backend_config={"frontmatter": {"lang": "en-AU", "aspectratio": 169}},
        )
        assert b.extra_frontmatter == {"lang": "en-AU", "aspectratio": 169}

    def test_frontmatter_defaults_to_empty(self):
        b = PandocBackend(resolution=(1920, 1080), backend_config={})
        assert b.extra_frontmatter == {}

    def test_overlay_passes_metadata_file_to_pandoc(self, tmp_path, monkeypatch):
        """When frontmatter is set, pandoc is invoked with --metadata-file."""
        fake_dir = tmp_path / "bin"
        fake_dir.mkdir()
        _make_fake_pandoc(fake_dir / "pandoc")
        monkeypatch.setenv("PATH", str(fake_dir) + os.pathsep + os.environ["PATH"])

        src = tmp_path / "lecture.md"
        src.write_text("---\ntitle: x\n---\n\n# A\n")

        out_dir = tmp_path / "out"
        out_dir.mkdir()
        pdf_path = out_dir / "slides.pdf"

        b = PandocBackend(
            resolution=(1920, 1080),
            backend_config={
                "frontmatter": {"aspectratio": 169, "lang": "en-AU"},
            },
        )
        b.markdown_to_pdf(str(src), str(pdf_path))

        argv = (fake_dir / "pandoc-argv.txt").read_text().splitlines()
        assert "--metadata-file" in argv
        meta_path = Path(argv[argv.index("--metadata-file") + 1])
        assert meta_path.exists()

        import yaml as _yaml
        loaded = _yaml.safe_load(meta_path.read_text())
        assert loaded == {"aspectratio": 169, "lang": "en-AU"}

    def test_no_metadata_file_when_empty(self, tmp_path, monkeypatch):
        """No --metadata-file flag when the overlay is empty (avoids
        leaving a stray YAML file beside every PDF)."""
        fake_dir = tmp_path / "bin"
        fake_dir.mkdir()
        _make_fake_pandoc(fake_dir / "pandoc")
        monkeypatch.setenv("PATH", str(fake_dir) + os.pathsep + os.environ["PATH"])

        src = tmp_path / "lecture.md"
        src.write_text("---\ntitle: x\n---\n\n# A\n")

        pdf_path = tmp_path / "out" / "slides.pdf"
        b = PandocBackend(resolution=(1920, 1080), backend_config={})
        b.markdown_to_pdf(str(src), str(pdf_path))

        argv = (fake_dir / "pandoc-argv.txt").read_text().splitlines()
        assert "--metadata-file" not in argv
        assert not (pdf_path.parent / "_scholium_meta.yaml").exists()


@pytest.mark.unit
class TestSlideBackendProbes:
    """Each backend reports its own external-dependency probes."""

    def test_pandoc_probe_finds_binaries(self, tmp_path, monkeypatch):
        """When pandoc + a LaTeX engine are on PATH, both probes pass."""
        fake_dir = tmp_path / "bin"
        fake_dir.mkdir()
        # Stubs that just exit 0; shutil.which only checks executability.
        for name in ("pandoc", "pdflatex"):
            stub = fake_dir / name
            stub.write_text("#!/bin/sh\nexit 0\n")
            stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        monkeypatch.setenv("PATH", str(fake_dir))

        probes = PandocBackend(resolution=(1920, 1080)).probe_dependencies()
        labels = {p.label: p for p in probes}
        assert labels["Pandoc binary"].ok is True
        assert labels["LaTeX engine"].ok is True
        assert "pdflatex" in labels["LaTeX engine"].detail

    def test_pandoc_probe_missing_latex(self, tmp_path, monkeypatch):
        """Pandoc present but no LaTeX engine → second probe fails with hint."""
        fake_dir = tmp_path / "bin"
        fake_dir.mkdir()
        stub = fake_dir / "pandoc"
        stub.write_text("#!/bin/sh\nexit 0\n")
        stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        monkeypatch.setenv("PATH", str(fake_dir))

        probes = PandocBackend(resolution=(1920, 1080)).probe_dependencies()
        labels = {p.label: p for p in probes}
        assert labels["Pandoc binary"].ok is True
        assert labels["LaTeX engine"].ok is False
        assert "TeX Live" in labels["LaTeX engine"].detail

    def test_slidev_probe_reports_node_and_launcher(self, tmp_path, monkeypatch):
        fake_dir = tmp_path / "bin"
        fake_dir.mkdir()
        for name in ("node", "npx"):
            stub = fake_dir / name
            stub.write_text("#!/bin/sh\nexit 0\n")
            stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        monkeypatch.setenv("PATH", str(fake_dir))
        # Avoid hitting the real ~/.cache/ms-playwright on the test box
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

        probes = SlidevBackend(
            resolution=(1920, 1080), backend_config={"command": ["npx", "@slidev/cli"]}
        ).probe_dependencies()
        labels = {p.label: p for p in probes}
        assert labels["Node.js"].ok is True
        assert labels["Slidev launcher (npx)"].ok is True
        # No Playwright Chromium present — must surface as not-ok with the
        # actionable hint.
        assert labels["Playwright Chromium"].ok is False
        assert "playwright install chromium" in labels["Playwright Chromium"].detail

    def test_marp_probe_flags_unconfigured_playwright_build(self, tmp_path, monkeypatch):
        """The Marp probe must NOT claim ready when only a Playwright
        Chromium is on disk and ``marp.browser_path`` isn't set — Marp
        won't auto-pick it and will time out launching Firefox instead."""
        fake_dir = tmp_path / "bin"
        fake_dir.mkdir()
        for name in ("node", "npx"):
            stub = fake_dir / name
            stub.write_text("#!/bin/sh\nexit 0\n")
            stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        monkeypatch.setenv("PATH", str(fake_dir))

        # Lay out a fake Playwright Chromium under tmp_path/.cache/ms-playwright
        pw = tmp_path / ".cache" / "ms-playwright" / "chromium-9999" / "chrome-linux64"
        pw.mkdir(parents=True)
        chrome = pw / "chrome"
        chrome.write_text("#!/bin/sh\nexit 0\n")
        chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

        probes = MarpBackend(
            resolution=(1920, 1080),
            backend_config={"command": ["npx", "@marp-team/marp-cli"]},
        ).probe_dependencies()
        labels = {p.label: p for p in probes}
        assert labels["Chrome binary"].ok is False  # not ready until configured
        assert "marp.browser_path" in labels["Chrome binary"].detail
        assert str(chrome) in labels["Chrome binary"].detail

    def test_marp_probe_accepts_configured_browser_path(self, tmp_path, monkeypatch):
        fake_dir = tmp_path / "bin"
        fake_dir.mkdir()
        for name in ("node", "npx"):
            stub = fake_dir / name
            stub.write_text("#!/bin/sh\nexit 0\n")
            stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        monkeypatch.setenv("PATH", str(fake_dir))

        my_chrome = tmp_path / "chrome"
        my_chrome.write_text("ok")

        probes = MarpBackend(
            resolution=(1920, 1080),
            backend_config={"browser_path": str(my_chrome)},
        ).probe_dependencies()
        labels = {p.label: p for p in probes}
        assert labels["Chrome binary"].ok is True
        assert str(my_chrome) in labels["Chrome binary"].detail


@pytest.mark.unit
class TestSlideBackendResolution:
    """``slide-backend:`` key in source frontmatter, with CLI/config precedence."""

    def test_cli_flag_wins(self, tmp_path):
        from scholium.cli._utils import _resolve_slide_backend

        src = tmp_path / "lecture.md"
        src.write_text("---\nslide-backend: marp\n---\n\n# A\n")
        cfg = Config(config_path="nonexistent.yaml")
        cfg.set("slide_backend", "slidev")

        name, origin = _resolve_slide_backend(
            cli_value="pandoc", slides_md=str(src), cfg=cfg
        )
        assert name == "pandoc"
        assert origin == "--slide-backend"

    def test_source_frontmatter_wins_over_config(self, tmp_path):
        from scholium.cli._utils import _resolve_slide_backend

        src = tmp_path / "lecture.md"
        src.write_text("---\ntitle: x\nslide-backend: marp\nslide-level: 2\n---\n\n# A\n")
        cfg = Config(config_path="nonexistent.yaml")
        cfg.set("slide_backend", "slidev")

        name, origin = _resolve_slide_backend(
            cli_value=None, slides_md=str(src), cfg=cfg
        )
        assert name == "marp"
        assert "frontmatter" in origin
        assert "lecture.md" in origin

    def test_config_wins_when_no_cli_or_source(self, tmp_path):
        from scholium.cli._utils import _resolve_slide_backend

        src = tmp_path / "lecture.md"
        src.write_text("---\ntitle: x\nslide-level: 2\n---\n\n# A\n")
        cfg = Config(config_path="nonexistent.yaml")
        cfg.set("slide_backend", "slidev")

        name, origin = _resolve_slide_backend(
            cli_value=None, slides_md=str(src), cfg=cfg
        )
        assert name == "slidev"
        assert origin == "config.yaml"

    def test_default_when_nothing_set(self, tmp_path):
        """If config has no slide_backend either, fall back to pandoc."""
        from scholium.cli._utils import _resolve_slide_backend

        src = tmp_path / "lecture.md"
        src.write_text("# A\n")  # no frontmatter at all
        cfg = Config(config_path="nonexistent.yaml")
        cfg.set("slide_backend", None)

        name, origin = _resolve_slide_backend(
            cli_value=None, slides_md=str(src), cfg=cfg
        )
        assert name == "pandoc"
        assert origin == "default"

    def test_invalid_source_value_rejected(self, tmp_path):
        from scholium.cli._utils import _resolve_slide_backend

        src = tmp_path / "lecture.md"
        src.write_text("---\nslide-backend: notreal\n---\n\n# A\n")
        cfg = Config(config_path="nonexistent.yaml")

        with pytest.raises(ValueError, match="Invalid slide-backend 'notreal'"):
            _resolve_slide_backend(cli_value=None, slides_md=str(src), cfg=cfg)

    def test_missing_source_file_returns_config(self, tmp_path):
        """A nonexistent source path shouldn't crash resolution — let
        the rest of the pipeline raise the file-not-found error."""
        from scholium.cli._utils import _resolve_slide_backend

        cfg = Config(config_path="nonexistent.yaml")
        cfg.set("slide_backend", "marp")

        name, origin = _resolve_slide_backend(
            cli_value=None, slides_md=str(tmp_path / "ghost.md"), cfg=cfg
        )
        assert name == "marp"
        assert origin == "config.yaml"


@pytest.mark.unit
class TestSlideBackendsCLI:
    """The ``scholium slides`` Click group (slide-rendering doctor commands)."""

    def test_list_command_runs(self):
        from scholium.cli.slides import slides

        result = CliRunner().invoke(slides, ["list"])
        assert result.exit_code == 0, result.output
        # Headers for each backend
        for name in VALID_BACKENDS:
            assert name in result.output

    def test_check_command_renders_via_fake_pandoc(self, tmp_path, monkeypatch):
        """``check pandoc`` should drive the real PandocBackend through
        ``process()``.  We stand a stub pandoc on PATH that writes the
        expected output PDF, plus a no-op pdf2image for the rasterise step."""
        from scholium.cli import slides as slides_module

        fake_dir = tmp_path / "bin"
        fake_dir.mkdir()
        _make_fake_pandoc(fake_dir / "pandoc")
        monkeypatch.setenv("PATH", str(fake_dir) + os.pathsep + os.environ["PATH"])

        # Patch convert_from_path so we don't need poppler installed.
        from PIL import Image as _PILImage

        def _fake_convert_from_path(pdf_path, dpi=300, fmt="png"):
            return [_PILImage.new("RGB", (640, 480), color=(120, 120, 120))]

        monkeypatch.setattr(
            "scholium.slides.pandoc.convert_from_path",
            _fake_convert_from_path,
        )

        result = CliRunner().invoke(slides_module.slides, ["check", "pandoc"])
        assert result.exit_code == 0, result.output
        assert "pandoc rendered" in result.output
        assert "All checked backends passed" in result.output
