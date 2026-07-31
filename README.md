# Build a Qurʾān app that matches the printed muṣḥaf

**An AI agent skill for building a Qurʾān reader whose pages, lines and words
match a real printed muṣḥaf** — the same āyāt on the same leaf, the same words
on the same line, in the same hand.

Install it, and your coding agent brings the whole method with it: where the
data comes from, what each source got wrong, how a page is fitted, how a tap
finds its āyah, and which fonts you are not allowed to ship.

Packaged as a Claude Code skill (`SKILL.md`), portable to any other agent via
`AGENTS.md`. The three verification scripts need no agent at all.

---

## Why this exists

Building a Qurʾān app is not hard. Building one that is **correct** is, and
almost nothing about it is written down.

The dangerous defects in this domain are the ones that **render beautifully**:

- A duplicated codepoint drawing one word twice, in perfect calligraphy.
- A single glyph out of place shifting **every glyph after it on the leaf** —
  still flawless script, saying something the Qurʾān does not.
- A bookmark filed on page 588 when the āyah is on 589.
- A dark-mode page where the base letters are black and the coloured tajwīd
  rules stay visible, so the failure looks deliberate.
- A bundled typeface whose own metadata forbids, in capitals, exactly what your
  app package does with it.

Every one of those shipped in a real app for multiple releases. None of them
looked like a bug. They looked like the muṣḥaf.

This skill is the accumulated cost of finding them.

## Install

### Claude Code

```bash
git clone https://github.com/abdelrahman-abied/build-a-quran-app-ai-skill ~/.claude/skills/mushaf
```

Or, scoped to one project:

```bash
git clone https://github.com/abdelrahman-abied/build-a-quran-app-ai-skill .claude/skills/mushaf
```

It is picked up on the next session and loads itself when you ask for anything
muṣḥaf-shaped — *"build a Qurʾān reader with real page layout"*, *"why is my
highlight one word off"*, *"can I bundle this font"*.

### Any other agent

Clone it anywhere in your project and point your agent at `AGENTS.md`, which
most tools read on their own:

```bash
git clone https://github.com/abdelrahman-abied/build-a-quran-app-ai-skill .agents/mushaf
```

`AGENTS.md` is a three-line pointer to `SKILL.md`, so there is one source of
truth and nothing to keep in sync. `.github/copilot-instructions.md` and
`GEMINI.md` point at the same place for the tools that look there instead.

What you lose outside Claude Code is the *automatic* loading — most agents read
their rules file in full, every turn. That is fine here: the whole repository is
under 3,000 lines.

### No agent at all

The three scripts in `scripts/` are dependency-free Python. Put them in CI and
you have the gates without any model in the loop.

Works in any language and any framework. The data and typography guidance is
framework-neutral; `references/flutter.md` is the only Flutter-specific file.

## What is inside

| File | What it holds |
|---|---|
| `SKILL.md` | The ten laws, the two rendering models, the six stages |
| `AGENTS.md` | The portable entry point, for agents that are not Claude Code |
| `references/sources.md` | Every text / layout / line / glyph / font source, its terms, and the defects found in it |
| `references/numbering.md` | Āyah, word, page and line numbering — and why three of the four are per-resource |
| `references/layout.md` | Glyph editions, Unicode editions (IndoPak), tajwīd `COLR`/`CPAL`, the fitting algorithms |
| `references/licensing.md` | The font-metadata check, the survey format, the postures |
| `references/verification.md` | Every gate, with the failure it catches, plus a device-pass checklist |
| `references/flutter.md` | Measured Flutter patterns |
| `scripts/` | Three runnable gates, no dependencies |

### The scripts are the point

Prose is advice. These are gates.

```bash
python3 scripts/font_licence.py assets/fonts/     # exit 1 on anything uncleared
python3 scripts/verify_corpus.py --sqlite quran.db --page-col qcf_page --pages 604
python3 scripts/reconcile_glyphs.py a.json b.json c.json --rulings rulings.json
```

