# Author Decisions

Dated record of the blocking creative decisions required by task 1 of the
`The-Final-Frontier-novel` spec. Each entry states the selected option, rationale, binding or
deferred state, and the records it affects. Decisions here are authoritative; design prose and
planning references are synchronized to match them.

Open decisions remain listed with state `pending` so downstream work can see what is still blocked.

---

## DEC-001 — Novel title

- **Task:** 1.1 Record the title decision **[AUTHOR]**
- **Date:** 2026-09-08
- **State:** `binding`
- **Selected:** The novel is titled ***The Final Frontier***.

### Rationale

The title is inherited directly from the source song *The Final Frontier* — the song that led to the
book. That song supplies the Mindwars_Part: the undeclared conflict over mindspace, counterphase as
both defense and transmission, and the null that succeeds while harming civilians throughout an
affected area canonically described as three counties wide. Naming the novel after it puts the
frontier reversal on the cover: the phrase reads as exploration and turns out to mean the mind
itself as the territory being crossed.

This is an author override of design open choice 1, which offered only *The Country Behind the Eyes*
and *The Quiet Radius*. The decision is taken before the Calibration_Batch rather than after it; the
design's deferral to calibration evidence is superseded.

### Retired candidates

Recorded rather than deleted, in case the author revisits after calibration:

| Candidate | Prior status | State |
|---|---|---|
| *The Country Behind the Eyes* | design primary working title | `retired` |
| *The Quiet Radius* | design leading alternate | `retired` |

### Preserved facts

- **“The Mindwars” remains the in-world historical name** for the undeclared war over mindspace, as
  required by Requirement 6.5. The title decision does not change the canonical term, and the cover
  title is not an in-world name.
- The title duplicates a source-song title. This is intentional, not a collision to be resolved by
  renaming either work.

### Affected records and required synchronization

| Record | Required change | State |
|---|---|---|
| `design.md` — Narrative Overview and Promise | Replace working-title paragraph with the settled title | done |
| `design.md` — Open Choices 1 | Close the choice and point to DEC-001 | done |
| `tasks.md` — task 1.1 | Record the selected title | done |
| `Mindwars Novel/front-matter.md` (task 2.2) | Title field reads *The Final Frontier* | blocked on task 3.1/3.2 |
| `Mindwars Novel/front-matter.md` — source acknowledgment (task 2.2) | Acknowledgment must state the title relationship explicitly so a reader is not left guessing why a source song shares the book's name. Suggested framing: the novel takes its title from the song *The Final Frontier*. Sound-recording (`℗`) and performance ownership language stays out of the prose notice per Requirement 9.11. | blocked on task 3.1/3.2 |
| `planning/canon-bible.md` (task 4.2) | No change required; the title is jacket-facing, not a continuity fact, so it is not a Novel_Extension | n/a |

### Consequence flagged for author attention

The manuscript working directory is `Mindwars Novel/`, selected by the design and wired into the
Site_Build exclusion as an exact resolved path. The recommendation is to **keep that directory name
unchanged**: it is an internal working path rather than a title, it stays stable if the title is ever
revisited, and it keeps the manuscript root textually distinct from the song titled *The Final
Frontier*. Renaming the root to match the title would require synchronized edits to the design's
Manuscript Organization section, the `EXCLUDED_SOURCE_FOLDERS` entry, the site-isolation fixture
test, and every planning path reference. No rename is performed without an explicit author decision.

---

## DEC-008 — Site isolation when the lyrics tooling is external

- **Task:** 3.1, 3.2 (spec re-scope)
- **Date:** 2026-09-08
- **State:** `provisional` — applied to the spec, awaiting author confirmation
- **Selected:** Option B, the Manuscript_Exclusion_Contract.

### Situation

The author confirmed the lyrics-site tooling lives in a separate repository. This workspace contains
no `.tools/` directory, no `build_site.py`, and no song-index generator. The four Canon_Sources here
are reference copies at `songs/The Synaptic Frontier.md`, `songs/Faraday.md`,
`songs/The Final Frontier.md`, and `songs/The Radius.md`.

Requirements 9.2, 9.3, 11.9, and 12.8 were written on the assumption that Site_Build is editable from
this project. It is not. The design's research finding that `build_site.py` scans every visible
top-level directory has been withdrawn as unverifiable here.

