# Method

How *The Final Frontier* was built, what the machine did, what I did, and how you
can check every claim on this page yourself.

I'm a lifetime software engineer. When I decided to write a novel I did the thing
I know how to do: I wrote a specification, built a verification harness, and
delivered against it in reviewed increments. The manuscript is the output. This
document is the build system.

Every number below is reproducible from a clean checkout. The commands are given
so you don't have to take my word for any of it.

## The shape of it

Five layers, each one authority for the layer beneath it:

1. **Requirements** — 15 numbered requirements fixing scale, structure, POV
   architecture, canon, motif discipline, rights, and the definition of done.
2. **Design** — 15 properties stated so a machine can falsify them, plus the
   architecture they describe.
3. **Tasks** — 19 top-level tasks, 5 of them hard gates that block everything
   downstream until they pass.
4. **Planning records** — the canon bible, arc outline, POV roster, voice briefs,
   motif ledger, record schemas, decision log, change log, editorial log, and
   gate results. Typed JSON inside Markdown, parsed by the checker.
5. **Prose** — 128 chapter files, each carrying a ten-key header the checker
   validates against its planning record.

Nothing in layer 5 is allowed to contradict layer 4, and a contradiction is a
build failure rather than a matter of opinion.

## The numbers

| | |
| --- | --- |
| Requirements | 15 |
| Machine-checkable properties | 15 |
| Tasks / complete / hard gates | 19 / 12 / 5 |
| Author decisions | 23 (`DEC-001`–`DEC-023`) |
| Arc entries / cross-cuts / baselines | 128 / 65 / 1 |
| Editorial findings / editorial gates | 183 / 85 |
| Planning records | 31,516 lines |
| Specification | 3,386 lines |
| Manuscript checker | 10,246 lines |
| Checker test suite | 702 tests, 30 modules |
| Audiobook pipeline | 25,470 lines |
| Chapters delivered | 128 (29 / 32 / 51 / 16) |
| Prose words | 149,988 |
| Chapters at `final` | 0 |

```sh
# chapter count per movement, and the delivered word total
for d in discovery-part private-defense-part mindwars-part aftermath-coda; do
  printf "%s: " "$d"; ls "The Final Frontier Novel/chapters/$d"/*.md | wc -l
done
grep -h '^words:' "The Final Frontier Novel/chapters/"*/*.md | awk '{s+=$2} END {print s}'

# the objective gate over the whole manuscript
python3 .tools/check_novel.py --scope global

# the checker's own test suite
python3 -m pytest .tools/tests -q
```

The word total lands at 149,988 against an approved target range of
130,000–150,000. I did not aim for that margin and I don't recommend it.

## What the AI did

The prose was drafted by Claude Opus 5 and GPT 5.6 Sol against the specification
above. The first full draft cost about $600 in model spend. The songs are my
lyrics with Suno composition and performance. The audiobook is synthesised
narration. The cover is generated.

The audiobook cost no cloud spend at all: it was rendered locally with Fish
S2 Pro on an Apple M4 Max with 64 GB of unified memory, using the Mac's
own GPU. That is the whole hardware bill — no rented accelerators, no per-minute
inference fees. It is not fast. Generation ran at roughly 1.3–1.5× real time per
chapter (a six-minute chapter takes eight or nine minutes to render), with peak
memory around 21–30 GB, and the full 128-chapter book is about 13.4 hours of
audio. Counting the whole-book render, the chapter announcements, the handful of
re-renders and verified repairs, and the MP3 and M4B encoding, building the
finished audiobook took roughly a day of machine time on that one laptop. A
reproducer should budget about that, and expect the memory ceiling to matter more
than clock speed.

What the models did not do: choose the premise, set the four-mode mechanism,
decide that the origin of Nia Calder's wanting is never resolved, hold the
consent line through 128 chapters, pick what the book refuses to do, or write a
single one of the 23 decisions. Those are the load-bearing calls and they are all
mine, dated, with the alternatives I rejected written down beside them.

I'd rather be judged on the decision record than on the word count. A decision
looks like this — `DEC-023`, the one that added the afterword, weighing six
alternatives including doing nothing:

> | Alternative | Why rejected |
> | --- | --- |
> | A front epigraph instead | Read before the evidence, so it instructs the reader's conclusion and pre-empts the null result the book spends 128 chapters earning. |
> | A chapter 129 in `aftermath-coda/` | Breaks the fixed 128-chapter architecture … all to make nonfiction pass a fiction gate. |
> | Say nothing and let the novel stand alone | Defensible, and it was the state until now. It leaves the most common honest reader question unanswered. |

There are 23 of those. No model produced them. They're in
[`planning/decisions.md`](The%20Final%20Frontier%20Novel/planning/decisions.md).

## Two gates, and neither one can overrule the other

This is the part I'd defend hardest as engineering, because it's the part that
keeps a machine from grading its own homework.

Every chapter passes through two independent gates:

**The objective gate** is `check_novel.py`. It decides only facts: word counts,
identifier resolution, status agreement, cross-cut reciprocity, movement
contiguity, POV run limits, length classification, motif synchronisation,
literal-phrase placement. It runs at three scopes — one chapter, a batch, or the
whole manuscript — and it fails closed. Missing or unreadable input is an
`incomplete` result and a nonzero exit, never a pass.

