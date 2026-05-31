from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from ck42x_pl_arch.config import Settings
from ck42x_pl_arch.emit import ducky, shell, powershell
from ck42x_pl_arch.forge import deepseek


@dataclass
class ForgeRequest:
    title: str
    goal: str
    platforms: list[str]
    handoff: bool = True
    deploy: bool = False


@dataclass
class ForgeResult:
    slug: str
    bundle_dir: Path
    files: list[str]
    risk: str
    notes: list[str]
    deploy_logs: list[str] = field(default_factory=list)
    deploy_ok: bool = False


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug[:48] or "mission").strip("-")


def _template_agents(goal: str, title: str) -> dict[str, str]:
    banner = f"# CK42X Mission: {title}\n# AUTHORIZED SYSTEMS ONLY\n# Goal: {goal}\n"
    ps1 = banner + powershell.template_agent_ps1(goal)
    sh = banner + shell.template_agent_sh(goal, platform="linux")
    mac = banner + shell.template_agent_sh(goal, platform="macos")
    return {"agent_ps1": ps1, "agent_sh_linux": sh, "agent_sh_macos": mac}


async def forge_mission(settings: Settings, request: ForgeRequest) -> ForgeResult:
    slug = slugify(request.title)
    bundle_dir = settings.output_path / slug
    bundle_dir.mkdir(parents=True, exist_ok=True)

    agents: dict[str, Any]
    risk = "low"
    notes: list[str] = ["Template agents (no DeepSeek API key configured)."]

    if settings.deepseek_api_key.strip():
        try:
            agents = await deepseek.generate_mission_bundle(
                api_key=settings.deepseek_api_key.strip(),
                model=settings.deepseek_model,
                goal=request.goal,
                title=request.title,
                platforms=request.platforms,
            )
            slug = agents.get("mission_slug") or slug
            risk = str(agents.get("risk", "medium"))
            notes = list(agents.get("notes") or [])
            bundle_dir = settings.output_path / slug
            bundle_dir.mkdir(parents=True, exist_ok=True)
        except json.JSONDecodeError as exc:
            agents = _template_agents(request.goal, request.title)
            agents["mission_slug"] = slug
            agents["mission_title"] = request.title
            notes = [
                f"DeepSeek returned invalid JSON ({exc.msg}); used template agents instead.",
                "Tip: retry forge, or remove DEEPSEEK_API_KEY to always use templates.",
            ]
        except httpx.HTTPError as exc:
            raise RuntimeError(f"DeepSeek API request failed: {exc}") from exc
    else:
        agents = _template_agents(request.goal, request.title)
        agents["mission_slug"] = slug
        agents["mission_title"] = request.title

    written: list[str] = []

    if "windows" in request.platforms:
        script_ps1 = f"agent-{slug}.ps1"
        ps1_path = bundle_dir / script_ps1
        ps1_path.write_text(str(agents.get("agent_ps1", "")), encoding="utf-8")
        written.append(script_ps1)

        txt_name = f"launch-{slug}.txt"
        ducky_body = ducky.windows_handoff(
            script_name=script_ps1,
            title=request.title,
            goal=request.goal,
            activity="CK42X PL-ARCH Handoff",
        ) if request.handoff else ducky.windows_direct(script_ps1, request.title)
        (bundle_dir / txt_name).write_text(ducky_body, encoding="utf-8")
        written.append(txt_name)

    if "linux" in request.platforms:
        sh_name = f"agent-{slug}-linux.sh"
        (bundle_dir / sh_name).write_text(str(agents.get("agent_sh_linux", "")), encoding="utf-8")
        written.append(sh_name)
        if request.handoff:
            txt = ducky.linux_handoff(f"agent-{slug}-linux.sh", request.title)
            name = f"launch-{slug}-linux.txt"
            (bundle_dir / name).write_text(txt, encoding="utf-8")
            written.append(name)

    if "macos" in request.platforms:
        mac_name = f"agent-{slug}-mac.sh"
        (bundle_dir / mac_name).write_text(
            str(agents.get("agent_sh_macos", agents.get("agent_sh_linux", ""))),
            encoding="utf-8",
        )
        written.append(mac_name)
        if request.handoff:
            txt = ducky.macos_handoff(f"agent-{slug}-mac.sh", request.title)
            name = f"launch-{slug}-mac.txt"
            (bundle_dir / name).write_text(txt, encoding="utf-8")
            written.append(name)

    manifest = {
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "slug": slug,
        "title": request.title,
        "goal": request.goal,
        "platforms": request.platforms,
        "handoff": request.handoff,
        "risk": risk,
        "notes": notes,
        "files": written,
        "flipperPath": f"/ext/ck42x-payloads/{written[0] if written else ''}",
    }
    (bundle_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    written.append("manifest.json")

    settings.last_slug = slug
    settings.save()

    result = ForgeResult(slug=slug, bundle_dir=bundle_dir, files=written, risk=risk, notes=notes)

    if request.deploy:
        from ck42x_pl_arch.flipper.deploy import deploy_mission_bundle

        deploy_out = deploy_mission_bundle(settings, bundle_dir, slug=slug)
        result.deploy_logs = deploy_out.logs
        result.deploy_ok = deploy_out.ok

    return result
