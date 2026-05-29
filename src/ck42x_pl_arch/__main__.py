from __future__ import annotations

import argparse
import asyncio
import sys

from ck42x_pl_arch import __version__
from ck42x_pl_arch.config import Settings
from ck42x_pl_arch.forge.mission import ForgeRequest, forge_mission


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ck42x",
        description="CK42X Payload Lab Architect — forge Flipper BadUSB mission bundles",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("tui", help="Launch interactive TUI (default)")

    forge = sub.add_parser("forge", help="Non-interactive forge")
    forge.add_argument("--title", required=True)
    forge.add_argument("--goal", required=True)
    forge.add_argument("--platform", action="append", default=["windows"])
    forge.add_argument("--no-handoff", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cmd = args.cmd or "tui"

    if cmd == "tui":
        from ck42x_pl_arch.tui.app import run_tui

        run_tui()
        return 0

    if cmd == "forge":
        settings = Settings.load()
        result = asyncio.run(
            forge_mission(
                settings,
                ForgeRequest(
                    title=args.title,
                    goal=args.goal,
                    platforms=args.platform,
                    handoff=not args.no_handoff,
                ),
            )
        )
        print(result.bundle_dir)
        for f in result.files:
            print(f"  {f}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
