"""Benchmark adapters: ingest established benchmarks, add the substrate lens."""

from __future__ import annotations

from typing import List

from .arc_agi_2.adapter import ArcAgi2Adapter
from .base import AdapterManifest, BenchmarkAdapter, LabelRecord, RawItem, deterministic_order
from .gpqa_diamond.adapter import GpqaDiamondAdapter

ADAPTERS = {
    "arc-agi-2": ArcAgi2Adapter,
    "gpqa-diamond": GpqaDiamondAdapter,
}


def get_adapter(benchmark_id: str) -> BenchmarkAdapter:
    if benchmark_id not in ADAPTERS:
        raise KeyError(f"unknown benchmark {benchmark_id!r}; have {sorted(ADAPTERS)}")
    return ADAPTERS[benchmark_id]()


def available() -> List[str]:
    return sorted(ADAPTERS)


__all__ = [
    "BenchmarkAdapter", "AdapterManifest", "LabelRecord", "RawItem",
    "deterministic_order", "ADAPTERS", "get_adapter", "available",
]
