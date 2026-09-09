"""Tests for Agency Agents catalog, registry, and Antigravity skill export (Phase 05)."""

from pathlib import Path
import tempfile
import pytest

from agency.catalog.antigravity_export import (
    export_agent_to_antigravity_skill,
    export_all_antigravity_skills,
)
from agency.catalog.registry import SPECIALIST_REGISTRY, SpecialistRegistry


def test_catalog_loads_curated_agents():
    """Verify that curated Agency Agents are indexed in registry."""
    agents = SPECIALIST_REGISTRY.list_agents()
    assert len(agents) >= 9

    slugs = SPECIALIST_REGISTRY.list_slugs()
    assert "agents-orchestrator" in slugs
    assert "academic-statistician" in slugs
    assert "testing-reality-checker" in slugs
    assert "testing-test-results-analyzer" in slugs
    assert "research-synthesist" in slugs
    assert "engineering-ai-engineer" in slugs


def test_agent_metadata_and_attribution():
    """Verify that each agent definition includes full metadata and MIT attribution."""
    stat = SPECIALIST_REGISTRY.get("academic-statistician")
    assert stat is not None
    assert stat.name == "Statistician"
    assert stat.division == "academic"
    assert "attribution" in stat.to_dict()
    assert "msitarzewski/agency-agents" in stat.attribution
    assert len(stat.instructions) > 100
    assert "design" in stat.vibe.lower() or "data" in stat.vibe.lower()


def test_case_insensitive_and_name_lookup():
    """Verify lookup by slug, display name, and case insensitivity."""
    a1 = SPECIALIST_REGISTRY.get("Testing-Reality-Checker")
    a2 = SPECIALIST_REGISTRY.get("Reality Checker")
    assert a1 is not None
    assert a2 is not None
    assert a1.slug == a2.slug == "testing-reality-checker"


def test_antigravity_skill_export():
    """Verify Antigravity-compatible skill directory and SKILL.md generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_base = Path(tmpdir)
        agent = SPECIALIST_REGISTRY.get("testing-reality-checker")
        assert agent is not None

        skill_file = export_agent_to_antigravity_skill(agent, out_base)
        assert skill_file.exists()
        assert skill_file.name == "SKILL.md"
        assert skill_file.parent.name == "agency-testing-reality-checker"

        content = skill_file.read_text(encoding="utf-8")
        assert content.startswith("---")
        assert 'name: "agency-testing-reality-checker"' in content
        assert "description:" in content
        assert "Reality Checker" in content


def test_export_all_antigravity_skills():
    """Verify batch export of all registered agents as Antigravity skills."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_base = Path(tmpdir)
        res = export_all_antigravity_skills(out_base)
        assert res["total_exported"] >= 9
        assert len(list(out_base.glob("agency-*"))) >= 9
