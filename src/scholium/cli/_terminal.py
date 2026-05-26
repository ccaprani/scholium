"""Terminal output helpers shared across CLI subcommands.

Falls back to ASCII symbols on terminals that don't advertise a UTF-8
encoding (typically Windows ``cmd.exe`` with cp1252).
"""

from __future__ import annotations

import sys

_UTF8 = (
    getattr(sys.stdout, "encoding", "ascii").casefold().replace("-", "") in ("utf8",)
)

# Status / bullet glyphs
_CHK = "✔" if _UTF8 else "+"      # check mark (sub-item done)
_OK = "✅" if _UTF8 else "OK"      # top-level success
_WARN = "⚠" if _UTF8 else "!!"   # warning
_BULL = "•" if _UTF8 else "-"     # list bullet
_NO = "✗" if _UTF8 else "x"       # not installed / not found


def _icon(emoji: str) -> str:
    """Return *emoji* on UTF-8 terminals, ``>>`` on ASCII-only terminals."""
    return emoji if _UTF8 else ">>"


__all__ = ["_UTF8", "_CHK", "_OK", "_WARN", "_BULL", "_NO", "_icon"]
