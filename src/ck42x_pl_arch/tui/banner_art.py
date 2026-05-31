"""CK42X PL-ARCH TUI banner — user-provided CK42X figlet art."""

from __future__ import annotations

_SUBTITLE = "Payload Lab Architect · bee ops // authorized labs only"

# Exact art as provided; do not reformat.
_CK42X_ART: tuple[str, ...] = (
    "        __      _____ ________                  __________               .__                    .___      ",
    "  ____ |  | __ /  |  |\\_____  \\ ___  ___        \\______   \\_____  ___.__.|  |   _________     __| _/______",
    "_/ ___\\|  |/ //   |  |_/  ____/ \\  \\/  /  ______ |     ___/\\__  \\<   |  ||  |  /  _ \\__  \\   / __ |/  ___/",
    "\\  \\___|    </    ^   /       \\  >    <  /_____/ |    |     / __ \\\\___  ||  |_(  <_> ) __ \\_/ /_/ |\\___ \\ ",
    " \\___  >__|_ \\____   |\\_______ \\/__/\\_ \\         |____|    (____  / ____||____/\\____(____  /\\____ /____  >",
    "     \\/     \\/    |__|        \\/      \\/                        \\/\\/                     \\/      \\/    \\/ ",
)

BANNER_LINES: tuple[str, ...] = (*_CK42X_ART, "", _SUBTITLE)
BANNER_WIDTH = max(len(line) for line in BANNER_LINES if line) if BANNER_LINES else 0


def banner_markup() -> str:
    """Rich/Textual markup: gold figlet + dim subtitle."""
    parts: list[str] = []
    for raw in BANNER_LINES:
        if not raw.strip():
            parts.append("")
        elif raw == _SUBTITLE:
            parts.append(f"[dim]{raw}[/]")
        else:
            parts.append(f"[#ffd400]{raw}[/]")
    return "\n".join(parts)


BANNER = "\n".join(BANNER_LINES)