### Options considered

| Option | Approach | Consequence |
|---|---|---|
| A | Drop the isolation requirements | Removes Req 9.2/9.3/11.9/12.8, Property 14, tasks 3.1/3.2/8.23. Nothing here can leak into an absent build, but protection is gone if the repositories are ever combined or the manuscript is copied across. |
| **B (selected)** | Manuscript_Exclusion_Contract | Keeps the requirement's intent as a portable declaration this project owns and the lyrics repository can adopt. Preserves Property 14 and the fixture test against a reference collector. States its own limit honestly. |
| C | Defer | Marks 3.1/3.2 blocked on an external dependency and revisits when the lyrics repository is available. Unblocks the critical path but leaves the obligation unowned indefinitely. |

### Rationale

Option B preserves the reason the requirement exists — the manuscript must never be mistaken for a
song source — without pretending this project can verify code it does not hold. It unblocks task 2.2
immediately and produces an artifact the other repository can consume rather than a note asking
someone to remember. Option A was rejected because the risk it dismisses is exactly the scenario
where the folders end up side by side. Option C was rejected because deferral leaves the manuscript
root undeclared while chapters accumulate.

### Honest limit

A passing `--site-exclusion` check proves the contract is well-formed, names the real manuscript root,
and is honored by a collector implementing the documented rule. It does **not** prove the external
Site_Build has adopted the contract. Adoption in the lyrics repository is an external follow-up and is
outside this project's acceptance criteria.

### Affected records and required synchronization

| Record | Change | State |
|---|---|---|
| `requirements.md` — Canon_Source glossary | Corrected to `songs/*.md` reference copies | done |
| `requirements.md` — Site_Build glossary | Marked external; added Manuscript_Exclusion_Contract term | done |
| `requirements.md` — criteria 9.2, 9.3, 11.9, 12.8 | Wording left untouched pending confirmation; the glossary now defines how they are satisfied | deliberate hold |
| `design.md` — research findings | Withdrew the `build_site.py` inspection claim | done |
| `design.md` — Manuscript Organization | Replaced the `EXCLUDED_SOURCE_FOLDERS` edit with the contract | done |
| `design.md` — Lightweight Checker location | Withdrew the false "beside existing `check_*.py`" rationale | done |
| `design.md` — Property 14, error handling, integration test 1, traceability, risks | Retargeted to the reference collector; added the non-adoption risk row | done |
| `design.md` — Open Choices | Added choice 9 with all three options | done |
| `tasks.md` — 3.1, 3.2, 8.23, 2.2, Notes | Re-scoped; 2.2 unblocked | done |

### If the author redirects

Choosing A means deleting Req 9.2/9.3/11.9/12.8, Property 14, and tasks 3.1/3.2/8.23, and dropping
the contract file. Choosing C means reverting 3.1/3.2 to blocked-external and leaving task 2.2
unblocked as it now is. Either redirect is a small, contained edit from the current state.

---

## DEC-009 — Namelessness is not binding on the novel

- **Task:** 1.5 (naming), general canon authority
- **Date:** 2026-09-08
- **State:** `binding`
- **Selected:** The novel names characters, places, and institutions freely. The songs' namelessness
  does not carry into the manuscript.

### Rationale

*The Radius* production notes state “Namelessness is preserved. Nothing in this world carries a proper
name except the Mindwars. She is the woman in the radius.” The author has confirmed that namelessness
was an **AI production choice, not an authorial constraint**, and does not govern the novel.

This aligns the note with what the requirements already approved: “Names are allowed. Characters,
places, institutions, and products may receive stable names selected during design and arc work”
(Approved Decisions 6). No requirement or design change is needed — the spec never imported the
namelessness constraint. The decision is recorded so the note cannot be mistaken later for a canon
obligation the novel is violating.

### Consequences

- `Mara Venn`, `Nia Calder`, `Julian Adebayo`, and `Safiya Mir` are unobstructed by canon.
- `DEC-005` (institutional and geographic names) is simplified: `Northline Array`, the Open Channel
  Consortium, the Civic Record Trust, and any country or county names can be chosen on narrative
  grounds alone, with no canon note to argue against.
- “The Mindwars” remains the canonical in-world term per Requirement 6.5. That is unaffected: it was
  always a name the songs used, not a namelessness exception the novel must honor.
