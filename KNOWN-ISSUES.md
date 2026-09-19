# Known issues

The current defect list for *The Final Frontier*, verified 2026-09-19.

This file exists because the project keeps an append-only audit trail and there's
no reason to make you dig through 7,000 lines of editorial log to find out what's
wrong with it. Everything here is reproducible with the commands at the bottom.

## Current gate state

The manuscript does not pass its own acceptance gate, and it isn't supposed to
yet.

```
python3 .tools/check_novel.py --scope global
→ result=incomplete exit=2  error=129 warning=0
  SCOPE chapter=0 batch=0 planning=0 global=129
```

Those 129 errors break down as:

| Count | Code | Meaning |
| ---: | --- | --- |
| 128 | `CHAPTER_STATUS_NOT_FINAL` | Every chapter is at `revised`. Nothing has been promoted to `approved` or `final`. |
| 1 | `FINALIZATION_GATE_MISSING` | No passing manuscript-global gate result exists. |

Every one of them is the gate correctly refusing to certify an unfinished book.
`chapter=0` means there are currently **no objective content defects in any of the
128 chapters** — no count mismatch, no dangling identifier, no status
disagreement, no motif or cross-cut break.

That is a narrow claim. It says the manuscript is internally consistent. It says
nothing about whether the prose is good, which is what I-1 and I-6 are about.

Test suite: **703 passed, 0 failed.**

## Open

