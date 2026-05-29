# ck42x-pl-arch

**CK42X Payload Lab Architect** — a cross-platform TUI for authorized Flipper Zero training labs.

Source: https://github.com/lordbuffcloud/ck42x-pl-arch

Forge mission bundles:

| Artifact | Use |
|----------|-----|
| `launch-<slug>.txt` | Flipper BadUSB / Payload Bay inject |
| `agent-<slug>.ps1` | Windows host agent |
| `agent-<slug>-linux.sh` | Linux host agent |
| `agent-<slug>-mac.sh` | macOS host agent |
| `manifest.json` | Metadata + reviewer notes |

## Install (website one-liner)

**Linux / macOS**

```bash
curl -fsSL https://www.ck42x.com/install/ck42x-pl-arch.sh | bash
```

**Windows (PowerShell)**

```powershell
irm https://www.ck42x.com/install/ck42x-pl-arch.ps1 | iex
```

## Run

```bash
ck42x-pl-arch          # interactive TUI
ck42x-pl-arch forge --title "repo-check" --goal "Safe git health snapshot"
```

## Config

`~/.config/ck42x-pl-arch/config.json`

- `DEEPSEEK_API_KEY` env var is also read when forging with AI agents
- Output default: `~/Documents/CK42X-PL-Arch/missions/`

## Dev

```bash
cd ck42x-pl-arch
python3 -m venv .venv && .venv/bin/pip install -e .
.venv/bin/ck42x-pl-arch
```

## Safety

Authorized lab systems only. No keys in generated payloads. Review all artifacts before inject.
