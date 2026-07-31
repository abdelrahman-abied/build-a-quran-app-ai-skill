#!/usr/bin/env python3
"""Reconcile two or three transcriptions of one print, and rule 2-of-3.

    python3 reconcile_glyphs.py mirror.json script57.json code_v1.json
    python3 reconcile_glyphs.py ours.db::ayahs::glyphs theirs.json --rulings rulings.json

Two sources cannot settle anything -- they can only disagree. A third,
independently produced, resolves it. Reconciling three transcriptions of the
1405H KFGQPC print across all 6,236 āyāt produced nine disagreeing āyāt, every
one settled 2-of-3, with no three-way split, and all three converging on 88,246
glyphs once each source's own defect was repaired.

SOURCE FORMATS

  file.json                 {"2:79": "<glyphs>", ...} or
                            [{"surah":2,"ayah":79,"glyphs":"..."}, ...]
  file.db::table::column    a SQLite table with surah/ayah columns

RULINGS (the second half of the guard)

A rulings file records which source you ruled against, per key:

    { "2:79":  {"wrong": "mirror.json", "why": "one code twice draws one word twice"} }

Every ruling is re-checked on every run. A ruling naming a key that now AGREES
fails just as loudly as an unruled disagreement -- the export was re-cut or the
ruling was wrong, and either way it must be re-read rather than left standing
as cover.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path


def _normalise(value) -> str:
    """Compare content, not formatting: a list and a spaced string are the same run."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return " ".join(str(v) for v in value)
    return " ".join(str(value).split())


def load(spec: str) -> tuple[str, dict[str, str]]:
    if "::" in spec:
        parts = spec.split("::")
        if len(parts) != 3:
            raise SystemExit(f"bad source spec {spec!r}; want file.db::table::column")
        path, table, column = parts
        con = sqlite3.connect(path)
        try:
            rows = con.execute(
                f'SELECT surah, ayah, "{column}" FROM "{table}"'
            ).fetchall()
        except sqlite3.Error as exc:
            raise SystemExit(f"{path}: {exc}")
        finally:
            con.close()
        return Path(path).name, {f"{s}:{a}": _normalise(v) for s, a, v in rows}

    with open(spec, encoding="utf-8") as fh:
        raw = json.load(fh)
    out: dict[str, str] = {}
    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, dict):
                v = v.get("glyphs") or v.get("text") or v.get("value")
            out[str(k)] = _normalise(v)
    else:
        for item in raw:
            key = f"{item['surah']}:{item['ayah']}"
            out[key] = _normalise(
                item.get("glyphs") or item.get("text") or item.get("value")
            )
    return Path(spec).name, out


def units(run: str) -> int:
    return len(run.split()) if run else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("sources", nargs="+", help="two or three sources")
    ap.add_argument("--rulings", help="JSON file of settled disagreements")
    ap.add_argument("--limit", type=int, default=40, help="rows to print")
    args = ap.parse_args()

    if not 2 <= len(args.sources) <= 3:
        raise SystemExit("give two or three sources")

    loaded = [load(s) for s in args.sources]
    names = [n for n, _ in loaded]
    maps = [m for _, m in loaded]

    print()
    for name, m in loaded:
        print(f"  {name:<28} {len(m):>6} rows, {sum(units(v) for v in m.values()):>7} units")
    print()

    if len(maps) == 2:
        print("  Two sources can only disagree. Add a third — quran.com's public")
        print("  code_v1 needs no account — or you are choosing by preference.\n")

    keys = sorted(
        set().union(*[set(m) for m in maps]),
        key=lambda k: tuple(int(p) for p in k.split(":")),
    )

    rulings = {}
    if args.rulings:
        with open(args.rulings, encoding="utf-8") as fh:
            rulings = json.load(fh)

    disagreements: list[tuple[str, list[str]]] = []
    missing: list[tuple[str, list[str]]] = []

    for key in keys:
        values = [m.get(key) for m in maps]
        absent = [names[i] for i, v in enumerate(values) if v is None]
        if absent:
            missing.append((key, absent))
            continue
        if len(set(values)) > 1:
            disagreements.append((key, values))

    if missing:
        print(f"  {len(missing)} key(s) absent from at least one source:")
        for key, absent in missing[: args.limit]:
            print(f"    {key:<10} missing from {', '.join(absent)}")
        print()

    ruled_keys = set(rulings)
    disagreeing_keys = {k for k, _ in disagreements}

    # Guard part 2: a ruling that is no longer needed is as loud as a new defect.
    stale = sorted(ruled_keys - disagreeing_keys)
    unruled: list[tuple[str, list[str], str | None]] = []

    if disagreements:
        print(f"  {len(disagreements)} disagreement(s):\n")
        for key, values in disagreements[: args.limit]:
            counts = Counter(values)
            majority, n = counts.most_common(1)[0]
            ruling = None
            if len(maps) == 3 and n == 2:
                odd = [names[i] for i, v in enumerate(values) if v != majority][0]
                ruling = odd
            elif len(maps) == 3:
                ruling = None  # three-way split

            print(f"    {key}")
            for name, value in zip(names, values):
                flag = " <- ODD" if ruling and value != majority else ""
                print(f"      {name:<26} {units(value):>4} units{flag}")

            declared = rulings.get(key, {}).get("wrong")
            if ruling and declared and declared != ruling:
                print(f"      !! ruling file says {declared!r}; 2-of-3 says {ruling!r}")
                unruled.append((key, values, ruling))
            elif declared:
                why = rulings[key].get("why", "")
                print(f"      ruled: {declared} is wrong{(' — ' + why) if why else ''}")
            elif ruling:
                print(f"      2-of-3: {ruling} is the odd one out — RULE IT AND SAY WHY")
                unruled.append((key, values, ruling))
            else:
                print("      THREE-WAY SPLIT — no majority. Ask the font.")
                unruled.append((key, values, None))
            print()

        if len(disagreements) > args.limit:
            print(f"    … {len(disagreements) - args.limit} more\n")
    else:
        print("  no disagreements\n")

    if stale:
        print(f"  {len(stale)} ruling(s) name rows that now AGREE:\n")
        for key in stale[: args.limit]:
            print(f"    {key:<10} ruled against {rulings[key].get('wrong')!r}")
        print(
            "\n  The export was re-cut or the ruling was wrong. Re-read it; do not\n"
            "  leave it standing as cover.\n"
        )

    totals = [sum(units(v) for v in m.values()) for m in maps]
    if len(set(totals)) == 1:
        print(f"  all sources converge on {totals[0]} units — that convergence is")
        print("  the result. State it at build time.\n")
    else:
        print(f"  totals differ: {dict(zip(names, totals))}")
        print("  Repair each source's OWN defect, then re-run. They should converge.\n")

    problems = len(unruled) + len(stale) + len(missing)
    if problems:
        print(f"{problems} thing(s) need a human. Nothing here may be repaired in")
        print("place — drop the row and say so, or rule it and record why.")
        return 1
    print("reconciled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
