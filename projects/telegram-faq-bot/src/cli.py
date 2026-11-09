#!/usr/bin/env python3
"""Offline interactive FAQ demo (no network, no secrets)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as `python src/cli.py` from project root or src/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.matcher import FaqMatcher, load_faq  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline FAQ matcher demo")
    parser.add_argument(
        "--faq",
        type=Path,
        default=ROOT / "data" / "faq.json",
        help="Path to FAQ JSON or CSV",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.62,
        help="Minimum similarity to accept a match (default 0.62)",
    )
    parser.add_argument(
        "--once",
        metavar="QUERY",
        help="Answer a single query and exit (for scripts/tests)",
    )
    args = parser.parse_args(argv)

    entries = load_faq(args.faq)
    matcher = FaqMatcher(entries, threshold=args.threshold)

    if args.once is not None:
        result = matcher.match(args.once)
        status = "MATCH" if result.matched else "FALLBACK"
        print(f"[{status}] score={result.score:.2f}")
        if result.entry_id:
            print(f"id={result.entry_id}")
        print(result.answer)
        return 0

    print("FAQ demo (offline). Type a question, or /quit to exit.")
    print(f"Loaded {len(entries)} entries from {args.faq}")
    print(f"Threshold={args.threshold}")
    print()

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in {"/quit", "/exit", "quit", "exit"}:
            break
        if line == "/reload":
            entries = load_faq(args.faq)
            matcher = FaqMatcher(entries, threshold=args.threshold)
            print(f"Reloaded {len(entries)} entries.")
            continue
        result = matcher.match(line)
        tag = "MATCH" if result.matched else "FALLBACK"
        print(f"[{tag} score={result.score:.2f}] {result.answer}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
