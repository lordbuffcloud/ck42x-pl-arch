from __future__ import annotations

import shutil
import urllib.request
from pathlib import Path

from pyfatfs.PyFatFS import PyFatFS

DEFAULT_TEMPLATE_URL = (
    "https://www.ck42x.com/downloads/flipper/companions/payloadbay-exfil-fat16.img"
)


def ensure_template_image(cache_path: Path, url: str = DEFAULT_TEMPLATE_URL) -> Path:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.is_file() and cache_path.stat().st_size > 0:
        return cache_path
    with urllib.request.urlopen(url, timeout=120) as resp:
        cache_path.write_bytes(resp.read())
    return cache_path


def patch_scripts_into_image(
    template: Path,
    scripts: dict[str, bytes],
    output: Path,
) -> Path:
    """Copy template FAT16 image and write scripts/<name> files for PAYLOADBAY handoff."""
    if not scripts:
        return template
    shutil.copy2(template, output)
    fs = PyFatFS(str(output))
    try:
        if not fs.exists("/scripts"):
            fs.makedirs("/scripts")
        for name, body in scripts.items():
            remote = f"/scripts/{name}"
            if fs.exists(remote):
                fs.remove(remote)
            with fs.open(remote, "wb") as remote_file:
                remote_file.write(body)
    finally:
        fs.close()
    return output


def copy_script_to_mounted_payloadbay(local_script: Path, remote_name: str) -> str | None:
    """If PAYLOADBAY is already mounted (Exfil Disk open), copy agent without re-flashing the image."""
    import string

    for letter in string.ascii_uppercase:
        root = Path(f"{letter}:/")
        tag = root / "CK42X.TAG"
        scripts_dir = root / "scripts"
        if tag.is_file() and scripts_dir.is_dir():
            dest = scripts_dir / remote_name
            shutil.copy2(local_script, dest)
            return str(dest)
    return None
