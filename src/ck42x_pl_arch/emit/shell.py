from __future__ import annotations


def template_agent_sh(goal: str, *, platform: str) -> str:
    safe = goal.replace("'", "'\\''")
    return f"""#!/usr/bin/env bash
# CK42X PL-ARCH — {platform} agent
set -euo pipefail
export PAYLOADBAY_MISSION_GOAL='{safe}'

echo ""
echo " CK42X Payload Lab Architect — Mission Agent"
echo " AUTHORIZED SYSTEMS ONLY"
echo ""
echo " Goal: $PAYLOADBAY_MISSION_GOAL"
echo ""

if [ -z "${{DEEPSEEK_API_KEY:-}}" ]; then
  echo " Set DEEPSEEK_API_KEY for AI-assisted planning."
  pwd
  command -v git >/dev/null 2>&1 && git status -sb || true
  read -r -p "Press Enter to exit "
  exit 0
fi

curl -fsS https://api.deepseek.com/chat/completions \\
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d "{{\\"model\\":\\"deepseek-chat\\",\\"messages\\":[{{\\"role\\":\\"system\\",\\"content\\":\\"Cautious lab assistant. Read-only commands.\\"}},{{\\"role\\":\\"user\\",\\"content\\":\\"$PAYLOADBAY_MISSION_GOAL\\"}}]}}" \\
  | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])" 2>/dev/null \\
  || echo " (install python3 for JSON pretty-print or inspect raw response)"

read -r -p "Press Enter to exit "
"""
