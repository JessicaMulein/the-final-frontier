# Contributing

Thanks for reading closely enough to want to change something.

This project is open, and the author intends to keep writing in this world — sequels,
adaptations, retellings, and works that may overlap with what is here. Those two facts
need one rule to coexist, and it is the only unusual thing on this page.

## Why there are terms at all

A contributor owns the copyright in what they write. If a contribution were merged with
no terms attached, it would become a piece of this corpus that the author could not
relicense and could not carry into a later work without the contributor's permission.
One paragraph of donated prose could constrain a sequel years later, and tracking down
a contributor after the fact is unpleasant for everyone.

So contributions are accepted on terms that keep the author's future free, while leaving
your rights in your own work intact.

## The terms

By submitting a contribution — a pull request, a patch, an issue containing prose or
code intended for inclusion — you agree that:

1. **You wrote it, or you have the right to submit it.** It is your original work, or
   you have permission to contribute it, and submitting it does not violate anyone
   else's rights.

2. **You keep your copyright.** Nothing here assigns it. You may use your own
   contribution however you like, elsewhere, forever.

3. **You grant Jessica Mulein a licence broad enough to be useful**: a perpetual,
   worldwide, non-exclusive, royalty-free, irrevocable, sublicensable licence to use,
   reproduce, modify, adapt, publish, distribute, and create derivative works from your
   contribution, **under any terms, including terms different from this repository's and
   including commercial ones**, and to include it in later works whether or not those
   works are distributed under the licences used here.

4. **Your contribution is also published under this repository's terms** — CC BY-NC-SA
   4.0 for prose and planning documents, MIT for tooling — so every reader gets it on
   the same footing as the rest.

Point 3 is the one that matters. Without it, the project would have to refuse
contributions to the prose entirely, which would be a worse outcome than asking for it.

If you would rather not grant that, say so in the pull request. Small corrections —
typos, factual errors, broken links, build fixes — can usually be taken as a report and
reimplemented independently, which costs you nothing and keeps the provenance clean.

## Building in the Mindwars world

You may. Section 1 of the LICENSE licenses adaptation, so new stories using Mara Venn,
Nia Calder, Safiya Mir, the null, the Trust or the Radius are permitted — with credit,
non-commercially, and shared under the same terms.

Those are your works, not contributions to this one, and they do not belong in a pull
request. Publish them yourself. A link in an issue is welcome and the author would
rather read it than not.

The commercial lane is reserved: nothing built on this corpus may be sold. That is what
NonCommercial means, and it is the boundary that lets the rest be open.

## What is especially welcome

- **Accessibility findings.** This book is meant to be usable by blind and low-vision
  readers. If the EPUB misbehaves with your screen reader, or the audiobook's chapter
  markers do not navigate properly in your player, that is a defect and worth reporting
  with the app and version.
- **Objective defects in the manuscript** — a word count that disagrees with its
  chapter, a dangling identifier, a continuity break. `python3 .tools/check_novel.py
  --scope global` finds these mechanically, and anything it misses is interesting.
- **Tooling bugs**, especially in the narration pipeline. It is MIT and has been wrong
  before in instructive ways; see `audiobook-studio/tools/narration/VOICE-CONSISTENCY.md`.

## What is unlikely to be accepted

- **Line edits to the prose.** The book has no professional copyedit and that is a known
  gap, recorded in `KNOWN-ISSUES.md`. It is a gap the author intends to close
  deliberately rather than by accumulating patches.
- **Changes to recorded decisions.** `planning/decisions.md`, the arc outline and the
  editorial log are an append-only audit trail. Later findings are added; earlier ones
  are not rewritten, even when superseded.
- **Attempts to make the objective checker smarter about craft.** It deliberately
  refuses to score prose voice, sentence artistry, emotional tone, or hook quality.
  That boundary is the point.

## Before opening a pull request

```sh
python3 -m pytest .tools/tests -q          # manuscript harness
python3 .tools/check_novel.py --scope global
python3 .tools/check_novel.py --site-exclusion
```

The global gate exits non-zero by design — the book is not finished and the gate
correctly refuses to certify it. What matters is that your change does not add new
diagnostics. `KNOWN-ISSUES.md` records the current expected state.

## A note on AI

Much of this repository was produced with AI assistance, under direction, and the
LICENSE says so. If your contribution was too, that is fine — say so, and make sure you
can still honestly agree to point 1.
