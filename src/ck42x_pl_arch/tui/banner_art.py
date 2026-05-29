"""CK42X nyanBEE banner — Flipper-style block art (width 94)."""

from __future__ import annotations

BANNER_WIDTH = 94

# Generated from public/brand/bee-crown.png (gold bee on black), Flipper block charset.
_BEE_FRAME: tuple[str, ...] = (
    "▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄",
    "                                                                                              ",
    "                                                                                              ",
    "                                         ▄▄  ▄▄  ▄▄                                          ",
    "                                          █ ▀  ▀ █                                           ",
    "                                           ▀ ▀▀▀█                                            ",
    "                                    ▄   ▄▄  █▀▀█  ▄▄   ▄                                     ",
    "                                     ▄    ▀▄█▄▄█▄▀    ▄                                      ",
    "                                      █▀▀▀ █    █▀▀▀▀█                                       ",
    "                                      ▀    █▀▀▀▀█    ▀                                       ",
    "                                          ▀▀    ▀▀                                           ",
    "                                           ▀    ▀                                            ",
    "                                                                                              ",
    "                    CK42X :: PAYLOAD LAB ARCHITECT (PL-ARCH)                                 ",
    "                         BEE OPS // AUTHORIZED LABS ONLY                                     ",
    "                                                                                              ",
    "▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀",
)


def _center(text: str, width: int = BANNER_WIDTH) -> str:
    text = text[:width]
    pad = max(0, (width - len(text)) // 2)
    return f"{' ' * pad}{text}"


def banner_markup() -> str:
    """Rich/Textual markup: gold bee frame on black."""
    lines: list[str] = []
    for raw in _BEE_FRAME:
        if raw.strip():
            lines.append(f"[#ffd400]{raw}[/]")
        else:
            lines.append("")
    return "\n".join(lines)


# Plain text for logs / CLI
BANNER = "\n".join(_BEE_FRAME)
