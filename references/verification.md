# Verification

Layout correctness cannot be eyeballed. Every defect worth fearing renders
beautifully, so every one of them has to be **counted**.

This file is the list of gates, each with the failure it catches.

---

## 1. Build-time gates on the data

Run these in the tool that builds the database, and **fail the build**, not a
test suite someone can skip.

| Gate | Catches |
|---|---|
| 114 sūras, **6,236** āyāt | a dropped or duplicated row anywhere |
| Per-sūra āyah counts against the known table | a drop that happens to balance |
| Content hash of the whole text, stored in `meta` | an upstream re-cut, silently downloaded |
| Basmala rows are headers, not āyāt | an off-by-112 that moves every page break |
| Sajda positions came from the source's metadata | a hand-transcribed list, which is always eventually wrong |
| Page numbers form a **monotonic walk**, ending on the layout's last page | a shifted or truncated layout export — this is what makes order-only alignment safe without a per-āyah key |
| Page count read from the layout's own `info` | a hardcoded 604 that hides six pages of a 610-page print |
| **Glyph total** stated explicitly (88,246 for the 1405H print) | a merged word, a duplicated code, a dropped row |
| Word boundaries **tile** the text exactly — no over-run, no gap | a line beginning mid-word |
| Every page of every edition resolves to real words | a page that renders empty for one user and is never reported |
| Every āyah is reachable in every edition | an āyah stranded off the end of a pager |
| **Count of rows dropped**, printed every run | the silent absorption of an upstream defect |

That last row is not optional. A build that drops rows and says nothing has
made a decision on your behalf.

## 2. The three-part guard on an import

When a second source arrives for data you already ship (Law 10):

1. **Every row is compared.** An unruled disagreement stops the build and names
   the āyah.
2. **A ruling is a claim, and the claim is checked.** A ruling naming āyāt that
   now *agree* stops the build just as loudly — the export was re-cut or the
   ruling was wrong. Same for a ruling naming a row the export no longer has.
3. **A ruling never imports the other file's answer.** Take only the narrow
   thing the second source is authoritative for, and assert it tiles your own
   data exactly.

Make repairs **self-asserting**: each names the index it edits *and the byte it
expects to find there*, so an upstream fix breaks the build instead of being
silently re-broken.

---

## 3. Rendering tests

### Goldens

Per edition, at minimum:

- **a sparse page** (al-Fātiḥa) — catches a fit that never reaches the bottom,
- **a dense page** — catches marks touching the line below,
- **a page with a sūra header** — catches furniture stealing a line slot,
- **both text directions** if the app is bilingual.

A golden that covers only the average page covers the case that was never going
to break.

### The test that a one-āyah fixture cannot pass

**When asserting that a target āyah is marked, assert that the others are
not.**

A fixture containing a single āyah proves the mark lands *somewhere*. It cannot
see a wash that bleeds into a neighbour, and bleeding into a neighbour is the
defect that actually happens — because a printed line usually carries the tail
of one āyah and the head of the next.

### Taps, pressed at real coordinates

The mapping from a touch point to an āyah is the hard part, so test the
mapping, not the resolver.

**Press real coordinates on a laid-out page.** On a line carrying the tail of
one āyah and the head of the next:

- pressing its **right** end (RTL start) must answer the first āyah,
- pressing its **left** end must answer the second.

Write these against the *old* code first and watch them fail. A test that
passes on the broken implementation is testing something else.

Also assert the fallback: an asset with no segment data answers the line's
first āyah — the old behaviour, not an exception.

### Fit caching

- The cached fit is **identical** to the synchronous one, probe for probe.
- Warming neighbours produces fits under the **exact keys** the build asks for.
  A page turn that mints a new key means the warm-up was measuring a different
  page than the render will draw — self-consistent, never visibly wrong, and
  entirely wasted.
- The warm-up counts neighbours against **the current edition's** page count,
  not a constant.

---

## 4. The device pass

Emulators lie about fonts, GPUs and networks. List what was actually checked,
on real hardware, and name what was not.

- [ ] Fonts download over a **real** network, per edition, from each origin.
- [ ] Cache **survives relaunch**; a second open costs no network.
- [ ] Airplane-mode cut mid-download → clean fallback, no truncated file on
      disk, resume works.
- [ ] Every page reaches the bottom — check al-Fātiḥa and the closing pages
      especially, and a dense page's marks against the line below.
- [ ] **Dark mode**: base letters are visible in a colour edition. This is the
      failure that looks deliberate.
- [ ] **One line, two āyāt, two answers** — press each end.
- [ ] Edition switch, twice, with page swipes in between: every page draws
      immediately, no stranded spinner.
- [ ] **Position across prints**: page N of edition A shows the same āyāt as
      page N of edition B via āyah-identity mapping.
- [ ] A bookmark set in edition A reopens in edition B.
- [ ] Download UI shows a **per-edition** breakdown, and a bundled-face edition
      is **absent** from it rather than showing 0 of N.
- [ ] Swipe feel on the slowest device you support, with a cold cache.

Then write down what you did **not** cover, by name. An unlisted gap reads as a
covered one.

---

## 5. Performance, measured rather than felt

- The pager builds each new page on the **first frame of a drag**. A cold fit
  there is the whole stutter — measured 5–9 ms per page on a desktop VM and
  several times that on a phone.
- **Warming neighbours** moved build-time p99 from **72 ms → 6.6 ms** and the
  worst frame from 100 ms → 15 ms in a flowing reader; from a 206 ms worst
  build to 33 ms in a glyph reader.
- What warming cannot fix: the **initial open** still fits several pages
  synchronously in one frame. Once per entry, mostly hidden by a route
  transition. The cure, if it ever reads as slow, is to seed the cache before
  navigating.
- A remaining cost in a glyph reader is **raster**, not build — first-time
  glyph-atlas rasterisation of each page's new font, identical with warming on
  or off.

Measure A/B with warming toggled, on the device, over a fixed number of swipes
at a fixed cadence. A number from an emulator's translated GPU is not a number.

---

## 6. Report defects upstream

A defect you drop and never report is a defect you have decided to keep — for
every other consumer of the same export.

Keep a defects document containing, per finding:

- the exact rows, in **the publisher's own numbering** (say which, per Law 6),
- what the correct value appears to be and **how you know**,
- whether you dropped it or repaired it, and
- a **paste-ready issue body**.

And keep a "checked and **not** a defect" section, so the next person does not
re-report it. Real examples from one such document: a gloss reading `None` that
turned out to be the English word *none* opening a negation; a publisher
counting the āyah-ending marker as a word, which is a convention the consumer
depends on knowing; a documented difference between two texts at 37:130 that is
not an error in either.

Confirm the venue before filing — an aggregator's GitHub repository may hold
its code while the data is generated into it from elsewhere.