**The editorial gate** is human judgement, recorded as dated findings with prose
locations and a requested action. It decides voice distinctness, pacing, hooks,
restraint, tenderness, human cost, whether a chapter earns its length.

The rule between them, from
[`planning/editorial-log.md`](The%20Final%20Frontier%20Novel/planning/editorial-log.md):

> A diagnostic must never produce, determine, or override an editorial finding.
> Conversely, an editorial pass must never waive an objective violation or
> incomplete objective prerequisite.

And the prohibition that matters most:

> Numeric craft scores, weighted rubrics, synthetic voice ratings, sentiment
> values, sentence-length proxies, and numeric pass thresholds are prohibited.

There is no quality score anywhere in this project. A green checker run says the
book is internally consistent. It says nothing about whether it's any good, and
the harness is built so it can never be mistaken for saying so.

Under Property 15, `final` status requires both gates to pass independently. No
chapter has both. All 128 sit at `revised`.

## What the checker actually verifies

Each of the 15 properties has its own generative test module using Hypothesis.
They run against synthetic manuscripts, not against this one, so a property holds
for a class of books rather than for the one I happened to write. A handful of
separate integration tests do run against the real repository:

| | |
| --- | --- |
| 1 | Chapter plan and file bijection |
| 2 | Stable identifier, mechanism-state, and evidence referential integrity |
| 3 | Cross-cut graph symmetry |
| 4 | Prose word-count round trip |
| 5 | Length classification and limits |
| 6 | Ordered movement architecture and scale |
| 7 | Human POV roster and anchor coverage |
| 8 | POV run cap and run word limit |
| 9 | Motif event synchronisation |
| 10 | Ledger-driven literal scope, count, and placement |
| 11 | Post-baseline change and status atomicity |
| 12 | Chapter-local and manuscript-global gate separation |
| 13 | Fail-closed incomplete inputs and exit status |
| 14 | Manuscript source exclusion |
| 15 | Finalisation requires both independent gates |

Property 2 is the large one. It holds the mechanism invariants: that a `CANCEL`
event is unaddressed and subtractive and declares its affected set unpredictable
before, unenumerable during, and incompletely mapped after; that a `PAIR` session
joins exactly two living consenting people with matching calibration; that no
transported contribution exists without a deliberate send act; and that no record
anywhere confirms the origin of the arriving want. The novel's ethics are
enforced by a test.

Property 14 has its own portable declaration,
[`exclusion-contract.json`](The%20Final%20Frontier%20Novel/exclusion-contract.json),
which exists because the manuscript shares a title with one of the songs and must
never be collected into the lyrics catalogue. It specifies the matching rule, the
ordering constraint, four rejected heuristics and why each one is wrong, and
seven fail-closed conditions. It also states what it does not prove.

## Where it broke

Extensively, and on purpose kept in the record.

The audit trail is append-only. When a later review contradicts an earlier one,
the earlier finding and its gate stay exactly where they are, as the honest record
of the state they evaluated. From the editorial log, on the `DEC-018` craft review
that reversed several earlier passes:

> every earlier finding and gate stays in the audit trail as the honest record of
> the state it evaluated.

A sample of what that trail contains: a length-governance audit whose arithmetic
made the outlier budget look about 15 entries underspent when the real shortfall
was about 2. A full reread that found 128 chapter statuses stale and reconciled
them. Two separate corrections to which chapter releases which reveal. Seven
chapters delivered and marked complete with no objective gate result ever
recorded, backfilled later as honest current runs rather than reconstructions.
Two chapters whose declared word count disagreed with the observed one, 1,124
against 1,116 and 1,191 against 1,186 — both found by the checker, neither
findable by reading.

The complete current list is in [KNOWN-ISSUES.md](KNOWN-ISSUES.md). I'd read that
before deciding what you think of this.

## What I'd do differently

**Write the editorial gate first.** I built the objective checker to a high
standard and then discovered that everything that actually matters about a novel
lives on the other side of it. The objective layer is 10,246 lines and 702 tests.
The editorial layer is me, reading, and I ran out of me.

**Derive the metadata, don't declare it.** Every drift in this project came from
the same shape: a field that had to be updated by hand as a separate step from the
work it described. Statuses went stale 128 at once. Word counts went stale one
line edit at a time — shorten a sentence, forget the header, and the only thing in
the project capable of noticing is the checker. A declared count that the tool can
compute should never have been a declared count.

**Budget the review, not the draft.** Drafting was cheap and fast, which is
exactly why the bottleneck moved to review and why I didn't see it coming. The
$600 was never the constraint.

## What this does not establish

It does not establish that the prose is good. The objective gate cannot evaluate
that and the editorial gate has not finished trying.

It does not establish that specification-first drafting produces better novels
than writing one the ordinary way. I have a sample of one, no control, and an
obvious interest in the answer.

It does not establish that the method is why the book works, where it works. It's
equally consistent with the method being scaffolding that a determined person
could have done without.

What it does establish is narrower: that a novel can be built against a written
specification with a real verification harness and a complete audit trail, that
the trail will record the author's mistakes if you let it, and that every
structural decision in this one has a name, a date, and a rejected alternative
beside it.

— Jessica Mulein, 2026
