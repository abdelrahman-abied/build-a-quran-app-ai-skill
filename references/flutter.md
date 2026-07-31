# Framework appendix — Flutter

Everything else in this skill is framework-neutral. This file is the part that
is not: patterns measured while shipping a three-edition muṣḥaf in Flutter.

If you are building in Swift, Kotlin, React Native or on the web, the *problems*
here are still yours — cold layout on the first frame of a drag, mapping a touch
back through a scale transform, selecting a font palette the platform will not
expose. Only the answers are Flutter's.

---

## 1. Fonts

### `FontLoader` deadlocks inside `testWidgets`

`FontLoader.load()` awaits an engine round trip that **never resolves inside the
fake-async zone a `testWidgets` body runs in**. It does not throw; every thread
parks and the whole suite hangs. It was first diagnosed by `sample`-ing an idle
`flutter_tester` and finding no Skia or HarfBuzz work at all.

```dart
// Any widget test that loads a font must do this.
await tester.runAsync(() => fontSource.ensure(page));
```

`runAsync` is the canonical escape hatch for real-async work in a widget test.
Make it a rule, not a fix — every future test that touches a font needs it.

### A palette variant is a different font FAMILY

A family name is the only handle Flutter gives you on *which bytes*. To ship a
dark-mode cut of a `COLR`/`CPAL` font:

```dart
final family = '${edition.familyPrefix}$page${dark ? 'D' : ''}';
FontLoader(family)..addFont(Future.value(patchedBytes))..load();
```

Registering both cuts under one family leaves the engine choosing. Patch the
`CPAL` bytes on the way into the engine and keep **one copy on disk** — see
`layout.md` Part IV for the two-byte write.

Let brightness reach the font path as a **provider key** derived from
`Theme.of(context)`, not from a stored preference: only the former is reactive
under `ThemeMode.system`.

### An already-complete `FutureBuilder` still flashes its waiting frame

If a page's font is already registered, a `FutureBuilder` will nevertheless
build once with `ConnectionState.waiting`. On a swipe that is a spinner flashing
over calligraphy. Give the source a synchronous `isLoaded(page)` and take a fast
path around the builder entirely.

---

## 2. Fitting and paging

### Cache the fit, key it honestly

Binary-searching a page's glyph size costs 5–9 ms on a desktop VM and several
times that on a phone. Memoise it, keyed by `(edition, page, constraints,
fontFamily)`.

**Include the family**, or a dark-mode variant collides with the light one's
entry and you draw a fit measured for other bytes.

### Warm the neighbours, and check the keys match

The pager builds each new page on the **first frame of a drag**. A cold fit
there is the entire stutter. So a built page warms its neighbours' fits ahead of
the swipe — and, for a glyph edition, `ensure()`s their fonts too, so a swipe
lands on calligraphy rather than a download gate.

Measured A/B on an arm64 emulator (profile mode, `Flutter.Frame` events from the
VM service, 15 swipes at 2 s cadence, warming toggled):

| | build p99 | worst frame |
|---|---|---|
| Flowing reader, cold | 72 ms | 100 ms |
| Flowing reader, warmed | **6.6 ms** | **15 ms** |
| Glyph reader, cold | 206 ms | 480 ms |
| Glyph reader, warmed | **33 ms** | **119 ms** |

The glyph reader's remainder is **raster**, not build — first-time glyph-atlas
rasterisation of each page's new font, identical with warming on or off.

Two tests that matter more than they look:

- **Key parity**: a page turn must not mint a new cache key. A warm-up measuring
  under a different key is self-consistent, never visibly wrong, and entirely
  wasted. One such bug warmed with *King Fahd's family and King Fahd's content
  regardless of the edition being read*, and counted neighbours against 604
  rather than the current edition's page count.
- **Idle search ≡ sync search**, probe for probe.

### Never pace idle work with `SchedulerBinding.scheduleTask`

A task queued below animation priority makes the scheduler's event-loop callback
return *"call me again"* without running it, **re-arming a zero-delay timer for
as long as anything animates**. On device that is a busy-loop; under fake-async
it is a `pump` that can never finish. It cost a two-hour test hang.

Pace idle work with your own `Timer`, backing off (≈50 ms) while frames are
being produced.

### RTL pagers

The muṣḥaf reads right to left, so a `PageView` under `TextDirection.rtl` turns
pages the other way. Two consequences: the pager's `itemCount` must come from
`edition.pageCount` (604 vs 610), and **an on-device swipe test must swipe
rightward** to advance.

---

## 3. Resolving a tap through a `FittedBox`

The page's text has been scaled by a `FittedBox` before it is drawn, and the
gesture arrives in the *line box's* coordinates. Reproducing that transform by
hand means re-deriving `applyBoxFit` and keeping your copy in step with every
future change to padding, frame and margins.

**Do not do the arithmetic.** Give the paragraph a `GlobalKey` and walk back up
the ancestor transforms:

```dart
final render = paragraphKey.currentContext!.findRenderObject() as RenderParagraph;
final local  = render.globalToLocal(details.globalPosition);
final offset = render.getPositionForOffset(local).offset;   // unscaled text space
final ayah   = line.ayahAt(offset);                          // via `segments`
```