Run over a real shipped app, `font_licence.py` finds eight fonts declaring SIL
OFL 1.1 and one declaring *NOT FOR DISTRIBUTION*. `verify_corpus.py` counts its
way to 88,246 glyphs — the number three independent transcriptions of the 1405H
print converge on.

## The ten laws

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

Each one is in `SKILL.md` with the measurement that produced it.

## What this repository does not ship

**No Qurʾānic text. No layout data. No typefaces.**

It tells you where those are, what their rights holders actually said, and how
to verify what you receive. Every one of them carries its own terms — several
carry terms their own distribution pages do not mention — and clearing them is
your responsibility, not this repository's.

Read `references/licensing.md` before you bundle anything. It exists because
the check it describes takes five seconds and was skipped.

## Provenance

Written from a shipped muṣḥaf that renders three prints: King Fahd (1405H),
QPC V4 tajwīd, and IndoPak Nastaʿlīq. Every number here was counted, every
device measurement made on real hardware, and every licence quotation read from
the source on the date given.

Where something is a judgement call, it is marked as one. Where a question is
open, it is left open — a record that quietly rewrites itself to agree with the
decision it informed is worth nothing later.

## Contributing

Most valuable, in order:

1. **A defect found in a source**, with the rows and how you know.
2. **A licence answer in writing** from a rights holder — several of the ⚠️ rows
   in `sources.md` are waiting on exactly that.
3. **A measurement that contradicts one here.** Bring the numbers; they will be
   taken seriously and the table will change.
4. **An OFL Nastaʿlīq with IndoPak orthography and PUA āyah numerals.** It would
   close the one ❌ row outright.

## Licence

MIT, for the prose and scripts in this repository only. See `LICENSE` — it
cannot and does not cover any muṣḥaf resource, because none is shipped here.

---

<div dir="rtl">

## بالعربية

**مهارة لبناء تطبيق قرآن تُطابق صفحاته المصحف المطبوع** — الآيات نفسها على
الورقة نفسها، والكلمات نفسها على السطر نفسه، وبالخط نفسه.

الخطر في هذا المجال ليس في الخطأ الذي يظهر، بل في الذي **يُرسَم جميلًا**: رمز
مكرر يرسم كلمة مرتين بخط بديع، أو رمز واحد في غير موضعه يُزيح كل رمز بعده على
الورقة كلها، أو علامة مرجعية تفتح ورقة ليست فيها آيتها، أو خط تشحنه في تطبيقك
وبياناته الداخلية تمنع ذلك بالحرف الواحد. كل ما سبق شُحن فعلًا في تطبيق حقيقي
لعدة إصدارات، ولم يبدُ أيٌّ منه خطأً — بدا مصحفًا.

هذه المهارة هي ثمن اكتشافها، مكتوبًا.

**التنصيب** — في Claude Code:

```bash
git clone https://github.com/abdelrahman-abied/build-a-quran-app-ai-skill ~/.claude/skills/mushaf
```

ومع أي وكيل آخر، استنسخها في مشروعك ووجّهه إلى `AGENTS.md`. والسكربتات الثلاثة
بايثون بلا اعتمادية واحدة، فتعمل في CI بلا نموذج أصلًا.

**ما فيها:** القوانين العشرة، ونموذجا العرض (طبعة الرموز مقابل الطبعة
اليونيكودية كإندوباك)، وضبط الصفحة والسطر، وألوان التجويد عبر `COLR`/`CPAL`،
وجدول التراخيص لكل مصدر، وثلاثة سكربتات تُنفَّذ فتفشل بصوت عالٍ بدل أن تنصح.

**ما ليس فيها:** لا نص قرآني، ولا بيانات تخطيط، ولا خطوط. تدلّك على مواضعها،
وتقول لك ما نصّ عليه أصحاب الحقوق فعلًا، وكيف تتحقق مما تستلمه. وتخليص الحقوق
مسؤوليتك أنت.

</div>
