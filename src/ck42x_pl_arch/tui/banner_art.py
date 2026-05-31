"""CK42X PL-ARCH TUI banner — compact bee + title (designed for the menu layout)."""

from __future__ import annotations

BANNER_WIDTH = 56

# Small top-down bee mark — gold on black, ~56 cols, 7 art lines.
_BEE: tuple[str, ...] = (
    "                    ▄▄▄▄▄▄▄▄▄                     ",
    "                  ▄████████████▄                   ",
    "                 ████▀▀▀██▀▀▀████                  ",
    "                ████  ▄████▄  ████                 ",
    "                 ████▄██▀▀██▄████                  ",
    "                  ▀████▀  ▀████▀                   ",
    "                    ▀▀      ▀▀                     ",
)

_TAGLINE = "CK42X  ·  PL-ARCH"
_SUBTITLE = "Payload Lab Architect"
_HINT = "bee ops // authorized labs only"


def _center(text: str, width: int = BANNER_WIDTH) -> str:
    text = text[:width]
    pad = max(0, (width - len(text)) // 2)
    return f"{' ' * pad}{text}"


BANNER_LINES: tuple[str, ...] = (
    *_BEE,
    "",
    _center(_TAGLINE),
    _center(_SUBTITLE),
    _center(_HINT),
)
BANNER_WIDTH = max(len(line) for line in BANNER_LINES if line) if BANNER_LINES else 0


def banner_markup() -> str:
    """Rich/Textual markup: gold bee crest + centered copy."""
    parts: list[str] = []
    for raw in BANNER_LINES:
        stripped = raw.strip()
        if not stripped:
            parts.append("")
        elif stripped == _TAGLINE:
            parts.append(f"[bold #ffd400]{raw}[/]")
        elif stripped == _SUBTITLE:
            parts.append(f"[#ffd400]{raw}[/]")
        elif stripped == _HINT:
            parts.append(f"[dim]{raw}[/]")
        else:
            parts.append(f"[#ffd400]{raw}[/]")
    return "\n".join(parts)


BANNER = "\n".join(BANNER_LINES)
