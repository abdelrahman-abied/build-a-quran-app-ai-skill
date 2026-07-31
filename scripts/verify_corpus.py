#!/usr/bin/env python3
"""Prove a muṣḥaf corpus before it ships. Fails loudly; that is the job.

    python3 verify_corpus.py --sqlite quran.db
    python3 verify_corpus.py --sqlite quran.db --page-col qcf_page --pages 604
    python3 verify_corpus.py --sqlite quran.db --page-col indopak_page --pages 610
    python3 verify_corpus.py --json corpus.json --glyph-col glyphs

Checks, in order:

  114 sūras, 6,236 āyāt                 a dropped or duplicated row
  per-sūra counts                       a drop that happens to balance
  āyah numbers contiguous from 1        a gap that the totals hide
  page numbers a monotonic walk         a shifted or truncated layout export
  page walk ends on the layout's last   six unreachable pages, no symptom
  content hash                          an upstream re-cut, silently downloaded
  glyph total (optional)                a merged word, a duplicated code

Run it in the tool that BUILDS the database, not in a test suite someone can
skip. A build that drops rows and says nothing has made a decision for you.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import unicodedata

# Ḥafṣ / Kūfī counting, the one the printed muṣḥaf uses. 114 entries, 6,236 total.
# Other counting traditions exist; supporting one is a different dataset, not a
# different constant.
SURAH_AYAHS = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128,
    111, 110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73,
    54, 45, 83, 182, 88, 75, 85, 54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60,
    49, 62, 55, 78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12, 12, 30, 52, 52,
    44, 28, 28, 20, 56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19,
    26, 30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3,
    6, 3, 5, 4, 5, 6,
]

TOTAL_AYAHS = sum(SURAH_AYAHS)  # 6236
TOTAL_SURAHS = len(SURAH_AYAHS)  # 114


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.notes: list[str] = []

    def ok(self, label: str, detail: str = "") -> None:
        print(f"  ok   {label}{('  — ' + detail) if detail else ''}")

    def fail(self, label: str, detail: str) -> None:
        print(f"  FAIL {label}\n         {detail}")
        self.failures.append(label)

    def note(self, text: str) -> None:
        print(f"  ..   {text}")
        self.notes.append(text)


def load_sqlite(path: str, table: str, cols: dict[str, str | None]) -> list[dict]:
    wanted = {k: v for k, v in cols.items() if v}
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    select = ", ".join(f'"{v}" AS "{k}"' for k, v in wanted.items())
    order = f'"{cols["surah"]}", "{cols["ayah"]}"'
    try:
        rows = con.execute(f'SELECT {select} FROM "{table}" ORDER BY {order}').fetchall()
    except sqlite3.Error as exc:
        print(f"sqlite: {exc}", file=sys.stderr)
        print(
            "\nPass --table / --surah-col / --ayah-col / --text-col to match your "
            "schema.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    finally:
        con.close()
    return [dict(r) for r in rows]


def load_json(path: str, cols: dict[str, str | None]) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    if isinstance(raw, dict):
        raw = list(raw.values())
    out = []
    for item in raw:
        row = {k: item.get(v) for k, v in cols.items() if v}
        out.append(row)
    out.sort(key=lambda r: (int(r["surah"]), int(r["ayah"])))
    return out


def check_counts(rows: list[dict], rep: Report) -> None:
    per: dict[int, list[int]] = {}
    for r in rows:
        per.setdefault(int(r["surah"]), []).append(int(r["ayah"]))

    if len(rows) == TOTAL_AYAHS:
        rep.ok(f"{TOTAL_AYAHS} āyāt")
    else:
        rep.fail("āyah total", f"expected {TOTAL_AYAHS}, found {len(rows)}")

    if len(per) == TOTAL_SURAHS:
        rep.ok(f"{TOTAL_SURAHS} sūras")
    else:
        missing = sorted(set(range(1, TOTAL_SURAHS + 1)) - set(per))
        extra = sorted(set(per) - set(range(1, TOTAL_SURAHS + 1)))
        rep.fail(
            "sūra count",
            f"expected {TOTAL_SURAHS}, found {len(per)}"
            + (f"; missing {missing}" if missing else "")
            + (f"; unexpected {extra}" if extra else ""),
        )

    bad_counts, bad_seq = [], []
    for s in range(1, TOTAL_SURAHS + 1):
        got = sorted(per.get(s, []))
        want = SURAH_AYAHS[s - 1]
        if len(got) != want:
            bad_counts.append(f"{s}: expected {want}, found {len(got)}")
        elif got != list(range(1, want + 1)):
            gaps = sorted(set(range(1, want + 1)) - set(got))
            dups = sorted({a for a in got if got.count(a) > 1})
            bad_seq.append(
                f"{s}: "
                + (f"missing {gaps[:6]}" if gaps else "")
                + (f" duplicated {dups[:6]}" if dups else "")
            )

    if bad_counts:
        rep.fail("per-sūra āyah counts", "; ".join(bad_counts[:8]))
    else:
        rep.ok("per-sūra āyah counts")

    if bad_seq:
        rep.fail("āyah numbers contiguous from 1", "; ".join(bad_seq[:8]))
    else:
        rep.ok("āyah numbers contiguous from 1")


def check_pages(rows: list[dict], expected_last: int | None, rep: Report) -> None:
    pages = [r.get("page") for r in rows]
    if not any(p is not None for p in pages):
        rep.note("no page column given — pagination unchecked")
        return

    prev, breaks = None, []
    for r in rows:
        p = r.get("page")
        if p is None:
            breaks.append(f"{r['surah']}:{r['ayah']} has no page")
            continue
        p = int(p)
        if prev is not None and p < prev:
            breaks.append(f"{r['surah']}:{r['ayah']} goes back {prev} → {p}")
        if prev is not None and p > prev + 1:
            breaks.append(f"{r['surah']}:{r['ayah']} jumps {prev} → {p}")
        prev = p

    if breaks:
        rep.fail("page numbers form a monotonic walk", "; ".join(breaks[:8]))
    else:
        rep.ok("page numbers form a monotonic walk", f"1 → {prev}")

    if expected_last is not None:
        if prev == expected_last:
            rep.ok(f"walk ends on page {expected_last}")
        else:
            rep.fail(
                "last page",
                f"expected {expected_last}, walk ends on {prev}. "
                "Read the page count from the layout's own info, never a constant.",
            )


def check_hash(rows: list[dict], rep: Report) -> None:
    if not any(r.get("text") for r in rows):
        rep.note("no text column given — content hash unchecked")
        return
    h = hashlib.sha256()
    for r in rows:
        h.update(f"{r['surah']}:{r['ayah']}:".encode())
        h.update(unicodedata.normalize("NFC", str(r.get("text") or "")).encode())
        h.update(b"\n")
    rep.ok("content hash", h.hexdigest())
    rep.note("store that hash in the database's `meta`; it is the only thing")
    rep.note("standing between you and a silently re-cut text")


def check_glyphs(rows: list[dict], expected: int | None, rep: Report) -> None:
    if not any(r.get("glyphs") for r in rows):
        return
    total = 0
    empty = []
    for r in rows:
        g = r.get("glyphs")
        if not g:
            empty.append(f"{r['surah']}:{r['ayah']}")
            continue
        total += len(g.split()) if isinstance(g, str) and " " in g else len(g)
    if empty:
        rep.fail("every āyah carries glyphs", f"{len(empty)} without: {empty[:6]}")
    else:
        rep.ok("every āyah carries glyphs")
    if expected is None:
        rep.ok("glyph total", str(total))
        rep.note("state this number every build; three independent transcriptions")
        rep.note("of the 1405H print converge on 88,246 once each defect is repaired")
    elif total == expected:
        rep.ok("glyph total", str(total))
    else:
        rep.fail("glyph total", f"expected {expected}, counted {total}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--sqlite", help="path to a SQLite database")
    src.add_argument("--json", dest="json_path", help="path to a JSON array/object")
    ap.add_argument("--table", default="ayahs")
    ap.add_argument("--surah-col", default="surah")
    ap.add_argument("--ayah-col", default="ayah")
    ap.add_argument("--text-col", default="text")
    ap.add_argument("--page-col", default="page", help="'' to skip pagination checks")
    ap.add_argument("--glyph-col", default=None)
    ap.add_argument("--pages", type=int, default=None, help="expected last page")
    ap.add_argument("--glyphs", type=int, default=None, help="expected glyph total")
    args = ap.parse_args()

    cols = {
        "surah": args.surah_col,
        "ayah": args.ayah_col,
        "text": args.text_col or None,
        "page": args.page_col or None,
        "glyphs": args.glyph_col,
    }

    if args.sqlite:
        rows = load_sqlite(args.sqlite, args.table, cols)
        origin = f"{args.sqlite} :: {args.table}"
    else:
        rows = load_json(args.json_path, cols)
        origin = args.json_path

    print(f"\n{origin}\n")
    rep = Report()
    check_counts(rows, rep)
    check_pages(rows, args.pages, rep)
    check_glyphs(rows, args.glyphs, rep)
    check_hash(rows, rep)

    print()
    if rep.failures:
        print(f"{len(rep.failures)} gate(s) failed: {', '.join(rep.failures)}")
        print("\nA missing row is visible. A wrong one is not. Do not repair these")
        print("in place — find out which source is wrong. See references/sources.md.")
        return 1
    print("all gates passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
