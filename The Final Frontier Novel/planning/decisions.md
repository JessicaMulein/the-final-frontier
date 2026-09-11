# Author Decisions

Dated record of the blocking creative decisions required by task 1 of the
`The-Final-Frontier-novel` spec. Each entry states the selected option, rationale, binding or
deferred state, and the records it affects. Decisions here are authoritative; design prose and
planning references are synchronized to match them.

Open decisions remain listed with state `pending` so downstream work can see what is still blocked.

---

---

## Naming map

Several distinct things carry similar names. This is the authoritative disambiguation; treat any
conflicting usage elsewhere as an error to fix.

| Name | What it is | Authority |
|---|---|---|
| ***The Final Frontier*** | **The novel's title.** Jacket-facing. | `DEC-001` |
| *The Final Frontier* | **A source song** at `songs/The Final Frontier.md`, the third of the trilogy. The novel takes its title from it. | Canon_Source |
| **the Mindwars** | **An event inside the book.** The in-world historical name for the undeclared war over mindspace, applied in hindsight by the histories. It is *not* the title. | Requirement 6.5, `The_Mindwars` |
| `Mindwars_Part` | **Main Part Three**, the structural division that dramatizes the war. | Requirement 3.1 |
| `mindwars-part/` | The **chapter directory** for that movement, and the filename prefix `mindwars-part-NNN-*.md`. | Requirement 9.5 |
| `The Final Frontier Novel/` | The **manuscript root directory** on disk. | `DEC-010` |

Two consequences worth holding onto:

- The war is named in the book but does not name the book. Characters have no stable term for it while
  it is happening; the name arrives afterward, once it is safe to write one down. That gap is a
  narrative asset, and the Mindwars beat architecture already uses it.
- The title's reversal is the payoff, not a label. “The final frontier” sounds outward and turns out to
  mean the mind was the territory crossed. Nothing in the prose should explain that; the Turn earns it.

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
| `The Final Frontier Novel/front-matter.md` (task 2.2) | Title field reads *The Final Frontier* | pending task 2.2; unblocked — task 3.1 is complete and task 3.2 is not a prerequisite |
| `The Final Frontier Novel/front-matter.md` — source acknowledgment (task 2.2) | Acknowledgment must state the title relationship explicitly so a reader is not left guessing why a source song shares the book's name. Suggested framing: the novel takes its title from the song *The Final Frontier*. Sound-recording (`℗`) and performance ownership language stays out of the prose notice per Requirement 9.11. | pending task 2.2; unblocked — task 3.1 is complete and task 3.2 is not a prerequisite |
| `planning/canon-bible.md` (task 4.2) | No change required; the title is jacket-facing, not a continuity fact, so it is not a Novel_Extension | n/a |

### Consequence — resolved by DEC-010

The manuscript root directory question raised here was answered by the author: the root is renamed to
match the title. See `DEC-010`.

---

## DEC-002 — Nia source/casualty braid: approved, causally linked

- **Task:** 1.2 Resolve the Nia source/casualty braid **[AUTHOR] [HARD GATE]**
- **Date:** 2026-09-09
- **State:** `binding`
- **Selected:** Option B. Nia Calder holds **both** roles in a protected causally linked sequence:
  Mara’s receive-only December apparatus identifies and locks onto Nia’s person-specific
  channel/address, then Mara later adds a temporary bench transmit path and sends a content-free
  handshake through that same address. The handshake may have reached Nia and produced the wanting,
  but nobody can prove it.

### What canon fixes, and what it does not

Verified against lyric text, not from memory.

| Event | Source | What the lyric establishes | Direction |
|---|---|---|---|
| December morning | *Faraday* v1 | Mara says come in, turns the front end up, and receives a stranger's ordinary morning eight seconds late. The bridge shows she grew fond of her. The invitation language does not establish a transmit stage; the author-selected novel chronology below makes this apparatus receive-only. | Mara **receives** |
| First casualty | *The Final Frontier* v1 | The first one lost was never told she'd been drafted; a thought arrived and she believed it was hers. | She **receives** |

Both are women. Neither song names either. **No line joins the identities**, so joining them is a
Novel_Extension, which is why this required an author gate rather than a design default.

### Correction to the prior evidence note

The earlier evidence recorded under `DEC-001` claimed both figures are "labeled *stranger* relative to
the finder" and treated that as the main pull toward one person. That overstates the text. *The Final
Frontier* never calls the casualty a stranger; she is "the first one that we lost." The word only
reaches her through *The Synaptic Frontier*'s bridge — a stranger somewhere feeling a thought arrive
that isn't theirs — and "stranger" there simply means unknown-to-the-observer, in two different
observers' frames. The conclusion that the evidence is thin stands; the stated reason was wrong.

### Corrected mechanism and chronology

The December apparatus is **receive-only** and has no transmit stage. Its discovery function is to
receive Nia’s continuous ordinary morning with Mara’s eight-second transport offset and identify or
lock onto Nia’s person-specific channel/address. No part of the approved braid depends on hidden
December transmission.

Later, in Chapters 16–20, Mara deliberately adds a temporary bench transmit path and sends the
content-free handshake through that same person-specific address. The protected causal claim is that
this later handshake may have reached Nia and produced the wanting. Channel identity and chronology
make the link plausible; neither proves it.

When Mara reads page-nine `transmit enable` in April, she learns that bidirectionality is a broader
architectural capability and danger. Page nine confirms that a receiver network can be write-capable
by design. It is **not** evidence that her receive-only December rig transmitted, and it does not
retroactively alter the December event.

### Why this option

It puts the book's thematic argument inside Discovery instead of saving it for the Coda. Mara’s
receive-only December discovery is innocent of transmission, but her later deliberate content-free
hello—no message and no intended influence—may still have injured someone, and her own authorization
did nothing to protect the person on the other end. That is the same debt the null later charges
Safiya, arriving roughly 100 chapters early and in a form nobody can prove. The two injuries bracket
the novel: curiosity and defense each incur a cost that consent did not discharge.

It also gives the record-and-testimony architecture something real to fail at. *The Final Frontier*
verse 1 is written afterward, by people who "didn't have a word for it while we were losing," and it
attributes the first loss to the adversary. If that attribution is wrong, the Civic Record Trust opens
its history with an error it cannot verify or correct — which makes Julian's arc a genuine failure
rather than a procedural win.

### Binding constraints on implementation

All five are load-bearing. Dropping any one of them changes the decision.

1. **Never confirmed.** The causal link between the later handshake and Nia’s wanting is `unverified`,
   under the same rule that governs every account of the Foreign_Signal. No instrument settles it, no
   character proves it, and no narrator gets privileged confirmation. Binding `DEC-007` distributes
   belief asymmetrically without changing that status: Mara’s high private conviction is
   non-authoritative, Nia refuses both accounts, and Julian records an inference as an inference.
2. **The adversary still owns the war.** Contested attribution covers the *first* casualty only. The
   Mindwars, the doctrine of taking the yes rather than the country, and every later intrusion remain
   the adversary's. If the linkage starts reading as "Mara caused everything," the balance is wrong
   and gets corrected in revision rather than defended.
3. **The record gets it wrong and stays wrong.** No late disclosure tidies the archive.
4. **Insertion and subtraction stay distinct.** Nia embodies an arrival mistaken for self, whatever
   its origin. Safiya embodies removal, with no foreign thought at all. The first injury is
   unprovable and the second is certain; that asymmetry is the point, so the two rhyme without being
   equated.
5. **The emotional question resolves even though the factual one does not.** Permanent factual
   ambiguity is not license to leave everything open. Nia eventually stops needing to know the
   wanting’s origin and regains usable self-trust: she can exercise judgment without proving whose
   certainty arrived. That movement does not decide causation, forgive Mara, or validate the archive.
   What she and Mara become to each other, and what each decides to do without knowing, must land. A
   chapter that treats “never confirmed” as permission for general vagueness fails this constraint,
   and every movement Editorial_Gate tests for it.

### Retired options

| Option | Why retired |
|---|---|
| A — approve as designed, two separate events | Workable, and it kept the adversary unambiguously responsible, but it left the coincidence intact: of everyone alive, the first voice Mara caught is also the first person the enemy hit. |
| C — reject, Nia keeps the source role | Diffuses Mara's guilt, loses the strongest reveal, and risks a distinct casualty who exists mainly to be harmed. |
| D — reject, Nia keeps the casualty role | Weakens the Discovery spine; the stranger Mara spends the movement hunting becomes a minor figure, and *Faraday*'s bridge affection attaches to someone with little presence. |

### Affected records and required synchronization

| Record | Change | State |
|---|---|---|
| `design.md` — Premise | Separate the receive-only December lock from the later deliberate bench handshake; state page nine as broader capability only; preserve the unverified causal link | done |
| `design.md` — Named POV Cast, beat architecture, Reveal Ledger, Voice_Briefs | Carry the corrected chronology and binding `DEC-007` asymmetry/release movement | done |
| `design.md` — braid section heading and body | Preserve the closed braid, correct the mechanism, and enumerate all five binding constraints | done |
| `design.md` — Open Choices 3 and 7 | Keep the braid closed and close the belief-distribution choice under `DEC-007` | done |
| `planning/canon-bible.md` (task 4.2) | Record the named/mechanistic braid under `DEC-002`; record the distinct `DEC-014` Canon_Lyric testimony that the same first-person speaker reports the December morning and later wanting; keep December receive-only, the later bench path separate, page nine as broader capability, and the causal linkage `unverified` with no reveal owner/window; tag all five constraints | pending task 4.2 |
| `planning/arc-outline.md` (task 5.1–5.2) | Fix the shared identity and corrected event sequence while keeping later-handshake causation unresolved | pending task 5 |
| `DEC-004` (task 1.4) | Emergency-routing consequence remains Nia’s and sits under the contested attribution | `binding` |
| `DEC-007` (task 1.7) | Asymmetric belief distribution and Nia’s movement toward release carry constraints 1 and 5 | `binding` |

---

### Canon evidence gathered for DEC-002 (closed — retained as the record of what was weighed)

Recorded from a full read of the then-four Canon_Sources before `DEC-014` promoted *Case Zero*, so the braid decision could be made against the binding text available at that time rather than from memory. This is historical evidence, not the current Canon_Source inventory and not a decision.

**Pointing toward one person:**

- Both figures are female. *Faraday* calls the received morning “a stranger’s ordinary morning” and
  later “I liked the stranger. I would let her back in.” *The Final Frontier* verse 1 uses “she.”
  Both are labeled *stranger* relative to the finder. This is lyric evidence.
- *The Final Frontier* Production_Notes state a motif chain: “‘a thought arrive that isn’t theirs’
  (Synaptic Frontier, bridge) returns in verse 1 as the first casualty who believed the thought was
  hers.” **Advisory under `DEC-011`:** the note claims a returning *phrase*, not a shared identity,
  and cannot independently establish one.

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
opposite acts, and no line joins the identities. `DEC-011` prevents advisory motif commentary from
settling that identity.

The design's position at the time therefore held: the then-binding four-source canon did not join the roles, so joining them required explicit approval as a Novel_Extension. `DEC-014` later promoted *Case Zero* and added binding first-person lyric testimony from the same speaker about both events; that later authority change does not alter this historical assessment or confirm the handshake's causation.

**Outcome — superseded in part by `DEC-002`.** The author approved the braid. Two claims in the
assessment above did not survive the closing review and are corrected there rather than edited out
here, so the reasoning stays auditable:

- The "both labeled *stranger*" evidence was overstated. *The Final Frontier* never calls the casualty
  a stranger.
- The recommendation that approval should keep the roles separate was **not** adopted. `DEC-002`
  instead links the December source identity to the later casualty through a two-step channel
  sequence: receive-only identification/lock in December, then a deliberately added transmit path and
  handshake through the same address in Chapters 16–20. *Faraday* verse 2’s `transmit enable`
  establishes broader bidirectional capability and danger, but does not prove or imply December
  transmission. Whether the later handshake caused the wanting remains unprovable on the page.

---

## DEC-003 — Safiya's maternal language: private two-person layer, heritage base unspecified everywhere

- **Task:** 1.3 Confirm Safiya Mir's maternal language and review dependency **[AUTHOR] [HARD GATE]**
- **Date:** 2026-09-09
- **State:** `binding`
- **Selected:** Safiya retains a public heritage language and works as an occasional community
  interpreter. The null removes only the private layer she and her mother built together—invented
  words, private grammar, and shared reference hardened into vocabulary. The underlying heritage base
  is **unspecified by the author everywhere, including planning**. The former private Kashmiri
  proposal is retained only as a clearly retired historical option.