Issue IDs are stable. A gap in the numbering means that issue is closed and has
moved to [Resolved](#resolved-and-left-in-the-record).

### I-1 — Mara and Nia share one syntactic register (blocking)

`DEC-022` clause 7 requires the four viewpoints to be separated structurally — by
syntax, rhythm, paragraph shape, and where attention goes — rather than by
subject-matter vocabulary. Mara Venn and Nia Calder still converge. A
paragraph-scale repair was completed across the delivered Nia chapters; the
movement gate `GATE-EDITORIAL-DISCOVERY-MOVEMENT-003` remains `revision`.

This is the reason task 14 is blocked, and it is a craft finding rather than
missing evidence. Every objective prerequisite for that checkpoint is complete.

Tracked as `EDITORIAL-DISCOVERY-MOVEMENT-CURRENT-VOICE` and its follow-up in
[`planning/editorial-log.md`](The%20Final%20Frontier%20Novel/planning/editorial-log.md),
which also records why local sentence-level repairs cannot close it.

### I-5 — Tasks 15 and 17 were never formally run

Tasks 15 and 17 draft the Mindwars chapters (62–112) and the Coda (113–128). Both
are unchecked in
[`tasks.md`](.kiro/specs/The-Final-Frontier-novel/tasks.md), and all 67 of those
chapters exist at `status: revised`.

The prose got ahead of the process. No movement-level drafting batch, objective
gate, or editorial gate was ever recorded for either range. The chapters are real
and reviewed informally; they have no gate evidence, and the task list is correct
to say so.

### I-6 — No line edit, and no editor

There has been no professional copyedit or line edit. There are errors in the
prose. I'd rather be precise about the cause: the drafting method didn't make the
book worse, the missing editing pass did, and that pass is missing because I don't
have an editor and on many days don't have the capacity to be one.

### I-8 — `config/production.toml` describes a pipeline that is no longer run

The tracked production config still declares `model_id = "amazon.nova-2-sonic-v1:0"`,
an AWS region, a Nova token-estimate block, and a pronunciation note about
stopping Nova reading "repeat" as an instruction. Narration is now local
(qvoice / Chatterbox under `audiobook-studio/tools/kokoro-local/`), so that config, and
the `frontier_audiobook` package built around it, document a path that isn't in
use.

Nothing is broken by it — the local tooling never reads that config. But a config
that describes the wrong system is a trap for whoever reads it next, including me
in six months.

### I-7 — The reference collector counts non-songs as songs

`python3 .tools/check_novel.py --site-exclusion` passes, and reports `songs=14`
against nine real song files. Root-level Markdown is collected as a song source,
so `README.md`, `METHOD.md`, and this file each register as a song, as do the two
files in `semantic-review/`.

It has no consequence here — this repository publishes no lyrics, and the
collector is a conformance fixture for a contract whose external adoption is
recorded as `not-adopted`. But the count is wrong, and a fixture that miscounts is
a fixture that will one day miscount something that matters.

Narrowing eligibility to `songs/` was tried and reverted: the contract's
`forbidden_heuristics` rule out guessing what *is* a song, and
`test_minimal_checker.py` deliberately asserts that root-level Markdown outside the
manuscript **is** a collectible source. The design requires declaring what is not a
source root instead, which is why `audiobook-studio` now carries its own exclusion.
Fixing the count means changing that design, not patching the collector.

### I-11 — The series name is undecided, and deliberately so

Not a defect. Recorded because the reasoning cost real research and would otherwise be
rediscovered.

The novel's own title is settled by `DEC-001` and is not in question. What is open is
what a *series* would be called, if a sequel is ever published commercially.

**"Mindwars" should not be the series brand.** It stays as in-world vocabulary for the
war — that use is safe, it is not on the cover, and it is load-bearing in the songs that
`DEC-014` makes binding canon, so renaming it would cascade for no benefit. But as a
series title the ground is packed, and series titles are the category that can actually
be registered as trademarks:

| work | author | note |
| --- | --- | --- |
| *The MindWar Trilogy* | Andrew Klavan | 2014, YA cyber-thriller, an actual series |
| *MindWar* | Douglas E. Richards | 2016, Nick Hall; the series is active and likely to continue |
| *The Mind Wars* trilogy | Eldon Cene / Carl Nelson | |
| *Mind Wars* | Peter Thompson | |

Adjacent but not a collision: Alex Hughes writes *Mindspace Investigations*, and her
in-world conflict is the Tech Wars, not Mindwars. Same neighbourhood thematically —
telepaths, an institution policing them — no shared name.

**The five song titles are all unavailable for a different reason.** *The Synaptic
Frontier*, *Faraday*, *The Final Frontier*, *The Radius* and *Case Zero* are a
progression, and this one novel compresses all five. Naming the series after any of
them names a part for the whole, and after the first one it names ground already
covered.

**A register constraint most series names would violate.** The book is built on the
`Refused_Swell` principle and resolves through restraint rather than triumph. A
hard-hitting series name would misrepresent it and draw readers expecting a thriller.
What fits is quiet on the surface and brutal underneath. `Clean Silence` is the
strongest candidate on that test: concrete, ironic, already a refrain in the book at
chapters 18 and 107, and it names an ongoing condition rather than a finished event,
which is what a series occupies.

**No decision is needed yet.** A registered series mark is franchise armour, not a
prerequisite for publishing or selling a sequel: copyright in a sequel is automatic,
nothing in this repository's licence constrains its sale, and NonCommercial already
reserves the commercial lane. A sequel can also reference the world descriptively —
"a novel of the Mindwars" — which carries far less exposure than branding a series on
it. Decide when book two's subject is known, and search properly then: USPTO plus
Books in Print, not a web search.

On the novel's own title: a title carries no copyright, so there is nothing for anyone
to assert on that basis. Any exposure from "Space: the final frontier" would be a
trademark question about likelihood of confusion, and this novel shares no characters,
setting or universe with that work. The larger practical cost is discoverability, not
law: the phrase is buried under decades of Star Trek, which is a headwind for a book
that is free and needs to be found. That is an argument for a distinctive series name
doing that work later, not for renaming the book.

### I-10 — The narrator's timbre steps at every chapter boundary (accepted)

A chapter ends measurably duller than it begins — spectral centroid falls 84.8 Hz on
average, in 17 of 17 measured chapters — and the next chapter starts fresh and bright.
Inside a chapter the drift is gradual and inaudible. At a boundary it is audible, and
was heard in four out of four blind clips, "repeatably, identically."

It is deterministic rather than random: with a fixed seed, the same text produces the
same brightness, so there is no better take to re-roll for.

Three approaches failed to remove it: time-varying tilt correction (made cross-chapter
brightness worse, 146 Hz spread to 325–403 Hz), spoken chapter announcements (they are
themselves fresh bright generations, 412–593 Hz on identical settings), and static
per-chapter spectral matching (corrects a 24.7 Hz between-chapter term when the
within-chapter decay is 126 Hz).

Accepted as a limitation. Deliberate anchoring is kept because it genuinely stabilises
F0, and no equalisation is applied to the narration, because for an audiobook aimed at
blind and low-vision listeners a processing artifact is worse than the drift.

Full record, including the measurements, the mistakes, and an explicit do-not-retry
list: [`audiobook-studio/tools/narration/VOICE-CONSISTENCY.md`](audiobook-studio/tools/narration/VOICE-CONSISTENCY.md).

## Resolved, and left in the record

The audit trail is append-only. When a later review contradicts an earlier one the
earlier finding and its gate stay where they are, as the honest record of the state
they evaluated. A representative sample:

| What went wrong | How it surfaced |
| --- | --- |
| **I-2** — Chapter 3 declared `words: 1191` against an observed 1186. The declared count was right when it was written; an uncommitted line edit shortened a sentence by five words and the header wasn't updated with it. | Reported by the objective gate, which is the only thing in the project that could have noticed. Corrected to 1186. That chapter now passes at chapter scope with zero diagnostics, and the global error count went from 130 to 129 with no chapter-level errors left. |
| **I-9** — Audio had no idea which draft it came from. `batch_render_qvoice.py` skipped on `output.is_file() and manifest_passed(...)`, so editing a chapter's prose and resuming a batch silently kept narration of the superseded text. Nothing recorded the narrated text, nothing gated packaging on a human listen, and a built M4B could not say which draft it contained. | Narrated-text identity now lives in one place, `spoken_text.py`, and the renderers import `extract_body` from it so a digest cannot drift from what was fed to the model. Manifests record `spoken_sha256`; resume requires a passing render *of the current text*; `audio_state.py` holds a six-state listen queue with a digest-bound append-only approval ledger; and `build_m4b.py` refuses to package anything not human-accepted, stamping the release and `text_version_sha256` into both a sidecar and the M4B's own `comment` tag. Approval is content-addressed, so an edit voids it with no revocation step to forget. Verified end to end: a front-matter edit leaves audio valid, a prose edit turns the chapter `stale` and blocks packaging, and reverting restores both. |
| **I-4** — `test_baseline_objective_gate.py::test_the_committed_repository_fails_closed_at_global_scope` was written when the outline held 128 planned entries and no chapter file existed, and asserted the diagnostics include `OUTLINE_ENTRY_WITHOUT_FILE`. All 128 chapters now exist, so that code no longer appears and pinning it only asserted that the book was unwritten. | Rewritten to assert what must stay true — exit 2, `result=incomplete`, and at least one incomplete-disposition diagnostic — rather than the obsolete reason. The docstring records why the reason moved. Suite went from 701 passed / 1 failed to **703 passed / 0 failed**. |
| **Chapter titles existed only as filename slugs**, and `build_book.py` derived display titles with a rule that capitalised every hyphen part. The shipped PDF and EPUB therefore read "The Mind As A Field" and "A Category With A Budget" — **53 of 128 titles** wrong by standard title case. There was also no machine-readable title for spoken chapter announcements, which are primary navigation for a blind listener. | `ChapterHeader` gained a required quoted `title` as a tenth key, amended in `record-schemas.md`, the requirements, and the design. All 128 chapters migrated with prose bodies byte-identical. Every consumer now reads the canonical field with no slug fallback: the book builder, the packaged audiobook parser, the announcement renderer, and the MP3/M4B metadata writers. Verified exact across all four consumers, and both editions rebuilt with correct casing. |
| **Segment offsets in every render manifest were wrong**, drifting behind the delivered audio by the accumulated inter-paragraph gap time — 650 ms per gap, about 21 s by the end of a 33-paragraph chapter. Harmless for the numbers they were written for, fatal for synchronised read-along, which is the accessibility feature those offsets would serve. | Found by the author asking whether timings survive the pause stitching. The assembly cursor now advances by the gap it inserts, the manifest records the gap duration and that offsets include it, and the renderer aborts if the last segment's end does not match the written file length. Drift verified at 0.000 s. |
| **I-3** — `--site-exclusion` failed closed with `SONG_SLUG_COLLISION`. `build_book.py` compiled the whole novel to `book/build/the-final-frontier.md`, whose stem collided with the song `songs/The Final Frontier.md`. The exclusion contract declares only the manuscript root, so the build was writing a complete copy of the manuscript into a directory nobody had excluded — and the collision fired on the name clash rather than on the copy, which is the part that should have been caught. | Intermediates moved to a dot-prefixed top-level directory, `.build/`, which the collector's existing eligibility rule skips. No contract amendment was needed, `book/dist/` still holds the EPUB and PDF, and the exclusion no longer depends on what the compiled file happens to be called. `--site-exclusion` now passes with the compiled manuscript present, and the suite went from 2 failures to 1. |
| A length-governance audit's arithmetic made the outlier budget look roughly 15 entries underspent when the true delivered shortfall was about 2, and it proposed widening the target on that basis. | Caught during the `DEC-021` review. The proposal was closed at the correct level, the bands were demoted to diagnostics, and the mass re-budget it had ordered was superseded rather than performed. |
| All 128 chapter headers and arc entries carried stale `draft` and `exploratory` labels after the prose had already been reread in full. | Full-manuscript reread, 2026-09-15. Reconciled to `revised`. No chapter was promoted and no finalisation gate was granted. |
| Reveal release chapters were recorded wrongly, corrected, and then corrected back. `REVEAL-NIA-SOURCE-CASUALTY` went 23 → 24 → 23. | Task 5.6 audit found the first error; a 2026-09-18 current-state correction found the fix was itself wrong. Both steps are in the arc outline. |
| Chapters 43–49 were delivered and the task marked complete with no objective gate result ever recorded. The log jumped straight from one batch to the next. | Noticed later and backfilled as honest current runs against present prose, explicitly not reconstructions of the historical state. |
| Chapter 34 declared 1,124 words against an observed 1,116. | Objective rerun after a voice-separation repair changed the prose. |
| Chapter 52's `record_horizon.knowledge_limit` was left stale when a reveal moved onto its owning POV's chapter. | Repaired under `ARC-CHANGE-REVISION-003` rather than silently during drafting. |
| An earlier craft review had passed work that a later review at larger scope failed. | The `DEC-018` review reversed several earlier passes without editing them. Nine revision findings added; every superseded gate retained. |

Counts as of this file: 183 editorial findings, 85 editorial gate results, 23
author decisions.

## Reproducing all of it

```sh
# objective gate, whole manuscript
python3 .tools/check_novel.py --scope global

# a single chapter
python3 .tools/check_novel.py --scope chapter \
  --chapter "The Final Frontier Novel/chapters/discovery-part/discovery-part-003-the-failed-check.md"

# the exclusion contract's reference collector
python3 .tools/check_novel.py --site-exclusion

# the harness
python3 -m pytest .tools/tests -q

# declared word total across the manuscript
grep -h '^words:' "The Final Frontier Novel/chapters/"*/*.md | awk '{s+=$2} END {print s}'
```

The single-chapter run is the tightest loop in the project. It's the one that
caught I-2, and it now reports:

```
SUMMARY scope=chapter chapters=3 result=pass exit=0
SEVERITY error=0 warning=0
PASS chapter-scope objective checks found no violation
```

Found something not on this list? Open an issue.
