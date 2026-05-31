"""Validate PowerShell one-liner extracted from ducky handoff payload."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ck42x_pl_arch.emit.ducky import windows_handoff

goal = "Inspect mass storage and propose safe read-only verification commands."
txt = windows_handoff(
    script_name="agent-test.ps1",
    title="repo-check",
    goal=goal,
    activity="CK42X Handoff",
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

ps = "".join(run_parts)
out = Path(__file__).resolve().parents[1] / "_test.ps1"
out.write_text(ps + "\n", encoding="utf-8")
print(ps)
print("---")
print(f"Braces before else: {ps.split('else{')[0].count('}')}")

result = subprocess.run(
    [
        "powershell",
        "-NoProfile",
        "-Command",
        f"$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('{out}', [ref]$null, [ref]$e); "
        "if ($e) { $e | ForEach-Object { $_.ToString() }; exit 1 } else { 'parse ok' }",
    ],
    capture_output=True,
    text=True,
)
print(result.stdout.strip() or result.stderr.strip())
raise SystemExit(result.returncode)
