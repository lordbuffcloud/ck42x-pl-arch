"""Validate PowerShell one-liner extracted from ducky handoff payload."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ck42x_pl_arch.emit.ducky import windows_handoff

goal = "find pictures of people and extract to mass storage"
txt = windows_handoff(
    script_name="agent-test.ps1",
    title="extract-images",
    goal=goal,
    activity="CK42X PL-ARCH Handoff",
)

run_parts: list[str] = []
capturing = False
for line in txt.splitlines():
    if line.startswith("STRING ") and "if($b)" in line:
        capturing = True
    if capturing:
        if line.startswith("STRING "):
            run_parts.append(line[7:])
        elif line.strip() == "ENTER":
            break

poll_parts: list[str] = []
capturing = False
for line in txt.splitlines():
    if line.startswith("STRING ") and line.startswith("STRING while(("):
        capturing = True
    if capturing:
        if line.startswith("STRING "):
            poll_parts.append(line[7:])
        elif line.strip() == "ENTER":
            break

for label, parts in [("poll", poll_parts), ("run", run_parts)]:
    ps = "".join(parts)
    out = Path(__file__).resolve().parents[1] / f"_test_{label}.ps1"
    out.write_text(ps + "\n", encoding="utf-8")
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            f"$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('{out}', [ref]$null, [ref]$e); "
            "if ($e) { $e | ForEach-Object { $_.ToString() }; exit 1 } else { Write-Output 'parse ok' }",
        ],
        capture_output=True,
        text=True,
    )
    print(label, result.stdout.strip() or result.stderr.strip())
    if result.returncode:
        raise SystemExit(result.returncode)

print("all ok")
