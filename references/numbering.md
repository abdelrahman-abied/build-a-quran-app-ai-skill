# Numbering — āyāt, words, pages, lines

Four numbering systems meet in a muṣḥaf reader, and three of them are
**per-resource**. Getting one wrong does not throw. It shifts a highlight, and
the page still looks right.

---

## 1. Āyah identity — the only stable key

`(sūra, āyah)` is the one identifier that survives every edition, every layout
and every publisher. Everything durable keys on it (Law 8): bookmarks, resume
points, khatmah progress, share cards, cross-edition navigation.

The flat index (1 … 6,236) is a convenience, not an identity. It is fine inside
one database and wrong across two.

**Fixed facts, worth asserting rather than trusting:**

- 114 sūras.
- **6,236** āyāt in the Ḥafṣ/Kūfī counting the printed muṣḥaf uses.
- The per-sūra counts are in `scripts/verify_corpus.py`. Other counting
  traditions exist and give other totals; if you support one, it is a different
  dataset, not a different constant.

**The basmala is not an āyah** except at 1:1, and it appears *inside* 27:30.
Store it as a header, not as a duplicated first āyah — otherwise every count
above is off by 112 and every page break moves.

---

## 2. Word numbering — the one that bites

**Two exports from the same publisher can number the same words differently,
and nothing in either file says so.**

Measured over all 6,236 āyāt against three script exports:

| | Tanzil-style | KFGQPC script exports |
|---|---|---|
| Total words | **77,433** | **83,668** |
| Āyah-ending marker | not a word | **counted as a word** |
| `إل ياسين` (37:130) | two words | **one word** |

So the script exports are `+1` on **6,235** of 6,236 āyāt, and break that
pattern at **37:130 alone**, where the two differences cancel exactly.

### What follows, and it is not obvious

**Every real word has the same index in both systems.** A word position pasted
from one into the other lands on the same word — *until the end of an āyah*.
The divergence bites only at the last position, which is exactly where
out-of-range bugs live and exactly where they are least visible.

Practical consequences seen in real data:

- A range ending on the marker is **in bounds in one numbering and out of
  bounds in the other**. Four phrase ranges in one export ended precisely
  there — so a consumer cutting text from the range gets a phrase ending in an
  āyah number, and it is invisible to anyone whose count includes the marker.
- A range genuinely out of bounds in *both* numberings is unambiguous and
  should be dropped (Law 3), not clamped.
- Marker segments can be counted **inconsistently within one resource** — one
  segmented set carried a marker segment on no āyah, others on 339–350 of
  6,236 each, and partially within a single resource.

### The rule

**Measure the relationship. Write it in exactly one file. Route every consumer
through it.**

Give that file a name that says what it owns (`qul_word_numbering.dart`,
`word_numbering.py`, …) and make it the only place the `+1` appears. A `+1`
scattered across three call sites is a `+1` that will be applied twice
somewhere.

How to measure it yourself, per resource, in one pass:

1. Count your own words per āyah, all 6,236.
2. Count theirs.
3. Take the difference per āyah and **histogram it**. A healthy answer is one
   dominant value with a tiny, explainable tail. `{+1: 6235, 0: 1}` is a
   description of a rule. A spread is a resource you do not yet understand.
4. Name every exception explicitly, with the āyah, and say what causes it.

Do this **once per resource**, not once per publisher.

---

## 3. Word keys

Exports commonly key words as `surah:ayah:word`, one-based, e.g. `2:181:4`.

Two cautions:

- **The `word` component uses that resource's numbering**, per §2.
- **A key can be absent.** In one gloss export three of 83,665 entries were
  missing — all three the same construction, where a two-word phrase's gloss
  had been placed on the first word and no row emitted for the second. Absence
  is data. Do not fill it (Law 3, and the adab section of `SKILL.md`).

---

## 4. Page numbering — edition-local, never global

There is no such thing as "the page number of an āyah". There is only the page
number *in a given layout*.

- Store one **named column per layout** (`page`, `qcf_page`, `indopak_page`),
  each carrying the layout it came from.
- Different presses of the same tradition paginate differently by an āyah or
  two. That is the presses disagreeing, not an error.
- **604 ≠ 610.** Read the page count from the layout's own metadata.
- Gate: the page numbers form a **monotonic walk** ending on the layout's last
  page. A shifted or truncated export breaks this — which is precisely what
  makes an order-only alignment safe without a per-āyah key.

**And verify a claimed divergence with a third source before you architect
around it.** One project documented that two paginations differed at 83:35 and
built a separate column partly on that example — until reconciliation showed
83:35 was a defect in its *own* mirror and the two paginations had always
agreed there. The separate column was still right; the evidence given for it
was not.

---

## 5. Line numbering, and why a line is not an āyah

A layout export numbers lines within a page: `(page_number, line_number)`.
Fifteen lines per page in the common prints.

**A printed line usually carries the tail of one āyah and the head of the
next.** So:

- A line row cannot be keyed to a single āyah.
- Recording only "which āyah does this line start in" produces two defects that
  look unrelated and are the same defect: recitation highlighting washes a
  neighbouring āyah's words, and a tap anywhere past the boundary opens the
  wrong āyah.

**Record per-āyah segments within the line** as you build it:

```
line.segments = [ "2:6:0-41", "2:7:42-88" ]     # code-unit offsets into line.text
```

The build tool knows each word's āyah at the moment it joins the line. Nothing
downstream can recover it. Store it there or lose it.

Two implementation notes that are easy to get wrong:

- **Code units, not code points.** Glyph codepoints reach into supplementary
  planes, so a "character" is two units in UTF-16 languages. Pick one and say
  which in the field's name.
- **The separating space belongs to neither āyah.** A wash must end at its
  āyah's last letter, or the highlight bleeds one space into its neighbour on
  every line.

A `surah_name` or `basmallah` line carries **no āyah at all**, and correctly
answers nothing when pressed.

---

## 6. Glyph counts as a checksum

For a glyph edition, the total glyph count across the muṣḥaf is a single number
that catches almost everything: a dropped row, a duplicated code, a merged
word, a shifted page.

Three independent transcriptions of the 1405H print converge on **88,246
glyphs** once each one's own defect is repaired.

**State the number at build time.** A build that cannot print its glyph total
has not reconciled anything — it has copied a file.