### Why not a known language

*The Radius* nearly settles this in two lines, both binding lyric text.

- "I was thinking in the language I only ever had with her." A known language cannot be had *only*
  with one person. Kashmiri has speakers, dictionaries, recordings, a diaspora. The phrase describes
  something that existed between exactly two people.
- "nine words for weather, one for the way she said my name." That is an inventory of a small private
  lexicon, not a description of a natural language. And a word *for the way she said my name* is not
  vocabulary a language has; it is vocabulary two people make.

The structural argument is decisive. Mara's refusal must be physics rather than principle: "Because I
haven't got her mother. All I've got is me." That only holds absolutely if **no corpus exists
anywhere.** If the lost thing were Kashmiri, a reader immediately supplies recordings, other speakers,
a tutor, a dictionary — and the refusal collapses into "have you tried relearning it," taking the
Coda's engine with it. A private layer held by two people, one dead and one emptied, has nothing to
restore from. That absence is the whole mechanism.

### What survives and what went

| Retained | Lost |
|---|---|
| Her public heritage language, and her work as an occasional community interpreter | The private two-person layer built on top of it |
| Her mother's face, hands, the smell of her coat | The sound of her, and the words that existed only between them |

She can still speak to her community. She cannot speak to her mother. The lived loss is specific and
precisely identifiable afterward, which is harder than a total one, and it keeps the interpreter irony
live: a woman who bridges languages for a living cannot interpret back the one that mattered. The
mechanism did not select it. Under `DEC-015`, `CANCEL` cannot be aimed at a faculty, a memory, or a
person, so the precision belongs to the description of what she lost and never to the field that took
it.

### Why the base is unspecified everywhere

The author has not selected a real-world language, region, religion, ethnicity, or political history for
the heritage base. This is not a concealed continuity fact for planning to solve later. The authoritative
structured value is:

`heritage_base: unspecified_by_author`

Every project artifact—Canon_Bible, Arc_Outline, POV_Roster, Voice_Brief, editorial record, and
Chapter_File—must preserve that state. No planning or drafting record may infer or invent real-world
linguistic, geographic, religious, ethnic, or political particulars from Safiya’s name or from the
unspecified base. Readers may form associations; the project may not use those associations as
continuity, characterization shorthand, or thematic weight.

This prohibition does not erase the stable facts the author selected: Safiya has a public heritage
language, works as an occasional community interpreter, and built a private two-person layer with her
mother. Continuity comes from those facts and from the shape of the private loss, not from a hidden
real-world identity.

### On-page wording — staged ladder

| Level | Status | Notes |
|---|---|---|
| Describe, never quote | **default, always available** | The language exists through what it did and what its absence feels like. This is how the song itself handles it, and it is the preferred register for the Coda. |
| Invented private-layer words | **permitted** | No real speech community is placed in a character's mouth. Use sparingly; the absence carries more than a glossary would. |
| Real heritage wording | **unavailable** | The author has specified no real language to quote. Unlocking this requires reopening `DEC-003`; until then every artifact preserves `heritage_base: unspecified_by_author`. |

### Review dependency

- **Required:** community-portrayal review. Safiya is a heritage-community interpreter living inside
  the affected area, and that portrayal carries risk whether or not a language is named.
- **Not required:** linguistic review of wording, because no real language is quoted. This removes the
  blocker that previously gated all Coda drafting.
- **Never a lever:** the absence of a linguistic-review requirement may not be used to weaken the
  canonical maternal-language loss or Safiya's agency. That prohibition survives from the original
  task text and is unchanged.

### Binding guardrails — no inference and no allegory

No project record may infer or invent real-world linguistic, geographic, religious, ethnic, or
political particulars from Safiya’s name or from `heritage_base: unspecified_by_author`. No
real-world conflict is used as allegory, parallel, or thematic echo for the Mindwars, and no character
draws the comparison. Safiya’s established heritage-community role requires care, but it cannot be
used as a route to smuggle in a specific community or conflict the author did not choose.

### Retired options

