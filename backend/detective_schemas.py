"""Pydantic schemas for Detective API (Phase 07)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QuestionParseRequest(BaseModel):
    question: str = Field(..., description="Natural language question to parse deterministically")


class InvestigateRequest(BaseModel):
    experiment_id: str = Field(..., description="ID of the experiment being investigated")
    question: str = Field(..., description="User question (e.g. 'Why did memory obj_A weaken?')")
    target_memory: Optional[str] = Field(None, description="Optional explicit target memory ID or concept")
    execute_tests: bool = Field(True, description="Whether to automatically design and run counterfactual tests")


class HypothesesRequest(BaseModel):
    experiment_id: str = Field(..., description="Experiment ID")
    target_memory: str = Field(..., description="Target memory ID or concept label")
    intent: Optional[str] = Field(None, description="Optional explicit question intent")


class ExecuteTestRequest(BaseModel):
    experiment_id: str = Field(..., description="Experiment ID")
    hypothesis_id: str = Field(..., description="Target candidate hypothesis ID")
    test_design: Dict[str, Any] = Field(..., description="TestDesign specification dictionary")


class SaveNotebookRequest(BaseModel):
    experiment_id: str = Field(..., description="Experiment ID")
    title: str = Field(..., description="Entry title")
    content: str = Field(..., description="Findings or hypothesis notes")
    author: str = Field("Researcher", description="Author signature")
    linked_investigation_id: Optional[str] = Field(None, description="Optional linked investigation ID")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")


class ReproduceRequest(BaseModel):
    target_experiment_id: Optional[str] = Field(None, description="Optional target experiment to reproduce on")
