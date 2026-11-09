"""Conservative FAQ matcher: never invents answers."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_THRESHOLD = 0.62
FALLBACK = (
    "I could not find a confident match in the FAQ. "
    "Please rephrase, or ask a person for help."
)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.casefold()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokens(text: str) -> set[str]:
    return {t for t in normalize(text).split() if t}


def similarity(a: str, b: str) -> float:
    """Token Jaccard with a small boost for shared character bigrams."""
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    jaccard = inter / union if union else 0.0

    def bigrams(s: str) -> set[str]:
        n = normalize(s).replace(" ", "")
        if len(n) < 2:
            return {n} if n else set()
        return {n[i : i + 2] for i in range(len(n) - 1)}

    ba, bb = bigrams(a), bigrams(b)
    if not ba or not bb:
        bigram = 0.0
    else:
        bigram = len(ba & bb) / len(ba | bb)

    # Conservative blend: prefer exact token overlap.
    return 0.7 * jaccard + 0.3 * bigram


@dataclass(frozen=True)
class FaqEntry:
    id: str
    questions: tuple[str, ...]
    answer: str


@dataclass(frozen=True)
class MatchResult:
    matched: bool
    answer: str
    score: float
    entry_id: str | None
    matched_question: str | None


def load_faq_json(path: Path | str) -> list[FaqEntry]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries: list[FaqEntry] = []
    for row in data:
        qs = row.get("questions") or []
        if isinstance(qs, str):
            qs = [qs]
        entries.append(
            FaqEntry(
                id=str(row["id"]),
                questions=tuple(str(q) for q in qs),
                answer=str(row["answer"]),
            )
        )
    return entries


def load_faq_csv(path: Path | str) -> list[FaqEntry]:
    """CSV columns: id,question,answer — multiple rows may share an id."""
    by_id: dict[str, dict] = {}
    with Path(path).open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            eid = str(row["id"]).strip()
            q = str(row["question"]).strip()
            a = str(row["answer"]).strip()
            if eid not in by_id:
                by_id[eid] = {"questions": [], "answer": a}
            by_id[eid]["questions"].append(q)
            by_id[eid]["answer"] = a
    return [
        FaqEntry(id=eid, questions=tuple(v["questions"]), answer=v["answer"])
        for eid, v in by_id.items()
    ]


def load_faq(path: Path | str) -> list[FaqEntry]:
    path = Path(path)
    if path.suffix.lower() == ".json":
        return load_faq_json(path)
    if path.suffix.lower() == ".csv":
        return load_faq_csv(path)
    raise ValueError(f"Unsupported FAQ format: {path.suffix}")


class FaqMatcher:
    def __init__(
        self,
        entries: Sequence[FaqEntry],
        threshold: float = DEFAULT_THRESHOLD,
        fallback: str = FALLBACK,
    ) -> None:
        if not entries:
            raise ValueError("FAQ must contain at least one entry")
        if not 0.0 < threshold <= 1.0:
            raise ValueError("threshold must be in (0, 1]")
        self.entries = list(entries)
        self.threshold = threshold
        self.fallback = fallback

    def match(self, query: str) -> MatchResult:
        query = (query or "").strip()
        if not query:
            return MatchResult(False, self.fallback, 0.0, None, None)

        best_score = 0.0
        best_entry: FaqEntry | None = None
        best_q: str | None = None

        for entry in self.entries:
            for q in entry.questions:
                score = similarity(query, q)
                # Exact normalized equality wins immediately.
                if normalize(query) == normalize(q):
                    return MatchResult(True, entry.answer, 1.0, entry.id, q)
                if score > best_score:
                    best_score = score
                    best_entry = entry
                    best_q = q

        if best_entry is not None and best_score >= self.threshold:
            return MatchResult(
                True, best_entry.answer, best_score, best_entry.id, best_q
            )
        return MatchResult(False, self.fallback, best_score, None, best_q)


def iter_demo_queries() -> Iterable[str]:
    return (
        "What are your opening hours?",
        "shipping times?",
        "Do you take PayPal?",
        "Can I get a refund?",
        "Where is my package?",
        "What is the weather in Dublin?",
    )
