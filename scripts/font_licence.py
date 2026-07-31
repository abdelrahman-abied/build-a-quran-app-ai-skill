#!/usr/bin/env python3
"""Dump the `name` table of every font given, and say whether it grants anything.

    python3 font_licence.py assets/fonts/*.ttf
    python3 font_licence.py --quiet fonts/          # directories are walked

Exits non-zero if any font states no licence, or states a prohibition. That is
the point: put it in CI before the fonts reach a build.

The authoritative record for a typeface is usually inside the binary, not on
the page it was downloaded from. Eight of nine fonts in the project this came
from declared SIL OFL 1.1 in name ID 13. The ninth declared, in capitals, that
it must not be distributed -- and it was the only one nobody had checked.

No third-party dependencies: the sfnt tables are read by hand so this runs
anywhere Python does.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

# The IDs worth reading. 1 and 2 identify the file; the rest carry the terms.
NAME_IDS = {
    0: "Copyright",
    1: "Family",
    2: "Subfamily",
    7: "Trademark",
    13: "Licence",
    14: "Licence URL",
}

GRANT_MARKERS = (
    "open font license",
    "ofl",
    "apache license",
    "mit license",
    "gnu general public",
    "public domain",
    "creative commons",
    "cc0",
    "cc-by",
    "freely available",
    "free to use",
)

PROHIBITION_MARKERS = (
    "not for distribution",
    "not for sale",
    "not for modification",
    "not for development",
    "without written",
    "all rights reserved",
    "may not be distributed",
    "may not be redistributed",
    "do not distribute",
    "prohibited",
)

FONT_SUFFIXES = {".ttf", ".otf", ".ttc", ".otc"}


class NotAFont(Exception):
    pass


def _read_name_records(data: bytes, sfnt_offset: int = 0) -> list[tuple[int, int, int, str]]:
    """Return (platform_id, encoding_id, name_id, text) for one sfnt font."""
    if len(data) < sfnt_offset + 12:
        raise NotAFont("file is too short to hold an sfnt header")

    tag = data[sfnt_offset : sfnt_offset + 4]
    if tag == b"ttcf":
        # A collection: recurse into the first font it offers.
        num_fonts = struct.unpack_from(">I", data, sfnt_offset + 8)[0]
        if num_fonts == 0:
            raise NotAFont("font collection contains no fonts")
        first = struct.unpack_from(">I", data, sfnt_offset + 12)[0]
        return _read_name_records(data, first)
    if tag in (b"wOFF", b"wOF2"):
        raise NotAFont("WOFF is compressed; convert to TTF/OTF before checking")
    if tag not in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1"):
        raise NotAFont(f"unrecognised sfnt version {tag!r}")

    num_tables = struct.unpack_from(">H", data, sfnt_offset + 4)[0]
    name_offset = name_length = None
    for i in range(num_tables):
        rec = sfnt_offset + 12 + i * 16
        if rec + 16 > len(data):
            raise NotAFont("table directory runs past end of file")
        t, _checksum, off, length = struct.unpack_from(">4sIII", data, rec)
        if t == b"name":
            name_offset, name_length = off, length
            break
    if name_offset is None:
        raise NotAFont("no `name` table -- this font declares nothing at all")
    if name_offset + 6 > len(data):
        raise NotAFont("`name` table offset runs past end of file")

    _fmt, count, string_offset = struct.unpack_from(">HHH", data, name_offset)
    storage = name_offset + string_offset

    out: list[tuple[int, int, int, str]] = []
    for i in range(count):
        rec = name_offset + 6 + i * 12
        if rec + 12 > len(data):
            break
        plat, enc, _lang, nid, length, off = struct.unpack_from(">HHHHHH", data, rec)
        start = storage + off
        raw = data[start : start + length]
        if not raw:
            continue
        try:
            if plat == 3 or plat == 0:
                text = raw.decode("utf-16-be", errors="replace")
            elif plat == 1:
                text = raw.decode("mac_roman", errors="replace")
            else:
                text = raw.decode("latin-1", errors="replace")
        except (UnicodeDecodeError, LookupError):
            text = raw.decode("latin-1", errors="replace")
        out.append((plat, enc, nid, text.strip()))
    return out


def _best(records, name_id: int) -> str | None:
    """Prefer the Windows/Unicode record; fall back to whatever exists."""
    candidates = [r for r in records if r[2] == name_id and r[3]]
    if not candidates:
        return None
    for plat in (3, 0, 1):
        for r in candidates:
            if r[0] == plat:
                return r[3]
    return candidates[0][3]


def _verdict(licence: str | None, copyright_: str | None) -> tuple[str, str]:
    """Return (symbol, note)."""
    blob = " ".join(filter(None, (licence, copyright_))).lower()
    hits = [m for m in PROHIBITION_MARKERS if m in blob]
    # "all rights reserved" alone is weak; a named grant outranks it.
    grant = any(m in blob for m in GRANT_MARKERS)
    hard = [h for h in hits if h != "all rights reserved"]

    if hard:
        return "FORBIDS", f"states a prohibition: {hard[0]!r}"
    if grant:
        return "GRANT", "states a licence"
    if licence:
        return "OPEN", "has a licence field, but no grant this script recognises"
    if "all rights reserved" in blob:
        return "OPEN", "all rights reserved, with no grant stated"
    return "OPEN", "no licence stated in the font"


def _wrap(text: str, width: int, indent: str) -> str:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return f"\n{indent}".join(lines)


def check(path: Path, quiet: bool) -> str:
    try:
        records = _read_name_records(path.read_bytes())
    except NotAFont as exc:
        print(f"?? {path}\n     {exc}")
        return "UNREADABLE"
    except OSError as exc:
        print(f"?? {path}\n     {exc}")
        return "UNREADABLE"

    licence = _best(records, 13)
    copyright_ = _best(records, 0)
    verdict, note = _verdict(licence, copyright_)

    symbol = {"GRANT": "ok  ", "OPEN": "OPEN", "FORBIDS": "STOP"}[verdict]
    print(f"{symbol} {path.name} -- {note}")

    if not quiet:
        for nid in sorted(NAME_IDS):
            value = _best(records, nid)
            if value:
                label = f"{NAME_IDS[nid]} ({nid})"
                print(f"       {label:<16} {_wrap(value, 76, ' ' * 24)}")
        print()
    return verdict


def collect(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            out.extend(
                sorted(f for f in path.rglob("*") if f.suffix.lower() in FONT_SUFFIXES)
            )
        else:
            out.append(path)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Dump font name IDs 0/1/2/7/13/14 and judge the licence."
    )
    ap.add_argument("paths", nargs="+", help="font files or directories")
    ap.add_argument("-q", "--quiet", action="store_true", help="verdict lines only")
    args = ap.parse_args()

    fonts = collect(args.paths)
    if not fonts:
        print("no fonts found", file=sys.stderr)
        return 2

    verdicts = [check(f, args.quiet) for f in fonts]

    granted = verdicts.count("GRANT")
    open_ = verdicts.count("OPEN")
    forbids = verdicts.count("FORBIDS")
    unreadable = verdicts.count("UNREADABLE")

    print(
        f"{len(fonts)} font(s): {granted} with a stated grant, "
        f"{open_} open, {forbids} forbidding, {unreadable} unreadable."
    )
    if forbids:
        print("\nA font that forbids distribution must not be bundled. Bundling a")
        print("TTF in an app package IS distribution.")
    if open_:
        print("\nOpen is not cleared. Find the rights holder -- not the distributor --")
        print("and get the sentence in writing. See references/licensing.md.")

    return 1 if (forbids or open_ or unreadable) else 0


if __name__ == "__main__":
    raise SystemExit(main())
