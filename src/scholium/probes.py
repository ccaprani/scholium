"""Shared dependency-probe primitives used across Scholium subsystems.

The three subsystem doctor commands (``scholium slides list`` /
``voice list`` / ``video list``) all render their dependency checks
through the same :class:`Probe` dataclass, defined here so each
subsystem can import it without reaching into a sibling subsystem's
internals.

Also exposes :func:`short_version`, the small ``--version`` runner
used by every backend's probe to read a one-line version banner from
an external CLI.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import List, Optional


__all__ = ["Probe", "short_version"]


@dataclass
class Probe:
    """Result of a single dependency check.

    ``label`` is the human-readable name of the dependency (e.g.
    "Pandoc binary", "Node.js", "ffmpeg binary"); ``ok`` is True iff
    the dependency was found and is usable; ``detail`` is either the
    resolved path/version on success or an install hint on failure.
    The CLI's doctor commands render these as one bullet per probe.
    """

    label: str
    ok: bool
    detail: str


def short_version(cmd: List[str], *, timeout: float = 5.0) -> Optional[str]:
    """Run ``cmd`` (typically a ``--version`` invocation) and return the
    first non-empty line of stdout, truncated to 80 chars.

    Returns ``None`` if the command is missing, times out, or otherwise
    fails — callers should treat that as "version unknown" rather than
    propagating an exception, since this is only used for friendly
    probe output.
    """
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    for line in res.stdout.splitlines():
        line = line.strip()
        if line:
            return line[:80]
    return None
