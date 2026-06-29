"""ARC-AGI-2 adapter: abstract grid induction -> strategy `search`.

ARC items carry their own gold output grid (the benchmark's answer). The lab adds
the substrate label: inducing the transformation from worked examples is a
hypothesis-space search, not verbal pattern-matching. See labels.json / the rubric.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Iterator, List, Optional

from ..base import BenchmarkAdapter, LabelRecord, RawItem

_API = "https://api.github.com/repos/arcprize/ARC-AGI-2/contents/data/evaluation?per_page=100"
_RAW = "https://raw.githubusercontent.com/arcprize/ARC-AGI-2/main/data/evaluation/{name}"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "substrate-bench-adapter"})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310 (public GitHub)
        return r.read()


def _render_grid(grid: List[List[int]]) -> str:
    return "\n".join(" ".join(str(c) for c in row) for row in grid)


class ArcAgi2Adapter(BenchmarkAdapter):
    def __init__(self, root=None):
        super().__init__(root or Path(__file__).resolve().parent)

    def fetch(self, limit: Optional[int] = None) -> int:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        listing = json.loads(_get(_API).decode("utf-8"))
        names = sorted(x["name"] for x in listing if x["name"].endswith(".json"))
        if limit is not None:
            names = names[:limit]
        n = 0
        for name in names:
            dest = self.cache_dir / name
            if not dest.exists():
                dest.write_bytes(_get(_RAW.format(name=name)))
            n += 1
        return n

    def iter_items(self) -> Iterator[RawItem]:
        if not self.cache_dir.is_dir():
            return
        for p in sorted(self.cache_dir.glob("*.json")):
            yield RawItem(item_id=p.stem, content=json.loads(p.read_text(encoding="utf-8")))

    def to_task_dict(self, raw: RawItem, label: LabelRecord) -> dict:
        c = raw.content
        test = c["test"][0]
        parts = [
            "You are shown input/output grid pairs that all follow one hidden "
            "transformation rule. Infer the rule from the examples and produce the "
            "output grid for the test input. Grids are 2D arrays of integers 0-9.\n",
        ]
        for i, pair in enumerate(c["train"], 1):
            parts.append(f"Example {i} input:\n{_render_grid(pair['input'])}")
            parts.append(f"Example {i} output:\n{_render_grid(pair['output'])}\n")
        parts.append(f"Test input:\n{_render_grid(test['input'])}\n")
        parts.append("Return ONLY the output grid as a JSON 2D array of integers.")
        prompt = "\n".join(parts)

        return {
            "id": f"arc-{raw.item_id}",
            "category": label.gold_substrate[0],
            "prompt": prompt,
            "gold_substrate": label.gold_substrate,
            "checker": {"type": "grid_match", "answer": test["output"]},
            "difficulty": label.difficulty,
            "rationale": label.rationale,
            "provenance": "benchmark",
            "source": {
                "benchmark": "arc-agi-2",
                "item_id": raw.item_id,
                "answer_provenance": "benchmark",
                "label_provenance": label.provenance,
            },
        }
