from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ck42x_pl_arch.config import Settings
from ck42x_pl_arch.flipper.payloadbay_image import (
    copy_script_to_mounted_payloadbay,
    ensure_template_image,
    patch_scripts_into_image,
)
from ck42x_pl_arch.flipper.serial_cli import FlipperCli, FlipperNotFoundError, FlipperSerialError

LogFn = Callable[[str], None]

PAYLOAD_DIR_DEFAULT = "/ext/ck42x-payloads"
MASS_STORAGE_IMAGE_DEFAULT = "/ext/apps_data/mass_storage/payloadbay.img"
MASS_STORAGE_DIR_DEFAULT = "/ext/apps_data/mass_storage"


@dataclass
class DeployResult:
    ok: bool
    launch_path: str = ""
    script_path: str = ""
    image_path: str = ""
    script_via_mount: bool = False
    logs: list[str] = field(default_factory=list)


def _log(callback: LogFn | None, message: str, bucket: list[str]) -> None:
    bucket.append(message)
    if callback:
        callback(message)


def _pick_launch_txt(bundle_dir: Path, slug: str) -> Path | None:
    preferred = bundle_dir / f"launch-{slug}.txt"
    if preferred.is_file():
        return preferred
    launches = sorted(bundle_dir.glob("launch-*.txt"))
    return launches[0] if launches else None


def _pick_agent_ps1(bundle_dir: Path, slug: str) -> Path | None:
    preferred = bundle_dir / f"agent-{slug}.ps1"
    if preferred.is_file():
        return preferred
    agents = sorted(bundle_dir.glob("agent-*.ps1"))
    return agents[0] if agents else None


def deploy_mission_bundle(
    settings: Settings,
    bundle_dir: Path,
    *,
    slug: str | None = None,
    log: LogFn | None = None,
) -> DeployResult:
    """Upload launch .txt to Flipper SD and agent .ps1 into PAYLOADBAY (mount or disk image)."""
    logs: list[str] = []
    manifest_path = bundle_dir / "manifest.json"
    if manifest_path.is_file():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            slug = slug or str(data.get("slug") or "")
        except json.JSONDecodeError:
            pass
    slug = slug or bundle_dir.name

    launch = _pick_launch_txt(bundle_dir, slug)
    agent = _pick_agent_ps1(bundle_dir, slug)
    if not launch:
        msg = "No launch-*.txt in bundle; nothing to flash to /ext/ck42x-payloads"
        _log(log, msg, logs)
        return DeployResult(ok=False, logs=logs)

    payload_dir = settings.flipper_payload_dir or PAYLOAD_DIR_DEFAULT
    image_dest = settings.flipper_mass_storage_image or MASS_STORAGE_IMAGE_DEFAULT
    launch_dest = f"{payload_dir.rstrip('/')}/{launch.name}"

    result = DeployResult(ok=False, launch_path=launch_dest, logs=logs)

    # 1) Host agent -> PAYLOADBAY scripts/ (mounted volume fast path)
    if agent and settings.deploy_use_mounted_volume:
        mounted = copy_script_to_mounted_payloadbay(agent, agent.name)
        if mounted:
            result.script_path = mounted
            result.script_via_mount = True
            _log(log, f"[ok] Copied {agent.name} to mounted PAYLOADBAY: {mounted}", logs)
        else:
            _log(
                log,
                "PAYLOADBAY not mounted; will patch Exfil Disk image and upload over serial.",
                logs,
            )

    # 2) Patch disk image if agent not on mounted volume
    image_bytes: bytes | None = None
    if agent and not result.script_via_mount and settings.deploy_upload_image:
        cache = Path(settings.payloadbay_template_path).expanduser()
        template = ensure_template_image(cache, settings.payloadbay_template_url)
        with tempfile.TemporaryDirectory(prefix="ck42x-pl-arch-") as tmp:
            patched = Path(tmp) / "payloadbay.img"
            patch_scripts_into_image(
                template,
                {agent.name: agent.read_bytes()},
                patched,
            )
            image_bytes = patched.read_bytes()
            result.image_path = image_dest
            _log(log, f"Patched PAYLOADBAY image with scripts/{agent.name}", logs)

    # 3) Serial upload launch .txt (+ optional full disk image)
    try:
        with FlipperCli.connect(settings.flipper_port or None, settings.flipper_baud) as cli:
            _log(log, f"Connected on {cli.port}", logs)
            cli.mkdir(payload_dir)
            if image_bytes:
                cli.mkdir(MASS_STORAGE_DIR_DEFAULT)

            launch_data = launch.read_bytes()
            _log(log, f"Uploading {launch.name} -> {launch_dest}", logs)

            def launch_progress(written: int, total: int) -> None:
                if written == total or written % 4096 == 0:
                    _log(log, f"  launch payload: {written}/{total} bytes", logs)

            cli.write_file(launch_dest, launch_data, label=launch.name, on_progress=launch_progress)
            _log(log, f"[ok] Flipper payload: {launch_dest}", logs)

            if image_bytes:
                _log(log, f"Uploading PAYLOADBAY disk image -> {image_dest}", logs)

                last_image_log = 0

                def image_progress(written: int, total: int) -> None:
                    nonlocal last_image_log
                    if written == total or written - last_image_log >= 262144:
                        pct = int(100 * written / total)
                        _log(log, f"  disk image: {pct}% ({written}/{total})", logs)
                        last_image_log = written

                cli.write_file(
                    image_dest,
                    image_bytes,
                    label="payloadbay.img",
                    on_progress=image_progress,
                )
                _log(log, f"[ok] Mass storage image: {image_dest}", logs)

            result.ok = True
    except FlipperNotFoundError as exc:
        _log(log, f"[error] {exc}", logs)
    except FlipperSerialError as exc:
        _log(log, f"[error] Serial deploy failed: {exc}", logs)

    if agent and result.script_via_mount and result.ok:
        _log(
            log,
            "Tip: Open Exfil Disk on Flipper before inject so the host sees scripts/ on PAYLOADBAY.",
            logs,
        )

    return result