`globalToLocal` includes the `FittedBox`'s scale among the transforms it
unwinds, so `getPositionForOffset` means something. The offset indexes
`line.text` directly **because the highlight spans are cut from that same string
and concatenate back to it exactly** — one property serving both features.

Round to the nearest span for the separating space and the margins: a press
inside a line always means one of the āyāt on it.

Route **long-press through the same resolver** — it matters more than the tap,
because it opens bookmark, share and tafsir.

**Test by pressing real coordinates on a laid-out page**, not by calling the
resolver. The mapping was the whole difficulty. Run the tests against the old
implementation first and watch them answer the wrong āyah.

---

## 4. Rendering the page

- **Glyph runs**: a plain `Text` with the per-page family renders the private-use
  codepoints. Insert a separator between glyphs so `TextAlign.justify` has break
  points (see `layout.md`).
- **Record āyah ranges in code UNITS.** These codepoints reach into supplementary
  planes, so Dart's `String` indices are UTF-16 units and a "character" is often
  two. Name the field accordingly.
- **Paint the furniture with a `CustomPainter`.** A double-ruled frame, corner
  diamonds and rosettes assembled from `Border` and `Icon` widgets steal layout
  height — and a sūra header has exactly one of fifteen line slots to spend. At
  that size the motifs are a few pixels across and the widget layer cannot place
  them without eating the space they need.
- **Lines stack at their own heights inside a centred column.** One `Expanded`
  per line gives fifteen stripes with gutters, because a line scales to the
  measure's *width* and a phone leaf is far taller than a muṣḥaf's.
- **`BoxFit.fitWidth` for a justified line, `BoxFit.scaleDown` for a centred
  one**, chosen from the layout's `is_centered`.
- **A `Column` in a `bottomNavigationBar` gets loose constraints** — it needs
  `MainAxisSize.min`, or the body silently renders at zero height.

---

## 5. Downloading ~62 MB of page fonts

Decisions that were measured, in one place:

```dart
// One keep-alive client for the whole run: one TLS handshake, not 604.
final client = HttpClient()..idleTimeout = const Duration(seconds: 30);

// A bounded worker pool over one shared cursor.
await Future.wait(List.generate(6, (_) => _worker(cursor)));

// Fetch without copying, write without registering.
final bytes = (BytesBuilder(copy: false)..add(chunk)).takeBytes();
```

- **`cache()` writes bytes; `ensure()` registers a typeface.** Bulk-loading 604
  faces into the engine would waste the whole ~62 MB in memory — a page's font
  is registered when the page is actually viewed.
- **Write-then-rename**, always. A kill mid-write must never leave a truncated
  `.TTF` that renders as tofu forever.
- **gzip at rest** (`GZipCodec(level: 9)`): −40% on v1 fonts, **−59%** on the v4
  cut. Decompress on the way into the engine.
- **Stamp the cache directory with the pinned upstream commit.** A re-pin then
  cannot mix two cuts of the same page.
- **Throttle progress to whole percents**; a per-file `setState` at 604 files is
  its own jank.
- **Keep the controller alive** (a `keepAlive` provider) so closing the sheet
  does not cancel the run, and **recount the cache when the sheet opens** —
  pages cached by ordinary reading never went through the controller, so its
  count goes stale.
- **Resumable and cancellable**: cached pages skip; a cancelled run keeps what it
  got; failures count rather than crash and retry next run.

### The in-flight de-duplication deadlock

A map of in-flight futures is the right way to avoid fetching one page twice.
This clean-up is a deadlock:

```dart
// WRONG: whenComplete awaits the future it is completing.
_inFlight[page] = fetch(page).whenComplete(() => _inFlight.remove(page));
```

`Map.remove` returns the future, and `whenComplete` awaits a non-null return
value. Use a block body:

```dart
_inFlight[page] = fetch(page).whenComplete(() { _inFlight.remove(page); });
```

---

## 6. Tests

- **Goldens**: a sparse page, a dense page, a header page, per edition. Font
  loading for goldens goes through `tester.runAsync` (§1).
- **A real-IO drain cannot end with a bare `pumpAndSettle`** — it waits on
  animations only the IO can end. Put quiescence inside the drain loop.
- **A stand-in font in a widget test should use ordinary Arabic.** Real PUA
  glyph codes hang shaping against a font that lacks them — a test artefact, not
  a runtime bug.
- **Assert the OTHER āyāt are unmarked.** A one-āyah fixture cannot see a wash
  bleeding into a neighbour, which is the defect that actually happens.
- Zombie `flutter_tools` processes make a fresh `flutter test` hang. `pkill -9 -f
  flutter_tools.snapshot` before a full run.

---

## 7. Measuring on device

- **`dumpsys gfxinfo` reports 0 frames for a Flutter app.** Use the VM-service
  timeline over a WebSocket and read `Flutter.Frame` events.
- For SurfaceFlinger timing, the layer to ask for is
  `SurfaceView - <package>/<activity>#0`. The activity layer reports zero.
- Measure with a **release or profile** build on the slowest device you support,
  with a **cold cache**, and state which. An emulator's translated GPU inflates
  raster time enough to make the number meaningless.
