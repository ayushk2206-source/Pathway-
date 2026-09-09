"""Mechanism registry: the plug-in point for new state-update rules.

To add a mechanism in a future phase: subclass ``Mechanism`` and register
it here (or import it into this module). The experiment engine, the API,
and the UI discover mechanisms exclusively through ``MECHANISM_REGISTRY``,
so nothing else needs to change.
"""

from __future__ import annotations

from typing import Dict, Type

from .base import (
    BaselineAccumulation,
    CompetitiveUpdate,
    HebbianAssociative,
    InterferenceSensitive,
    LeakyRecurrent,
    Mechanism,
    MechanismParams,
)

MECHANISM_REGISTRY: Dict[str, Type[Mechanism]] = {
    cls.name: cls
    for cls in (
        BaselineAccumulation,
        LeakyRecurrent,
        CompetitiveUpdate,
        HebbianAssociative,
        InterferenceSensitive,
    )
}

MECHANISM_INFO = {
    name: {
        "name": cls.name,
        "description": cls.description,
        "state_is_matrix": cls.state_is_matrix,
    }
    for name, cls in MECHANISM_REGISTRY.items()
}


def create_mechanism(
    name: str, params: MechanismParams, seed: int | str
) -> Mechanism:
    """Instantiate a registered mechanism by name (raises ``KeyError``)."""
    if name not in MECHANISM_REGISTRY:
        raise KeyError(
            f"unknown mechanism {name!r}; available: {sorted(MECHANISM_REGISTRY)}"
        )
    return MECHANISM_REGISTRY[name](params, seed)


__all__ = [
    "BaselineAccumulation",
    "CompetitiveUpdate",
    "HebbianAssociative",
    "InterferenceSensitive",
    "LeakyRecurrent",
    "MECHANISM_INFO",
    "MECHANISM_REGISTRY",
    "Mechanism",
    "MechanismParams",
    "create_mechanism",
]