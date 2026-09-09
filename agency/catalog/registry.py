"""Specialist agent catalog and registry for Agency Agents integration (Phase 05).

Loads, validates, and indexes curated specialist agent definitions from
the upstream msitarzewski/agency-agents catalog.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AgentDefinition:
    """Parsed representation of an Agency Agent markdown definition."""
    name: str
    slug: str
    division: str
    description: str
    vibe: str
    color: str
    emoji: str
    instructions: str
    source_file: str
    attribution: str = "msitarzewski/agency-agents (MIT License)"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "slug": self.slug,
            "division": self.division,
            "description": self.description,
            "vibe": self.vibe,
            "color": self.color,
            "emoji": self.emoji,
            "instructions": self.instructions,
            "source_file": self.source_file,
            "attribution": self.attribution,
        }


class SpecialistRegistry:
    """Registry maintaining curated specialist agent personas."""

    def __init__(self, catalog_dir: Optional[Path] = None) -> None:
        if catalog_dir is None:
            catalog_dir = Path(__file__).resolve().parent.parent / "prompts" / "curated_agents"
        self.catalog_dir = catalog_dir
        self._agents: Dict[str, AgentDefinition] = {}
        self._name_to_slug: Dict[str, str] = {}
        self._load_catalog()

    def _parse_frontmatter(self, text: str) -> tuple[Dict[str, str], str]:
        """Extract YAML-style frontmatter and markdown body."""
        pattern = r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$"
        match = re.search(pattern, text, re.DOTALL)
        if not match:
            return {}, text

        fm_text, body = match.group(1), match.group(2).strip()
        data: Dict[str, str] = {}
        for line in fm_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip("\"'")
                data[k] = v
        return data, body

    def _infer_division(self, slug: str) -> str:
        """Infer division category from slug prefix or standard mappings."""
        if slug.startswith("academic-"):
            return "academic"
        elif slug.startswith("testing-"):
            return "testing"
        elif slug.startswith("engineering-"):
            return "engineering"
        elif slug.startswith("research-"):
            return "research"
        elif slug.startswith("specialized-") or slug == "agents-orchestrator":
            return "specialized"
        return "general"

    def _load_catalog(self) -> None:
        """Scan catalog directory and parse all markdown agent definitions."""
        if not self.catalog_dir.exists():
            return

        for p in sorted(self.catalog_dir.glob("*.md")):
            slug = p.stem
            try:
                content = p.read_text(encoding="utf-8")
                fm, body = self._parse_frontmatter(content)
                name = fm.get("name", slug.replace("-", " ").title())
                division = self._infer_division(slug)

                agent_def = AgentDefinition(
                    name=name,
                    slug=slug,
                    division=division,
                    description=fm.get("description", ""),
                    vibe=fm.get("vibe", ""),
                    color=fm.get("color", "#4B5563"),
                    emoji=fm.get("emoji", "🤖"),
                    instructions=body,
                    source_file=str(p),
                )
                self._agents[slug] = agent_def
                self._name_to_slug[name.lower()] = slug
                self._name_to_slug[slug.lower()] = slug
            except Exception as e:
                # Silently preserve resilience, error logged if needed
                continue

    def get(self, identifier: str) -> Optional[AgentDefinition]:
        """Lookup an agent definition by slug or display name."""
        clean = identifier.lower().strip()
        slug = self._name_to_slug.get(clean, clean)
        return self._agents.get(slug)

    def list_agents(self) -> List[AgentDefinition]:
        """Return all registered agent definitions."""
        return list(self._agents.values())

    def list_slugs(self) -> List[str]:
        """Return all registered agent slugs."""
        return list(self._agents.keys())

    def get_by_division(self, division: str) -> List[AgentDefinition]:
        """Return all agents belonging to a specific division."""
        div_clean = division.lower().strip()
        return [a for a in self._agents.values() if a.division.lower() == div_clean]


# Global singleton instance
SPECIALIST_REGISTRY = SpecialistRegistry()
