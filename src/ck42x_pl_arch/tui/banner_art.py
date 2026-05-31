"""CK42X PL-ARCH TUI banner — nyanBEE bee crown + title."""

from __future__ import annotations

BANNER_WIDTH = 52

# Front-facing bee crown (Flipper / nyanBEE brand charset). Stripped from the
# bee-crown mark and centered — reads clearly as a bee, not an abstract blob.
_BEE_CROWN: tuple[str, ...] = (
    "                   ▄▄  ▄▄  ▄▄                   ",
    "                    █ ▀  ▀ █                    ",
    "                     ▀ ▀▀▀█                     ",
    "               ▄   ▄▄  █▀▀█  ▄▄   ▄              ",
    "                ▄    ▀▄█▄▄█▄▀    ▄               ",
    "                 █▀▀▀ █    █▀▀▀▀█                ",
    "                 ▀    █▀▀▀▀█    ▀                ",
    "                     ▀▀    ▀▀                     ",
    "                      ▀    ▀                      ",
)

_TAGLINE = "CK42X  ·  PL-ARCH"
_SUBTITLE = "Payload Lab Architect"
_HINT = "bee ops // authorized labs only"


def _center(text: str, width: int = BANNER_WIDTH) -> str:
    text = text[:width]
    pad = max(0, (width - len(text)) // 2)
    return f"{' ' * pad}{text}"


BANNER_LINES: tuple[str, ...] = (
    *_BEE_CROWN,
    "",
    _center(_TAGLINE),
    _center(_SUBTITLE),
    _center(_HINT),
)
BANNER_WIDTH = max(len(line) for line in BANNER_LINES if line) if BANNER_LINES else 0


def banner_markup() -> str:
    """Rich/Textual markup: gold bee crown + centered copy."""
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