| Option | Why retired |
|---|---|
| Private Kashmiri register as the whole loss (design's provisional choice) | Weakest fit to "only ever had with her," and it puts a restorable thing at the center of an unrestorable refusal. |
| Purely private language, no heritage base | Loses the interpreter irony and the selected heritage-community context, and thins Safiya's specificity without adding anything in return. |
| Kashmiri retained with a no-allegory guardrail | Viable, but the author chose not to commit the book to a real speech community. |
| A different named heritage | Same reason. |

### Affected records and required synchronization

| Record | Change | State |
|---|---|---|
| `design.md` — research/authenticity note | Replace the retired split-scope heritage model with `heritage_base: unspecified_by_author`; preserve review dependencies and no-softening rule | done |
| `design.md` — Named POV Cast, Canon system, calibration, risks, error handling | Keep public heritage language/interpreter role and private-layer loss while forbidding inferred real-world particulars | done |
| `design.md` — Open Choice 2 | Close the choice on unspecified everywhere | done |
| `tasks.md` — task 1.3 and downstream Canon_Bible/voice/arc/calibration/drafting/test tasks | Remove superseded page-only heritage-value instructions; require the exact unspecified value and anti-inference guardrail | done |
| `planning/canon-bible.md` (task 4.2) | Record the private-layer construction with `authority: DEC-003`, `heritage_base: unspecified_by_author`, the wording ladder, community-portrayal review, and no-inference/no-allegory guardrails | pending task 4.2 |
| `planning/voice-briefs.md` (task 4.4) | Encode describe-never-quote and forbid real-world particulars inferred from Safiya’s name or unspecified base | pending task 4.4 |
| `planning/arc-outline.md` (tasks 5.1, 5.5) | Keep the base unspecified in every Coda entry; Chapters 118–119 carry the shape of the private absence without quoting or inferred heritage detail | pending task 5 |

---

## DEC-004 — First casualty's operational consequence

- **Task:** 1.4 Fix the first casualty's operational consequence **[AUTHOR]**
- **Date:** 2026-09-09
- **State:** `binding`
- **Selected:** Real harm that Nia did not cause. The evidence clears her decision and says nothing
  about her authorship. What arrived was a **wanting**, not a message; where the wanting came from is
  never settled. One fixed experience and two unresolved origin accounts coexist in the book.

### What arrived — one experience, two origin theories

The distinction matters because Mara's Discovery handshake is deliberately content-free. A
content-free handshake cannot carry "send the second unit north." Canon resolves this: the doctrine in
*The Final Frontier* is to take the yes and **edit what they want** — not to issue orders.

| Layer | Content | Status |
|---|---|---|
| **Phenomenology** (fixed by canon) | A wanting. A certainty, arriving exactly as her own professional judgment arrives. No voice, no words, nothing to trace. She *becomes sure*. | Binding. This is what Nia's POV renders. |
| **Origin account 1** — the record's | The adversary reached her deliberately. The histories describe it as an instruction, because an undeclared war eventually needs an author once it is safe to write one down. That description is the archive's interpretation and not transported content: no instruction physically crossed, because `INTRUDE` carries no propositions. | `unverified`. Never confirmed, and the "instruction" wording is unsupported by the mechanism. |
| **Origin account 2** — Mara's private fear | Her own handshake bled something of hers into Nia. | `unverified`. Never confirmed, never dismissible. |

Neither origin account receives narrative confirmation, per the standing rule that Foreign_Signal
theories are always attributed and never promoted. Binding `DEC-007` gives Mara high private
conviction in account 2, Nia no unsupported attribution, and Julian a professional use of account 1
that he privately recognizes as inference.

### The incident

**Triage under scarcity**, which is where a wanting can hide, because triage is judgment rather than
protocol. Two calls arrive close together in her county with one available advanced unit. Ordinary
practice points one way. Her certainty points the other. She is not persuaded and does not reason —
she is simply sure, and she routes on it.

**Outcome:** the person on the call she deprioritized dies. Singular, serious, documented. No mass
casualty, no spectacle.

**Who the first casualty is.** These are two different people and every record must keep them apart.
**Nia** is the first documented casualty of mental intrusion: the injury is to her authorship of her
own judgment, it is the injury the histories name, and it is the one the archive gets wrong. **The
caller who dies** is a real emergency fatality that the timestamps later show was already unsurvivable
before Nia routed anything; that death is the documentary occasion for the record's entry, is not
caused by Nia, and is not the first Mindwars casualty in the classification this book uses. The
distinction is load-bearing rather than terminological. Collapsing it either turns the novel into a
story about a death Nia did not cause, or makes the classification look like a way of not counting a
dead civilian — and the second reading would be fatal to the book's moral credibility.

**The hours after:** she reconstructs her own reasoning and finds no chain. She can recover *what she
wanted* and not *why*. That absence, not the death, is what she cannot put down — it is the chapters
21–25 beat where she looks for a memory that generated the thought and there is none.

**What she fears:** not simply that she made a fatal call, but that the certainty behind it was not
hers. She cannot even own the mistake as her own mistake, which is why she refuses "case zero" — the
label would file the violation as a symptom.

### The evidence point — chapters 50–55

Dispatch is heavily logged: call times, unit assignments, transcripts, timestamps. Unlike Safiya's
loss, a corpus exists here and something can actually be checked.

The logs show the death was already unsurvivable before her routing decision. By the timestamps, no
assignment she could have made would have changed the outcome. Her decision was causally irrelevant.

**The relief does not relieve.** The log clears the outcome and proves nothing about the wanting. She
still cannot say whose certainty that was, and she now knows she *can be made certain* — which puts
every future judgment call under suspicion. That is the injury: epistemic, not consequentialist. It is
also precisely what qualifies her to build consent architecture in the Mindwars_Part, and what lets
her force Mara to hear the difference between receiving a signal and losing confidence in your own yes.

### Why this shape

It keeps the book's wound in the right place. Had her decision caused the death, the novel would become
about the death; the subject is authorship. Making the harm real but her causation nil preserves the
stakes while keeping the subject intact, and the asymmetry pays off in the Coda: Nia's injury is
unprovable, Safiya's is certain, and neither is dischargeable by consent.

It also hands `DEC-002` constraint 3 a concrete, checkable mechanism. Because a death occurred and a
log exists, this incident becomes the documentary anchor for the histories' "first casualty" entry.
Julian later finds it. The record names her the adversary's first loss on the strength of a dispatch
log that clears her decision and is silent on origin. The archive's opening entry is an inference its
own evidence does not support, and it can never be corrected.

### Load-bearing versus texture

Binding: triage under scarcity; a wanting rather than an instruction; one real death; logs that clear
the decision and not the authorship; release in chapters 50–55 driven by evidence; the log becoming the
record's anchor for the misattribution; Nia's refusal of "case zero."

Adjustable during Arc_Outline work (task 5.2) without an ArcChange: the specific nature of the two
calls, the unit type, descriptive county context that does not supply a proper county name, and any
supporting-character names. `DEC-005` keeps the country and individual counties unnamed. **Author
flag:** the two-call triage scenario is my construction, not yours. It satisfies every recorded
constraint, but if the specifics do not suit you, they are the replaceable part; the structure above
is what the spec depends on.

### Affected records and required synchronization

| Record | Change | State |
|---|---|---|
| `design.md` — Discovery 16–20 beat | "receiving an instruction" replaced with the wanting; the content-free-handshake tension resolved | done |
| `design.md` — Named POV Cast, Nia row | Blind spot rewritten: she fears a mistake the evidence will not confirm | done |
| `design.md` — Reveal Ledger | Consequence content fixed; release window and evidence basis recorded | done |
| `design.md` — Private Defense 50–55 beat | Evidence beat added to Nia's deposit | done |
| `design.md` — Open Choices 4 | Closed | done |
| `tasks.md` — 1.4, 12.4, 12.5, 13.4 | Outcome, mechanism, and evidence beat recorded | done |
| `planning/canon-bible.md` (task 4.2) | Record the wanting as the binding phenomenology; both origin accounts as `unverified` with no reveal owner; the dispatch log as the record's misattribution anchor | pending task 4.2 |
| `DEC-007` (task 1.7) | Binding asymmetric distribution: Mara high/private/non-authoritative; Nia refuses both accounts and moves toward release; Julian records the adversary inference professionally | `binding` |


## DEC-005 — Institutional and geographic names, post-null public visibility

- **Task:** 1.5 **[AUTHOR]**
- **Date:** 2026-09-09
- **State:** `binding`
- **Selected:** Keep the institutional names **Northline Array**, **Open Channel Consortium**, and
  **Civic Record Trust**; keep the country and every individual county unnamed; and use a
  **contested-archive** model after the null. Official summaries and the Trust’s
  provenance-preserving released record compete in public without either becoming an omniscient or
  final account.

### Rationale

The three existing names distinguish the story’s technical, commercial, and custodial institutions
cleanly, and `DEC-009` removes the discarded production-note objection to naming them. Replacing the
names would add continuity churn without adding narrative clarity.

Leaving the country and individual counties unnamed keeps attention on people, institutions, and the
canonical scale of harm without inventing a national analogue or local political map the story does
not need. This is selected geography, not missing planning: county functions and descriptive
locations remain available, but no proper country or county names are introduced.

The contested archive gives the post-null public sphere two visible records. Official summaries keep
institutional reach and smooth uncertainty into an adversary narrative. The Civic Record Trust makes
provenance-preserving releases and continues accepting witness-controlled deposits, so its record can
publicly challenge those summaries. The Trust authenticates custody and provenance, not the objective
truth of every account, and therefore cannot convert Julian’s professional adversary attribution into
proof or correct the archive’s opening error.

This is neither a fully open public inquiry nor a merely secret or one-time partial release. No single
inquiry compels the complete holdings, reconciles the accounts, or issues a final finding. At the same
time, the Trust is not hidden: records whose witness embargo and release conditions permit disclosure
enter an ongoing public contest, while unreleased holdings retain their conditions.

### Binding constraints

1. Use the exact institutional names `Northline Array`, `Open Channel Consortium`, and
   `Civic Record Trust` in planning and continuity-dependent prose.
2. Keep the country and all individual counties unnamed. Generic references such as “the country,”
   “the county,” county functions, and descriptive locations are permitted; proper fictional country
   or county names require reopening this decision.
3. Preserve the exact canonical extent as `three counties wide` or the equivalent formulation
   `affected area canonically described as three counties wide`. Do not substitute named counties,
   infer their boundaries, or convert the wording into a radial measurement.
4. After the null, official summaries and the Trust’s released record are both publicly visible and
   remain in contest. Trust releases honor witness embargo and release conditions; public visibility
   never implies that the complete holdings are open.
5. The Trust warrants provenance, not truth. The first-casualty adversary attribution remains the
   uncorrectable institutional inference required by `DEC-002` constraint 3 and `DEC-007`; no public
   process, release, narrator, or later record confirms or disproves either origin account.
6. Preserve the settled armistice facts: the Foreign_Signal is silent, active defender counterphase
   has ended, there is no surrender, counterparty, treaty, or all-clear, and the Coda contains
   postwar accounting rather than renewed war.
7. Preserve record chronology: Julian sees the April negotiation record altered before forming the
   Trust; Discovery-era logs and voice memoranda are composed before the Trust and deposited later
   with original provenance; rolling Trust deposits begin only after formation.
8. This decision changes no `DEC-002`, `DEC-003`, `DEC-004`, or `DEC-007` constraint. In particular,
   Nia’s usable-self-trust resolution supplies no factual closure, Safiya’s heritage base stays
   `unspecified_by_author`, and the dispatch evidence clears Nia’s routing decision without proving
   the wanting’s origin.

### Retired alternatives

| Alternative | Why retired |
|---|---|
| Rename one or more of the three institutions | The confirmed names already separate technical discovery, commercial pressure, and public-interest custody clearly. |
| Give the country or counties fictional proper names | Adds an unnecessary geopolitical map and risks weakening the exact canonical scale language. |
| Fully open public inquiry | A compelled, adjudicating inquiry would tend to resolve or officially settle the first-casualty attribution, violating `DEC-002` constraint 3. |
| Secret archive or merely partial release | Would remove the public competition between official summaries and witness records; release conditions remain, but the selected model is an ongoing visible contest rather than hidden custody or a single limited disclosure. |

### Affected records and required synchronization

| Record | Change | State |
|---|---|---|
| `design.md` — Testimony Frame and post-null beats | Replace complete-holdings/public-inquiry implications with conditioned public Trust releases competing with official summaries | done |
| `design.md` — Canon system, risks, acceptance review, and Open Choices 5/8 | Confirm names and unnamed geography; close post-null visibility on the contested-archive model | done |
| `tasks.md` — task 1.5 | Record the selected names, geography, public model, and constraints | done |
| `tasks.md` — planning, arc, and downstream drafting instructions | Carry the contested archive, release conditions, exact extent wording, and unresolved first-casualty attribution | done |
| `planning/canon-bible.md` (task 4.2) | Record all three names as approved Novel_Extensions, the intentionally unnamed geography, and the contested-archive/release model under `DEC-005` | pending task 4.2 |
| `planning/arc-outline.md` (task 5) | Place the public contest between official summaries and conditioned Trust releases without adding an adjudicating inquiry or hidden-only archive | pending task 5 |
| `DEC-006` (task 1.6) | Fix the reader-facing frame at one concise Front_Matter note plus rare in-story references while preserving `DEC-005` as the separate in-world public model | done |

---

## DEC-006 — Record-frame visibility: concise note, rare references

- **Task:** 1.6 Choose record-frame visibility **[AUTHOR]**
- **Date:** 2026-09-09
- **State:** `binding`
- **Selected:** Use one concise Front_Matter framing note plus rare in-story references. The overall
  visibility model is settled now and is not deferred to calibration.

### Rationale

Readers need one clear orientation to understand why first-person-past accounts from different periods
can coexist, but the archive must support the novel rather than become its visible apparatus. A concise
Front_Matter note establishes the Trust's chronology, custodial limit, and relation to the contested
public record once. Rare in-story references remain available when alteration, deposition, release
conditions, or witness control materially changes a scene.

Routine source notes, transcript conventions, and heavy archival labels would cool the immediate
novelistic testimony and turn provenance bookkeeping into a reading surface. The restrained model keeps
that bookkeeping available in planning while allowing the prose to invoke the record only when it has
dramatic work to do.

### Binding constraints

1. Front_Matter contains one concise framing note. It identifies the Trust's place in the record
   without becoming a dossier, chain-of-custody appendix, or recurring source-note system.
2. In-story references to the archive remain rare and appear only when dramatically necessary.
   Reader-facing chapters do not acquire routine source notes, transcript apparatus, docket labels,
   evidence citations, or heavy archival labeling.
3. Reader-facing chapter labels remain restrained. Planning metadata, record horizons, composition and
   deposit bookkeeping, and detailed chain-of-custody facts stay out of prose unless a specific fact is
   necessary to the scene.
4. The chronology is fixed: Julian sees the April negotiation record altered before forming the Civic
   Record Trust; Discovery-era logs and voice memoranda predate the Trust and are deposited later with
   their original provenance; rolling Trust deposits begin only after formation.
5. `DEC-005` remains the separate in-world public model. Conditioned, provenance-preserving Trust
   releases compete with official summaries; complete holdings are not presumed public; no unified
   inquiry adjudicates the records; and provenance does not certify objective truth.
6. Calibration may test whether an individual rare reference earns its place or should be removed. It
   may not replace this selected model with routine notes, transcript apparatus, or heavier archival
   labeling.
7. This decision changes no constraint established by `DEC-002`, `DEC-003`, `DEC-004`, `DEC-005`,
   `DEC-007`, `DEC-008`, or `DEC-011`.

### Retired option

| Option | Why retired |
|---|---|
| Defer exact record-frame visibility to calibration | The author selected the restrained model before calibration. Calibration now tests the dramatic necessity of individual rare references, not whether the manuscript should adopt a different overall apparatus. |

### Affected records and required synchronization

| Record | Change | State |
|---|---|---|
| `design.md` — Testimony Frame, Reader-Facing Labels, and Front Matter | Fix one concise framing note, rare dramatically necessary references, restrained labels, and planning-only custody detail | done |
| `design.md` — Design Acceptance Review and choice 6 | Close record-frame visibility under `DEC-006`; limit calibration to individual-reference necessity | done |
| `tasks.md` — task 1.6 and task 1 parent | Record the selection and complete the final blocking creative-decision task | done |
| `tasks.md` — tasks 2.2, 4.2, and 10.2 | Replace pending/deferred visibility language with the selected restrained model | done; implementation remains in the named later tasks |
| `DEC-001` task-2.2 dependency rows | Replace the stale task 3.1/3.2 block with the true unblocked state | done |
| `The Final Frontier Novel/front-matter.md` | Write the concise framing note without routine apparatus | pending task 2.2 |
| `planning/canon-bible.md` | Preserve the Trust chronology and `DEC-005` public model while distinguishing them from reader-facing presentation | pending task 4.2 |
| `planning/arc-outline.md` and Chapter_Files | Use in-story archive references only where dramatically necessary; do not add routine source-note fields to the reading surface | pending tasks 5 and drafting tasks |

---

## DEC-007 — Character belief strength: asymmetric, and Nia moves toward release

- **Task:** 1.7 **[AUTHOR]**
- **Date:** 2026-09-09
- **State:** `binding`
- **Selected:** Option 1, **“Asymmetric, and Nia moves toward release.”**

### Distribution

| Character / record | Binding position | What it does not mean |
|---|---|---|
| **Mara** | High private conviction that her later content-free handshake caused Nia’s wanting. She mostly leaves it unvoiced. Her guilt-seeking tendency to make herself central makes the conviction emotionally powerful but epistemically non-authoritative. | Her belief is not confirmation, privileged intuition, instrument evidence, or proof that the December receive-only rig transmitted. |
| **Nia** | Refuses both unsupported origin accounts and demands evidence. She rejects Mara’s attempted confession as an appropriation of Nia’s injury—the conceptual boundary is that Mara does not get to make the event hers. No exact line of dialogue is prescribed. | Her refusal is not proof against Mara’s account, acceptance of the archive’s adversary account, or absolution for Mara. |
| **Julian / the archive** | Professionally records the adversary attribution because it is the only institutionally enterable account, while privately knowing it is inference rather than proof. | Professional entry does not validate the attribution, correct the archive, or give Julian privileged knowledge. |

### Movement and resolution

Nia eventually stops needing to know the wanting’s origin. She regains usable self-trust: she can make,
review, and stand behind judgments without first proving whose certainty arrived. This resolves the
emotional question required by `DEC-002` constraint 5 while leaving the factual question open. It does
not decide causation, forgive Mara, or validate the archive.

Mara’s movement is different: she must learn that taking responsibility does not entitle her to own
the injured person’s account. Julian’s movement is to preserve the difference between an enterable
institutional claim and a true one even when his public record cannot repair the error.

### Binding constraints

1. Both origin accounts remain `unverified`: the archive’s adversary attribution and Mara’s belief
   that her later handshake caused the wanting.
2. Neither account has a reveal owner or release window.
3. No instrument, narrator, metadata record, chapter order, or later disclosure confirms or disproves
   either account.
4. Mara’s high conviction must remain character evidence of guilt and self-centralization, not a
   covert authorial answer.
5. Nia’s rejection of Mara’s attempted confession must preserve Nia’s ownership without requiring
   literal protected dialogue and without becoming absolution.
6. Nia’s release is from needing provenance in order to trust herself; it is not factual closure,
   forgiveness, or archive validation.
7. Julian may record the adversary attribution only with the private understanding that it is an
   institutionally usable inference rather than proof.

### Rationale

The asymmetry keeps the causal question alive without flattening three characters into equal agnostics
or allowing Mara’s guilt to answer the mystery. It gives each POV a distinct pressure: Mara wants to
confess, Nia refuses appropriation and demands evidence, and Julian must enter a claim he cannot certify.
Most importantly, it supplies the emotional landing required by `DEC-002`: uncertainty remains, but Nia
does not remain suspended inside it for 128 chapters.

### Retired options

| Retired option | Why retired |
|---|---|
| Leave belief strength pending for calibration | The author has selected the distribution; calibration now tests execution rather than deciding canon. |
| Give Mara, Nia, and Julian roughly symmetric uncertainty | Flattens POV function and gives Nia no movement from evidentiary refusal toward usable self-trust. |
| Let the characters converge on Mara’s account or the archive’s account | Would effectively confirm causation, absolve or condemn without evidence, and violate `DEC-002` constraint 1. |
| Let Nia’s release take the form of forgiving Mara or accepting the archive | Confuses emotional resolution with absolution or factual closure and violates the selected option. |

### Affected records and required synchronization

| Record | Change | State |
|---|---|---|
| `design.md` — POV rows and Voice_Briefs | Carry Mara’s non-authoritative conviction, Nia’s refusal/release, and Julian’s professional/private split | done |
| `design.md` — beat architecture and Reveal Ledger | Place the attempted confession/refusal, archive inference, and Nia’s Mindwars-to-Coda self-trust movement without adding a reveal | done |
| `design.md` — error handling, risks, acceptance review, Open Choice 7 | Treat drift as revision-worthy and close the choice | done |
| `tasks.md` — task 1.7 | Mark complete and record the exact distribution/movement | done |
| `tasks.md` — Canon_Bible, POV/voice, arc, calibration/editorial, and drafting tasks | Carry the distribution without over-specifying literal dialogue | done |
| `planning/canon-bible.md` (task 4.2) | Record both accounts as `unverified` with no owner/window and store the three positions plus Nia’s non-factual resolution | pending task 4.2 |
| `planning/pov-roster.md` / `planning/voice-briefs.md` (tasks 4.3–4.4) | Encode distinct pressures, evasions, and movement | pending tasks 4.3–4.4 |
| `planning/arc-outline.md` (task 5) | Place the belief/refusal/release beats while preserving record horizons and permanent factual ambiguity | pending task 5 |

---

## DEC-008 — Site isolation when the lyrics tooling is external

- **Task:** 3.1, 3.2 (spec re-scope)
- **Date:** 2026-09-08
- **State:** `binding` — confirmed by the author 2026-09-09
- **Selected:** Option B, the Manuscript_Exclusion_Contract.

### Situation

The author confirmed the lyrics-site tooling lives in a separate repository. This workspace contains
no `.tools/` directory, no `build_site.py`, and no song-index generator. The five current
Canon_Sources here are reference copies at `songs/The Synaptic Frontier.md`, `songs/Faraday.md`,
`songs/The Final Frontier.md`, `songs/The Radius.md`, and `songs/Case Zero.md`; `DEC-014` added the
fifth after this site-isolation decision. The *One-Time Pad* draft is preserved in git history and
removed from the working tree; it is not a
Canon_Source for the novel.

Requirements 9.2, 9.3, 11.9, and 12.8 were written on the assumption that Site_Build is editable from
this project. It is not. The design's research finding that `build_site.py` scans every visible
top-level directory has been withdrawn as unverifiable here.

### Options considered

| Option | Approach | Consequence |
|---|---|---|
| A | Drop the isolation requirements | Removes Req 9.2/9.3/11.9/12.8, Property 14, tasks 3.1/3.2/8.23. Nothing here can leak into an absent build, but protection is gone if the repositories are ever combined or the manuscript is copied across. |
| **B (selected)** | Manuscript_Exclusion_Contract | Keeps the requirement's intent as a portable declaration this project owns and the lyrics repository can adopt. Preserves Property 14 and the fixture test against a reference collector. States its own limit honestly. |
| C | Defer | Marks 3.1/3.2 blocked on an external dependency and revisits when the lyrics repository is available. Unblocks the critical path but leaves the obligation unowned indefinitely. |

### Author confirmation

Confirmed 2026-09-09. The author selected option B from the three options as presented. Options A
and C are `retired`. The contract file written by task 3.1 stands as the binding artifact, and task
3.2 is unblocked to build the reference collector on top of it.

Recorded alongside the confirmation, because the two are easy to conflate: the author also restated
that **the then-four original Canon_Source song files were fixed and were not edited by this project,
while the novel could diverge and grow beyond them.** `DEC-014` later added *Case Zero* as a fifth
binding Canon_Source without authorizing edits to any source lyric; the *One-Time Pad* draft is
preserved in git history and removed from the working tree.
That is a canon-authority position, not a tooling one, and it is already binding under `DEC-011` —
Canon_Lyric sits at tier 3 and Novel_Extensions at tier 6, free to add compatible facts but never to
contradict a higher tier. No option under `DEC-008` would have edited lyrics. What the contract
protects is the reverse direction: manuscript markdown must never be collected *as* a song.

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
| `requirements.md` — criteria 9.2, 9.3, 11.9, 12.8 | Wording retained as written; the Site_Build and Manuscript_Exclusion_Contract glossary entries govern how they are satisfied. The hold is released by the confirmation above; no rewording needed | done |
| `design.md` — research findings | Withdrew the `build_site.py` inspection claim | done |
| `design.md` — Manuscript Organization | Replaced the `EXCLUDED_SOURCE_FOLDERS` edit with the contract | done |
| `design.md` — Lightweight Checker location | Withdrew the false "beside existing `check_*.py`" rationale | done |
| `design.md` — Property 14, error handling, integration test 1, traceability, risks | Retargeted to the reference collector; added the non-adoption risk row | done |
| `design.md` — Open Choices 9 | Closed on confirmation; now points to this decision and marks A and C retired | done |
| `tasks.md` — 3.1, 3.2, 8.23, 2.2, Notes | Re-scoped; 2.2 unblocked | done |

### Retired options

| Option | Why retired |
|---|---|
| A — drop the isolation requirements | Rejected. The risk it dismisses is exactly the scenario where the two repositories end up side by side or the manuscript is copied across; at that point there would be no declaration and no test to catch a chapter entering song discovery. |
| C — defer as blocked-external | Rejected. Deferral leaves the manuscript root undeclared while 128 chapters accumulate, and "revisit when the lyrics repository is available" carries no forcing function. |

Reopening either is still a small, contained edit — A deletes Req 9.2/9.3/11.9/12.8, Property 14,
tasks 3.1/3.2/8.23, and the contract file; C reverts 3.1/3.2 to blocked-external — but neither is
pending. `DEC-008` is closed.

### Remaining external follow-up

Not a task in this spec and not part of its acceptance criteria. Tracked here so it is not lost:

| Item | Owner | Status |
|---|---|---|
| Adopt `exclusion-contract.json` in the lyrics repository's Site_Build source discovery, with a standing regression test against it | lyrics repository (external) | `not-adopted` |

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
- `DEC-005` later confirmed `Northline Array`, the Open Channel Consortium, and the Civic Record
  Trust, while deliberately leaving the country and individual counties unnamed. Those selections
  were made on narrative grounds, with no canon note to argue against.
- “The Mindwars” remains the canonical in-world term per Requirement 6.5. That is unaffected: it was
  always a name the songs used, not a namelessness exception the novel must honor.
- Canonical unnamed specificity such as “eleven miles from the array” remains usable as texture; it is
  no longer treated as a naming prohibition.

### Canon authority — resolved by DEC-011

The author delegated the authority choice. `DEC-011` makes lyric text and explicit author decisions
binding, while production notes are advisory unless an approved requirement or later author decision
expressly adopts a particular note. Namelessness therefore remains discarded; no exception is needed.

Facts checked directly against lyric text and therefore binding include December discovery, the
eight-second late morning, the April term sheet, page-nine `transmit enable`, three counties wide,
eleven miles from the array, two post-null years, the Tuesday kettle, three unhurried knocks, the
Mindwars term, the arriving thought that felt like her own, the null silencing the foreign voice while
the defender's own went quieter, the maternal-language loss, the visitor's spoken consent, and the
refusal grounded in not having her mother. Requirement 3's Coda constraints remain binding because
the author approved that structure independently.

---

## DEC-010 — Manuscript root renamed to `The Final Frontier Novel/`

- **Task:** 2.1 (manuscript layout), supersedes the recommendation under `DEC-001`
- **Date:** 2026-09-08
- **State:** `binding` — executed
- **Selected:** The manuscript root is **`The Final Frontier Novel/`**, renamed from `Mindwars Novel/`.

### Rationale

The author chose to align the directory with the title from `DEC-001` and to do it now, while the
manuscript contained a single planning file. This overrides the earlier recommendation to keep
`Mindwars Novel/` as a title-independent working path. The timing argument is the decisive one: the
same rename after 128 chapter files, a populated Motif_Ledger, and a 128-entry Arc_Outline would touch
far more references and risk missing some.

Naming the directory after the book also removes a small ongoing friction — a root whose name does not
match the title it holds invites confusion in every later path reference and editorial record.

### Disambiguation from the song

The root does not collide with `songs/The Final Frontier.md`:

- the songs live one level down in `songs/`, so the two paths never occupy the same namespace;
- the `Novel` suffix distinguishes the manuscript from the song by name alone;
- there is no local Site_Build, so no discovery routine is scanning for either.

### Executed changes

| Record | Change |
|---|---|
| Filesystem | `Mindwars Novel/` → `The Final Frontier Novel/`, carrying `planning/decisions.md` |
| `requirements.md` | All root path references updated |
| `design.md` | Title heading, Manuscript Organization root and tree, checker default root, staged-gate reference, Property 14, integration test 1, traceability row, open choice 1 |
| `tasks.md` | Tasks 1, 1.1, 2.1, 2.2, 3.1 path references |
| `tasks.meta.json` | Task 2.2 execution-history key retitled so its history stays associated |
| `decisions.md` | This file, including its own path references |
| Exclusion contract | Declared excluded root becomes `The Final Frontier Novel` when task 3.1 writes the contract |

Verified after the rename: `Mindwars_Part`, the `mindwars-part/` chapter directory, `mindwars-part-NNN-*.md`
filenames, and the canonical term `The_Mindwars` are all untouched. Only the exact root name, its
URL-encoded form, and the `mindwars-novel` property-test feature tag changed. The feature tag is now
`the-final-frontier-novel`, matching the spec directory.

### Note

Nothing in-world is renamed. “The Mindwars” remains the canonical historical term for the undeclared
war per Requirement 6.5, and `Mindwars_Part` remains the name of Main Part Three.

---

## DEC-011 — Canon authority and the title's governing premise

- **Task:** General canon authority; task 4.2 Canon_Bible input
- **Date:** 2026-09-08
- **State:** `binding`
- **Selected:** Lyric text and explicit author decisions are binding. Production notes are advisory
  unless a specific note is expressly adopted by an approved requirement or author decision.

### Authority order

When two sources conflict or differ in scope, the project uses this order:

1. **Explicit author decisions**, including direct instructions and dated records in this file.
2. **Approved requirements and design decisions** that formalize those instructions for the novel.
3. **Lyric text** in the five Canon_Source files, treated as binding story canon while allowing
   ordinary metaphor, compression, first-person limitation, and attributed testimony; a speaker's
   report is not automatically omniscient fact. `DEC-014` adds *Case Zero* at this same tier.
4. **Expressly ratified production-note material**, binding only because a higher tier adopted it. Its
   authority is the adopter's, so it never outranks the tier that ratified it.
5. **Approved Novel_Extensions**, which may add compatible facts but may not contradict a higher tier.

**Unratified Production_Notes sit outside this precedence order entirely.** They are advisory evidence
for motif, tone, structure, and possible interpretation. They cannot create a Binding_Canon_Fact,
Literal_Phrase_Constraint, naming rule, character identity, chronology, or continuity obligation, and
they **cannot defeat an approved Novel_Extension**. An advisory note that conflicts with an approved
extension loses. A note only ever wins by being ratified, and at that point its authority is tier 4's.

**Corrected 2026-09-13.** The earlier ordering listed unratified notes above Novel_Extensions, which
would have let non-story production commentary override author-approved continuity — precisely the
outcome `DEC-009` and `DEC-012` were recorded to prevent. No other tier changed.

Credit, copyright, performance, and recording metadata in the song documents are rights information,
not story canon. If the Canon_Bible cites a production note, it must record the higher-tier decision
that ratified the cited proposition or label the note `advisory`.

### Governing premise of *The Final Frontier*

The author confirmed the book's central meaning: **the final frontier was not outer space; it was our
own minds**. This is independently present in the lyric and therefore binding under tier 3:

- the apparent frontier begins “out there in the black” and is revealed “somewhere behind the eyes”;
- humanity expected to be the explorer, but the frontier “crossed us”;
- people become the shore, territory, and “new world” on which the landing occurs;
- the final chorus reclaims grammatical agency: the people who were crossed stand in the door and
  decide what may enter.

The novel title carries that reversal across the whole book. It must be earned dramatically rather
than explained as a thesis: Discovery points outward through spectrum, Private Defense discovers the
door runs inward, and Mindwars reveals human minds as the contested territory. The Mindwars are an
event within that argument, not another title for the novel. The Aftermath/Coda then asks what the
successful defense removed from the territory it protected.

### Ratified production-note material

The following note-derived ideas remain binding because the requirements or author decisions already
adopted them independently:

- three Main Parts plus a shorter postwar Aftermath/Coda that does not restart the war;
- the consent rule distinguishing a shield from an occupier;
- the carried motif architecture explicitly enumerated in Requirement 7;
- testimony and record framing adopted by the requirements and design;
- qualitative production-language translation into Voice_Briefs and Reverb_Profiles;
- the Refused_Swell and the Coda's move toward domestic room tone and human presence.

Their authority comes from those adoptions, not from the production-note layer itself. Other note-only
claims — including namelessness and any implication that a returned motif proves two people share an
identity — remain advisory or rejected.

### Consequences

- `DEC-009` is confirmed without requiring a special exception.
- The named and mechanistic Nia source/casualty braid remains controlled by `DEC-002`; `DEC-014`
  additionally makes *Case Zero*'s same-speaker account binding Canon_Lyric as attributed testimony.
  Neither layer confirms that Mara's handshake caused the wanting.
- Literal_Phrase_Constraints arise only from lyric text plus explicit specification/author adoption.
- Task 4.2 must tag every CanonFact with its authority basis and must never promote an advisory note
  into binding continuity merely because it appears under “Production notes.”
- The design's title reversal and Chapters 86–93 territory turn are binding expressions of this
  premise, not optional motif commentary.

---

## DEC-012 — ESP / Electronic Speech Pairings

- **Task:** General mechanism terminology; tasks 4.2–5.4 planning input
- **Date:** 2026-09-08
- **State:** `binding`; mechanism scope clarified and completed by `DEC-015`
- **Selected:** `ESP` expands in-world to **Electronic Speech Pairings**. One addressed, mutually
  calibrated link is a **pairing**. The term is an approved Novel_Extension under `DEC-011`, with
  authority `DEC-012`; it is not lyric-level canon.

### Meaning and chronology

`ESP` is a contested institutional simplification. It usefully names the near-natural internal-speech
conversation available inside a valid consented pairing, but it can also blur the decisive difference
among observation, unconsented influence, and deliberate conversation. Characters may dispute the
name without requiring the false claim that fluent paired conversation is not speech-like at all.

The term is coined only after Discovery — in Private Defense at the earliest — and later histories may
apply it backward as a label. Discovery POVs do not use it as established language. The late label does
not revise the apparatus: December remains receive-only with no transmit stage; Mara's later temporary
bench path remains a separate deliberate addition; and page-nine `transmit enable` remains later
evidence of broader architectural capability rather than retroactive evidence about December or Nia's
wanting. The acronym deliberately collides with discredited extrasensory perception, giving public and
institutional actors a means of mockery or mystification without validating a supernatural mechanism.

### Binding terminology and register constraints

1. **The mode boundary is mandatory.** `RECEIVE` observes a live experiential or attentional signal,
   `INTRUDE` performs an addressed unconsented low-dimensional write, `CANCEL` emits an unaddressed
   subtractive counterphase field, and `PAIR` carries deliberate near-natural internal speech after
   mutual pair-specific calibration. The single institutional label may not collapse those four modes
   into one capability. `ESP` names paired conversation in particular and never legitimately describes
   observation, unconsented influence, or cancellation.
2. **Unconsented influence remains nonsemantic.** Without consent and pair-specific calibration, a
   write may alter only crude salience, valence, urgency, certainty, preference, or wanting. It cannot
   carry language, propositions, commands, a voice, arbitrary memories, or a semantically readable
   signature.
3. **Consented pairing is fluently conversational.** Two living people with current, specific,
   revocable consent and pair-specific joint calibration may deliberately exchange near-natural
   internal speech. A deliberate cognitive send act gates every contribution; unoffered thoughts,
   images, memories, and emotions remain private.
4. **No origin closure follows.** The terminology and fluent capability supply no evidence for either
   account of Nia's earlier uncalibrated wanting and change no `DEC-002`, `DEC-004`, or `DEC-007`
   ambiguity.
5. **Register remains uneven.** Julian, institutions, histories, and public argument carry most uses
   of `ESP`; Mara uses the term rarely and technically; Nia resists the label when it obscures consent
   state or makes her wanting sound like conversation.
6. **The old acronym stays cultural, not causal.** Public mockery may invoke supernatural ESP, but
   neither narration nor mechanism validates extrasensory perception.

### Operational paired use

Operational pairs in Chapters 78–93 may be fluent after sustained mutual calibration rather than
restricted to a small codebook. Supporting operatives may remain supporting characters or deposited
records inside existing POV chapters; fluency creates no new POV requirement and no sender/adversary
viewpoint. Traffic analysis may inspect timing and transport metadata, but it cannot recover unrecorded
meaning. Any deliberately recorded content follows the separate mutual-consent rules in `DEC-015`.

Operational pairing remains categorically distinct from Safiya's organic, relational, corpus-less
private layer. A live calibrated partner can deliberately send; Safiya's mother is dead, Safiya cannot
send what the null removed, and no source corpus survives. Human spies, institutions, endpoints, or
recordings never become a hidden solution to Foreign_Signal or Nia-wanting provenance.

### Retired alternatives

| Alternative | Why retired |
|---|---|
| Literal supernatural ESP | Contradicts the physical, evidentiary mechanism and would turn public mockery into confirmation. |
| Treating unconsented influence as verbal telepathy | Contradicts the wanting, the content-free handshake, and the nonsemantic limit of `INTRUDE`. |
| **Superseded fixed-token ceiling** | Consented, pair-specific calibration now supports deliberate near-natural internal speech; tokens may remain a training or operational fallback, not the capability ceiling. |
| Pre-Discovery coinage | Erases the late institutional naming process and falsely gives Discovery characters settled language. |
| Transferable or installable calibration | Would erase pair-specific consent and permit access without the two living calibrated participants. |
| Operative or sender POVs | Breaks the fixed four-human-POV architecture or falsely closes provenance. |
| A paired channel duplicating Safiya's loss | Conflates live voluntary sending with an organic private layer whose second participant and source corpus are gone. |

### Affected records and required synchronization

| Record | Change | State |
|---|---|---|
| `planning/decisions.md` | Replace the broken partial amendment with this coherent terminology decision and complete `DEC-015` | done in corrective design-first pass |
| `design.md` | Distinguish all four modes, fluent consented pairing, evidence boundaries, mandatory beats, and Safiya limit | synchronized in corrective design-first pass; four-mode wording corrected 2026-09-13 |
| `requirements.md` | Add testable mode, consent, evidence, beat, and protected-boundary requirements | synchronized in corrective design-first pass |
| `tasks.md` | Carry the decisions into existing planning, checker-fixture, arc, and drafting tasks without renumbering | synchronized in corrective design-first pass |
| `planning/canon-bible.md`, `planning/pov-roster.md`, and `planning/voice-briefs.md` | Replace the old token ceiling and record the completed mechanism/register boundaries | pending subsequent Task 4 execution wave |
| `planning/arc-outline.md` | Select exact fluent pairs and place every mandatory use beat without changing the four POV loads | pending Task 5 |
| `songs/*.md` | No source-song edit; the term remains a novel extension rather than retroactive lyric fact | unchanged |

---

## DEC-013 — *Case Zero* draft companion status (superseded history)

> **Superseded by `DEC-014`.** This section preserves the prior author decision and the state that
> governed before *Case Zero* was approved for publication and promoted to the fifth binding
> Canon_Source. It is historical only and must not be used as current-state guidance.

- **Task:** General canon authority; task 4.2 Canon_Bible input
- **Date:** 2026-09-08
- **State:** `superseded-by-DEC-014`
- **Selected:** `songs/Case Zero.md` is an **unpublished, unproduced draft companion
  counter-deposition**. It is not a fifth binding Canon_Source and is not an approved release or
  publication. The four primary Canon_Sources remain exactly *The Synaptic Frontier*, *Faraday*,
  *The Final Frontier*, and *The Radius*.

### Authority and permitted use

This classification is an explicit author decision and therefore controls over any inference from the
file's location under `songs/` or its lyric-like form. The draft is downstream of the author decisions
already recorded here. Its propositions are advisory unless a requirement or explicit author decision
independently ratifies them.

It may inform Nia's voice, civilian-loss intake work, consent-protocol authorship, her refusal of
“case zero,” the logs clearing her decision but not authorship, and “Go ahead” as her permission
phrase. It does **not** by itself lock the shower, a twenty-minute interval, ten-to-seven, five people
and a whiteboard, revocation at noon, or diegetic wartime songs or choirs. Those details remain free
unless separately approved.

### Compatibility and literal constraints

The companion must remain compatible with `DEC-002`, `DEC-004`, and `DEC-007`: Nia receives a wanting,
not a message; the institutional record remains wrong; she accepts neither origin account; and she
eventually uses her own judgment without factual closure, absolution, or archive validation. Nothing
in the draft confirms Mara's belief or the archive's attribution.

Chapter-file Literal_Phrase_Constraints scan Chapter_File Prose_Bodies, not this companion. Its use of
“Did I say yes?” creates no chapter violation. “Whose was that?” remains absent, so the novel's final
phrase is not spent by the draft.

### Release status and rights follow-up

Presence under `songs/` is not release approval. External Site_Build publication and visibility are
unverified and require a separate explicit author release decision. This project cannot enforce or
claim external nonpublication.

The draft footer simultaneously claims Suno performance copyright and public-domain status. That
conflict remains an unresolved author/rights-review follow-up. This record supplies neither a legal
conclusion nor replacement rights language.

### Retired alternative

| Alternative | Why retired |
|---|---|
| Promote *Case Zero* to a fifth Canon_Source | Rejected unless the author explicitly reopens this decision; promotion would collapse a downstream advisory draft into lyric-level canon and could falsely imply release approval. |

### Affected records and required synchronization

| Record | Change | State |
|---|---|---|
| `design.md` — source authority, canon system, literal scope, error handling, and risks | Distinguish the four binding sources from the advisory unpublished companion | done |
| `tasks.md` — Canon_Bible and Notes instructions | Preserve advisory status, nonbinding details, literal-scan scope, unverified publication, and rights follow-up | done |
| `planning/canon-bible.md` | Record the companion classification and its permitted/advisory uses without promoting its propositions | pending task 4.2 |
| External Site_Build release/visibility | Require a separate author release decision; do not infer publication from path | `unverified` / external |
| Author/rights review | Resolve the contradictory performance-copyright/public-domain footer claims | unresolved, nonblocking for current planning |
| `requirements.md` | No live requirement changes; the glossary already names exactly the four primary Canon_Sources and literal checks already apply to Chapter_Files | n/a |
| `songs/Case Zero.md` and the four Canon_Source files | No content changes | n/a |

---

## DEC-014 — *Case Zero* publication and Canon_Source promotion

- **Task:** Author-decision synchronization only; task 4.2 Canon_Bible input
- **Date:** 2026-09-09
- **State:** `binding`; supersedes `DEC-013`
- **Author decision (verbatim):** **“case zero is being published now and is now canon.”**
- **Selected:** Publication of `songs/Case Zero.md` is author-approved and in progress as stated by
  the author, and the song is now the fifth binding Canon_Source for this novel.

### Exact Canon_Source inventory

The Canon_Source set now contains exactly these five files:

1. `songs/The Synaptic Frontier.md`
2. `songs/Faraday.md`
3. `songs/The Final Frontier.md`
4. `songs/The Radius.md`
5. `songs/Case Zero.md`

`songs/One-Time Pad.md` is not in that set. The immediately preceding author decision was to keep the
draft after reviewing it as nonbinding. It was committed for archival preservation in `4cd23e2` and
then removed from the working tree in `3828f40`, so it is preserved in git history, absent from the
working tree, unpublished, noncanonical for book purposes, and supplies no binding continuity for this
novel. The decision to exclude it is unchanged; only its storage location is stated accurately here.

### Authority boundary

Under `DEC-011`, the **lyric text** of *Case Zero* now has the same tier-3 authority as the lyric text
of the other four Canon_Sources. Ordinary metaphor, compression, first-person limitation, and
attributed testimony still apply. Nia's first-person statements are binding as her canonical account;
they are not automatically omniscient proof of every inferred cause, institutional fact, or literal
staging detail.

Promotion does not turn the song's Production_Notes, style prompt, exclude-style list, generation
workflow, credits, or rights metadata into story canon. Those materials remain non-story metadata or
advisory interpretation unless a higher-tier requirement or author decision separately ratifies a
specific proposition. In particular, production directions cannot establish a character identity,
chronology, mechanism, literal diegetic event, or protected wording by themselves.

### Compatibility with `DEC-002`, `DEC-004`, and `DEC-007`

The canonical Nia account remains inside the existing protected structure:

- what arrived was a wanting or certainty, not words, a voice, or an order;
- the archive's adversary attribution and Mara's handshake theory both remain `unverified`;
- no lyric statement, instrument, narrator, metadata record, or publication status confirms whether
  Mara's later content-free handshake caused the wanting;
- Nia's limited exoneration does not identify the wanting's origin;
- Nia's usable self-trust supplies neither absolution for Mara nor validation of the archive.

*Case Zero* now supplies binding first-person lyric testimony that the same speaker reports the
December morning and the later wanting. `DEC-002` still controls the proper-name mapping to Nia, the
person-specific channel and bench-path mechanism, and the protected causal sequence. The Canon_Bible
must keep those authority layers explicit rather than either ignoring the lyric or converting Nia's
testimony into omniscient causal proof.

### Lyric-fact inventory for task 4.2

Task 4.2 must inventory at least the following lyric facts with `authority_basis: lyric`, speaker and
source location, and an attribution/limitation note where appropriate:

| Lyric material | Required Canon_Bible treatment |
|---|---|
| Nia's ordinary December details: alarm, shower, road call, twenty minutes, and the console at ten to seven | Binding as details Nia reports in her first-person account; do not silently convert recollection into an external omniscient timestamp record. |
| The eight-second offset belonged to the receiver; Nia experienced no source-side gap | Binding account consistent with the receive-only December chronology and `DEC-002`. |
| Two close calls, one available unit, routing against ordinary practice, and one death | Binding as Nia's account of the triage event; keep the arriving state a wanting rather than an articulated instruction. |
| The five-person/whiteboard consent confrontation | Binding as Nia's reported scene; preserve first-person testimonial scope. |
| Consent must be current, specific to the requested act, and revocable, with noon as the lyric's example | Binding consent testimony and chronology detail; the noon example does not become a universal deadline rule. |
| The histories and songs appropriated Nia's experience | Binding as Nia's testimony about appropriation; the lyric does not automatically prove a literal diegetic choir or every production-stage image. |
| Logs showed the death was already unavoidable before her routing while remaining silent on who wanted it | Binding limited exoneration; no origin account is confirmed. |
| Nia's postwar civilian-loss intake work | Binding as her reported postwar role and continuation of usable self-trust. |
| “Go ahead.” | Canonical permission phrase spoken by Nia; record dialogue provenance if adapted or quoted in a Chapter_File. |

This inventory is a minimum for later Canon_Bible work, not permission to treat every first-person
inference as objective fact. The ordinary details and reported scenes may constrain continuity while
their epistemic form remains testimony.

### Literal constraints and rights

Occurrences of protected phrases in *Case Zero* do not change the existing Chapter_File-only literal
scan boundary. Song lyrics, including Canon_Source lyrics, remain outside Chapter_File Prose_Body
scans unless an approved requirement explicitly expands the scope.

The footer still contains contradictory performance-copyright and public-domain claims. That remains
an unresolved, nonlegal author/rights-review issue. Publication approval, publication in progress, and
Canon_Source promotion do not resolve the contradiction, supply a legal conclusion, or authorize
replacement rights language.

### Affected records and synchronization

| Record | Required current state | State |
|---|---|---|
| `requirements.md` | Exactly five Canon_Sources; lyric/production boundary; *One-Time Pad* excluded | synchronized with DEC-014 |
| `design.md` | Fifth-source authority, attributed-testimony handling, checker/tests/risks, and superseded DEC-013 | synchronized with DEC-014 |
| `tasks.md` | Task 2.2 acknowledgment and future Canon_Bible/checker/test instructions use exact-five state without changing task completion or DAG | synchronized with DEC-014 |
| `planning/canon-bible.md` | Add the inventory and authority layers above | pending numbered task 4.2; not executed by this synchronization |
| `songs/Case Zero.md` | Update only non-lyric publication/canon metadata and unresolved-rights warning | synchronized with DEC-014 |
| Four original Canon_Source files | No change | unchanged |
| *One-Time Pad* draft | No change; preserved in git history, removed from the working tree, and noncanonical | unchanged |

---

## DEC-015 — Four-mode neural communication and evidence boundary

- **Task:** Corrective design-first mechanism decision; tasks 4.2–5.6 and 7–8 planning/checker input
- **Date:** 2026-09-10
- **Amended:** 2026-09-11 — fourth mode `CANCEL` added; see the amendment note below
- **State:** `binding`; approved NovelExtension/mechanism authority
- **Selected:** The novel uses four non-overlapping communication modes—`RECEIVE`, `INTRUDE`, `CANCEL`,
  and `PAIR`—with fluent consented pairing, explicit evidence boundaries, and mandatory on-page use
  through the middle of the book.

### Amendment note — 2026-09-11: the fourth mode

The original decision defined three modes, and none of them described **subtraction**. `RECEIVE`
observes and writes nothing at all; `INTRUDE` writes crudely; `PAIR` transports deliberately offered
speech. Two of the three insert and the third only observes, but the null subtracts, and no mode in the
taxonomy did.

That omission produced a real contradiction. The null-night chronology records an active transmit
stage with no person-specific address whose effect cancels the Foreign Signal and causes subtraction.
Under the original three-mode taxonomy the only available classification was `INTRUDE`, but `INTRUDE` is
limited to nonsemantic salience, valence, urgency, certainty, preference, or wanting. Safiya losing
access to her private maternal layer is not a preference. Every neural event must occupy exactly one
mode, and the only mode the null could occupy forbade what the null canonically does. The entire Coda
rests on that event, so the gap was load-bearing.

The canon already carried the distinction the taxonomy lacked: Nia's first injury is insertion,
Safiya's is defensive subtraction, and `DEC-002` constraint 4 makes the asymmetry structural. This
amendment adds `CANCEL` to name the subtractive case that was always present in the story.

Nothing else changes. The amendment creates no new decision number, adds no capability, and reverses
no prior constraint. December remains receive-only with no transmit stage. `INTRUDE` keeps its
nonsemantic limit unchanged; the null is simply no longer an `INTRUDE` event. Page nine remains
evidence of broader architectural capability only. Both origin accounts of Nia's wanting remain
`unverified`, with no reveal owner and no release window.

### Mode A — `RECEIVE` / observation

`RECEIVE` is passive observation. In December, Mara's apparatus has no transmit stage and resolves
Nia's continuous live experiential and attentional field with an eight-second reception/transport
offset at Mara's receiver and a person-specific address lock. Nia does not deliberately author speech
to Mara and experiences no gap.

A rich observed stream does not imply a rich unconsented write. The receiver measures and models
high-dimensional structure already present in the live field; it injects no pattern into Nia. Writing
requires active modulation of another field. Semantic conversation additionally requires the two
participants to build a pair-specific encode/decode mapping through mutual calibration and to perform
deliberate send acts. Read resolution, write bandwidth, and semantic authorization are therefore
separate capabilities rather than symmetric permissions.

### Mode B — `INTRUDE` / unconsented write

`INTRUDE` is an active write without valid pair consent and calibration. Its channel is deliberately
low-dimensional: it can alter salience, valence, urgency, certainty, preference, or wanting. It cannot
carry language, propositions, commands, a voice, arbitrary memories, or a semantically readable
signature.

Mara's later content-free bench handshake and Nia's wanting are separate from December in apparatus,
time, and mode. The handshake may be causally relevant, but both the handshake account and adversary
account remain `unverified`, with no reveal owner or release window. Neither later fluent pairing,
transport evidence, endpoint evidence, nor page-nine `transmit enable` may retroactively identify the
origin or give December a transmit stage.

### Mode C — `CANCEL` / unaddressed subtractive counterphase

`CANCEL` is an active counterphase cancellation field. It is the mode of the bounded Chapter 73
counterphase test and of null night; those are one mode at two scopes, not two mechanisms. Eight
properties are binding.

1. **Unaddressed and field-volume based.** A `CANCEL` event carries no person-specific address. This is
   the structural reason it is not `INTRUDE`: `INTRUDE` requires a person-specific target and
   cancellation has none. It propagates across whatever field volume the emitter reaches, which is why
   one mode covers both a single bounded room and an area canonically described as three counties wide.
2. **Nonsemantic in both directions.** It carries no language, proposition, order, voice, or memory,
   and it reads nothing back. It is a cancellation field, not a message.
3. **Subtractive, not insertive.** Its effect is the removal or degradation of access to mental
   content and faculties. It inserts nothing. This is what makes Safiya's loss mechanically possible
   while keeping it categorically distinct from the insertion that injured Nia.
4. **Spatially boundable, never person-targetable.** The emitter controls the field volume: Mara can
   confine a cancellation to one room and can run it across a wide area. What she cannot do is aim it
   *inside* that volume. Which faculties, memories, and people lose what cannot be predicted before the
   event, enumerated during it, or fully mapped after it, so her model predicts that subtraction may
   occur and can never identify whose. Both halves are load-bearing: spatial control is what makes the
   bounded Chapter 73 test possible at all, and the absence of targeting inside the volume is why null
   night harms civilians nobody chose. This is already canon in the civilian-harm fact and the Chapters
   94–101 chronology; it is now a mode property.
5. **No additive inverse.** Cancellation has no reverse operation. Nothing removed by a cancellation
   can be restored by another cancellation, by `PAIR`, or by any combination of modes. This is a
   second, independent physical reason Chapter 124's refusal is truthful rather than scrupulous:
   even if Mara possessed Safiya's mother and the erased corpus, the mechanism still has no undo.
6. **Consent cannot scale.** Individual consent is obtainable for a bounded local cancellation, which
   is what Chapter 73 tests, and is structurally unobtainable at area scale, which is null night.
   Area-scale authorization is therefore institutional and never individual consent from everyone
   affected. Nia's refusal of manufactured unanimity stands: no consent record and no pair transcript
   speaks for the affected area.
7. **Confined to the Mindwars Part.** `CANCEL` begins and ends inside Mindwars, preserving the
   settled armistice facts and the noncombat Coda. The Coda's retained capacity is deliberately
   switched off rather than used.
8. **Supplies no provenance.** Cancelling the Foreign Signal reveals nothing about its source.
   Silencing a transmission is not identifying it. Both accounts of Nia's wanting and the
   Foreign Signal's origin remain `unverified`.

### Mode D — `PAIR` / consented conversation

`PAIR` is an intentional conversational channel between exactly two living people. Both participants
must hold current, act-specific, revocable consent and complete joint calibration unique to that pair.
After calibration, each participant can deliberately send near-natural internal speech to the other.
A cognitive send gate is required for every contribution; unoffered thoughts, imagery, memories,
emotions, and background mentation remain private.

Calibration is mutual, pair-specific, and nontransferable. It cannot be installed from another pair,
reused with a replacement partner, or applied to a dead or absent person, simulation, archive, model,
or reconstruction. Trained partners may reach operational fluency through repeated sessions rather
than an implausible one-time miracle. The protocol must expose session start, deliberate send state,
acknowledgment, pause, revocation, latency, and integrity/error state. Either participant can pause or
revoke immediately; the semantic channel then stops rather than guessing, completing, or buffering an
unoffered meaning. Latency, clipping, or integrity failures are surfaced as transport failures and
handled through confirmation or ordinary speech, not silently repaired into presumed content.

### Evidence and logging boundary

Every authorized pairing produces mandatory consent-state and transport metadata: participant and
pair addresses, consent start, pause, revocation, session timing, channel volume, and integrity/error
events. This metadata can establish that a channel existed and how it behaved; it cannot reveal
unrecorded semantic content.

Content recording is a separate option, off by default, and requires explicit mutual consent distinct
from consent to pair. A consensual transcript proves only what the protocol carried during that
recorded pairing. It does not prove either participant's unoffered thoughts, complete mental state,
private intent, memory source, or truthfulness. No system can retrospectively reconstruct unrecorded
meaning from transport metadata.

Endpoint compromise or unauthorized content logging may become an institutional danger only if Task 5
selects and bounds that plot use. It cannot reveal the source of Nia's earlier uncalibrated wanting,
which had no pair-specific semantic channel or content transcript, and it cannot become a hidden route
to Foreign_Signal provenance. Civic Record Trust custody continues to warrant provenance of a record,
not objective truth within it.

### Safiya and the hard source boundary

A pairing requires two living consenting minds and voluntary send acts. Safiya cannot pair with her
dead mother, an archive, a model, or a reconstruction. Safiya also cannot voluntarily send what the
null removed, and no source corpus of the private maternal layer survives. Fluent pairing therefore
does not weaken Chapter 124: Mara's refusal remains a physics-and-truth limit because any fabricated
replacement would be Mara's construction and could falsely self-authenticate as Safiya's own memory.
Safiya's consent remains valid; consent cannot manufacture the absent source.

`CANCEL` closes the remaining escape route. What the null took, it took by cancellation, and
cancellation has no additive inverse. The loss cannot be undone by another `CANCEL`, carried back by
`PAIR`, recovered from consent or transport metadata, read out of a Pairing Transcript, or rebuilt
from a simulation, archive, model, or reconstruction. Chapter 124 therefore rests on two independent
physical limits rather than one: Mara lacks the source truth, and the mechanism has no reverse
operation.

### Mandatory on-page use and deferred pair identities

Fluent pairing is a major middle-book capability, not optional background:

1. **Chapters 36–42:** legitimate benefits are demonstrated and pair-specific calibration begins, so
   readers understand why people freely choose the technology.
2. **Chapters 56–61:** the first sustained fluent conversation appears on page and demonstrates the
   send gate, pause, revocation, latency/integrity handling, and one consent-protocol failure followed
   by a concrete repair.
3. **Chapters 70–77:** pairing operates under counterphase pressure; Chapter 73 retains the exact
   question `Did I say yes?` and tests local/current consent and Nia's authority without absolution.
4. **Chapters 78–93:** operational paired communication becomes a principal thriller engine. Existing
   POVs or supporting operatives inside existing POV chapters may carry fluent exchanges; traffic
   analysis sees transport patterns and metadata, not unrecorded meaning.
5. **Chapters 94–108:** scale exposes ethical and infrastructural risk without producing group mind,
   hive mind, mass mind reading, or evidence of the Foreign Signal's source.
6. **Chapters 109–112:** Nia's usable-self-trust resolution and the contested public record remain
   intact.
7. **Chapters 113–128:** neural communication recedes; ordinary spoken voice, listening, presence,
   and the Chapter-124 refusal retain their force.

Task 5 selects the exact fluent pairs and session ownership. That deferred selection may not add a POV,
change the 56/32/33/7 loads, create a sender/adversary viewpoint, make the supporting-operative thread
mandatory, or omit any required range-level beat.

### Protected boundaries

This decision preserves `DEC-002`, `DEC-003`, `DEC-004`, `DEC-005`, `DEC-007`, `DEC-011`, `DEC-012`,
and `DEC-014`: exact five Canon Sources; unresolved wanting and Foreign_Signal provenance;
`heritage_base: unspecified_by_author`; the canonical extent `three counties wide`; protected phrase
placement; the four human POVs; the settled null; and the quiet noncombat Coda. It authorizes no
unconsented language, arbitrary memory access, retrospective semantic readback, pairing with a dead or
absent participant, transferred calibration, sender POV, or third-act provenance solution. Adding
`CANCEL` authorizes no new capability either: it names the subtraction the null already performed,
keeps that subtraction irreversible, and leaves `INTRUDE`'s nonsemantic limit exactly as written.

### Affected records and required synchronization

| Record | Required current state | State |
|---|---|---|
| `planning/decisions.md` | Complete the missing authority and repair DEC-012 without a token ceiling; add `CANCEL` as the fourth mode | done; `CANCEL` added 2026-09-11 |
| `design.md` | Define modes, interfaces, evidence model, mandatory beats, risks, tests, and Coda limit | synchronized; four-mode architecture added 2026-09-11 |
| `requirements.md` | Add EARS-compliant mode, consent, evidence, usage, and prohibition criteria | synchronized; `CANCEL` criteria added and Requirements 14–15 trimmed 2026-09-11 |
| `tasks.md` | Update existing Task 4/5/7/8 and drafting prompts without checkbox, numbering, or DAG changes | synchronized; four-mode and renumbered references applied 2026-09-11 |
| `planning/canon-bible.md` | Replace token-only EXT-ESP state; add four-mode, evidence, transcript-scope, and Safiya boundary records | executed by task 4.2; four-mode wording corrected 2026-09-13 |
| `planning/pov-roster.md` | Add fluent-pair capability and privacy/evidence boundaries without changing four profiles or loads | pending subsequent Task 4.3 execution |
| `planning/voice-briefs.md` | Replace token-only register instructions and describe deliberate paired speech from each relevant POV | pending subsequent Task 4.4 execution |
| `planning/arc-outline.md` | Select exact pairs and encode every mandatory range-level beat | pending Task 5 |
| `planning/record-schemas.md` | Extend `TimelineEntry.technical_state` with the four-mode enum, consent/calibration/send state, `CANCEL` subtraction state, and pairing evidence fields; add no new record type | done 2026-09-11 |
| Motif, editorial, and arc-change records and chapter prose | No changes required by this mechanism decision | unchanged; later numbered work only where already planned |
| `songs/*.md` | No source lyric or song-file change | unchanged |

---

## DEC-016 — Original rotating-perspective technothriller architecture

- **Task:** Corrective design-first craft and architecture direction; tasks 5 and later drafting input
- **Date:** 2026-09-10
- **State:** `binding`; craft/architecture authority, not Canon Lyric and not a Binding Canon Fact
- **Selected:** Use original short-chapter, rotating-viewpoint commercial-technothriller architecture
  that combines rapid information-driven cross-cutting with premise-forward neurotechnology escalation.
  The named inspirations supplied by the author identify high-level structural strengths only; this
  novel must not imitate Dan Brown's or Douglas E. Richards's sentence-level prose, distinctive voice,
  phrasing, scenes, characters, or proprietary expression.
- **Amended 2026-09-13:** target 1 now limits continuous same-POV exposure by word count as well as by
  chapter count, and the thread description is corrected to match the actual load distribution.

### Thread structure, stated accurately

The book runs **three active threads through Chapters 1–112 and then adds a fourth viewpoint that
changes the moral scale of the Coda.** Safiya holds no chapter before 115. Describing this as a
four-thread rotation throughout is wrong about the plan and would send reviewers looking for a Safiya
thread the architecture deliberately does not have.

The late entrance is a strength rather than a compromise. Putting Safiya in Discovery or Mindwars
chapters would either make her a bystander waiting for her own injury or give the reader advance access
to a subtraction the Coda needs to receive as testimony. Her absence is what lets Chapter 118 land. The
real cost is that she carries very large weight across seven chapters, which is recorded as a craft risk
rather than treated as an architecture problem.

### Binding architecture targets

1. Each chapter remains short, first-person past, and exactly one POV. The threads rotate under a
   **two-part same-POV run limit**, because chapter count alone does not control how long a reader stays
   inside one viewpoint.

   A **same-POV run** is a maximal uninterrupted sequence of chapters assigned to one `pov_id`. Every
   run must satisfy both limits:

   | Limit | Value |
   |---|---|
   | Maximum chapters per run | **3** |
   | Maximum combined Prose_Words per run | **3,600** |

   The word limit is the operative one. Under the chapter cap alone, three normal chapters could reach
   4,800 Prose_Words, three maximum-length chapters could reach 7,500, and even a two-chapter run could
   reach 5,000 — so a chapter break could disguise an overlong stay in one head. At 3,600 a
   three-chapter run averages at most 1,200 Prose_Words, inside the Normal Chapter Range and consistent
   with the roughly 1,094-word planning average.

   Application rules:

   - Runs are counted on the global chapter sequence, so the movement boundaries at 29/30, 61/62, and
     112/113 are counted like any other adjacency.
   - The single-chapter Hard_Chapter_Maximum of 2,500 Prose_Words is unchanged and applies
     independently. A 2,500-word chapter may be followed by at most one more short chapter in the same
     run.
   - Final compliance is evaluated from actual Chapter_Header `words` values.
   - Planning compliance requires a provisional word estimate wherever consecutive entries share a
     `pov_id`. `estimated_length_class` alone is insufficient, because a class is a band rather than a
     number.
   - This is an objective structural limit rather than a craft judgment, so it is checkable and does not
     belong to Editorial_Review.
2. Cross-cuts converge simultaneous threads and compress clocks only where chronology permits,
   especially across null night. The whole novel does not occur inside one global twenty-four-hour
   clock.
3. Chapter endings turn on information, a decision lock, reversal, arrival, danger, absence, or moral
   remainder. Repetitive fake cliffhangers, withheld nouns, and threat inflation do not substitute for
   consequence.
4. Technical explanation follows **experiment → action → result → human or institutional
   consequence**. Characters do not stop the novel for lecture dialogue or exposition set pieces.
5. Every material capability escalation promptly changes a relationship, institution, consent state,
   evidentiary position, or bodily risk. Fluent pairing must produce choices and consequences rather
   than product demonstration alone.
6. Discovery and Private Defense accelerate procedurally. Mindwars has the fastest POV turnover,
   tightest simultaneous threading, and greatest total word count. After Chapter 112, the same short
   rotating architecture remains, but threat-cliffhanger pressure deliberately decelerates.
7. Coda hooks arise from disclosures, arrivals, choices, refusals, emotional decisions, and moral
   remainders. The Coda remains a quiet Aftermath/Coda rather than a spectacle ending or fourth war.
8. The provisional architecture remains exactly 128 chapters and 140,000 Prose Words: 29 Discovery,
   32 Private Defense, 51 Mindwars, and 16 Coda; four POV loads remain Mara 56, Nia 32, Julian 33, and
   Safiya 7.
9. The Normal Chapter Range remains 700–1,600 Prose Words with a 2,500-word hard maximum. Planning
   retains at least 108 normal chapters, no more than 20 combined micro/long outliers, and the global
   requirement that at least 80 percent of final chapters are normal.
10. Craft outcomes remain human Editorial Gates. No checker may score sentence style, suspense,
    exposition quality, hook force, pacing, voice resemblance, emotional truth, or compliance with a
    named author's style.

### Explicit exclusions

- no imitation or close paraphrase of either named author's prose voice, syntax, recognizable phrases,
  set pieces, or characters;
- no antagonist, Foreign Signal, or alleged-sender POV and no third-act culprit/mechanism reveal that
  resolves provenance;
- no exposition set piece or lecture dialogue substituted for experiment and consequence;
- no group mind, hive mind, mass mind reading, or spectacle escalation used to close the mechanism;
- no spectacle Coda, renewed counterphase, sequel attack, or fourth war movement; and
- no global twenty-four-hour compression.

### Affected records and required synchronization

| Record | Required current state | State |
|---|---|---|
| `design.md` | Translate the direction into original pacing, cross-cut, exposition, hook, and movement architecture | synchronized in corrective design-first pass |
| `requirements.md` | Add solution-appropriate structural and editorial acceptance criteria without numeric prose-style scoring | synchronized in corrective design-first pass |
| `tasks.md` | Carry the direction through existing arc, calibration, drafting, and editorial tasks without renumbering | synchronized in corrective design-first pass |
| `planning/arc-outline.md` | Encode chapter-level threading, hooks, clocks, experiment/consequence beats, and preserved counts/loads | chapters 1–112 written by tasks 5.2–5.4; 113–128 pending task 5.5 |
| `planning/editorial-log.md` and prose | No edits in this pass; later human review records originality and craft evidence | pending later numbered tasks |
| `planning/canon-bible.md` and Canon Sources | No Canon Fact created from this craft decision and no song edit | unchanged |

**Propagation required by the 2026-09-13 run-cap amendment.** The 3,600-word same-POV run limit is a
new objective structural rule, so it is not yet reflected anywhere downstream:

| Record | Required change | State |
|---|---|---|
| `requirements.md` — Requirement 2.7 | Add the 3,600-Prose_Word run limit beside the existing three-chapter limit, and define `same-POV run` in the glossary | pending |
| `requirements.md` — Requirement 11 or 12 | Add the objective check for run word totals against actual `words` values | pending |
| `design.md` | Record the run-limit rule, its planning-versus-final evaluation, and the estimated-word-target need | pending |
| `planning/record-schemas.md` — `ArcEntry` | Add a provisional word-estimate field, or an equivalent run-budget mechanism, so planned runs are auditable before drafting | pending |
| `planning/arc-outline.md` — global invariants | Replace the chapter-only POV-run invariant with both limits and audit every existing two-chapter run in 1–112 | pending |
| `tasks.md` — task 5.6 and 5.8 audits, task 7/8 checker and Property 8 | Extend the POV-run check and its principal property test to cover combined run words | pending |

Until that propagation is complete, the run word limit is binding as an author decision and unenforced
by any objective check.

---

## DEC-017 — Chapter 73 / null-night consent parallel: delayed disclosure, named once in 128

- **Task:** Corrective design-first disclosure and craft direction; tasks 5.4, 5.5, 8.3, 8.4, 8.7,
  17.3, and 17.4 input
- **Date:** 2026-09-12
- **State:** `binding`; craft/disclosure authority, not Canon Lyric and not a Binding Canon Fact
- **Selected:** Delayed disclosure with a single named payoff. The parallel between Nia's consented
  bounded cancellation in Chapter 73 and the unconsentable area-scale cancellation that later takes
  Safiya's private maternal layer stays unnamed through Chapters 62–123, is made assemblable by the
  reader through shared concrete physical vocabulary, and is stated explicitly exactly once — by Mara,
  inside the Chapter 128 entry she writes against herself.

### Why this is load-bearing

`DEC-015`'s fourth mode makes the bounded Chapter 73 counterphase test and null night the same
operation at two scopes rather than two mechanisms. That single fact converts Nia's `Did I say yes?`
from a local consent challenge into part of the book's ethical spine: Nia consented to the very
mechanism that later takes Safiya's private maternal layer at a scale where consent is structurally
impossible. `CANCEL` property 6 already fixes that consent cannot scale. This decision governs only
when, how, and by whom that consequence is said out loud.

### Binding disclosure rule

1. **Unnamed through the Mindwars and the accounting.** No character states the connection in
   Chapters 62–123 — not Mara, not Nia, not Julian. The reason is characterization rather than
   suspense: Mara's binding weakness is converting a room into doctrine, so if she articulates the
   parallel while the war or the accounting is still live it becomes a thesis statement about consent.
   That is exactly the lecture tasks 8.5, 17.2, and 17.3 already forbid, and it violates the
   Refused_Swell.
2. **Findable instead.** The parallel must be assemblable by the reader without narration. Chapter
   73's bounded consenting cancellation and Chapter 118's Tuesday account share a concrete physical
   vocabulary — the same sensation, sound, or bodily register of a cancellation field experienced from
   inside. Chapter 73 has the question asked and answered; Chapter 118 has the same experience with no
   question anywhere near it. **The absence of the question is the echo.** A reader who assembles it
   receives the connection roughly forty-five chapters before any character says it.
3. **Named exactly once, in Chapter 128.** Mara names it inside the entry she writes against herself:
   the consent protocol she was held to was one room wide, and she then ran the same mechanism across
   an area canonically described as `three counties wide` with no one to ask. This is the only
   permitted explicit statement of the parallel anywhere in the manuscript. It is characterization
   rather than thesis because she is not explaining the world, she is indicting herself, and it is her
   last act before going out to knock and wait.
4. **Boundaries.** The Chapter 128 naming resolves no provenance, absolves Mara of nothing, validates
   no archive, and neither invalidates nor retroactively reinterprets Safiya's consent. It does not
   convert the Coda into argument. It stays inside the existing entry-against-herself beat, stays dry,
   and creates no new reveal, no reveal owner, and no release window for anything currently
   `unverified`.
5. **Nia's consent is never transferred responsibility.** Nia's current, specific consent to one
   bounded Chapter 73 cancellation neither authorized, legitimized, nor caused the later area-scale
   null. The parallel is about one physical operation and the limits of scalable consent, not about
   moving responsibility from Mara and the authorizing institution onto the person who agreed to a
   single test in a single room. Under `CANCEL` property 6 consent cannot scale, so the area-scale
   action did not extend Nia's protocol — it proceeded without one. Any drafting or review that lets the
   Chapter 128 naming imply Nia's yes made the null possible is a `revision` finding.

### What this decision does not create

This is craft direction enforced by the existing human Editorial Gates, exactly as `DEC-016` is.

- No new requirement and no new acceptance criterion. Requirements 14 and 15 were deliberately
  trimmed on 2026-09-11 because prose-judgeable criteria belong to Editorial Review under Requirement
  12.12; this decision adds none back.
- No new correctness property. Exactly fifteen properties remain, and no checker evaluates this rule.
- No new Motif_Event ID and no new Literal_Phrase_Constraint. The parallel rides entirely on three
  motif events that already exist: `MOT-YES-01` in Chapter 73, `MOT-KETTLE-01` in Chapter 118, and
  `MOT-RECORD-03` in Chapter 128. The closed `MOT-CHAIN-01..03` and `MOT-COPPER-01..03` mappings stay
  closed, and no fourth event of any motif family is created.
- No new Reveal record. This is delayed disclosure of an already-recorded consequence of `DEC-015`,
  not a withheld fact requiring `fact_id`, knowers, owner, or release window.
- No task checkbox, task ID, or Task Dependency Graph change.

### Retired alternatives

| Retired option | Why it was rejected |
|---|---|
| Name the parallel during the Mindwars or the accounting, Chapters 62–123 | Turns Mara's realization into a consent lecture, hands the reader the moral instead of letting it be assembled, and flattens it. It also breaks the Refused_Swell and `DEC-016` exposition discipline while the war or the request is still live. |
| Never name it at all | Risks Safiya's injury reading as bad luck rather than as the structural cost of a defense that abandoned the individual protocol because that protocol could not scale. The book would carry the parallel without ever letting the person who ran the machine account for it. |
| Have Nia or Julian name it | Nia refusing appropriation under `DEC-007` makes it land as accusation; Julian's institutional hearing-chamber register makes it land as policy. Neither carries the cost. The cost has to fall on the person who ran the machine. |

### Affected records and required synchronization

| Record | Required current state | State |
|---|---|---|
| `planning/decisions.md` | Record this decision in house format with retired alternatives and a sync table | done in this pass |
| `design.md` | Carry the rule into the Chapter 73 Mindwars beat row, the Chapter 118 and Chapter 128 Coda rows, the Ending Design sequence, Mara's Voice_Brief movement evolution, a Reveal Ledger delayed-disclosure note, and one new risk row for early naming becoming doctrine | synchronized in this pass |
| `requirements.md` | No change; this decision creates no requirement and no acceptance criterion | unchanged by design |
| `tasks.md` | Carry the rule into instruction wording for tasks 5.4, 5.5, 8.3, 8.4, 8.7, 17.3, and 17.4 plus Notes, with no checkbox, task ID, or DAG change | synchronized in this pass |
| `planning/canon-bible.md` | Record the disclosure rule as craft direction beside `DEC-015`/`DEC-016`; create no Canon Fact and no Literal_Phrase_Constraint | pending task 4.2 |
| `planning/pov-roster.md` | Carry the Chapter 128 self-indictment into Mara's profile without changing the four POVs or the 56/32/33/7 loads | pending task 4.3 |
| `planning/voice-briefs.md` | Carry the unnamed-then-named movement through Mara's evolution and keep Nia's and Julian's registers clear of the naming | pending task 4.4 |
| `planning/motif-ledger.md` | Note that the parallel rides on existing `MOT-YES-01`, `MOT-KETTLE-01`, and `MOT-RECORD-03`; add no ID and no literal constraint | pending task 4.5 |
| `planning/arc-outline.md` | Encode the shared physical vocabulary in 73 and 118, the silence across 62–123, and the single Chapter 128 naming | pending Task 5 |
| `planning/editorial-log.md` and prose | No edits in this pass; later human review records the evidence | pending later numbered tasks |
| `songs/*.md` | No source lyric or song-file change | unchanged |

---

## Pending decisions

No pending blocking author decisions remain. `DEC-015`, as amended on 2026-09-11, completes the
four-mode mechanism and evidence boundary; `DEC-016`, as amended on 2026-09-13, closes the original
thriller architecture and the same-POV run limit; and `DEC-017` closes when the Chapter 73 / null-night
consent parallel may be named.

Fluent pair identities and session ownership were deferred to Task 5 within those binding decisions,
and tasks 5.3 and 5.4 have now made those selections: Mara and Nia are the carried fluent pair, with
supporting participants placed inside existing POV chapters. That was implementation of a deferred
selection, not a reopened mechanism or POV decision, and the 56/32/33/7 loads are unchanged.

## Synchronization state — audit of 2026-09-13

The per-decision synchronization tables above record each obligation **as it stood when that decision
was made**, which is the correct historical record but is no longer an accurate picture of the
workspace. Many rows still read `pending` for artifacts that now exist. This block is the authoritative
current state; where it disagrees with a row above, this block governs.

| Artifact | State |
|---|---|
| `requirements.md`, `design.md`, `tasks.md` | synchronized through `DEC-017`; **not** synchronized for the 2026-09-13 run-cap amendment |
| `The Final Frontier Novel/front-matter.md` | written |
| `The Final Frontier Novel/exclusion-contract.json` | written |
| `planning/record-schemas.md` | written, including the 2026-09-11 four-mode `technical_state` amendment; needs a run-word field |
| `planning/canon-bible.md` | written |
| `planning/pov-roster.md` | written, amended 2026-09-12 |
| `planning/voice-briefs.md` | written, amended 2026-09-12 |
| `planning/motif-ledger.md` | written, amended 2026-09-12 |
| `planning/editorial-log.md`, `planning/arc-changes.md` | schemas written; zero active findings and zero active changes |
| `planning/arc-outline.md` | chapters 1–112 and all 55 cross-cuts written and verified reciprocal; `estimated_words` migrated across all 112 entries; chapters 113–128 not written |
| Chapter prose | none written; all voice, pacing, and originality judgments remain untested |

Two defects are known and unresolved at the time of this audit:

1. **Arc outline count drift — resolved 2026-09-13.** The Mindwars cross-cut section's final ten records
   were written, bringing the fence to 30 Mindwars and 55 overall and matching the stated totals. An
   integrity check confirmed zero reciprocity errors across all 55 records, a closed null-night ring with
   exactly three temporal braids, every null-night chapter participating twice, no cross-cut joining
   Chapter 73 to any null-night chapter, and all 18 `"none"` chapters absent from every cut. Task 5.4 is
   complete.
2. **Run-cap propagation — mostly resolved 2026-09-13.** `requirements.md` (glossary `Same_POV_Run`,
   criteria 2.7, 2.15, 2.16, 11.12, 12.16), `design.md` (rotation rule 1, global checks, Property 8),
   `record-schemas.md` (`ArcEntry.estimated_words` and the run invariant), `tasks.md` (5.1, 5.6, 5.8, 8.8,
   8.17, Notes), and `arc-outline.md` (invariant 6, field contract, run budget, all 112 entries) now carry
   the limit. What remains is implementation rather than specification: no checker code exists yet, so the
   rule is unenforced until tasks 7 and 8 build and test it.

## Nonblocking follow-ups

None of these block drafting, and none is an open author decision. They are recorded so they are not
lost.

| Item | Owner | State |
|---|---|---|
| Contradictory performance-copyright and public-domain claims in the *Case Zero* footer | author / rights review | unresolved; publication and canon status do not settle it, and it should be closed before release |
| Adopt `exclusion-contract.json` in the external lyrics repository, with a standing regression test | lyrics repository (external) | `not-adopted`; outside manuscript acceptance, but recommended as a release gate rather than an open-ended follow-up |
| Title positioning for ***The Final Frontier*** | author | open; the title is binding under `DEC-001` and correct thematically, but it collides with a very well-known franchise usage and reads as space fiction. A subtitle or positioning check is recommended before publication. Not a reason to reopen `DEC-001`. |

## Recorded craft risks

These are drafting and review risks rather than decisions. They are recorded because the decisions
above do not by themselves prevent them, and because the movement Editorial_Gates are where they get
caught.

| Risk | Why it matters | Where it is caught |
|---|---|---|
| No recurring human counterforce | The Foreign Signal is correctly faceless and the opposition is institutional, so scenes can lack a specific adversary to play against. A recurring negotiator, program director, regulator, or operations lead inside the existing POV architecture would give the middle book someone to lose arguments to. Such a character must not be the sender and must not receive a POV. | tasks 12.7, 13.6, 15.8 movement gates |
| Safiya arriving as a moral instrument | She enters at 115 and structurally exists to present Mara with the bill. She needs work, obligations, irritation, and relationships that are not about Mara, and the request must be one thing she is doing rather than her whole identity. Civilian subtraction should also be established earlier through other people. | tasks 8.7, 17.4 gates |
| Doctrine voice bleeding across all four POVs | The planning documents necessarily speak in *consent, provenance, authorization, inference, mechanism*. In prose that vocabulary belongs mostly to Mara and Julian. Nia carries operational specifics and corrections; Safiya must not sound like she has read the Canon Bible. | task 8.7 calibration review |
| Professional authenticity | Three domains carry real credibility risk and are not covered by the community-portrayal review already required by `DEC-003`: emergency dispatch and EMS for the Chapter 17 routing and the exonerating timestamps; neuroscience or signal processing for receive, write, and calibration language; technology-transactions and archival governance for the term sheet, record alteration, and the speed of Trust formation. The dispatch evidence in particular must clear Nia without feeling conveniently miraculous. | before Approved_Baseline, task 10.2 |
