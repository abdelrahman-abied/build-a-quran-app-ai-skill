# The licence gate

Do this before you write rendering code, because it decides what you are
allowed to build.

Nothing here is legal advice. It is a method for finding out what the rights
holders actually said, and a format for recording it so that the next person —
including you in six months — can tell a cleared resource from an open one.

---

## 1. The five-second check that gets skipped

**Before bundling any typeface, dump its `name` table.**

```
python3 scripts/font_licence.py assets/fonts/*.ttf
```

The IDs that matter:

| ID | What it holds |
|---|---|
| **0** | Copyright notice — often names rights holders the download page does not |
| **1** | Family name — check it is the font you think you have |
| **7** | Trademark |
| **13** | **Licence description** — the grant, or the prohibition |
| **14** | Licence info URL |

A licensed font looks like this in ID 13:

> *"…licensed under the SIL Open Font License, Version 1.1"*

Eight of nine fonts bundled in the project this skill comes from said exactly
that. The ninth said:

> ***NOT FOR SALE, NOT FOR MODIFICATION, NOT FOR DISTRIBUTION OR NOT FOR
> DEVELOPMENT WITHOUT WRITTEN NOTICE***

It was the only font that had not been checked before it shipped, and it was
the only one that forbade shipping. **Bundling a TTF in an app package is
distribution.**

### Why the page is the wrong place to look

Every licence hunt in that project went to the **distributor's web page** and
stopped when the page was silent. For a typeface the authoritative record is
usually **inside the binary**, put there by the person who made it.

The `name` table was three IDs away in a file that had already been opened
closely enough to discover its private-use āyah numerals.

---

## 2. Silence is not a grant, and it is not a verdict either

A page that states no terms means **you have not found the sentence yet.**

Three places to look, in order:

1. **The binary** — `name` IDs 0/7/13/14 for fonts; embedded headers, footers
   and `meta` blocks for text and data files.
2. **The rights holder**, who is often not the distributor. Aggregators
   aggregate; presses and foundries own.
3. **Whoever they derived from.** A font offered "for the sake of daʿwah" can
   be a derivative of a *sold* commercial typeface, in which case even written
   permission from its author clears only the top link of a three-deep chain.

### The aggregator trap

**An aggregator's MIT licence covers its code, never the resources it
aggregates.**

A repository can be genuinely MIT while every layout, script and font it serves
belongs to someone who has stated nothing. Phrases like *"we've curated and
open-sourced them"* or *"the toolkit for developers"* are descriptions of
curation, not grants — and the aggregator usually is not the rights holder of
any of it.

### The dead URL is worse than no URL

The one licence pointer for a major set of muṣḥaf fonts returns **HTTP 404**,
and the mirrors that redistribute those fonts link the same dead page and quote
nothing themselves.

That is worse than an open question, **because it looks closed.** A note saying
"read the terms before release" about a page that can no longer be read reads,
to the next maintainer, as due diligence already done.

**Replace a URL with the terms themselves.** Quote them, date them, and if you
cannot, write down that you could not.

---

## 3. Write to the rights holder

It costs a message and can only improve your position. Ask for:

- Whether bundling the resource in a distributed application is permitted.
- Whether the permission covers a free application, a paid one, or both.
- The **provenance** of the resource — for a font, which print it was cut
  from; for layout data, which press and which edition.

Keep the letters in the repository, and **record the answers where the question
was asked**, replacing the open note rather than appending to it.

---

## 4. The survey format

Not a paragraph. A table, plus a section per ⚠️ or ❌ row.

```markdown
| Resource | Ships as | What the source says |
|---|---|---|
| <name + id>  | bundled TTF / runtime fetch / rows in the DB | ✅ / ⚠️ / ❌ + one line |
```

- ✅ **Cleared** — a grant you have read, quoted and dated.
- ⚠️ **Open** — no stated terms, or terms you cannot reach. *Not cleared.*
- ❌ **Forbidden** — the rights holder wrote a sentence that names what you are
  doing.

Rules for the document:

- **Quote verbatim**, with the URL and the date read.
- **Mark judgement calls as judgement calls.** "Page numbers are close to
  facts" is a lawyer's question, not yours to close.
- **Keep the ⚠️ rows visible.** They are the whole point.
- **If a decision goes against the survey's recommendation, record both.** A
  document that quietly rewrites itself to agree with the decision it informed
  is worth nothing later — and the decision is the owner's to make, not the
  document's.

---

## 5. Postures, from safest to least

1. **An OFL resource.** For fidelity level 2 an OFL Qurʾānic face exists, which
   is why level 2 is a viable permanent fallback and not a compromise.
2. **Fetch from upstream at runtime.** The client talks to the rights holder's
   own origin (or the mirror they publish). You are not in the distribution
   path.
3. **Bundle a cleared resource** whose grant you have read and quoted.
4. **Self-host the bytes.** This makes you a **redistributor**. Do not do it
   for anything in ⚠️, however convenient a single archive would be.
5. **Bundle an uncleared resource.** This is a decision, not an oversight — so
   make it explicitly, in writing, with a name attached.

---

## 6. Attribution belongs in the app

A common term on Qurʾānic text is that it may be used in any application
**provided the source is indicated and linked.** That is a requirement on the
*app*, not on the repository.

- Name and link the source on a reachable screen.
- Name the layout's press and the font's cutter where their terms ask for it.
- Decide deliberately whether an **exported image or shared text** carries the
  attribution, and write down which way you decided and why — this comes up
  again, and re-litigating it from scratch is how a share card silently gains
  or loses a source line.

---

## 7. A build flag is not a mitigation

If your database is built from optional exports, an edition whose resource is
missing simply does not appear in the picker. That is what a clone without the
exports does anyway — it is not a mitigation anyone has to apply, and it does
not make bundling the resource acceptable.

State it as a fact about the build, not as a control.
