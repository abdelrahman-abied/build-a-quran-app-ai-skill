# AGENTS.md

Portable entry point for coding agents. Claude Code reads `SKILL.md` directly
and loads `references/` on demand; every other tool should start here.

## Read this first

1. **`SKILL.md`** — the twelve laws, the two rendering models, the seven stages.
   Read it in full before writing muṣḥaf code.
2. **`references/`** — load only what the task needs:

   | File | When |
   |---|---|
   | `sources.md` | choosing or ingesting a text / layout / line / glyph / font source |
   | `numbering.md` | any word, āyah, page or line index |
   | `layout.md` | rendering a page, fitting, IndoPak, tajwīd colour fonts |
   | `licensing.md` | before bundling any font or dataset |
   | `verification.md` | writing gates, tests, or a device-pass checklist |
   | `flutter.md` | only if the project is Flutter |

3. **`scripts/`** — run these before shipping. They exit non-zero on purpose.

```bash
python3 scripts/font_licence.py <font-dir>
python3 scripts/verify_corpus.py --sqlite quran.db --page-col qcf_page --pages 604
python3 scripts/reconcile_glyphs.py a.json b.json c.json --rulings rulings.json
```

## The twelve laws, in one line each

Full statements, with the measurements behind them, are in `SKILL.md`.

1. **Two sources cannot settle anything. Three can.**
2. **A pin is not correctness.**
3. **Drop the row and say so. Never repair it in place.**
4. **Never derive one edition's layout from another's.**
5. **A font's licence is inside the font, not on its download page.**
6. **Word numbering is per-resource. Measure it; never inherit it.**
7. **The font does not imply the line breaks.**
8. **Position travels by āyah, never by page.**
9. **Never export the glyphs. Export the text.**
10. **Every guard fails loudly in both directions.**
11. **A page is written in one pen.**
12. **A line's words and a page's lines belong to the print.**

## Why the laws exist

In this domain the dangerous errors **render beautifully**. A duplicated
codepoint draws one word twice in perfect calligraphy; a single glyph out of
place shifts every glyph after it on the leaf and the page still reads as
scripture. Nothing about the render says so.

So the standing instruction for any agent working here: **when data is wrong,
make it loud — never plausible.** Do not clamp a range to fit, do not invent a
missing word, do not shift an index until it looks right. Drop the row, report
it, and say what you dropped.

## What this repository does not contain

No Qurʾānic text, no layout data, no typefaces. Do not add any. It documents
where they are and how to verify them; several carry terms their own
distribution pages do not mention. See `references/licensing.md`.
