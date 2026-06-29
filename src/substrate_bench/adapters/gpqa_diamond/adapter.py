"""GPQA Diamond adapter: graduate science MCQs.

GPQA items carry their own gold answer (the correct option). The lab adds the
substrate label: most items are knowledge/conceptual reasoning (`language`), a
minority reduce to a closed-form calculation (`exact_computation`) or dynamics
(`simulation`). See labels.json / the rubric.

GATED + contamination-sensitive: content is fetched with the user's licensed HF
token and cached (gitignored); never committed. Item ids here are content hashes,
so committing labels leaks nothing.
"""

from __future__ import annotations

import csv
import hashlib
import os
import urllib.request
from pathlib import Path
from typing import Iterator, List, Optional

from ..base import BenchmarkAdapter, LabelRecord, RawItem, deterministic_order

_CSV_URL = "https://huggingface.co/datasets/Idavidrein/gpqa/resolve/main/gpqa_diamond.csv"
_LETTERS = ["A", "B", "C", "D"]


def _token() -> str:
    tok = os.environ.get("HUGGING_FACE_TOKEN") or os.environ.get("HF_TOKEN")
    if not tok:
        raise RuntimeError(
            "GPQA is gated: set HUGGING_FACE_TOKEN (or HF_TOKEN) after accepting the "
            "dataset licence at https://huggingface.co/datasets/Idavidrein/gpqa"
        )
    return tok


def _stable_id(question: str) -> str:
    return "q" + hashlib.sha1(question.strip().encode("utf-8")).hexdigest()[:12]


class GpqaDiamondAdapter(BenchmarkAdapter):
    def __init__(self, root=None):
        super().__init__(root or Path(__file__).resolve().parent)
        self.csv_path = self.cache_dir / "gpqa_diamond.csv"

    def fetch(self, limit: Optional[int] = None) -> int:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(
            _CSV_URL, headers={"Authorization": f"Bearer {_token()}", "User-Agent": "substrate-bench-adapter"}
        )
        with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310 (HF, authenticated)
            self.csv_path.write_bytes(r.read())
        return sum(1 for _ in self.iter_items())

    def iter_items(self) -> Iterator[RawItem]:
        if not self.csv_path.exists():
            return
        with self.csv_path.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                q = (row.get("Question") or "").strip()
                if not q:
                    continue
                yield RawItem(item_id=_stable_id(q), content=row)

    def to_task_dict(self, raw: RawItem, label: LabelRecord) -> dict:
        row = raw.content
        question = row["Question"].strip()
        correct = row["Correct Answer"].strip()
        options = [correct] + [row[f"Incorrect Answer {i}"].strip() for i in (1, 2, 3)]
        order = deterministic_order(raw.item_id, 4)  # reproducible placement, no PRNG
        placed = [options[i] for i in order]
        gold_letter = _LETTERS[placed.index(correct)]

        body = [question, "", "Options:"]
        for letter, opt in zip(_LETTERS, placed):
            body.append(f"{letter}) {opt}")
        body.append("\nRespond with the single letter (A, B, C, or D) of the correct option.")
        prompt = "\n".join(body)

        return {
            "id": f"gpqa-{raw.item_id}",
            "category": label.gold_substrate[0],
            "prompt": prompt,
            "gold_substrate": label.gold_substrate,
            "checker": {"type": "exact_label", "answer": gold_letter, "labels": list(_LETTERS)},
            "difficulty": label.difficulty,
            "rationale": label.rationale,
            "provenance": "benchmark",
            "source": {
                "benchmark": "gpqa-diamond",
                "item_id": raw.item_id,
                "answer_provenance": "benchmark",
                "label_provenance": label.provenance,
            },
        }
