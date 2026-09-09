"""In-memory Cache and Persistence Store for Phase 08."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from .models import CascadeMap, MemoryGenome


class GenomeStore:
    """Provides memoized caching for computationally intensive Genomes and Cascade replays."""

    _genome_cache: Dict[Tuple[str, str], MemoryGenome] = {}
    _cascade_cache: Dict[Tuple[str, str, str, float], CascadeMap] = {}

    @classmethod
    def get_genome(cls, experiment_id: str, memory_id: str) -> Optional[MemoryGenome]:
        return cls._genome_cache.get((experiment_id, memory_id))

    @classmethod
    def put_genome(cls, experiment_id: str, memory_id: str, genome: MemoryGenome) -> None:
        cls._genome_cache[(experiment_id, memory_id)] = genome

    @classmethod
    def get_cascade(
        cls, experiment_id: str, memory_id: str, intervention: str, dose: float
    ) -> Optional[CascadeMap]:
        return cls._cascade_cache.get((experiment_id, memory_id, intervention, round(dose, 2)))

    @classmethod
    def put_cascade(
        cls, experiment_id: str, memory_id: str, intervention: str, dose: float, cascade: CascadeMap
    ) -> None:
        cls._cascade_cache[(experiment_id, memory_id, intervention, round(dose, 2))] = cascade

    @classmethod
    def clear(cls) -> None:
        cls._genome_cache.clear()
        cls._cascade_cache.clear()
