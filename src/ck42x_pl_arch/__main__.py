from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

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
    forge.add_argument("--deploy", action="store_true", help="Flash launch .txt and PAYLOADBAY scripts to Flipper")

    deploy = sub.add_parser("deploy", help="Flash a forged mission bundle to Flipper")
    deploy.add_argument("--slug", help="Mission slug under output dir (default: last forged)")
    deploy.add_argument("--bundle", type=str, help="Path to mission bundle directory")
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
                    deploy=args.deploy,
                ),
            )
        )
        print(result.bundle_dir)
        for f in result.files:
            print(f"  {f}")
        for line in result.deploy_logs:
            print(line)
        return 0 if not args.deploy or result.deploy_ok else 1

    if cmd == "deploy":
        settings = Settings.load()
        bundle: Path | None = None
        if args.bundle:
            bundle = Path(args.bundle).expanduser()
        else:
            slug = args.slug or settings.last_slug
            if not slug:
                print("error: pass --slug or --bundle, or forge a mission first", file=sys.stderr)
                return 1
            bundle = settings.output_path / slug
        if not bundle.is_dir():
            print(f"error: bundle not found: {bundle}", file=sys.stderr)
            return 1
        from ck42x_pl_arch.flipper.deploy import deploy_mission_bundle

        out = deploy_mission_bundle(settings, bundle, slug=args.slug or settings.last_slug)
        for line in out.logs:
            print(line)
        return 0 if out.ok else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
