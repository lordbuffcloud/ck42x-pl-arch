from __future__ import annotations

import json
import re
from typing import Any

import httpx

FORGE_SYSTEM = """You are CK42X Payload Lab Architect, a security-training artifact generator for authorized labs.

Return ONLY valid JSON (no markdown fences):
{
  "mission_slug": "kebab-case-id",
  "mission_title": "short title",
  "goal_summary": "one paragraph",
  "risk": "low|medium|high",
  "notes": ["reviewer notes"],
  "agent_ps1": "complete PowerShell agent for Windows lab host",
  "agent_sh_linux": "complete bash agent for Linux",
  "agent_sh_macos": "complete bash/zsh agent for macOS"
}

Rules:
- AUTHORIZED LAB / training framing only.
- Never embed API keys or exfiltration of third-party credentials.
- Agents read DEEPSEEK_API_KEY from environment; goal from PAYLOADBAY_MISSION_GOAL env var.
- Read-only diagnostics first; block destructive, persistence, lateral movement, C2 patterns.
- Each agent under 200 lines with a tight REPL or single-shot plan loop and clear banners.
- Tailor prompts to the operator goal while enforcing safety boundaries.
"""


def _strip_json_fence(text: str) -> str:
    clean = text.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\s*", "", clean)
        clean = re.sub(r"\s*```$", "", clean)
    return clean.strip()


async def generate_mission_bundle(
    *,
    api_key: str,
    model: str,
    goal: str,
    title: str,
    platforms: list[str],
) -> dict[str, Any]:
    platform_note = ", ".join(platforms) or "windows, linux, macos"
    user = f"""Mission title: {title}
Operator goal:
{goal}

Target platforms: {platform_note}
Generate host agents for each listed platform."""

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": FORGE_SYSTEM},
            {"role": "user", "content": user},
        ],
        "temperature": 0.25,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
        )
        response.raise_for_status()
        payload = response.json()

    content = payload["choices"][0]["message"]["content"]
    return json.loads(_strip_json_fence(content))
