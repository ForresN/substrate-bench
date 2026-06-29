"""BenchmarkAdapter interface (the frontier pivot).

An adapter ingests an external benchmark's items into substrate-bench's task
schema, **carrying the benchmark's own gold ANSWER**, and the lab adds the
substrate-selection layer (the `gold_substrate` label) on top via a documented
rubric (see ``SUBSTRATE_RUBRIC.md``) recorded in the adapter's ``labels.json``.

Integrity:
  * gold ANSWER provenance = the benchmark; gold SUBSTRATE provenance = rubric /
    human_review. Never a solver.
  * Raw benchmark data is fetched/cached at runtime (cache dirs are gitignored);
    data is never vendored where the licence forbids. Only our labels + the
    manifest are committed.
  * Materialised tasks are scored through the same prompt-only view, planted-gold,
    declaration and two-level scoring machinery as the smoke tier.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from ..schema import Task, validate_task


@dataclass(frozen=True)
class AdapterManifest:
    benchmark_id: str
    name: str
    version: str
    licence: str
    source_url: str
    citation: str
    redistributable: bool
    contamination_note: str
    fetch_instructions: str

    @classmethod
    def load(cls, path: str | Path) -> "AdapterManifest":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        fields = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in fields})


@dataclass
class LabelRecord:
    """The lab's substrate label for one benchmark item (committed in labels.json)."""

    item_id: str
    gold_substrate: List[str]
    difficulty: int
    rationale: str = ""
    provenance: str = "rubric"  # "rubric" | "human_review"
    status: str = "labelled"    # "labelled" | "needs_human_review"

    @classmethod
    def from_dict(cls, item_id: str, d: dict) -> "LabelRecord":
        return cls(
            item_id=item_id,
            gold_substrate=list(d["gold_substrate"]),
            difficulty=int(d["difficulty"]),
            rationale=d.get("rationale", ""),
            provenance=d.get("provenance", "rubric"),
            status=d.get("status", "labelled"),
        )


@dataclass
class RawItem:
    """A benchmark item straight from cache: an id + opaque content."""

    item_id: str
    content: dict


def deterministic_order(item_id: str, n: int) -> List[int]:
    """A reproducible permutation of range(n), seeded by the item id (no PRNG).

    Used to place multiple-choice options without a random seed so runs are
    byte-identical.
    """
    def key(i: int) -> str:
        return hashlib.sha256(f"{item_id}:{i}".encode("utf-8")).hexdigest()

    return sorted(range(n), key=key)


class BenchmarkAdapter(ABC):
    """Ingest one external benchmark into substrate-bench tasks."""

    def __init__(self, root: str | Path):
        self.dir = Path(root)
        self.manifest = AdapterManifest.load(self.dir / "manifest.json")
        self.cache_dir = self.dir / "cache"

    # --- data acquisition (respect the licence) ---------------------------- #
    @abstractmethod
    def fetch(self, limit: Optional[int] = None) -> int:
        """Populate the (gitignored) cache from the benchmark source. Returns count."""

    @abstractmethod
    def iter_items(self) -> Iterator[RawItem]:
        """Yield raw items from cache."""

    # --- ingest into the substrate-bench schema ---------------------------- #
    @abstractmethod
    def to_task_dict(self, raw: RawItem, label: LabelRecord) -> dict:
        """Map a raw item + its substrate label into a task JSON dict, carrying
        the benchmark's own gold answer."""

    # --- labels ------------------------------------------------------------ #
    def load_labels(self) -> Dict[str, LabelRecord]:
        path = self.dir / "labels.json"
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return {k: LabelRecord.from_dict(k, v) for k, v in data.get("items", {}).items()}

    def build_tasks(self, include_needs_review: bool = False) -> List[Task]:
        """Materialise validated Tasks for every cached item that has a label.

        Items flagged `needs_human_review` are excluded from the scored slice by
        default (we don't guess)."""
        labels = self.load_labels()
        tasks: List[Task] = []
        for raw in self.iter_items():
            label = labels.get(raw.item_id)
            if label is None:
                continue
            if label.status != "labelled" and not include_needs_review:
                continue
            tasks.append(validate_task(self.to_task_dict(raw, label)))
        return tasks