- Canonical unnamed specificity such as “eleven miles from the array” remains usable as texture; it is
  no longer treated as a naming prohibition.

### Open question raised — canon authority tiers

This exposes a scoping question the spec has not answered. Requirements treat the Canon_Source as “the
four song documents **and their production notes**,” and Requirement 7 lets Literal_Phrase_Constraints
be established by “the Canon_Source notes.” If some production-note content records AI production
choices rather than authorial intent, the Canon_Bible needs a tier distinction:

| Tier | Content | Proposed authority |
|---|---|---|
| 1 | Lyric text, credited “Lyrics by Jessica Mulein” | Binding canon |
| 2 | Production notes: style prompts, exclude-styles, trilogy note, cycle note, carried-motif analysis | Advisory — authoritative on motif function and tonal intent where the author affirms it, overridable where it records an AI choice |

**Awaiting author input:** is the whole production-note layer advisory, or is namelessness a single
exception while the trilogy and cycle notes remain authorial intent? Task 4.2 needs the answer before
the Canon_Bible fixes its Binding_Canon_Facts, because several spec positions currently cite notes
rather than lyrics.

Facts checked against lyric text and therefore **safe under either answer**: December discovery, the
eight-second late morning, the April term sheet, page-nine `transmit enable`, three counties wide,
eleven miles from the array, two post-null years, the Tuesday kettle, three unhurried knocks, the
Mindwars term, the arriving thought that felt like her own, the null silencing the foreign voice while
the defender's own went quieter, the maternal-language loss, the visitor's spoken consent, and the
refusal grounded in not having her mother. Requirement 3's Coda constraints are also safe: the author
approved that structure independently in Approved Decisions 2.

---

## Pending decisions

| ID | Task | Decision | State |
|---|---|---|---|
| DEC-002 | 1.2 | Nia source/casualty braid — approve or reject **[HARD GATE]** | `pending` |
| DEC-003 | 1.3 | Safiya Mir's maternal language and review dependency **[HARD GATE]** | `pending` |
| DEC-004 | 1.4 | First casualty's operational consequence | `pending` |
| DEC-005 | 1.5 | Institutional/geographic names and post-null public visibility | `pending` |
| DEC-006 | 1.6 | Record-frame visibility | `pending` |
| DEC-007 | 1.7 | Character belief strength about handshake causation | `pending` |

### Canon evidence bearing on DEC-002 (the next hard gate)

Recorded from a full read of the four Canon_Sources so the braid decision can be made against the
text rather than from memory. This is evidence, not a decision.

**Pointing toward one person:**

- Both figures are female. *Faraday* calls the received morning “a stranger’s ordinary morning” and
  later “I liked the stranger. I would let her back in.” *The Final Frontier* verse 1 uses “she.”
  Both are labeled *stranger* relative to the finder. This is lyric evidence.
- *The Final Frontier* production notes state a motif chain: “‘a thought arrive that isn’t theirs’
  (Synaptic Frontier, bridge) returns in verse 1 as the first casualty who believed the thought was
  hers.” **Weight reduced per `DEC-009`:** this is note-tier material, and it claims a returning
  *phrase* rather than a shared identity even at full weight.

**Pointing toward two people:**

- The two events run in opposite directions. In *Faraday* the finder **receives** a stranger’s
  morning eight seconds late. In *The Final Frontier* the casualty **has something arrive** in her.
  Reception and insertion are different acts.
- The Synaptic Frontier bridge places the researcher turning something on **and** a stranger feeling
  an alien thought, which is the insertion direction, not the reception direction that *Faraday*
  describes for December.
- No source line states that the person whose morning was received is the person the intrusion later
  reached. The trilogy note links a **phrase** across songs; it does not assert one identity.

**Assessment:** the pull toward one person rests mostly on both women being strangers to the finder,
which is thin. The strongest counter-evidence is in the lyrics themselves: reception and insertion are
opposite acts, and no line joins the identities. `DEC-009` weakens the note-tier motif chain further.

The design's position therefore holds and is if anything better supported than before: canon does not
join the roles, so joining them is a Novel_Extension requiring explicit approval. If the author
approves the braid, the strongest canon-consistent framing keeps the two events separate in kind and
time, exactly as the design already requires, so the identity becomes a discovery the characters make
rather than a fact the prose assumes.
