"""Antigravity skill exporter for Agency Agents (Phase 05).

Converts Agency Agent definitions into standard Antigravity skill directories
containing SKILL.md files compatible with Antigravity and Agent-Skills hosts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .registry import AgentDefinition, SPECIALIST_REGISTRY


def export_agent_to_antigravity_skill(
    agent_def: AgentDefinition,
    output_base_dir: Path,
) -> Path:
    """Export a single agent definition as an Antigravity skill directory."""
    skill_name = f"agency-{agent_def.slug}"
    skill_dir = output_base_dir / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)

    skill_file = skill_dir / "SKILL.md"

    # YAML escape description
    desc = agent_def.description.replace('"', '\\"')

    content = f"""---
name: "{skill_name}"
description: "{desc}"
---

# {agent_def.name} ({agent_def.division.title()})

{agent_def.instructions}
"""
    skill_file.write_text(content, encoding="utf-8")
    return skill_file


def export_all_antigravity_skills(
    output_base_dir: Path,
    agents: Optional[List[AgentDefinition]] = None,
) -> Dict[str, Any]:
    """Export all registered agents as Antigravity skills."""
    if agents is None:
        agents = SPECIALIST_REGISTRY.list_agents()

    exported: List[Dict[str, str]] = []
    for agent in agents:
        skill_path = export_agent_to_antigravity_skill(agent, output_base_dir)
        exported.append({
            "name": f"agency-{agent.slug}",
            "slug": agent.slug,
            "skill_file": str(skill_path),
        })

    return {
        "output_directory": str(output_base_dir),
        "total_exported": len(exported),
        "skills": exported,
    }
