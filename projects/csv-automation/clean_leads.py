#!/usr/bin/env python3
"""Clean / merge / dedupe a CSV of leads. Demo with fake sample data only."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


PHONE_DIGITS = re.compile(r"\D+")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class Lead:
    name: str
    email: str
    phone: str
    source: str
    city: str

    @property
    def dedupe_key(self) -> str:
        if self.email:
            return f"email:{self.email}"
        if self.phone:
            return f"phone:{self.phone}"
        return f"name:{self.name.casefold()}"


def normalize_phone(raw: str) -> str:
    """Keep digits only; preserve leading + as international marker in output E.164-ish."""
    raw = (raw or "").strip()
    if not raw:
        return ""
    keep_plus = raw.startswith("+")
    digits = PHONE_DIGITS.sub("", raw)
    if not digits:
        return ""
    return f"+{digits}" if keep_plus else digits


def normalize_email(raw: str) -> str:
    email = (raw or "").strip().casefold()
    if not email:
        return ""
    return email if EMAIL_RE.match(email) else ""


def normalize_name(raw: str) -> str:
    parts = [p for p in re.split(r"\s+", (raw or "").strip()) if p]
    return " ".join(p[:1].upper() + p[1:].lower() if len(p) > 1 else p.upper() for p in parts)


def read_leads(path: Path) -> list[Lead]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"name", "email", "phone", "source", "city"}
        if not reader.fieldnames or required - set(reader.fieldnames):
            missing = sorted(required - set(reader.fieldnames or []))
            raise ValueError(f"CSV missing columns: {', '.join(missing)}")
        leads: list[Lead] = []
        for row in reader:
            leads.append(
                Lead(
                    name=normalize_name(row.get("name", "")),
                    email=normalize_email(row.get("email", "")),
                    phone=normalize_phone(row.get("phone", "")),
                    source=(row.get("source") or "").strip().casefold(),
                    city=normalize_name(row.get("city", "")),
                )
            )
        return leads


def merge_leads(batches: list[list[Lead]]) -> list[Lead]:
    merged: list[Lead] = []
    seen: dict[str, int] = {}
    for batch in batches:
        for lead in batch:
            if not lead.name and not lead.email and not lead.phone:
                continue
            key = lead.dedupe_key
            if key in seen:
                existing = merged[seen[key]]
                # Prefer non-empty fields from the newer row without inventing data
                if not existing.email and lead.email:
                    existing.email = lead.email
                if not existing.phone and lead.phone:
                    existing.phone = lead.phone
                if not existing.city and lead.city:
                    existing.city = lead.city
                if lead.source and lead.source not in existing.source.split("|"):
                    existing.source = (
                        f"{existing.source}|{lead.source}" if existing.source else lead.source
                    )
                continue
            seen[key] = len(merged)
            merged.append(lead)
    return merged


def write_leads(path: Path, leads: list[Lead]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["name", "email", "phone", "source", "city"])
        writer.writeheader()
        for lead in leads:
            writer.writerow(
                {
                    "name": lead.name,
                    "email": lead.email,
                    "phone": lead.phone,
                    "source": lead.source,
                    "city": lead.city,
                }
            )


def write_report(path: Path, raw_count: int, clean: list[Lead], dropped_empty: int) -> None:
    by_source = Counter(lead.source.split("|")[0] or "unknown" for lead in clean)
    with_phone = sum(1 for lead in clean if lead.phone)
    with_email = sum(1 for lead in clean if lead.email)
    lines = [
        "# Leads cleanup report",
        "",
        f"- Raw rows read: {raw_count}",
        f"- Empty rows dropped: {dropped_empty}",
        f"- Unique leads after dedupe: {len(clean)}",
        f"- With email: {with_email}",
        f"- With phone: {with_phone}",
        "",
        "## By source",
    ]
    for source, count in sorted(by_source.items()):
        lines.append(f"- {source}: {count}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean, merge and dedupe lead CSVs (demo)")
    parser.add_argument("inputs", nargs="+", type=Path, help="One or more input CSV files")
    parser.add_argument("-o", "--output", type=Path, default=Path("cleaned_leads.csv"))
    parser.add_argument("-r", "--report", type=Path, default=Path("cleanup_report.md"))
    args = parser.parse_args(argv)

    batches: list[list[Lead]] = []
    raw_count = 0
    empty_dropped = 0
    for path in args.inputs:
        batch = read_leads(path)
        raw_count += len(batch)
        kept = []
        for lead in batch:
            if not lead.name and not lead.email and not lead.phone:
                empty_dropped += 1
            else:
                kept.append(lead)
        batches.append(kept)

    clean = merge_leads(batches)
    write_leads(args.output, clean)
    write_report(args.report, raw_count, clean, empty_dropped)
    print(f"Wrote {len(clean)} leads -> {args.output}")
    print(f"Report -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
