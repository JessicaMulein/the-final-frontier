# Canon Bible

Schema version: **1**
Project: ***The Final Frontier***
Status: **provisional planning reference; not an Approved Baseline**
Authority through: **DEC-018**
Amended: **2026-09-18** — `DEC-018` supporting canon for the author-directed revision pass on delivered Chapters 1–46. Five `CanonFact` records under `source_location: DEC-018` record Mara's Northline-internal exposed-persons list, one unverified private report by the Northline technician, his reassignment request and Mara's resulting personal cost inside Private_Defense, the identity of the vehicle at the Northline Array gate at the end of Chapter 35, and the recognized class of private two-person language layer established through Ada and Lena Ferris. `EXT-CHAR-RAVI-NAME` gains the surname **Anand** without changing `CHAR-011`; two new non-viewpoint Character IDs, `CHAR-015` Joss Calder and `CHAR-016` Ruth Venn, carry one recurring non-professional relationship each for Nia Calder and Mara Venn; `CHAR-011` joins `TL-PRIVATE-COPPER.participants`. The supporting-character count is now twelve. Nothing here creates a POV, Voice Brief, chapter, motif, literal phrase constraint, or Reveal, and the four `POVProfile` records and the 56/32/33/7 loads are unchanged. See [`DEC-018` supporting canon](#dec-018-supporting-canon).
Amended: **2026-09-16** — corrective calibration synchronization. The December eight seconds are recorded as reproducible acquisition-to-resolved-output reconstruction latency under the early apparatus configuration, requested fidelity, context, information load, noise, and confidence conditions used in Chapters 1–5, never as a permanent physical constant or source-side delay; the receiver remains receive-only. Four non-viewpoint continuity witnesses are added as approved `character-name` Novel Extensions, `CHAR-011` through `CHAR-014`: Ravi, Kev, Dev, and Halloran. The supporting-character summary now contains ten names and still creates no POV, Voice Brief, roster load, or inferred real-world cultural detail.
Amended: **2026-09-12** — the four-mode neural communication mechanism, `CANCEL` properties, and pairing evidence boundary of `DEC-012`/`DEC-015` are recorded as one Novel Extension family; every mechanism-bearing `TimelineEntry` now declares exactly one `mode`; `DEC-016` and `DEC-017` are recorded as craft/architecture direction that creates no Canon Fact and no Literal Phrase Constraint.
Amended: **2026-09-15** — author-approved amendment pass closing the pairing-chronology gap referred upward by tasks 5.6 and 5.8. Six non-viewpoint supporting participants are declared as approved `character-name` Novel Extensions, `CHAR-005` through `CHAR-010`, under `DEC-012`'s operational-pairing clause, `DEC-015`, and Requirement 15.3; they create no POV, no Voice Brief obligation, and no change to the 56/32/33/7 loads. Thirteen `mode: PAIR` `TimelineEntry` records now classify every declared Fluent_Pairing beat in 36–42, 70–77, 78–93, and 94–108, so Requirement 14.1 holds for each of them and Requirements 14.10 through 14.12 are machine-recorded rather than only narrated. Chapter 83 is deliberately cancellation-only and carries no paired channel, so the apparent gap between 82 and 88 is an author-approved craft decision and must not be closed by adding a PAIR entry for it. Chapter 88 remains the single recorded session. Four sentences that sent readers to the Arc Outline for pairing chronology now name these entries instead — the `evidence_scope` of `TL-MINDWARS-COUNTERPHASE` and `TL-MINDWARS-SHIELD` and an `uncertainty_notes` line on `TL-PRIVATE-OFFER` and `TL-MINDWARS-TERRITORY` — because the Arc Outline creates no `TimelineEntry` and never could. No Canon Fact, POV, mode enum, `CANCEL` record, load, or motif changed.
Amended: **2026-09-14** — task 5.6 audit synchronization. Every `TimelineEntry.cross_cut_ids` array is now populated from the Arc Outline's `CrossCut` records, discharging the obligation the Arc Outline assigned to task 5.6; 21 chronology entries carry 58 back-references and the remaining 10 keep `[]` because no cross-cut names them. Two `Reveal` records had a `reader_release_chapter` narrated by a POV other than their `reveal_owner_pov`, which `record-schemas.md` forbids: `REVEAL-NIA-SOURCE-CASUALTY` moved from 23 to 24 and `REVEAL-CASUALTY-CONSEQUENCE` from 53 to 52, each onto the owning `POV-NIA` chapter already inside its unchanged payoff window. No owner, window, truth status, withholding basis, Canon Fact, or Novel Extension changed.

This document records binding canon, approved continuity extensions, the four-mode neural communication mechanism and its evidence boundary, chronology, unresolved questions, reveal ownership, names/entities, Canon Dialogue provenance, and the craft direction that governs how some of this material may be said on the page. Machine-readable values appear only in typed fenced JSON records governed by [`record-schemas.md`](record-schemas.md). Commentary is explanatory and has no record value; the checker must never infer or repair a record from prose or tables.

No Arc Entries, Chapter Headers, POV Profiles, Voice Briefs, Motif Events, Literal Phrase Constraints, Baselines, Arc Changes, Editorial Findings, or Gate Results are created here.

## Canon authority and source boundary

The controlling order from `DEC-011`, as updated by `DEC-014`, is:

1. explicit author decisions;
2. approved requirements and design decisions;
3. Canon Lyric in the exact five-file set below, retaining metaphor, compression, speaker attribution, and first-person limitation;
4. expressly ratified note material, whose authority comes only from its identified adopter; and
5. approved compatible Novel Extensions.

Unratified Production Notes and other non-lyric metadata sit outside this precedence order, remain advisory/non-story, and cannot defeat a Novel Extension. No record below uses `authority_basis: ratified-note`. Where a note-derived proposition has already been adopted, the record cites the adopting requirement or author decision directly. No unratified note, style prompt, exclude list, generation workflow, credit, or rights line establishes identity, chronology, naming, continuity, or protected wording.

Three later decisions sit at tier 1 without becoming Canon Lyric, and each is recorded at its true authority level:

| Decision | What it is here | Record form |
|---|---|---|
| `DEC-012` / `DEC-015` | mechanism authority for the four neural communication modes, consent, and evidence limits | approved `NovelExtension` family plus `TimelineEntry.technical_state` |
| `DEC-016` | craft and architecture direction | readable direction only; **no** Canon Fact, Novel Extension, or Literal Phrase Constraint |
| `DEC-017` | disclosure direction for the Chapter 73 / null-night consent parallel | readable direction only; **no** Canon Fact, Reveal, Motif Event, or Literal Phrase Constraint |
| `DEC-018` | chapter shape, forward pressure, voice separation, human cost, warmth, and the normal-class word target, plus one narrow canon authorization | ten craft clauses are readable direction only and create no record; the narrow authorization creates five `CanonFact` and four `NovelExtension` records in [`DEC-018` supporting canon](#dec-018-supporting-canon) and **no** Reveal, Motif Event, or Literal Phrase Constraint |

### Closed Canon Source inventory

| Included | Exact workspace path | Binding scope |
|---|---|---|
| yes | `songs/The Synaptic Frontier.md` | lyric only |
| yes | `songs/Faraday.md` | lyric only |
| yes | `songs/The Final Frontier.md` | lyric only |
| yes | `songs/The Radius.md` | lyric only |
| yes | `songs/Case Zero.md` | lyric only; tier-3 attributed testimony under `DEC-014` |
| **no** | `songs/One-Time Pad.md` | not a Canon Source; unpublished, noncanonical for book purposes, and no continuity authority |

The set is closed at exactly five. Song-file occurrences are outside Chapter File Prose Body literal scans. Publication of *Case Zero* is author-approved and in progress because `DEC-014` says so, not because its Production Notes say so.

The *One-Time Pad* draft is **not** added as a sixth source. Under `DEC-014` it is preserved in git history and removed from the working tree, so it is absent from the tree, unpublished, and noncanonical for book purposes. It supplies no Binding Canon Fact, continuity obligation, chronology, identity, naming rule, or Literal Phrase Constraint, and its absence from the working tree is a storage fact rather than a change to that exclusion.

### Non-story/advisory classification

For all five Canon Sources, Production Notes, style prompts, exclude prompts, generation workflow, credits, performance information, recording information, and rights metadata remain advisory/non-story unless a higher authority adopts one specific proposition. For *Case Zero* specifically, the relevant non-lyric classes are also enumerated as `supporting_advisory_citations` on `CF-AUTHORITY-SOURCE-INVENTORY`; those citations confer no binding force.

The *Case Zero* footer's conflicting performance-copyright and public-domain claims are retained only as an **unresolved nonlegal author/rights-review follow-up**. This Canon Bible reaches no legal conclusion and supplies no replacement wording. Publication approval and canon promotion do not resolve the conflict.

## Binding Canon Facts

```json record=CanonFact schema=1
[
  {
    "canon_id": "CF-AUTHORITY-SOURCE-INVENTORY",
    "authority_basis": "author-decision",
    "source_path": "The Final Frontier Novel/planning/decisions.md",
    "source_location": "DEC-014, Exact Canon_Source inventory and Authority boundary",
    "source_material_class": "author-decision",
    "adopted_by": null,
    "statement": "The Canon Source set is exactly The Synaptic Frontier, Faraday, The Final Frontier, The Radius, and Case Zero; Case Zero publication is author-approved and in progress, its lyric is tier-3 attributed canon, and One-Time Pad remains excluded and noncanonical for book purposes.",
    "first_person_testimony": false,
    "speaker": null,
    "attribution": null,
    "epistemic_limitation": null,
    "truth_scope": "authoritative-proposition",
    "binding_implications": [
      "Only lyric text from the exact five included paths may support lyric-authority Canon Facts.",
      "Case Zero first-person lyric statements bind as Nia's canonical account without becoming omniscient causal proof.",
      "One-Time Pad supplies no binding continuity, identity, chronology, phrase constraint, or source authority.",
      "Non-lyric song material remains advisory/non-story unless separately adopted by a higher authority."
    ],
    "protected_ambiguities": [
      "Case Zero publication and canon status do not resolve its contradictory rights footer.",
      "Case Zero lyric authority does not confirm the origin of Nia's wanting."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [],
    "affected_chapters": [],
    "supporting_advisory_citations": [
      {
        "source_path": "songs/Case Zero.md",
        "source_location": "Production notes: Publication status, Canon status, Cycle note, and carried-motif commentary",
        "material_class": "production-note",
        "classification": "advisory-non-story",
        "note": "Publication and canon status are binding only because DEC-014 independently establishes them; the remaining commentary cannot establish story facts."
      },
      {
        "source_path": "songs/Case Zero.md",
        "source_location": "Production notes: Style prompt",
        "material_class": "style-prompt",
        "classification": "advisory-non-story",
        "note": "Performance and arrangement direction is not story continuity."
      },
      {
        "source_path": "songs/Case Zero.md",
        "source_location": "Production notes: Exclude styles",
        "material_class": "exclude-prompt",
        "classification": "advisory-non-story",
        "note": "Excluded generation styles create no story obligation."
      },
      {
        "source_path": "songs/Case Zero.md",
        "source_location": "Production notes: Voice generation workflow",
        "material_class": "generation-workflow",
        "classification": "advisory-non-story",
        "note": "Persona and audition instructions create no identity, chronology, or diegetic event."
      },
      {
        "source_path": "songs/Case Zero.md",
        "source_location": "Post-lyric credits",
        "material_class": "credits",
        "classification": "advisory-non-story",
        "note": "Authorship, composition, performance, mixing, and mastering credits are not story canon."
      },
      {
        "source_path": "songs/Case Zero.md",
        "source_location": "Post-lyric rights footer and unresolved rights warning",
        "material_class": "rights-metadata",
        "classification": "advisory-non-story",
        "note": "Conflicting performance-copyright and public-domain claims remain an unresolved nonlegal review item and supply no story or legal conclusion."
      }
    ]
  },
  {
    "canon_id": "CF-INWARD-FRONTIER-PREMISE",
    "authority_basis": "author-decision",
    "source_path": "The Final Frontier Novel/planning/decisions.md",
    "source_location": "DEC-011, Governing premise of The Final Frontier",
    "source_material_class": "author-decision",
    "adopted_by": null,
    "statement": "The final frontier was not outer space but humanity's own minds: people expected to cross it as explorers, but it crossed them and made human minds the shore, new world, and contested territory.",
    "first_person_testimony": false,
    "speaker": null,
    "attribution": null,
    "epistemic_limitation": null,
    "truth_scope": "authoritative-proposition",
    "binding_implications": [
      "Discovery points outward through spectrum, Private Defense reveals that the door runs inward, and the Mindwars reveal people as the territory crossed.",
      "The Mindwars dramatize the premise but are neither the novel's title nor its whole meaning.",
      "The premise must be earned through events rather than explained as a thesis."
    ],
    "protected_ambiguities": [
      "The identity and origin of the entity or process that crossed human minds remain unestablished."
    ],
    "protected_wording": "the final frontier",
    "affected_timeline_ids": [
      "TL-MINDWARS-TERRITORY"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-DISCOVERY-FIELD-CHANNEL",
    "authority_basis": "lyric",
    "source_path": "songs/The Synaptic Frontier.md",
    "source_location": "Lyric: Verse 1 through final chorus and outro, especially 'a mind is a field', the unfound inward channel, and somebody alive finding it",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "The canonical discovery argument treats mathematical radio as capable of representing waves, the mind as an active field with current in the bone, an unfound channel behind the eye as real, and its discovery by somebody alive as inevitable within the song's promise.",
    "first_person_testimony": true,
    "speaker": "CHAR-001",
    "attribution": "Binding as the finder-facing source lyric mapped to Mara by the approved novel design.",
    "epistemic_limitation": "The lyric's metaphor and future certainty do not by themselves specify the later apparatus chronology, sender, or causal origin of an intrusion.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "Discovery must dramatize the mind as a field, the unfound frequency, spectrum-to-bone transmission imagery, and the certainty that somebody alive finds the channel.",
      "The Foreign Signal remains known through reception and effects rather than an adversary viewpoint."
    ],
    "protected_ambiguities": [
      "The source and agency behind anything later received through the channel remain unknown."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-DECEMBER-RECEIVE",
      "TL-DISCOVERY-DUE-DILIGENCE"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-DECEMBER-MARA-MORNING",
    "authority_basis": "lyric",
    "source_path": "songs/Faraday.md",
    "source_location": "Lyric: Verse 1, from 'I found it in December' through 'a channel running inward is still a door'",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Mara reports finding the signal in December at the bottom of the noise and receiving a stranger's ordinary morning in resolved form eight seconds after her receive-only apparatus acquired it, without siren, announcement, or public date.",
    "first_person_testimony": true,
    "speaker": "CHAR-001",
    "attribution": "Binding as Mara's first-person account of the discovery reception.",
    "epistemic_limitation": "Her account establishes what she received and measured, not a source-side gap, a December transmission, or the cause of Nia's later wanting.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "The discovery occurs in December.",
      "The received material is an ordinary continuous morning; under the early apparatus configuration, requested fidelity, context, information load, noise, and confidence requirements used in these scenes, Mara reproducibly observes eight seconds from raw acquisition timestamp to legible resolved output.",
      "The inward channel immediately carries threshold and consent implications."
    ],
    "protected_ambiguities": [
      "The December lyric does not establish a transmit stage or handshake."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-DECEMBER-RECEIVE"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-DECEMBER-RECEIVE-ONLY",
    "authority_basis": "author-decision",
    "source_path": "The Final Frontier Novel/planning/decisions.md",
    "source_location": "DEC-002, Corrected mechanism and chronology",
    "source_material_class": "author-decision",
    "adopted_by": null,
    "statement": "The December apparatus is receive-only with no transmit stage; it continuously acquires and timestamps Nia's raw continuous field, reconstructs it as legible experience with reproducible eight-second latency under the early configuration and information load used in Chapters 1–5, and identifies or locks onto Nia's person-specific channel or address.",
    "first_person_testimony": false,
    "speaker": null,
    "attribution": null,
    "epistemic_limitation": null,
    "truth_scope": "authoritative-proposition",
    "binding_implications": [
      "No December transmission event may appear in chronology, prose, or planning.",
      "Nia experiences no source-side discontinuity or delay and is never late to her own morning.",
      "Reprocessing the same raw sample with the same early settings reproduces eight seconds; insufficient context or processing degrades or destroys coherence.",
      "Eight seconds is not a permanent physical constant or necessarily irreducible: later hardware, algorithms, information volume, complexity, fidelity, noise, confidence requirements, and other conditions may change reconstruction latency.",
      "The person-specific lock is distinct from later use of that address for transmission."
    ],
    "protected_ambiguities": [
      "The lock does not establish what later caused Nia's wanting."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-DECEMBER-RECEIVE",
      "TL-DISCOVERY-DUE-DILIGENCE"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-LATER-BENCH-HANDSHAKE",
    "authority_basis": "author-decision",
    "source_path": "The Final Frontier Novel/planning/decisions.md",
    "source_location": "DEC-002, Corrected mechanism and chronology; binding constraint 1",
    "source_material_class": "author-decision",
    "adopted_by": null,
    "statement": "Only later, in the Discovery open-invitation sequence, Mara deliberately adds a temporary bench transmit path and sends a content-free handshake through the person-specific address identified in December.",
    "first_person_testimony": false,
    "speaker": null,
    "attribution": null,
    "epistemic_limitation": null,
    "truth_scope": "authoritative-proposition",
    "binding_implications": [
      "The bench path and handshake are distinct in kind and time from the receive-only December event.",
      "The handshake contains no words, order, or triage instruction.",
      "The handshake may be causally relevant to Nia's later wanting but can never be confirmed or disproved as its cause."
    ],
    "protected_ambiguities": [
      "Handshake-to-wanting causation remains unresolved with no privileged instrument or narrator."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-DISCOVERY-HANDSHAKE",
      "TL-DISCOVERY-NIA-AFTERMATH"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-APRIL-TERM-SHEET-PAGE-NINE",
    "authority_basis": "lyric",
    "source_path": "songs/Faraday.md",
    "source_location": "Lyric: Verse 2, from the April term sheet through 'Page nine. One line. Transmit enable.'",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Mara reports that representatives arrived by April with a term sheet and pen, that she believed some promised benefits, and that page nine of the specification contained the line 'Transmit enable', exposing two-way capability.",
    "first_person_testimony": true,
    "speaker": "CHAR-001",
    "attribution": "Binding as Mara's first-person report of the April document and her response to it.",
    "epistemic_limitation": "The April line establishes broader architectural capability and intent; it is not evidence that the December receive-only rig transmitted.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "The term-sheet arrival occurs in April.",
      "The page-nine line must be preserved as the documentary discovery of write-capable architecture.",
      "Mara's refusal follows genuine temptation rather than prior disbelief in every promised benefit."
    ],
    "protected_ambiguities": [
      "Page nine says nothing about who caused Nia's wanting."
    ],
    "protected_wording": "Transmit enable.",
    "affected_timeline_ids": [
      "TL-APRIL-TERM-SHEET"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-PAGE-NINE-EVIDENCE-LIMIT",
    "authority_basis": "author-decision",
    "source_path": "The Final Frontier Novel/planning/decisions.md",
    "source_location": "DEC-002, Corrected mechanism and chronology; DEC-012, Meaning and chronology",
    "source_material_class": "author-decision",
    "adopted_by": null,
    "statement": "Page-nine transmit enable is later evidence that the proposed receiver network is write-capable by architecture; it never retroactively gives the December apparatus a transmit stage and never proves December or handshake causation.",
    "first_person_testimony": false,
    "speaker": null,
    "attribution": null,
    "epistemic_limitation": null,
    "truth_scope": "authoritative-proposition",
    "binding_implications": [
      "Timeline and technical-state records must keep December receive-only, the bench path later, and page nine later still.",
      "Historical back-application of later terminology cannot alter the apparatus state."
    ],
    "protected_ambiguities": [
      "Neither origin account for Nia's wanting gains evidentiary support from page nine."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-DECEMBER-RECEIVE",
      "TL-DISCOVERY-HANDSHAKE",
      "TL-APRIL-TERM-SHEET"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-PRIVATE-COPPER-BOUNDARY",
    "authority_basis": "lyric",
    "source_path": "songs/Faraday.md",
    "source_location": "Lyric: Pre-Chorus, Chorus, Bridge, and Outro, especially copper and quiet, the inside handle, and 'Come in. But ask.'",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Mara frames copper and quiet as a private boundary, not disappearance: a room must retain a door, the handle belongs on the inside, and entry must follow a current answer from the person behind it.",
    "first_person_testimony": true,
    "speaker": "CHAR-001",
    "attribution": "Binding as Mara's first-person boundary doctrine in Faraday.",
    "epistemic_limitation": "A private copper room proves that shielding can create a local boundary; it does not establish a complete social defense or identify the sender.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "Private Defense must dramatize the copper room, quiet, inside handle, and conditional invitation.",
      "Permanent isolation cannot be treated as freedom or as the final answer.",
      "Consent, rather than sender identity alone, controls legitimate entry."
    ],
    "protected_ambiguities": [],
    "protected_wording": "Come in. But ask.",
    "affected_timeline_ids": [
      "TL-PRIVATE-COPPER",
      "TL-PRIVATE-PROTOCOL"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-FARADAY-RECORD-DEMAND",
    "authority_basis": "lyric",
    "source_path": "songs/Faraday.md",
    "source_location": "Lyric: Verse 2, 'I went looking for a door and I found one. Put that on the record.'",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Mara insists that the discovery of the inward door and write-capable danger be put on the record rather than softened or omitted.",
    "first_person_testimony": true,
    "speaker": "CHAR-001",
    "attribution": "Binding as Mara's first-person demand in the April refusal sequence.",
    "epistemic_limitation": "The demand establishes her insistence, not that any later institutional record remains complete or correct.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "The private record insistence precedes the Trust and begins the three-stage record progression.",
      "Later alteration of the April record is a Novel Extension and must not be misattributed to the lyric itself."
    ],
    "protected_ambiguities": [],
    "protected_wording": "Put that on the record.",
    "affected_timeline_ids": [
      "TL-APRIL-TERM-SHEET",
      "TL-APRIL-RECORD-ALTERATION"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CONSENT-SOVEREIGNTY",
    "authority_basis": "requirement",
    "source_path": ".kiro/specs/The-Final-Frontier-novel/requirements.md",
    "source_location": "Requirements 6.8 and 7.8; approved consent rule",
    "source_material_class": "requirement",
    "adopted_by": null,
    "statement": "Consent is the rule that distinguishes a shield from an occupier: legitimate entry must follow the freely given, specific, current answer of the person whose mind is crossed.",
    "first_person_testimony": false,
    "speaker": null,
    "attribution": null,
    "epistemic_limitation": null,
    "truth_scope": "authoritative-proposition",
    "binding_implications": [
      "Known or friendly identity cannot substitute for authorization.",
      "Defender counterphase remains ethically dangerous because a counterwave is still a transmitted wave.",
      "Safiya's valid consent removes lack of authorization as Mara's reason to refuse but cannot manufacture source truth."
    ],
    "protected_ambiguities": [],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-PRIVATE-PROTOCOL",
      "TL-MINDWARS-COUNTERPHASE",
      "TL-CODA-CONSENT"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-FIRST-CASUALTY-ARRIVAL",
    "authority_basis": "lyric",
    "source_path": "songs/The Final Frontier.md",
    "source_location": "Lyric: Verse 1, 'the first one that we lost' and the thought she believed was hers",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "The postwar account identifies the first casualty as a woman who was never told she had been drafted and experienced an arriving thought as if it were her own.",
    "first_person_testimony": true,
    "speaker": "CHAR-001",
    "attribution": "Binding as Mara's postwar collective testimony about the first casualty; the novel maps that casualty to Nia under DEC-002.",
    "epistemic_limitation": "The testimony establishes the injury and later historical framing, not the sender or whether Mara's handshake caused this first wanting.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "Nia's injury is insertion: a crude arriving state indistinguishable from her own judgment.",
      "The first-casualty history may carry an adversary attribution but that attribution remains an institutional inference."
    ],
    "protected_ambiguities": [
      "The origin of the first wanting remains unresolved."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-DISCOVERY-HANDSHAKE",
      "TL-DISCOVERY-NIA-AFTERMATH",
      "TL-MINDWARS-ONSET"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-MINDWARS-TERM-UNDECLARED",
    "authority_basis": "lyric",
    "source_path": "songs/The Final Frontier.md",
    "source_location": "Lyric: Verse 1, 'Nobody declared it' through 'History calls them the Mindwars'",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "The conflict has no declaration, first shot, or moved border; histories later call it the Mindwars, though participants lack that stable term while losing it.",
    "first_person_testimony": true,
    "speaker": "CHAR-001",
    "attribution": "Binding as Mara's retrospective war testimony and the canonical historical naming of the event.",
    "epistemic_limitation": "Retrospective naming does not supply a sender, declaration, flag, or objective first-shot account.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "The Mindwars is the established term for the undeclared war over mindspace.",
      "In-scene participants do not use the stable historical term before it exists.",
      "The Mindwars remains an event within the inward-frontier argument, not the book title."
    ],
    "protected_ambiguities": [
      "No border, demand, language, or confirmed sender defines the conflict."
    ],
    "protected_wording": "the Mindwars",
    "affected_timeline_ids": [
      "TL-MINDWARS-ONSET",
      "TL-POSTNULL-HISTORY"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-FOREIGN-SIGNAL-PROVENANCE",
    "authority_basis": "requirement",
    "source_path": ".kiro/specs/The-Final-Frontier-novel/requirements.md",
    "source_location": "Requirements 3.13, 4.11, 6.6, and 6.7",
    "source_material_class": "requirement",
    "adopted_by": null,
    "statement": "The origin and sender identity of the Foreign Signal are unestablished and remain unconfirmed across every narrative and reference component.",
    "first_person_testimony": false,
    "speaker": null,
    "attribution": null,
    "epistemic_limitation": null,
    "truth_scope": "authoritative-proposition",
    "binding_implications": [
      "Every proposed state, startup, emergent-system, natural-phenomenon, or unknown-agent account remains attributed theory.",
      "No Foreign Signal or alleged-sender POV is permitted.",
      "No document, metadata, chapter order, or later revelation may privilege one theory as fact."
    ],
    "protected_ambiguities": [
      "Sender, origin, nature, intention, and relation to Nia's first wanting remain unresolved."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-MINDWARS-ONSET",
      "TL-MINDWARS-TERRITORY",
      "TL-NULL-NIGHT",
      "TL-CODA-PUBLIC-ACCOUNTING"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-COUNTERPHASE-DEFENSE",
    "authority_basis": "lyric",
    "source_path": "songs/The Final Frontier.md",
    "source_location": "Lyric: Verse 2 and Bridge, mirror cancellation and 'A counterwave is still a wave ... we had to transmit too'",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "The defenders learn to meet the incoming signal with its counterphase image; cancellation works by transmitting through the same human frontier and therefore carries the same capacity for violation.",
    "first_person_testimony": true,
    "speaker": "CHAR-001",
    "attribution": "Binding as Mara's first-person account of active defense and its ethical danger.",
    "epistemic_limitation": "The account establishes defender mechanism and risk, not the Foreign Signal's sender or an unlimited ability to read or write minds.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "Active defender counterphase is confined to the Mindwars Part.",
      "Counterphase trials require specific, revocable consent where consent can be obtained.",
      "The defense cannot be narrated as clean, friendly, or noninvasive merely because the defenders control it."
    ],
    "protected_ambiguities": [],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-MINDWARS-COUNTERPHASE",
      "TL-MINDWARS-SHIELD",
      "TL-NULL-DECISION",
      "TL-NULL-NIGHT"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-NULL-SILENCE-DIMINISHMENT",
    "authority_basis": "lyric",
    "source_path": "songs/The Final Frontier.md",
    "source_location": "Lyric: Verse 2 and counterphase instrumental, especially 'when the foreign voice went quiet, mine was quieter too'",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "The null succeeds in silencing the Foreign Signal while diminishing the defending voice by the same act.",
    "first_person_testimony": true,
    "speaker": "CHAR-001",
    "attribution": "Binding as Mara's first-person report of the null's successful defense and personal diminishment.",
    "epistemic_limitation": "Mara's account establishes her perceived and measurable diminishment but does not exhaust or omnisciently catalogue civilian losses.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "The Foreign Signal is silent when the Mindwars Part ends.",
      "Mara's own inner voice is measurably and subjectively quieter.",
      "No Coda transmission may revive the Foreign Signal or restart counterphase combat."
    ],
    "protected_ambiguities": [
      "No surrender, counterparty, or sender is revealed by the silence."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-NULL-NIGHT",
      "TL-POSTNULL-HISTORY",
      "TL-CODA-PUBLIC-ACCOUNTING"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-NULL-EXTENT",
    "authority_basis": "lyric",
    "source_path": "songs/The Radius.md",
    "source_location": "Lyric: Chorus, 'I fired a quiet three counties wide'",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Mara describes the defensive quiet as three counties wide and admits that she asked no one inside that affected area.",
    "first_person_testimony": true,
    "speaker": "CHAR-001",
    "attribution": "Binding as Mara's post-null first-person accounting of the defense's canonical extent and consent failure.",
    "epistemic_limitation": "The phrase states canonical affected-area width; it does not define a mathematical radius, geometry, named counties, or a complete census of harm.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "Preserve the extent as 'three counties wide' or 'affected area canonically described as three counties wide'.",
      "Do not derive a radius, list county names, or substitute another extent."
    ],
    "protected_ambiguities": [
      "The country and individual counties remain intentionally unnamed."
    ],
    "protected_wording": "three counties wide",
    "affected_timeline_ids": [
      "TL-NULL-DECISION",
      "TL-NULL-NIGHT",
      "TL-CODA-ACCOUNT"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-NULL-CIVILIAN-HARM",
    "authority_basis": "requirement",
    "source_path": ".kiro/specs/The-Final-Frontier-novel/requirements.md",
    "source_location": "Requirements 6.10 and 3.10 through 3.12",
    "source_material_class": "requirement",
    "adopted_by": null,
    "statement": "The successful null silences the Foreign Signal, diminishes the defending voice, and harms civilians throughout the affected area canonically described as three counties wide; that cost remains postwar consequence rather than a renewed conflict.",
    "first_person_testimony": false,
    "speaker": null,
    "attribution": null,
    "epistemic_limitation": null,
    "truth_scope": "authoritative-proposition",
    "binding_implications": [
      "Civilian subtraction is a real defensive harm and cannot be softened into telemetry or negligible side effect.",
      "The Coda opens a second cycle through accounting without renewing transmission or combat."
    ],
    "protected_ambiguities": [
      "The complete number and form of civilian losses remain unknown."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-NULL-NIGHT",
      "TL-POSTNULL-HISTORY",
      "TL-CODA-PUBLIC-ACCOUNTING",
      "TL-CODA-ACCOUNT"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CODA-POSTWAR-STATE",
    "authority_basis": "lyric",
    "source_path": "songs/The Radius.md",
    "source_location": "Lyric: Verse 1 and Bridge, two years, no all-clear, no treaty or return address, and nobody surrendered",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Two years after the null there has been no all-clear, treaty, surrender, or counterparty to ask; the Foreign Signal remains silent and people call the continuing quiet peace or armistice without a signed ending.",
    "first_person_testimony": true,
    "speaker": "CHAR-001",
    "attribution": "Binding as Mara's first-person description of the post-null state.",
    "epistemic_limitation": "The absence of contact or counterparty does not prove a sender's destruction, intention, identity, or permanent incapacity.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "The Coda begins two post-null years later.",
      "Active defender counterphase has ceased and no renewed Foreign Signal transmission occurs.",
      "Coda action is accounting and attempted repair, not a fourth war movement."
    ],
    "protected_ambiguities": [
      "Silence is not a negotiated peace and supplies no provenance answer."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-CODA-PUBLIC-ACCOUNTING"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CODA-THREE-KNOCKS",
    "authority_basis": "lyric",
    "source_path": "songs/The Radius.md",
    "source_location": "Lyric: Intro and Verse 1, three unhurried knocks followed by waiting",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "The visitor arrives with three unhurried knocks and waits, following the defenders' threshold protocol correctly.",
    "first_person_testimony": true,
    "speaker": "CHAR-001",
    "attribution": "Binding as Mara's first-person account of hearing the visitor at her door.",
    "epistemic_limitation": "Protocol compliance guarantees neither admission, remedy, restoration, nor absolution.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "The three knocks form one visitor-arrival event seen from both sides of the threshold.",
      "The knock later changes function into Mara's outward obligation to ask and wait."
    ],
    "protected_ambiguities": [],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-CODA-THRESHOLD",
      "TL-CODA-OUTWARD"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CODA-ELEVEN-MILES",
    "authority_basis": "lyric",
    "source_path": "songs/The Radius.md",
    "source_location": "Lyric: Pre-Chorus, visitor's statement 'I was eleven miles from the array'",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Safiya reports that she was eleven miles from the array when the null harmed her.",
    "first_person_testimony": true,
    "speaker": "CHAR-004 (quoted by CHAR-001)",
    "attribution": "Binding as Safiya's reported statement within Mara's first-person lyric account; the approved novel maps the visitor to Safiya.",
    "epistemic_limitation": "The distance does not name a county, define the null's geometry, or authorize a derived radial measure.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "Keep the visitor's location eleven miles from Northline Array.",
      "Preserve deliberately unnamed country and county geography."
    ],
    "protected_ambiguities": [],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-CODA-APPROACH",
      "TL-CODA-ACCOUNT"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CODA-TUESDAY-KETTLE",
    "authority_basis": "lyric",
    "source_path": "songs/The Radius.md",
    "source_location": "Lyric: Verse 2, visitor's account 'it was a Tuesday' and 'the kettle was on'",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Safiya reports that the null loss occurred on a Tuesday while the kettle was on and she was thinking in the language she had only with her mother.",
    "first_person_testimony": true,
    "speaker": "CHAR-004 (quoted by CHAR-001)",
    "attribution": "Binding as Safiya's concrete recollection within Mara's first-person lyric account.",
    "epistemic_limitation": "The domestic details locate Safiya's experience but do not create an omniscient timestamp or identify every simultaneous null effect.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "The Tuesday kettle anchors Safiya's own account of the null.",
      "This is distinct from Mara's later kettle as an available human response."
    ],
    "protected_ambiguities": [],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-NULL-NIGHT",
      "TL-CODA-ACCOUNT"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CODA-MATERNAL-LANGUAGE-LOSS",
    "authority_basis": "lyric",
    "source_path": "songs/The Radius.md",
    "source_location": "Lyric: Pre-Chorus and Verse 2, loss of the mother's language on null night and retained face, hands, and coat but not sound",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Safiya reports that she was never occupied by anything foreign, but the null removed access to the language she had only with her dead mother; she retains other memories while losing the sound and private lexical layer.",
    "first_person_testimony": true,
    "speaker": "CHAR-004 (quoted by CHAR-001)",
    "attribution": "Binding as Safiya's reported loss within Mara's first-person lyric account.",
    "epistemic_limitation": "The lyric does not identify a real heritage language, community, geography, religion, ethnicity, politics, or surviving corpus from which the private layer could be rebuilt.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "Safiya's injury is subtraction caused by the defenders' null, not insertion by the Foreign Signal.",
      "Her public heritage language remains; the lost two-person layer has no surviving source corpus.",
      "The loss must remain materially specific without quoting or inventing a real language."
    ],
    "protected_ambiguities": [
      "The heritage base is unspecified by the author and must stay unspecified everywhere."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-NULL-NIGHT",
      "TL-CODA-ACCOUNT"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CODA-SAFIYA-FREE-CONSENT",
    "authority_basis": "lyric",
    "source_path": "songs/The Radius.md",
    "source_location": "Lyric: Bridge, visitor's sober repeated request, 'The answer's mine to give', 'I'm saying yes', and 'Come in'",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Safiya freely, soberly, specifically, and repeatedly consents to Mara using the retained transmitter in an attempt to put something back.",
    "first_person_testimony": true,
    "speaker": "CHAR-004 (quoted by CHAR-001)",
    "attribution": "Binding as Safiya's direct request and affirmative consent within Mara's first-person lyric account.",
    "epistemic_limitation": "Valid consent authorizes the requested act in principle but does not create missing source truth, compel Mara to transmit, waive truth, or guarantee restoration.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "The narrative must affirm Safiya's consent as genuine rather than infantilizing or retroactively invalidating it.",
      "Mara's refusal must rest somewhere other than lack of consent."
    ],
    "protected_ambiguities": [],
    "protected_wording": "Come in.",
    "affected_timeline_ids": [
      "TL-CODA-CONSENT",
      "TL-CODA-REFUSAL"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CODA-TRUTH-BASED-REFUSAL",
    "authority_basis": "lyric",
    "source_path": "songs/The Radius.md",
    "source_location": "Lyric: Bridge, 'Because I haven't got her mother. All I've got is me' and the stranger in the mother's chair",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Mara refuses transmission because she does not possess Safiya's mother or the erased private language; anything fabricated could arrive with false self-authentication and counterfeit memory phenomenology.",
    "first_person_testimony": true,
    "speaker": "CHAR-001",
    "attribution": "Binding as Mara's first-person account of the physics-and-truth limit on restoration.",
    "epistemic_limitation": "The refusal does not invalidate Safiya's consent, claim moral victory, prove all repair impossible, or turn Mara's ethics into absolution.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "The requested maternal-language restoration remains unmet.",
      "No successful, ambiguous, or consoling counterfeit may be transmitted.",
      "The relay goes off before the available human remedy begins.",
      "The refusal rests on two independent physical limits under DEC-015: Mara possesses no source corpus of the private two-person layer, and CANCEL has no additive inverse, so nothing the null removed can be restored by a further CANCEL, by PAIR, or by any combination of modes."
    ],
    "protected_ambiguities": [
      "Human companionship can be real and insufficient without becoming restoration."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-CODA-REFUSAL",
      "TL-CODA-STAYING"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CODA-HUMAN-REMEDY-OBLIGATION",
    "authority_basis": "lyric",
    "source_path": "songs/The Radius.md",
    "source_location": "Lyric: Turn, Final Verse, and Outro, kettle, voice through air, staying, walking the affected area, knocking, and waiting",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "After refusing the machine, Mara puts the kettle on, offers only her own spoken voice through ordinary air to a consenting listener, stays, and accepts an outward duty to walk the affected area, knock, and wait.",
    "first_person_testimony": true,
    "speaker": "CHAR-001",
    "attribution": "Binding as Mara's first-person account of the available human response and continuing obligation.",
    "epistemic_limitation": "Kettle, listening, staying, and outward visits do not restore Safiya's loss, earn forgiveness, settle the debt, or become a renewed campaign.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "The ending contracts from public scale to domestic presence and a quiet threshold action.",
      "The broader obligation remains incomplete and nontriumphal.",
      "No Foreign Signal return, counterphase, anthem, or moral victory may follow."
    ],
    "protected_ambiguities": [
      "What repair beyond truthful presence and accounting may become possible remains open."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-CODA-REFUSAL",
      "TL-CODA-STAYING",
      "TL-CODA-OUTWARD"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CODA-PROVENANCE-QUESTION",
    "authority_basis": "lyric",
    "source_path": "songs/The Radius.md",
    "source_location": "Lyric: Outro, terminal repeated question 'Whose was that?'",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "The Coda closes on an unresolved question of provenance after insertion, deletion, reconstruction, and testimony rather than on a returned signal or identified sender.",
    "first_person_testimony": true,
    "speaker": "CHAR-001",
    "attribution": "Binding as Mara's terminal first-person question in The Radius.",
    "epistemic_limitation": "The question opens inquiry and supplies no answer about sender, ownership, memory, or causation.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "The exact question is reserved for the final passage under the separate Motif Ledger constraint.",
      "This Canon Fact records provenance only and does not itself create a Literal Phrase Constraint.",
      "The second cycle opens through consequence and ownership questions without restarting the war."
    ],
    "protected_ambiguities": [
      "The ownership and origin of damaged, inserted, deleted, or reconstructed mental content remain unresolved."
    ],
    "protected_wording": "Whose was that?",
    "affected_timeline_ids": [
      "TL-CODA-OUTWARD"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CASE-ZERO-DECEMBER-DETAILS",
    "authority_basis": "lyric",
    "source_path": "songs/Case Zero.md",
    "source_location": "Lyric: Verse 1, alarm, shower, road call, twenty minutes, and console at ten to seven",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Nia reports a December morning consisting of an alarm, a shower, a call about the roads, twenty minutes of ordinary time, and reaching the console at ten to seven as usual.",
    "first_person_testimony": true,
    "speaker": "CHAR-002",
    "attribution": "Binding as the Case Zero speaker's first-person recollection; DEC-002 separately maps that speaker to Nia Calder.",
    "epistemic_limitation": "These details bind as Nia's account and do not become an external omniscient timestamp, prove handshake causation, or establish an exact calendar date beyond December.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "The source-side morning remains ordinary and continuous.",
      "Planning may use the reported twenty-minute interval and ten-to-seven console detail only with testimonial attribution."
    ],
    "protected_ambiguities": [
      "The account does not identify why Mara could receive it or what later caused Nia's wanting."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-DECEMBER-RECEIVE"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CASE-ZERO-OFFSET-NO-GAP",
    "authority_basis": "lyric",
    "source_path": "songs/Case Zero.md",
    "source_location": "Lyric: Verse 1, 'The eight seconds were hers' and 'I have never once been late to my own life'",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Nia reports that the receiver owned the eight-second offset and that she experienced no gap or lateness in her own life.",
    "first_person_testimony": true,
    "speaker": "CHAR-002",
    "attribution": "Binding as Nia's first-person report; DEC-002 separately supplies the proper-name and receiver-mechanism mapping.",
    "epistemic_limitation": "Her report establishes source-side continuity in her experience and does not prove the cause of any later wanting.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "Encode the eight seconds only as Mara's configuration-dependent acquisition-to-resolved-output reconstruction latency.",
      "Never introduce a source-side discontinuity or December transmission."
    ],
    "protected_ambiguities": [
      "The relation between December reception and the later wanting remains causal possibility, not proof."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-DECEMBER-RECEIVE"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CASE-ZERO-WANTING",
    "authority_basis": "lyric",
    "source_path": "songs/Case Zero.md",
    "source_location": "Lyric: Verse 1, Pre-Chorus, and Chorus, certainty with no perceptible moment, voice, word, or order",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Nia reports coming out the other side already sure: there was no nameable arrival moment, voice, word, order, or trace, only a wanting or certainty that fit as if it were her own.",
    "first_person_testimony": true,
    "speaker": "CHAR-002",
    "attribution": "Binding as Nia's first-person phenomenology of the injury.",
    "epistemic_limitation": "The account establishes the form of the experience and her unresolved provenance, not whether the state came from Mara, the Foreign Signal, or another source.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "Unconsented, uncalibrated crossing carries crude states rather than articulate language.",
      "Nia must not retrospectively hear a verbal instruction or decoded order.",
      "Her injury is the ability to be made sure without a traceable authorship chain."
    ],
    "protected_ambiguities": [
      "Nia has never found where the certainty began."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-DISCOVERY-HANDSHAKE",
      "TL-DISCOVERY-NIA-AFTERMATH"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CASE-ZERO-TRIAGE",
    "authority_basis": "lyric",
    "source_path": "songs/Case Zero.md",
    "source_location": "Lyric: Verse 2, two close calls, one available unit, routing against practice, and one death",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Nia reports two calls close together, one unit that could go, ordinary practice pointing one way, her unexplained certainty taking her the other way, and one person dying on the call she put second.",
    "first_person_testimony": true,
    "speaker": "CHAR-002",
    "attribution": "Binding as Nia's first-person account of the triage event and its human consequence.",
    "epistemic_limitation": "Her report does not by itself establish that her routing caused the death, identify what generated the wanting, or supply call specifics not fixed by DEC-004.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "Preserve two close calls, one available unit, routing against ordinary practice, and one real death.",
      "Treat the dead person as a person rather than a mechanism or exculpatory data point.",
      "Specific call types and unit details remain adjustable during Arc Outline work."
    ],
    "protected_ambiguities": [
      "Origin and causal authorship of the wanting remain unresolved."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-DISCOVERY-HANDSHAKE",
      "TL-DISCOVERY-NIA-AFTERMATH"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CASE-ZERO-CONSENT-SCENE",
    "authority_basis": "lyric",
    "source_path": "songs/Case Zero.md",
    "source_location": "Lyric: Bridge, a shut-door room with five people and a whiteboard, where Nia asks 'Did I say yes?' twice",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Nia reports confronting five people and a whiteboard in a room with the door shut and asking the exact authorization question twice before requiring the protocol to be written down.",
    "first_person_testimony": true,
    "speaker": "CHAR-002",
    "attribution": "Binding as Nia's first-person account of the consent confrontation.",
    "epistemic_limitation": "The account binds Nia's authorship and reported scene without turning every production-stage image into omniscient fact or fixing later staging beyond what she reports.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "Nia owns the authorization challenge and cannot be reduced to an emblem for another character's doctrine.",
      "The exact phrase remains subject to the separate Mindwars-only Literal Phrase Constraint in the Motif Ledger.",
      "This Canon Fact does not scan song text or create a Chapter File occurrence."
    ],
    "protected_ambiguities": [],
    "protected_wording": "Did I say yes?",
    "affected_timeline_ids": [
      "TL-PRIVATE-PROTOCOL",
      "TL-MINDWARS-COUNTERPHASE"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CASE-ZERO-CONSENT-RULE",
    "authority_basis": "lyric",
    "source_path": "songs/Case Zero.md",
    "source_location": "Lyric: Bridge, 'ask me now, ask me for this one thing, and I can take it back at noon'",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Nia reports requiring consent to be current, specific to the requested act, and revocable, using revocation at noon as the scene's example.",
    "first_person_testimony": true,
    "speaker": "CHAR-002",
    "attribution": "Binding as Nia's first-person account of the protocol she forced the group to record.",
    "epistemic_limitation": "Noon is one lyric-scene example and never becomes a universal revocation deadline or general legal rule.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "Consent prompts must be contemporaneous and act-specific.",
      "Consent remains revocable and cannot be converted into blanket service assent.",
      "The protocol's authorial and moral pressure belongs materially to Nia."
    ],
    "protected_ambiguities": [],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-PRIVATE-PROTOCOL",
      "TL-MINDWARS-COUNTERPHASE",
      "TL-CODA-CONSENT"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CASE-ZERO-APPROPRIATION",
    "authority_basis": "lyric",
    "source_path": "songs/Case Zero.md",
    "source_location": "Lyric: Bridge, histories and songs taking Nia's question and putting a choir behind her worst afternoon",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Nia testifies that histories and songs appropriated her experience and transformed her consent question into a beautiful collective chorus that no longer felt hers.",
    "first_person_testimony": true,
    "speaker": "CHAR-002",
    "attribution": "Binding as Nia's first-person judgment about appropriation of her account.",
    "epistemic_limitation": "Her testimony binds the experience and critique; it does not automatically establish a literal diegetic choir, every production-stage image, or objective intent by every historian or singer.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "Do not make Nia a rhetorical collective or absorb her singular account into Mara's public 'we'.",
      "Nia may challenge record ownership without supplying an answer to causal provenance."
    ],
    "protected_ambiguities": [
      "The precise public forms of every history or song remain unspecified unless later selected as compatible extensions."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-POSTNULL-HISTORY"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CASE-ZERO-LOGS",
    "authority_basis": "lyric",
    "source_path": "songs/Case Zero.md",
    "source_location": "Lyric: Turn, timestamps, call times, assignments, the death already over, and the log not knowing who wanted it",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Nia reports that dispatch logs showed the death was already unavoidable before her routing and that nothing she could have sent would have arrived in time, while the same logs remained silent on who or what generated the wanting.",
    "first_person_testimony": true,
    "speaker": "CHAR-002",
    "attribution": "Binding as Nia's first-person account of the documentary review and its limited exoneration.",
    "epistemic_limitation": "The logs clear the routing decision's causal effect on the death; they do not identify the wanting's origin, erase the death, resolve Nia's injury, absolve Mara, or validate the archive.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "The documentary release belongs in the Private Defense record sequence.",
      "The evidence resolves outcome causation but not mental authorship.",
      "The logs become the misleading documentary anchor for the histories' first-casualty entry."
    ],
    "protected_ambiguities": [
      "Both origin accounts remain unverified after the logs return."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-PRIVATE-RECORD-DEPOSITS",
      "TL-POSTNULL-HISTORY"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CASE-ZERO-LOSS-INTAKE",
    "authority_basis": "lyric",
    "source_path": "songs/Case Zero.md",
    "source_location": "Lyric: Outro, drawing a missing line on the form and taking calls for losses at a different desk",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Nia reports postwar work receiving civilian loss accounts, adding by hand the category for what went out, and helping callers state losses that existing forms cannot contain.",
    "first_person_testimony": true,
    "speaker": "CHAR-002",
    "attribution": "Binding as Nia's first-person report of her postwar loss-intake work and continued use of judgment.",
    "epistemic_limitation": "Her work demonstrates usable self-trust without proving origin, forgiving Mara, endorsing the archive, or claiming that the forms now capture every loss.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "Nia participates in Coda public accounting rather than renewed combat.",
      "Official and archival categories remain better at recording intrusion than subtraction.",
      "Nia's emotional movement lands in action despite unresolved provenance."
    ],
    "protected_ambiguities": [
      "Nia still does not know where her certainty began."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-CODA-PUBLIC-ACCOUNTING"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-CASE-ZERO-GO-AHEAD",
    "authority_basis": "lyric",
    "source_path": "songs/Case Zero.md",
    "source_location": "Lyric: Intro and Outro, Nia's permission phrase 'Go ahead.'",
    "source_material_class": "lyric",
    "adopted_by": null,
    "statement": "Nia uses 'Go ahead.' as her canonical dispatcher permission phrase, granting a caller permission to speak at the opening and close of her account.",
    "first_person_testimony": true,
    "speaker": "CHAR-002",
    "attribution": "Binding Canon Dialogue spoken by Nia in her professional and ethical register.",
    "epistemic_limitation": "The phrase permits speech in context; it is not blanket mental consent, proof of origin, or authorization for a different act.",
    "truth_scope": "attributed-testimony",
    "binding_implications": [
      "If quoted or closely adapted in a Chapter File, attribute the dialogue to Nia and preserve permission-to-speak meaning.",
      "Record any Chapter File use in dialogue provenance without treating song occurrences as prose-body literal matches."
    ],
    "protected_ambiguities": [],
    "protected_wording": "Go ahead.",
    "affected_timeline_ids": [
      "TL-CODA-PUBLIC-ACCOUNTING"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-NIA-OPERATIONAL-SYNTHESIS",
    "authority_basis": "author-decision",
    "source_path": "The Final Frontier Novel/planning/decisions.md",
    "source_location": "DEC-004, The incident and evidence point",
    "source_material_class": "author-decision",
    "adopted_by": null,
    "statement": "Nia's first operational consequence is triage under scarcity with two close calls and one available advanced unit; a wanting rather than an instruction drives routing against practice, one person dies, and later logs show the outcome was already unsurvivable before her decision while proving nothing about authorship.",
    "first_person_testimony": false,
    "speaker": null,
    "attribution": null,
    "epistemic_limitation": null,
    "truth_scope": "authoritative-proposition",
    "binding_implications": [
      "The real death matters, but Nia's routing is causally irrelevant to it.",
      "The injury remains epistemic authorship rather than consequential guilt.",
      "The log becomes the record's anchor for an adversary attribution that its evidence cannot establish.",
      "Specific call and unit texture remains adjustable without changing this structure."
    ],
    "protected_ambiguities": [
      "Where the wanting came from remains unsettled."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-DISCOVERY-HANDSHAKE",
      "TL-DISCOVERY-NIA-AFTERMATH",
      "TL-PRIVATE-RECORD-DEPOSITS",
      "TL-POSTNULL-HISTORY"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-NIA-BELIEF-DISTRIBUTION",
    "authority_basis": "author-decision",
    "source_path": "The Final Frontier Novel/planning/decisions.md",
    "source_location": "DEC-007, Distribution, movement, and binding constraints",
    "source_material_class": "author-decision",
    "adopted_by": null,
    "statement": "Mara privately holds a high but non-authoritative conviction that her later handshake caused Nia's wanting; Nia refuses both unsupported origin accounts and eventually stops needing an origin to regain usable self-trust; Julian professionally enters the adversary attribution while privately recognizing it as inference.",
    "first_person_testimony": false,
    "speaker": null,
    "attribution": null,
    "epistemic_limitation": null,
    "truth_scope": "authoritative-proposition",
    "binding_implications": [
      "Mara's conviction remains mostly unvoiced and functions as evidence of guilt-seeking self-centralization, never authorial confirmation.",
      "Nia rejects Mara's attempted confession as appropriation without absolving her or accepting the archive's account.",
      "Julian preserves the distinction between an institutionally enterable inference and truth.",
      "Nia's usable self-trust resolves an emotional question without resolving causation, forgiveness, or archive validity."
    ],
    "protected_ambiguities": [
      "Both the handshake account and adversary account remain unresolved with no reveal owner or release window."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-DISCOVERY-NIA-AFTERMATH",
      "TL-PRIVATE-RECORD-DEPOSITS",
      "TL-MINDWARS-ONSET",
      "TL-POSTNULL-HISTORY",
      "TL-CODA-PUBLIC-ACCOUNTING"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  }
]
```

## Novel Extensions

These records add continuity beneath higher authority. The Nia name/mechanism mapping is intentionally separate from the *Case Zero* lyric facts above: `DEC-014` makes the same-speaker testimony binding, while `DEC-002` supplies the proper name, person-specific address, and later bench-path mapping. Neither authority layer confirms causation.

```json record=NovelExtension schema=1
[
  {
    "extension_id": "EXT-CHAR-MARA-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-001 and POV-MARA identify the Anchor POV selected as Dr. Mara Venn; no alias is currently selected.",
    "rationale": "A stable name and identifiers support continuity across all four movements.",
    "authority_ref": "DESIGN-NAMED-POV-CAST",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DECEMBER-RECEIVE"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-DECEMBER-RECEIVE"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-CODA-OUTWARD"
      }
    ],
    "consistency_implications": [
      "Use Mara Venn consistently for CHAR-001 and POV-MARA.",
      "Mara is the finder, private defender, counterphase lead, null decision-maker, and Coda accounting witness."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CHAR-NIA-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-002 and POV-NIA identify Nia Calder; no alias is currently selected, and 'case zero' is a label she refuses rather than an alias.",
    "rationale": "A stable name preserves one human identity across the December source account, first wanting, consent work, and loss intake.",
    "authority_ref": "DESIGN-NAMED-POV-CAST",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DECEMBER-RECEIVE"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-DECEMBER-RECEIVE"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-CODA-PUBLIC-ACCOUNTING"
      }
    ],
    "consistency_implications": [
      "Use Nia Calder consistently for CHAR-002 and POV-NIA.",
      "Never convert 'case zero' into a preferred name or neutral table identity."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CHAR-JULIAN-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-003 and POV-JULIAN identify Julian Adebayo; no alias is currently selected.",
    "rationale": "A stable name supports institutional, contractual, and archive continuity.",
    "authority_ref": "DESIGN-NAMED-POV-CAST",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DISCOVERY-DUE-DILIGENCE"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-DISCOVERY-DUE-DILIGENCE"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-TRUST-CONDITIONED-RELEASES"
      }
    ],
    "consistency_implications": [
      "Use Julian Adebayo consistently for CHAR-003 and POV-JULIAN.",
      "Julian never gains privileged certainty merely because he controls document custody."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CHAR-SAFIYA-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-004 and POV-SAFIYA identify Safiya Mir; no alias is currently selected.",
    "rationale": "A stable name gives the Coda claimant her own narrative identity rather than reducing her to a category of harm.",
    "authority_ref": "DESIGN-NAMED-POV-CAST",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-CODA-APPROACH"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-CODA-APPROACH"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-CODA-STAYING"
      }
    ],
    "consistency_implications": [
      "Use Safiya Mir consistently for CHAR-004 and POV-SAFIYA.",
      "Her name may not be used to infer unselected real-world linguistic, geographic, religious, ethnic, or political particulars."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-PROFESSION-MARA",
    "extension_kind": "profession",
    "fact": "Mara Venn is a computational radio physicist at Northline Array.",
    "rationale": "The role grounds the mathematical-radio discovery and her responsibility for later technical decisions.",
    "authority_ref": "DESIGN-NAMED-POV-CAST",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DECEMBER-RECEIVE"
    },
    "affected_records": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-DECEMBER-RECEIVE-ONLY"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-NULL-NIGHT"
      }
    ],
    "consistency_implications": [
      "Mara owns technical choices but never another person's interior harm.",
      "Her expertise does not grant omniscient sender knowledge."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-PROFESSION-NIA",
    "extension_kind": "profession",
    "fact": "Nia Calder is a county emergency dispatcher and later works at a civilian-loss intake desk.",
    "rationale": "Dispatch judgment makes the wanting's epistemic injury concrete, and later intake work embodies usable self-trust.",
    "authority_ref": "DESIGN-NAMED-POV-CAST-AND-DEC-014",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DECEMBER-RECEIVE"
    },
    "affected_records": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-TRIAGE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-LOSS-INTAKE"
      }
    ],
    "consistency_implications": [
      "Her dispatcher register remains distinct from Mara's scientific register.",
      "Her postwar work is not forgiveness, archive validation, or factual closure."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-PROFESSION-JULIAN",
    "extension_kind": "profession",
    "fact": "Julian Adebayo is a technology-transactions lawyer who brings the April term sheet, later breaks with consortium representation, and establishes the record institution.",
    "rationale": "His role owns contractual language, institutional incentives, altered records, custody, and the difference between enterable claims and truth.",
    "authority_ref": "DESIGN-NAMED-POV-CAST",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DISCOVERY-DUE-DILIGENCE"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-APRIL-TERM-SHEET"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-TRUST-FORMATION"
      }
    ],
    "consistency_implications": [
      "Julian's legal and custodial authority never certifies Foreign Signal provenance.",
      "His professional adversary attribution remains an acknowledged inference."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-PROFESSION-SAFIYA",
    "extension_kind": "profession",
    "fact": "Safiya Mir is a school librarian and occasional community interpreter who retains her public heritage language.",
    "rationale": "The profession gives her an independent civic life and sharpens the specific loss of the private language layer without making her only an instrument of Mara's guilt.",
    "authority_ref": "DEC-003-AND-DESIGN-NAMED-POV-CAST",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-CODA-APPROACH"
    },
    "affected_records": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-MATERNAL-LANGUAGE-LOSS"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-CODA-ACCOUNT"
      }
    ],
    "consistency_implications": [
      "Safiya continues to use a public heritage language and may interpret for her community.",
      "No real language, region, religion, ethnicity, politics, or conflict may be inferred from her name or unspecified heritage base.",
      "Community-portrayal review remains required; linguistic review of quoted real wording is not required because no real wording is available."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-INSTITUTION-NORTHLINE",
    "extension_kind": "institution",
    "fact": "The technical institution and array are named Northline Array.",
    "rationale": "The exact selected name distinguishes the discovery site from commercial and custodial institutions.",
    "authority_ref": "DEC-005",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DECEMBER-RECEIVE"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-DECEMBER-RECEIVE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-ELEVEN-MILES"
      }
    ],
    "consistency_implications": [
      "Use the exact name Northline Array wherever continuity depends on the site.",
      "Eleven miles is measured from this array without naming the containing county."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-INSTITUTION-OPEN-CHANNEL",
    "extension_kind": "institution",
    "fact": "The commercial coalition is named Open Channel Consortium.",
    "rationale": "The exact selected name distinguishes commercial benevolence and write-capable deployment pressure from Northline Array.",
    "authority_ref": "DEC-005",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DISCOVERY-DUE-DILIGENCE"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PRIVATE-OFFER"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-APRIL-TERM-SHEET"
      }
    ],
    "consistency_implications": [
      "Use the exact name Open Channel Consortium.",
      "The consortium's promises may be sincerely attractive without making write-capable defaults consensual."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-INSTITUTION-CIVIC-RECORD",
    "extension_kind": "institution",
    "fact": "The independent public-interest archive is named Civic Record Trust.",
    "rationale": "The exact selected name distinguishes provenance-preserving witness custody from official summaries.",
    "authority_ref": "DEC-005",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-TRUST-FORMATION"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-TRUST-FORMATION"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-TRUST-CONDITIONED-RELEASES"
      }
    ],
    "consistency_implications": [
      "Use the exact name Civic Record Trust.",
      "The Trust warrants custody and provenance, never objective truth."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-GEOGRAPHY-UNNAMED",
    "extension_kind": "place",
    "fact": "The country and every individual county remain intentionally unnamed; this is selected geography rather than an unresolved placeholder.",
    "rationale": "Unnamed geography keeps attention on people and the canonical extent without inventing a national analogue or derived map.",
    "authority_ref": "DEC-005",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DECEMBER-RECEIVE"
    },
    "affected_records": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-NULL-EXTENT"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-CODA-APPROACH"
      }
    ],
    "consistency_implications": [
      "Generic county functions and descriptive locations are permitted.",
      "No fictional proper country or county name may be introduced without reopening DEC-005.",
      "Three counties wide remains canonical text and never becomes named geography or a computed radius."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-NIA-SOURCE-CASUALTY",
    "extension_kind": "other-continuity",
    "fact": "Nia Calder is both the source of the continuous December morning Mara receives eight seconds late and the woman who later experiences the first documented wanting; Case Zero is Nia's counter-deposition.",
    "rationale": "DEC-002 approves the named role braid, while DEC-014 separately supplies binding same-speaker lyric testimony.",
    "authority_ref": "DEC-002",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DECEMBER-RECEIVE"
    },
    "affected_records": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-DECEMBER-DETAILS"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-WANTING"
      },
      {
        "record_type": "Reveal",
        "record_id": "REVEAL-NIA-SOURCE-CASUALTY"
      }
    ],
    "consistency_implications": [
      "The shared identity is confirmed, while December reception and the later insertion remain distinct in kind and time.",
      "DEC-002 constraint 1 — Never confirmed: handshake-to-wanting causation remains unverified; no instrument or narrator settles it, and it has no reveal owner or release window.",
      "DEC-002 constraint 2 — The adversary still owns the war: contested causation is limited to the first casualty; every later intrusion and the Mindwars remain the adversary's, and Mara is never the sole cause.",
      "DEC-002 constraint 3 — The record gets it wrong and cannot fix it: the first-casualty adversary attribution remains an uncorrectable institutional inference, and no late disclosure tidies the archive.",
      "DEC-002 constraint 4 — Insertion through Nia and subtraction through Safiya remain distinct harms; their rhyme never makes them equivalent.",
      "DEC-002 constraint 5 — Nia regains usable self-trust without deciding causation, forgiving Mara, or validating the archive."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-NIA-PERSON-ADDRESS",
    "extension_kind": "mechanism",
    "fact": "The December receive-only apparatus identifies and locks onto Nia's person-specific channel or address; the later temporary bench path deliberately reuses that same address for a content-free handshake.",
    "rationale": "The mechanism makes the protected causal possibility plausible while preserving the receive-only December state and permanent lack of proof.",
    "authority_ref": "DEC-002",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DECEMBER-RECEIVE"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-DECEMBER-RECEIVE"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-DISCOVERY-HANDSHAKE"
      },
      {
        "record_type": "Reveal",
        "record_id": "REVEAL-HANDSHAKE-WANTING-ORIGIN"
      }
    ],
    "consistency_implications": [
      "December has no transmit stage.",
      "The later path is deliberate, temporary, and content-free.",
      "Shared address and chronology are evidence of possibility only, never causal proof."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-ESP-PAIRINGS",
    "extension_kind": "mechanism",
    "fact": "ESP expands in-world to Electronic Speech Pairings and one authorized link is a pairing; the term is a contested late institutional simplification coined only after Discovery, and it is not supernatural extrasensory perception.",
    "rationale": "DEC-012, as completed by DEC-015, supplies stable in-world terminology for the consented conversational mode while refusing the earlier fixed-token ceiling and refusing to let one institutional label collapse four distinct modes into one capability.",
    "authority_ref": "DEC-012",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-PRIVATE-PROTOCOL"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-MINDWARS-COUNTERPHASE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-WANTING"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-TAXONOMY"
      }
    ],
    "consistency_implications": [
      "ESP names deliberate paired conversation in particular and never legitimately describes RECEIVE observation, INTRUDE influence, or CANCEL cancellation.",
      "Superseded: the earlier fixed agreed-token ceiling is retired. Repeated pair-specific calibration may reach fluent near-natural internal speech; tokens survive only as a training or operational fallback.",
      "The acronym deliberately collides with discredited extrasensory perception as a target for institutional and public mockery; neither the label nor the mechanism validates a supernatural reading.",
      "Julian, institutions, histories, and public argument carry most uses; Mara uses the term rarely and technically; Nia resists the label when it obscures consent state or makes her wanting sound like conversation.",
      "The term cannot be established in Discovery, retroactively create a December transmit stage, or support either origin account, and a later historical back-application remains a label rather than evidence.",
      "Any operational paired material stays inside existing POV chapters or deposited records, adds no POV, exposes only consent-state and transport metadata to traffic analysis, identifies no Foreign Signal or wanting source, and remains categorically distinct from Safiya's corpus-less private layer."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-SAFIYA-HERITAGE",
    "extension_kind": "other-continuity",
    "fact": "heritage_base: unspecified_by_author; Safiya retains a public heritage language, while the null removes only the private two-person layer of invented words, private grammar, and shared reference built with her dead mother.",
    "rationale": "DEC-003 protects the physics of an unrestorable corpus-less loss without inventing a real-world community the author did not select.",
    "authority_ref": "DEC-003",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-CODA-ACCOUNT"
    },
    "affected_records": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-MATERNAL-LANGUAGE-LOSS"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-TRUTH-BASED-REFUSAL"
      }
    ],
    "consistency_implications": [
      "The exact structured value heritage_base: unspecified_by_author must remain unfilled in every project artifact.",
      "No artifact may infer or invent real-world linguistic, geographic, religious, ethnic, or political particulars from Safiya's name or the unspecified base.",
      "No real conflict may be used as allegory, parallel, or thematic echo for the Mindwars.",
      "Describe-never-quote is the default; sparse invented private-layer words are permitted; real heritage wording is unavailable unless DEC-003 is reopened.",
      "Community-portrayal review remains required, and absence of linguistic review may never weaken Safiya's loss or agency."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-APRIL-RECORD-ALTERATION",
    "extension_kind": "document",
    "fact": "After the April negotiation, institutional summaries soften or alter the meeting record before Julian forms the Civic Record Trust.",
    "rationale": "The altered record motivates an independent provenance-preserving archive and makes record custody a plot consequence rather than preexisting infrastructure.",
    "authority_ref": "DESIGN-TESTIMONY-FRAME",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-APRIL-RECORD-ALTERATION"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-APRIL-RECORD-ALTERATION"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-TRUST-FORMATION"
      }
    ],
    "consistency_implications": [
      "Trust formation must occur after Julian observes the alteration.",
      "The altered record cannot erase the original source material or turn a later summary into omniscient truth."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-ARCHIVE-CONTESTED",
    "extension_kind": "other-continuity",
    "fact": "Official summaries and conditioned, provenance-preserving Civic Record Trust releases compete publicly after the null; neither stream is complete or final, and no unified inquiry adjudicates between them.",
    "rationale": "DEC-005 preserves visible public contest without allowing the archive to become secret, fully open, or omniscient.",
    "authority_ref": "DEC-005",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-POSTNULL-HISTORY"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-TRUST-CONDITIONED-RELEASES"
      },
      {
        "record_type": "Reveal",
        "record_id": "REVEAL-HANDSHAKE-WANTING-ORIGIN"
      },
      {
        "record_type": "Reveal",
        "record_id": "REVEAL-FOREIGN-SIGNAL-PROVENANCE"
      }
    ],
    "consistency_implications": [
      "Witness embargo and release conditions remain enforceable, and complete holdings are never presumed public.",
      "The Trust warrants provenance rather than objective truth.",
      "The first-casualty adversary attribution remains an uncorrectable institutional inference despite public counter-records.",
      "No inquiry, release, narrator, or later record confirms or disproves either account of Nia's wanting."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-RECORD-FRAME",
    "extension_kind": "document",
    "fact": "The reader-facing archive frame consists of one concise Front Matter note plus rare, dramatically necessary in-story references; there are no routine source notes, transcript apparatus, docket labels, or heavy archival labels.",
    "rationale": "DEC-006 supplies enough orientation for first-person-past testimony while protecting novelistic immediacy.",
    "authority_ref": "DEC-006",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-RECORD-PRETRUST-COMPOSITION"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-RECORD-PRETRUST-COMPOSITION"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-TRUST-ROLLING-DEPOSITS"
      }
    ],
    "consistency_implications": [
      "Detailed record horizons, composition dates, deposit dates, release conditions, and custody bookkeeping remain in planning unless dramatically necessary.",
      "Calibration may remove an unearned rare reference but may not replace the selected restrained model.",
      "The frame authenticates provenance of an account, not truth inside it."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-TRUST-GOVERNANCE",
    "extension_kind": "institution",
    "fact": "The Civic Record Trust is governed by custodians rather than Julian alone, accepts encrypted signed deposits with witness-controlled embargo and release conditions, and preserves original provenance.",
    "rationale": "Custodial governance prevents Julian from becoming an omniscient or unilateral archive authority.",
    "authority_ref": "DESIGN-TESTIMONY-FRAME",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-TRUST-FORMATION"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-TRUST-ROLLING-DEPOSITS"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-TRUST-CONDITIONED-RELEASES"
      }
    ],
    "consistency_implications": [
      "The board has no POV and never certifies objective truth.",
      "Discovery records predate the institution and are deposited only later with original dates and provenance.",
      "Rolling Trust deposits begin only after formation."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-REL-MARA-NIA",
    "extension_kind": "relationship",
    "fact": "Mara and Nia move from unknown receiver and source to investigator and witness, then collaborators under moral tension; Nia remains a check on Mara's self-centralizing guilt and never grants causal confirmation or absolution.",
    "rationale": "The relationship must land emotionally while the factual origin question stays open.",
    "authority_ref": "DEC-002-AND-DEC-007",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DISCOVERY-NIA-AFTERMATH"
    },
    "affected_records": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-NIA-BELIEF-DISTRIBUTION"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PRIVATE-PROTOCOL"
      }
    ],
    "consistency_implications": [
      "Mara's attempted confession cannot appropriate Nia's injury.",
      "Nia's refusal is neither proof against Mara's theory nor forgiveness.",
      "Collaboration may deepen without collapsing their distinct knowledge and moral positions."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-REL-MARA-JULIAN",
    "extension_kind": "relationship",
    "fact": "Julian is Mara's former trusted counsel; their loyalty is strained by the April term sheet, record alteration, consortium break, and Trust custody.",
    "rationale": "The relationship carries institutional complicity and record pressure through personal trust without giving either character authority over the other's account.",
    "authority_ref": "DESIGN-NAMED-POV-CAST",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DISCOVERY-DUE-DILIGENCE"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-APRIL-TERM-SHEET"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-POSTNULL-HISTORY"
      }
    ],
    "consistency_implications": [
      "Julian's professional language may conceal his complicity but cannot erase it.",
      "Mara's technical certainty and Julian's documentary authority remain independently limited."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-REL-MARA-SAFIYA",
    "extension_kind": "relationship",
    "fact": "Safiya is a stranger to Mara before the Coda visit; the debt between them is civic rather than personal, and Safiya controls her request, consent, disappointment, and choice to remain.",
    "rationale": "The lack of prior relationship prevents the null's civilian debt from becoming only private guilt or a preexisting bond.",
    "authority_ref": "DESIGN-NAMED-POV-CAST",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-CODA-THRESHOLD"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-CODA-CONSENT"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-CODA-STAYING"
      }
    ],
    "consistency_implications": [
      "Safiya does not exist to deliver absolution or complete Mara's redemption.",
      "Mara may offer truthful presence but cannot define it as repair for Safiya.",
      "Safiya's decision to stay remains autonomous and insufficient as restoration."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CHAR-ADA-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-005 identifies Ada Ferris, a community interpreter who lost expressive speech years before any neural communication event in the novel; she is a non-viewpoint supporting character with no POV and no alias.",
    "rationale": "The freely chosen benefit of Chapters 36-42 needs one named living pair rather than an anonymous demonstration, and a recurring name lets the same pair return as working interpreters instead of multiplying one-off participants.",
    "authority_ref": "DEC-012-AND-DEC-015-AND-REQUIREMENT-15-3",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-PAIR-CLINICAL-BENEFIT"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PAIR-CLINICAL-BENEFIT"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-CHAR-LENA-NAME"
      }
    ],
    "consistency_implications": [
      "Ada holds a Character ID and no POV, no VoiceBrief, and no chapter load; nothing is narrated from inside her.",
      "Her speech loss is an ordinary medical fact that predates December, has no relation to RECEIVE, INTRUDE, or CANCEL, and is never an earlier casualty, a precedent, or a rehearsal for Safiya's subtraction.",
      "Pairing carries only what she deliberately sends. It restores nothing, reverses nothing, and supplies no template for undoing what the null removed from anyone."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CHAR-LENA-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-006 identifies Lena Ferris, Ada Ferris's adult daughter and her calibrated pairing partner; she is a non-viewpoint supporting character with no POV and no alias.",
    "rationale": "PAIR requires exactly two living named participants, and the daughter Julian watches at 36 is the same person who carries the professional passage at 41, which keeps the demonstration cast small and recurring.",
    "authority_ref": "DEC-012-AND-DEC-015-AND-REQUIREMENT-15-3",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-PAIR-CLINICAL-BENEFIT"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PAIR-CLINICAL-BENEFIT"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-CHAR-ADA-NAME"
      }
    ],
    "consistency_implications": [
      "Lena holds a Character ID and no POV, no VoiceBrief, and no chapter load.",
      "The Ferris calibration belongs to Ada and Lena alone; it cannot be transferred, inherited, or pointed at anyone else, including a later replacement partner.",
      "Their pairing is a chosen benefit between two living people and never evidence about origin, provenance, or another person's interior."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CHAR-TOMAS-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-007 identifies Tomas Reyner, a county emergency dispatcher who works Nia Calder's floor; he is a non-viewpoint supporting character with no POV and no alias.",
    "rationale": "The dispatch demonstration, the later clipped live operation, and the null-night consent shelter all need the same working colleagues, so one named dispatcher recurs instead of three anonymous ones.",
    "authority_ref": "DEC-012-AND-DEC-015-AND-REQUIREMENT-15-3",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-PAIR-DISPATCH-DEMONSTRATION"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PAIR-DISPATCH-DEMONSTRATION"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PAIR-DISPATCH-OPERATIONS"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PAIR-SHELTER-INTAKE"
      }
    ],
    "consistency_implications": [
      "Tomas holds a Character ID and no POV, no VoiceBrief, and no chapter load; his sessions are supporting action inside Nia's or Julian's chapters.",
      "His calibration with Cora Baird and his separate calibration with Nia are distinct, pair-specific, and nontransferable; neither is reused with a third person.",
      "He is a dispatcher and a volunteer, never an operative, an adversary, or a route to the Foreign Signal's provenance."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CHAR-CORA-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-008 identifies Cora Baird, a county emergency dispatcher and Tomas Reyner's calibrated pairing partner; she is a non-viewpoint supporting character with no POV and no alias.",
    "rationale": "The paired-dispatcher benefit at 38 and the paired shelter intake on null night are the same two working people, which keeps the supporting cast recurring rather than disposable.",
    "authority_ref": "DEC-012-AND-DEC-015-AND-REQUIREMENT-15-3",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-PAIR-DISPATCH-DEMONSTRATION"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PAIR-DISPATCH-DEMONSTRATION"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PAIR-SHELTER-INTAKE"
      }
    ],
    "consistency_implications": [
      "Cora holds a Character ID and no POV, no VoiceBrief, and no chapter load.",
      "A demonstrated operational benefit never converts broad-form enrollment into consent; the form Nia reads at 38 is criticized by the same scene that shows the benefit.",
      "Shelter pairing on null night coordinates people and carries no cancellation, no group mind, and no claim about who is affected."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CHAR-IDRIS-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-009 identifies Idris Vane, a protective-network operator separately calibrated with Mara Venn and with Rhea Osei; he is a non-viewpoint supporting character with no POV and no alias.",
    "rationale": "Operational pairing is the coordination layer of the protective network, and naming one operator lets the same channel recur under shield pressure, under Julian's traffic analysis, and on null night.",
    "authority_ref": "DEC-012-AND-DEC-015-AND-REQUIREMENT-15-3",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-PAIR-OPERATOR-SHIFT-VANE"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PAIR-OPERATOR-SHIFT-VANE"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PAIR-OPERATOR-TRAFFIC"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PAIR-NULL-NIGHT-COORDINATION"
      }
    ],
    "consistency_implications": [
      "Idris holds a Character ID and no POV, no VoiceBrief, and no chapter load; every session of his is supporting action inside a Mara, Nia, or Julian chapter.",
      "He holds two separate pair-specific calibrations, one with Mara and one with Rhea Osei, and neither can be installed, inherited, or extended to a third participant.",
      "Operators pair; they do not cancel, do not read arbitrary memory, and never become an adversary, a sender, or a provenance answer."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CHAR-RHEA-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-010 identifies Rhea Osei, a protective-network operator separately calibrated with Mara Venn and with Idris Vane; she is a non-viewpoint supporting character with no POV and no alias.",
    "rationale": "Coverage accounting needs a second separately calibrated operator so the network's reach is visibly bounded by how many pairs consent, and the two operators' own channel is the traffic Julian later reads.",
    "authority_ref": "DEC-012-AND-DEC-015-AND-REQUIREMENT-15-3",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-PAIR-OPERATOR-SHIFT-OSEI"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PAIR-OPERATOR-SHIFT-OSEI"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PAIR-OPERATOR-TRAFFIC"
      }
    ],
    "consistency_implications": [
      "Rhea holds a Character ID and no POV, no VoiceBrief, and no chapter load.",
      "Because Mara must calibrate separately with each operator, protective coverage scales only as fast as consenting pairs, which is the accounting Chapter 84 performs.",
      "Traffic analysis of the operators' channel exposes timing, volume, acknowledgments, consent transitions, and errors, and never unrecorded meaning."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CHAR-RAVI-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-011 identifies Ravi Anand, a Northline Array technician who independently reruns Mara Venn's December timing and control checks and who continues on the shielded-room programme through the copper-room window; he is a non-viewpoint supporting character with no POV and no alias.",
    "rationale": "The December reconstruction-latency claim needs an independent witness who can repeat the same-sample/same-settings control without turning Mara's interpretation into self-certifying evidence. DEC-018 adds the surname because he recurs across at least seventeen delivered chapters, is entered on Mara's exposed-persons list over his objection, and now carries a named consequence of that entry, so a first name alone can no longer identify him in dialogue, records, or a reassignment request.",
    "authority_ref": "REQUIREMENTS-4-5-AND-6-16-AUTHOR-CALIBRATION-DIRECTIVE-AND-DEC-018",
    "first_dependency": {
      "record_type": "ArcEntry",
      "record_id": "3"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-DECEMBER-RECEIVE"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PRIVATE-COPPER"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-PRIVATE-EXPOSED-PERSONS-LIST"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-PRIVATE-TECHNICIAN-REPORT"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-PRIVATE-TECHNICIAN-REASSIGNMENT"
      }
    ],
    "consistency_implications": [
      "Ravi independently repeats timing and control work but does not originate Mara's interpretation, receive a POV, or become evidence of a transmit stage.",
      "His selected name licenses no inferred nationality, ethnicity, religion, language, geography, or other real-world cultural detail.",
      "He is not a sender, adversary, or source of the received field.",
      "The surname changes no Character ID: CHAR-011 is the same person named Ravi in every delivered chapter, and the added surname is a naming synchronization rather than a new character.",
      "He holds no POV even where his report and his departure are the material events, so both reach the reader only through a viewpoint lead's account of them."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CHAR-KEV-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-012 identifies Kev, the county dispatch colleague finishing the night shift who answers Nia Calder's 6:31 road call and repeats the fence-call handover in person; he is a non-viewpoint supporting character with no POV, surname, or alias selected.",
    "rationale": "A stable continuity witness anchors the canonical road-call-to-console sequence without converting Nia's own dispatch chronology into omniscient narration.",
    "authority_ref": "REQUIREMENTS-4-5-AND-6-16-AUTHOR-CALIBRATION-DIRECTIVE",
    "first_dependency": {
      "record_type": "ArcEntry",
      "record_id": "2"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-DECEMBER-RECEIVE"
      }
    ],
    "consistency_implications": [
      "Kev witnesses the 6:31 road-call and handover continuity only; he knows nothing about Mara's receiver or its latency.",
      "He creates no POV, VoiceBrief, pairing identity, or chapter load.",
      "His selected name licenses no inferred real-world cultural detail."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CHAR-DEV-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-013 identifies Dev, an incidental depot colleague who shows Nia Calder the freezing routing screen during the December shift; Dev is a non-viewpoint supporting character with no POV, surname, alias, or wider plot function selected.",
    "rationale": "The Chapter 2 routing-screen detail uses one stable incidental name rather than an untracked one-off colleague and remains subordinate to Nia's sequence-and-correction register.",
    "authority_ref": "REQUIREMENTS-4-5-AND-6-16-AUTHOR-CALIBRATION-DIRECTIVE",
    "first_dependency": {
      "record_type": "ArcEntry",
      "record_id": "2"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-DECEMBER-RECEIVE"
      }
    ],
    "consistency_implications": [
      "Dev remains incidental to the depot and routing-screen continuity and receives no expanded technical authority or later role by implication.",
      "Dev creates no POV, VoiceBrief, pairing identity, or chapter load.",
      "The selected name licenses no inferred gender, nationality, ethnicity, religion, language, geography, or other real-world cultural detail."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CHAR-HALLORAN-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-014 identifies Halloran, the test-floor recorder who transcribes Nia Calder's four conditions, receives her spoken time-bound consent, records her spoken phrase-loss report, and reads corrections back; Halloran is a non-viewpoint supporting character with no POV, given name, or alias selected.",
    "rationale": "The bounded cancellation scene needs one stable procedural witness while preserving that Nia, not the recorder or institution, originates the consent ethics and controls every correction.",
    "authority_ref": "REQUIREMENTS-4-5-AND-6-16-AUTHOR-CALIBRATION-DIRECTIVE",
    "first_dependency": {
      "record_type": "ArcEntry",
      "record_id": "73"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-MINDWARS-COUNTERPHASE"
      },
      {
        "record_type": "MotifEvent",
        "record_id": "MOT-YES-01"
      }
    ],
    "consistency_implications": [
      "Nia originates the four conditions, the badge-versus-person correction, and the ethical distinction; Halloran transcribes and receives consent but does not invent the doctrine.",
      "Her yes is spoken aloud to Halloran in the room and never supplied over PAIR.",
      "Halloran creates no POV, VoiceBrief, pairing identity, chapter load, or implied real-world cultural detail."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  }
]
```

Ten supporting participants hold Character IDs and no viewpoint in this fence, and `DEC-018` adds two more in [`DEC-018` supporting canon](#dec-018-supporting-canon) for a current total of twelve. Under the [Character ID registry](record-schemas.md#character-id-registry) an approved `character-name` extension declares a Character ID whether or not a `POVProfile` exists for it, so `CHAR-005` through `CHAR-016` resolve in `TimelineEntry.participants`, `PairState.participants`, and other Character ID references while creating no POV, no Voice Brief obligation, and no change to the 56/32/33/7 loads. Six support operational pairing; Ravi Anand, Kev, Dev, and Halloran witness only the bounded continuity functions recorded above. None is a sender, adversary, archive, simulation, model, or group mind, and none may be narrated from inside.

### Names and entities quick reference

| Stable identity | Selected name / reference | Continuity state |
|---|---|---|
| `CHAR-001` / `POV-MARA` | Dr. Mara Venn | approved; Anchor POV; no alias selected |
| `CHAR-002` / `POV-NIA` | Nia Calder | approved; “case zero” is refused, not an alias |
| `CHAR-003` / `POV-JULIAN` | Julian Adebayo | approved; no alias selected |
| `CHAR-004` / `POV-SAFIYA` | Safiya Mir | approved; no alias selected; name licenses no heritage inference |
| `CHAR-005` | Ada Ferris | approved; non-viewpoint; community interpreter without expressive speech; paired with `CHAR-006` |
| `CHAR-006` | Lena Ferris | approved; non-viewpoint; Ada's adult daughter and calibrated partner |
| `CHAR-007` | Tomas Reyner | approved; non-viewpoint; county dispatcher; paired with `CHAR-008`, separately with `CHAR-002` |
| `CHAR-008` | Cora Baird | approved; non-viewpoint; county dispatcher; paired with `CHAR-007` |
| `CHAR-009` | Idris Vane | approved; non-viewpoint; network operator; paired with `CHAR-001`, separately with `CHAR-010` |
| `CHAR-010` | Rhea Osei | approved; non-viewpoint; network operator; paired with `CHAR-001`, separately with `CHAR-009` |
| `CHAR-011` | Ravi Anand | approved; non-viewpoint; independent December timing/control witness and copper-room technician; surname added by `DEC-018`; no alias selected |
| `CHAR-012` | Kev | approved; non-viewpoint; 6:31 road-call and handover continuity witness; no surname selected |
| `CHAR-013` | Dev | approved; non-viewpoint; incidental depot/routing-screen colleague; no surname selected |
| `CHAR-014` | Halloran | approved; non-viewpoint; transcribes Nia's conditions and receives spoken consent; no given name selected |
| `CHAR-015` | Joss Calder | approved; non-viewpoint; Nia's older brother; `DEC-018` clause 9 warmth; no professional role |
| `CHAR-016` | Ruth Venn | approved; non-viewpoint; Mara's aunt; `DEC-018` clause 9 warmth; no institutional role |
| technical institution | Northline Array | exact approved name |
| commercial institution | Open Channel Consortium | exact approved name |
| custodial institution | Civic Record Trust | exact approved name |
| system term | Electronic Speech Pairings (`ESP`); singular `pairing` | approved late misnomer, post-Discovery only |
| country and counties | deliberately unnamed | selected state, not a blank |
| Safiya heritage base | `unspecified_by_author` | exact protected state everywhere |

No absolute calendar year, fictional country name, county proper name, or real heritage language is selected here. The twelve supporting names carry no nation, county, ethnicity, religion, politics, language, or other inferred real-world cultural detail: like `Safiya Mir`, each is a plain selected name and licenses no such inference under `DEC-003` and `DEC-005`. The four POV rows are the complete viewpoint roster; the twelve `CHAR-005` through `CHAR-016` rows are non-viewpoint participants, continuity witnesses, or `DEC-018` warmth relationships and hold no `POV-` identity at all.

## Neural communication mechanism

`DEC-012`, completed and amended by `DEC-015`, is mechanism authority rather than Canon Lyric. It is recorded here as one coherent Novel Extension family: the contested institutional term, the four non-overlapping modes, the `CANCEL` properties, pair calibration, the evidence boundary, and the Safiya limit. Every mechanism-bearing chronology record in the Timeline declares exactly one `mode`.

`ESP` expands in-world to **Electronic Speech Pairings** and one authorized link is a **pairing**. The term is a contested late institutional simplification coined no earlier than Private Defense, never supernatural extrasensory perception. It names deliberate paired conversation only; using it for observation, unconsented influence, or cancellation is the error the novel dramatizes rather than a fact it endorses.

### The four modes

| Mode | Direction of effect | Addressing | Consent and calibration | Bound |
|---|---|---|---|---|
| `RECEIVE` | passive observation of structure already present in one living person's field | person-specific address identified or locked | none required; nothing is written | no write stage and no transmit stage |
| `INTRUDE` | active write | person-specific address required | absent or uncalibrated | nonsemantic salience, valence, urgency, certainty, preference, or wanting only |
| `CANCEL` | active subtraction | **no** person-specific address | one deliberately exposed consenting individual in a bounded local field volume, or institutional authorization at area scale | removal or degradation of access only; inserts nothing |
| `PAIR` | deliberate two-way transport of offered internal speech | pair-specific address between exactly two living people | current, specific, revocable mutual consent plus `Pair_Calibration` unique to that pair | only what a deliberate send act offers |

`INTRUDE` requires an address and `CANCEL` forbids one. That is the structural boundary between them, and it is why the null — an unaddressed transmission whose canonical effect is subtraction — can never be recorded as `INTRUDE`. `INTRUDE`'s nonsemantic limit structurally forbids what the null does: losing access to a private maternal layer is not a preference.

### The eight binding `CANCEL` properties

The null cannot be classified without all eight. They are recorded machine-readably on `EXT-MODE-CANCEL`, `EXT-CANCEL-CONSENT-SCALE`, and `EXT-CANCEL-NO-INVERSE`.

| # | Property | Consequence in the novel |
|---:|---|---|
| 1 | unaddressed, propagating across whatever field volume the emitter reaches | not `INTRUDE`; nobody is targeted and nobody is spared by being untargeted |
| 2 | nonsemantic in both directions | carries no language, proposition, order, voice, or memory, and reads nothing back |
| 3 | subtractive, never insertive | removal or degradation of access to mental content and faculties; inserts nothing |
| 4 | unpredictable before, unenumerable during, incompletely mapped after | Mara's model predicts that subtraction may occur and cannot identify whose |
| 5 | no additive inverse | nothing removed is restorable by another `CANCEL`, by `PAIR`, or by any combination of modes |
| 6 | consent cannot scale | bounded local cancellation can be individually consented; area scale is institutionally authorized and never individual consent from every affected person |
| 7 | confined to `Mindwars_Part` | the Coda's retained capacity is switched off rather than used |
| 8 | supplies no provenance | silencing the Foreign Signal identifies nothing about it |

The bounded Chapter 73 test and null night are **the same mode at two scopes**, not two mechanisms. Property 5 is a second, independent physical reason Chapter 124's refusal is truthful, alongside the missing source corpus. Property 3 is what keeps Nia's insertion injury and Safiya's defensive subtraction categorically distinct: they rhyme and are never equated.

### Evidence boundary

The evidence boundary is recorded independently of any narrative inference. Consent-state and transport metadata are mandatory and semantically opaque; `Content_Recording` is a separate explicit mutual choice initialized off; and a `Pairing_Transcript` contains only protocol-carried content from that one recorded session. Metadata establishes that an authorized transport existed and how it behaved and can never reconstruct unrecorded semantics. No transcript proves truth, intent, memory provenance, unoffered thought, a complete mental state, Nia's earlier causation, or the Foreign Signal's provenance. Endpoint compromise may be selected only as a bounded institutional danger, never as hidden provenance closure.

```json record=NovelExtension schema=1
[
  {
    "extension_id": "EXT-MODE-TAXONOMY",
    "extension_kind": "mechanism",
    "fact": "Every neural communication event occupies exactly one of four non-overlapping modes: RECEIVE, INTRUDE, CANCEL, and PAIR. The modes share an addressable field but do not share addressing, permission, bandwidth, direction of effect, or evidentiary meaning.",
    "rationale": "DEC-015 requires one authoritative classification per event so that observation, unconsented influence, defensive subtraction, and consented conversation cannot be collapsed into a single capability by an institutional label or by prose commentary.",
    "authority_ref": "DEC-015",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DECEMBER-RECEIVE"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-DISCOVERY-HANDSHAKE"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PRIVATE-PROTOCOL"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-MINDWARS-COUNTERPHASE"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-NULL-NIGHT"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-ESP-PAIRINGS"
      }
    ],
    "consistency_implications": [
      "No record may classify one event under two modes or leave a neural communication event unclassified.",
      "INTRUDE requires a person-specific address and CANCEL forbids one; that boundary is why an unaddressed subtractive event is never INTRUDE.",
      "Observation resolution, write bandwidth, and semantic authorization are independent capabilities, so a rich RECEIVE stream implies no rich unconsented write.",
      "Mode is declared in TimelineEntry.technical_state and is never inferred from apparatus_mode, a nearby heading, or prose commentary.",
      "The taxonomy authorizes no new capability; it names distinctions the canon already carried, including the subtraction the null always performed."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-MODE-RECEIVE",
    "extension_kind": "mechanism",
    "fact": "RECEIVE passively observes high-dimensional structure already present in one living person's experiential and attentional field, with no write stage and no transmit stage.",
    "rationale": "DEC-015 Mode A fixes the December apparatus as observation only, which keeps the discovery innocent of transmission while still identifying a person-specific address.",
    "authority_ref": "DEC-015",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DECEMBER-RECEIVE"
    },
    "affected_records": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-DECEMBER-RECEIVE-ONLY"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-OFFSET-NO-GAP"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-DISCOVERY-DUE-DILIGENCE"
      }
    ],
    "consistency_implications": [
      "The December event is RECEIVE: continuous source side, an eight-second offset at Mara's receiver only, receive-only apparatus, and a locked person-specific address.",
      "Nia authors no speech to Mara and experiences no gap, so the eight seconds are never stored as a source-side discontinuity.",
      "Observation injects nothing, so no RECEIVE record may be cited as evidence of transmission, influence, or later causation.",
      "Page-nine transmit enable is a separate architectural fact and never converts a RECEIVE entry into a transmit event."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-MODE-INTRUDE",
    "extension_kind": "mechanism",
    "fact": "INTRUDE is an active write to a person-specific address without current specific revocable mutual consent or matching Pair_Calibration, and its channel is deliberately low-dimensional.",
    "rationale": "DEC-015 Mode B keeps unconsented influence real and frightening while preventing it from carrying language, which is what makes the wanting a wanting rather than an order.",
    "authority_ref": "DEC-015",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-DISCOVERY-HANDSHAKE"
    },
    "affected_records": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-FIRST-CASUALTY-ARRIVAL"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-WANTING"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-DISCOVERY-DOOR-INWARD"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-MINDWARS-ONSET"
      }
    ],
    "consistency_implications": [
      "The represented effect is limited to nonsemantic salience, valence, urgency, certainty, preference, or wanting.",
      "It cannot carry language, propositions, commands, a voice, arbitrary memories, or a semantically readable signature.",
      "Mara's later content-free bench handshake and Nia's wanting are separate post-December events in apparatus, time, and mode, and their causal relationship remains unverified.",
      "A cooperative but uncalibrated test write is still INTRUDE, because PAIR additionally requires pair-specific calibration.",
      "INTRUDE structurally forbids what the null does, so no unaddressed subtractive event may be recorded under this mode."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-MODE-CANCEL",
    "extension_kind": "mechanism",
    "fact": "CANCEL is an unaddressed subtractive counterphase cancellation field; the bounded Chapter 73 test and null night are the same mode at two scopes rather than two mechanisms.",
    "rationale": "DEC-015 added CANCEL because the null is an active transmission with no person-specific address whose canonical effect is subtraction, which the earlier three insertive modes could not classify without contradicting INTRUDE's nonsemantic limit.",
    "authority_ref": "DEC-015",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-MINDWARS-COUNTERPHASE"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-MINDWARS-SHIELD"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-NULL-NIGHT"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-NULL-SILENCE-DIMINISHMENT"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-NULL-CIVILIAN-HARM"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-MATERNAL-LANGUAGE-LOSS"
      }
    ],
    "consistency_implications": [
      "Property 1 — unaddressed: a CANCEL event carries no person-specific address, which is the structural reason it is not INTRUDE, and it propagates across whatever field volume the emitter reaches.",
      "Property 2 — nonsemantic in both directions: it carries no language, proposition, order, voice, or memory, and it reads nothing back.",
      "Property 3 — subtractive, not insertive: its only effect is the removal or degradation of access to mental content and faculties, and it inserts nothing.",
      "Property 4 — unpredictable and untargetable: the affected faculties, memories, and people are unpredictable before the event, unenumerable during it, and incompletely mapped after it.",
      "Property 5 — no additive inverse: nothing it removed can be restored by another CANCEL, by PAIR, or by any combination of modes.",
      "Property 6 — consent cannot scale: individual current specific revocable consent is obtainable only for a bounded local cancellation, while area scale is institutionally authorized and never individual consent from every affected person.",
      "Property 7 — confined to Mindwars_Part: CANCEL begins and ends inside Mindwars, preserving the settled armistice facts and the noncombat Coda, where retained capacity is switched off rather than used.",
      "Property 8 — supplies no provenance: cancelling the Foreign Signal identifies nothing about it, so both origin accounts of Nia's wanting and the Provenance Question remain unverified.",
      "Nia's insertion injury and Safiya's defensive subtraction remain categorically distinct; they may rhyme but are never equated or merged.",
      "Every CANCEL chronology record carries a populated cancel_state with inserted_content none, all three affected-set booleans false, additive_inverse_exists false, and provenance_yield none."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CANCEL-CONSENT-SCALE",
    "extension_kind": "mechanism",
    "fact": "A bounded cancellation is authorized by one individual's current, specific, revocable consent, while area-scale cancellation is authorized institutionally; no consent record and no pair transcript speaks for the affected area.",
    "rationale": "DEC-015 CANCEL property 6 makes the consent gap structural rather than accidental, which is what gives Nia's authorization challenge and the later null their shared ethical spine.",
    "authority_ref": "DEC-015",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-MINDWARS-COUNTERPHASE"
    },
    "affected_records": [
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-MINDWARS-SHIELD"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-NULL-NIGHT"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CONSENT-SOVEREIGNTY"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-NULL-CIVILIAN-HARM"
      }
    ],
    "consistency_implications": [
      "A bounded-local cancel_state describes a field volume containing one deliberately exposed consenting individual, records that person's consent, and records a null institutional authorization; an area-scale cancel_state records institutional authorization and a null individual consent.",
      "Manufactured unanimity is refused: area-scale authorization is never represented as consent collected from every affected person.",
      "The bounded test and the area-scale null are one operation at two scopes, so the consent difference is a property of scale rather than of mechanism.",
      "Under DEC-017 the parallel between the bounded consented test and the unconsentable area-scale null stays unstated through Chapters 62 to 123 and is named exactly once, by Mara, inside her Chapter 128 entry against herself.",
      "That single naming creates no reveal, resolves no provenance, absolves nobody, validates no archive, and does not reinterpret Safiya's consent."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CANCEL-NO-INVERSE",
    "extension_kind": "mechanism",
    "fact": "A Subtraction_Effect has no additive inverse and is unrecoverable by a further CANCEL, by PAIR, by Content_Recording, by consent or transport metadata, or by simulation, archive, model, or reconstruction.",
    "rationale": "DEC-015 CANCEL property 5 closes the last escape route from Chapter 124 and gives the refusal a second physical basis that does not depend on Mara's honesty.",
    "authority_ref": "DEC-015",
    "first_dependency": {
      "record_type": "CanonFact",
      "record_id": "CF-CODA-TRUTH-BASED-REFUSAL"
    },
    "affected_records": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-MATERNAL-LANGUAGE-LOSS"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-NULL-NIGHT"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-CODA-REFUSAL"
      }
    ],
    "consistency_implications": [
      "Chapter 124's refusal is truthful for two independent physical reasons: Mara possesses no source corpus, and the mechanism has no reverse operation.",
      "No record may describe a cancellation as reversed, partially undone, or restorable by another mode.",
      "Safiya's consent remains valid; consent cannot manufacture an absent source or an absent inverse.",
      "Retained Coda capacity therefore adds no restoration option and is switched off rather than used."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-MODE-PAIR",
    "extension_kind": "mechanism",
    "fact": "PAIR transports deliberately offered near-natural internal speech between exactly two living people who hold current, specific, revocable mutual consent and completed Pair_Calibration unique to that pair.",
    "rationale": "DEC-015 Mode D replaces the retired fixed-token ceiling so consented conversation can become a genuine middle-book capability while every crossing remains an offered act.",
    "authority_ref": "DEC-015",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-PRIVATE-PROTOCOL"
    },
    "affected_records": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-ESP-PAIRINGS"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-PRIVATE-OFFER"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CONSENT-SOVEREIGNTY"
      }
    ],
    "consistency_implications": [
      "Every transported contribution requires a deliberate send act; unoffered thought, imagery, emotion, memory, and background mentation remain private.",
      "Repeated calibration may reach operational fluency rather than remaining a small codebook, and fluency creates no new POV requirement.",
      "A pause or revocation stops semantic transport immediately; the channel never guesses, completes, or buffers an unoffered meaning.",
      "Clipping, latency, or integrity failure surfaces as a transport failure handled by confirmation, retry, or ordinary-speech fallback rather than silently repaired into presumed content.",
      "Fluent pairing produces no group mind, hive mind, mass mind reading, arbitrary memory access, or provenance closure."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-PAIR-CALIBRATION",
    "extension_kind": "mechanism",
    "fact": "Pair_Calibration is mutual, pair-specific, and nontransferable.",
    "rationale": "DEC-015 makes calibration the technical form of two-person consent, so a channel cannot be inherited, installed, or pointed at someone who cannot answer.",
    "authority_ref": "DEC-015",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-PRIVATE-PROTOCOL"
    },
    "affected_records": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-PAIR"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-MINDWARS-SHIELD"
      }
    ],
    "consistency_implications": [
      "Calibration cannot be installed from another pair, reused with a replacement partner, or applied to a dead or absent person, a simulation, an archive, a model, or a reconstruction.",
      "A PAIR record's calibration participants always equal its two living participants.",
      "Exact fluent pair identities and session ownership beyond the first sustained conversation remain deferred to Arc Outline work, which may not add a POV, create a sender, operative, adversary, archive, simulation, or group-mind viewpoint, or change the provisional 56/32/33/7 loads."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-PAIRING-EVIDENCE",
    "extension_kind": "mechanism",
    "fact": "Each authorized Pairing_Session preserves semantically opaque Consent_State_Metadata and Transport_Metadata; Content_Recording is a separate explicit mutual choice initialized off; and a Pairing_Transcript contains only content the protocol carried during that recorded session.",
    "rationale": "DEC-015 fixes an evidence boundary independently of narrative inference so that a real evidentiary record can exist without becoming a route to semantics, truth, or provenance.",
    "authority_ref": "DEC-015",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-PRIVATE-PROTOCOL"
    },
    "affected_records": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-PAIR"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-ARCHIVE-CONTESTED"
      },
      {
        "record_type": "Reveal",
        "record_id": "REVEAL-HANDSHAKE-WANTING-ORIGIN"
      },
      {
        "record_type": "Reveal",
        "record_id": "REVEAL-FOREIGN-SIGNAL-PROVENANCE"
      }
    ],
    "consistency_implications": [
      "Metadata can establish that an authorized transport existed and how it behaved and can never reconstruct unrecorded semantics.",
      "Content recording is enabled only when both participants consent to recording separately from consenting to pair, and any transcript is scoped to that one recorded session.",
      "No transcript proves truth, intent, memory provenance, unoffered thought, a complete mental state, Nia's earlier causation, or the Foreign Signal's provenance.",
      "Endpoint compromise or unauthorized content logging may be selected only as a bounded institutional danger, never as hidden provenance closure.",
      "Traffic analysis in the operational Mindwars range discovers consent-state and transport metadata patterns only.",
      "Civic Record Trust custody continues to warrant provenance of a record rather than truth within it."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-SAFIYA-PAIRING-BOUNDARY",
    "extension_kind": "mechanism",
    "fact": "No pairing can restore Safiya's corpus-less private maternal layer.",
    "rationale": "DEC-015 keeps fluent pairing from weakening Chapter 124: the mode requires two living consenting minds and voluntary sends, and none of those conditions can be met for a dead participant and an unrecorded two-person layer.",
    "authority_ref": "DEC-015",
    "first_dependency": {
      "record_type": "TimelineEntry",
      "record_id": "TL-CODA-CONSENT"
    },
    "affected_records": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-MATERNAL-LANGUAGE-LOSS"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-TRUTH-BASED-REFUSAL"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-SAFIYA-HERITAGE"
      }
    ],
    "consistency_implications": [
      "Safiya's mother is dead, a living second participant is absent, and Safiya cannot deliberately send what the null removed.",
      "Pairing with an archive, simulation, model, generated proxy, or reconstruction is invalid by mechanism rather than by policy.",
      "Content recording, consent-state metadata, transport metadata, and transcripts hold nothing of the private two-person layer, because none of it was recorded and no corpus survives anywhere.",
      "Any fabricated replacement would be Mara's construction and could falsely self-authenticate as Safiya's own memory."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  }
]
```

## Timeline

Chronology uses global provisional chapter windows from the approved design but creates no Arc Entries. `cross_cut_ids` remain empty until the Arc Outline defines reciprocal Cross Cut records. Where a source account is involved, chronology distinguishes event time, composition time, later deposit time, and conditioned release time.

Mechanism-bearing entries declare exactly one `mode`. `mode: not-applicable` means the entry records no neural communication event, which is the correct state for the April specification reading, the null decision sequence, and the Coda refusal where the retained relay is switched off. A narrative range whose mechanism events are not yet fixed keeps `technical_state: null` and says so in `uncertainty_notes`; that absence is not a claim that nothing happens in those chapters. Individual Pairing_Sessions are **placed in chapters** by the Arc Outline under `DEC-015` and **classified here**, each in its own `mode: PAIR` entry overlapping the scene window it belongs to; see [PAIR-mode session chronology](#pair-mode-session-chronology). Mode-specific facts to preserve:

- the December source-side interval is **continuous** and the apparatus is **receive-only** with no transmit stage; under the early apparatus configuration, requested fidelity, context, information load, noise, and confidence requirements used in Chapters 1–5, the continuously acquired and timestamped raw field reproducibly takes eight seconds to become legible resolved output. Reprocessing the same sample with the same settings reproduces eight seconds, while inadequate context or processing degrades or destroys coherence. The number belongs only to Mara's configured receiver and is neither a permanent physical constant nor necessarily irreducible;
- a **distinct later entry** carries the temporary bench transmit path and the content-free handshake through that same address;
- page-nine `transmit enable` is recorded as evidence of broader architectural capability and never as evidence that the December rig transmitted;
- the bounded counterphase test and null night both carry `mode: CANCEL`, differing only in `cancel_state.scope`;
- every Pairing_Session carries `mode: PAIR` with exactly two living participants, a pair-unique nontransferable `calibration_id`, and its own evidence boundary; a paired channel that coordinates a cancellation never absorbs the cancellation's mode, and the two events stay separate records;
- null extent is stored as the canonical text `three counties wide`, never as a derived radial measure and never as a list of named counties;
- compressed-clock threading is limited to chronology-supported clusters such as null night. The manuscript is not placed inside one global twenty-four-hour frame.

```json record=TimelineEntry schema=1
[
  {
    "timeline_id": "TL-DECEMBER-RECEIVE",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "In December, before the Civic Record Trust exists, Mara receives Nia's continuous ordinary morning through a receive-only apparatus at Northline Array.",
    "exact_time": "ten to seven at Nia's console, as reported by Nia; no absolute date",
    "duration": "twenty minutes in Nia's attributed account",
    "location": "Northline Array and Nia's unnamed county",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-011",
      "CHAR-012",
      "CHAR-013"
    ],
    "chapter_numbers": [
      1,
      2,
      3,
      4,
      5
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-DECEMBER-MARA-MORNING"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-DECEMBER-RECEIVE-ONLY"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-DECEMBER-DETAILS"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-OFFSET-NO-GAP"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-NIA-SOURCE-CASUALTY"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-NIA-PERSON-ADDRESS"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-INSTITUTION-NORTHLINE"
      }
    ],
    "uncertainty_notes": [
      "Nia experiences no gap or delay; the eight seconds are solely Mara's acquisition-to-resolved-output reconstruction latency under the tested early configuration.",
      "Reprocessing the same raw sample with the same settings reproduces eight seconds, while insufficient context or processing degrades or destroys coherence; later hardware, algorithms, information volume, complexity, fidelity, noise, confidence requirements, and other conditions may produce different latency.",
      "This interval contains no transmit stage, no handshake, and no evidence about the later wanting's origin."
    ],
    "record_chronology": {
      "composition_timeline_id": "TL-RECORD-PRETRUST-COMPOSITION",
      "deposit_timeline_id": "TL-RECORD-PRETRUST-DEPOSIT",
      "release_timeline_ids": [
        "TL-TRUST-CONDITIONED-RELEASES"
      ]
    },
    "technical_state": {
      "mode": "RECEIVE",
      "source_side_continuity": "continuous",
      "receiver_offset_seconds": 8,
      "apparatus_mode": "receive-only",
      "transmit_stage_present": false,
      "person_specific_address_state": "locked",
      "cancel_state": null,
      "pair_state": null,
      "pairing_evidence": null,
      "evidence_scope": "The apparatus continuously acquires and timestamps the raw field, locks a person-specific address, and under the tested early context, fidelity, information load, noise, confidence requirements, hardware, and algorithms reconstructs legible experience eight seconds later. Same-sample/same-setting reprocessing reproduces eight seconds; inadequate context or processing degrades coherence. The apparatus does not transmit, create a source-side discontinuity, establish a universal latency constant, or prove later causation."
    },
    "cross_cut_ids": [
      "CUT-NOISE-FLOOR-HANDOFF",
      "CUT-RECONSTRUCTION-LATENCY"
    ]
  },
  {
    "timeline_id": "TL-DISCOVERY-DUE-DILIGENCE",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "After the initial December reception and before any bench transmission, Mara repeats and verifies reception while Julian audits the receiver and institutional interest forms.",
    "exact_time": null,
    "duration": null,
    "location": "Northline Array",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003"
    ],
    "chapter_numbers": [
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-DISCOVERY-FIELD-CHANNEL"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-DECEMBER-RECEIVE-ONLY"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-PROFESSION-JULIAN"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-INSTITUTION-OPEN-CHANNEL"
      }
    ],
    "uncertainty_notes": [
      "Source identity is under verification, and no later causal claim is settled."
    ],
    "record_chronology": {
      "composition_timeline_id": "TL-RECORD-PRETRUST-COMPOSITION",
      "deposit_timeline_id": "TL-RECORD-PRETRUST-DEPOSIT",
      "release_timeline_ids": [
        "TL-TRUST-CONDITIONED-RELEASES"
      ]
    },
    "technical_state": {
      "mode": "RECEIVE",
      "source_side_continuity": "continuous",
      "receiver_offset_seconds": 8,
      "apparatus_mode": "receive-only",
      "transmit_stage_present": false,
      "person_specific_address_state": "locked",
      "cancel_state": null,
      "pair_state": null,
      "pairing_evidence": null,
      "evidence_scope": "Repeated reception supports a person-specific channel while preserving receive-only hardware and no source-side gap."
    },
    "cross_cut_ids": [
      "CUT-ATTENTION-AND-THE-CALL",
      "CUT-ORDINARY-DETAIL-MATCH",
      "CUT-PERSON-SPECIFIC-RIGHTS"
    ]
  },
  {
    "timeline_id": "TL-DISCOVERY-HANDSHAKE",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "Later in Discovery, Mara deliberately adds a temporary bench transmit path and sends a content-free handshake through Nia's previously identified address while Nia makes a triage decision under an arriving wanting.",
    "exact_time": null,
    "duration": null,
    "location": "Northline Array and Nia's unnamed county dispatch center",
    "participants": [
      "CHAR-001",
      "CHAR-002"
    ],
    "chapter_numbers": [
      16,
      17,
      18,
      19,
      20
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-LATER-BENCH-HANDSHAKE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-WANTING"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-TRIAGE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-NIA-OPERATIONAL-SYNTHESIS"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-NIA-PERSON-ADDRESS"
      }
    ],
    "uncertainty_notes": [
      "Chronology and address identity make a causal link plausible but never prove or disprove it.",
      "The handshake carries no words, order, or triage instruction."
    ],
    "record_chronology": {
      "composition_timeline_id": "TL-RECORD-PRETRUST-COMPOSITION",
      "deposit_timeline_id": "TL-RECORD-PRETRUST-DEPOSIT",
      "release_timeline_ids": [
        "TL-TRUST-CONDITIONED-RELEASES"
      ]
    },
    "technical_state": {
      "mode": "INTRUDE",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bench-transmit",
      "transmit_stage_present": true,
      "person_specific_address_state": "reused",
      "cancel_state": null,
      "pair_state": null,
      "pairing_evidence": null,
      "evidence_scope": "The later temporary path sends a content-free handshake through the known address without consent or pair calibration, so it is INTRUDE and is limited to nonsemantic effect; this technical fact does not identify the origin of Nia's wanting."
    },
    "cross_cut_ids": [
      "CUT-HANDSHAKE-AND-TRIAGE",
      "CUT-UNANSWERED-SILENCE"
    ]
  },
  {
    "timeline_id": "TL-DISCOVERY-NIA-AFTERMATH",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "In the hours and days after the triage decision, Nia reconstructs her wanting, Mara reaches her and attempts confession, and the shared December-source and later-casualty identity becomes known without resolving causation.",
    "exact_time": null,
    "duration": null,
    "location": "Nia's unnamed county and Northline Array",
    "participants": [
      "CHAR-001",
      "CHAR-002"
    ],
    "chapter_numbers": [
      21,
      22,
      23,
      24,
      25
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-FIRST-CASUALTY-ARRIVAL"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-WANTING"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-NIA-BELIEF-DISTRIBUTION"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-NIA-SOURCE-CASUALTY"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-REL-MARA-NIA"
      }
    ],
    "uncertainty_notes": [
      "Nia refuses both unsupported origin accounts.",
      "Mara's attempted confession remains non-authoritative and risks appropriating Nia's injury."
    ],
    "record_chronology": {
      "composition_timeline_id": "TL-RECORD-PRETRUST-COMPOSITION",
      "deposit_timeline_id": "TL-RECORD-PRETRUST-DEPOSIT",
      "release_timeline_ids": [
        "TL-TRUST-CONDITIONED-RELEASES"
      ]
    },
    "technical_state": null,
    "cross_cut_ids": [
      "CUT-CONFESSION-REFUSED",
      "CUT-SOURCE-AND-CASUALTY-JOINED"
    ]
  },
  {
    "timeline_id": "TL-DISCOVERY-DOOR-INWARD",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "At the end of Discovery, Mara confirms addressability and broader write implications while external interest gathers around a problem already outside the lab.",
    "exact_time": null,
    "duration": null,
    "location": "Northline Array",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003"
    ],
    "chapter_numbers": [
      26,
      27,
      28,
      29
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-DISCOVERY-FIELD-CHANNEL"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-LATER-BENCH-HANDSHAKE"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-INSTITUTION-OPEN-CHANNEL"
      }
    ],
    "uncertainty_notes": [
      "Addressability does not establish who or what originated Nia's wanting."
    ],
    "record_chronology": {
      "composition_timeline_id": "TL-RECORD-PRETRUST-COMPOSITION",
      "deposit_timeline_id": "TL-RECORD-PRETRUST-DEPOSIT",
      "release_timeline_ids": [
        "TL-TRUST-CONDITIONED-RELEASES"
      ]
    },
    "technical_state": {
      "mode": "INTRUDE",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bench-transmit",
      "transmit_stage_present": true,
      "person_specific_address_state": "reused",
      "cancel_state": null,
      "pair_state": null,
      "pairing_evidence": null,
      "evidence_scope": "The temporary path demonstrates addressability under a controlled but uncalibrated write, which is INTRUDE rather than PAIR; the later April architecture is still a distinct documentary discovery."
    },
    "cross_cut_ids": [
      "CUT-ADDRESSABLE-AND-TESTED",
      "CUT-CONTAINMENT-ALREADY-LOST"
    ]
  },
  {
    "timeline_id": "TL-PRIVATE-COPPER",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "Mara designs and tests a copper room as a private boundary; Nia experiences both relief and the proof that ordinary space is permeable; the technician who built and probed it with Mara is entered on her exposed-persons list over his objection, reports one experience he will not characterize, and asks to leave the project.",
    "exact_time": null,
    "duration": null,
    "location": "Northline Array copper room",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003",
      "CHAR-011"
    ],
    "chapter_numbers": [
      30,
      31,
      32,
      33,
      34,
      35
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-PRIVATE-COPPER-BOUNDARY"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CONSENT-SOVEREIGNTY"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-PRIVATE-EXPOSED-PERSONS-LIST"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-PRIVATE-TECHNICIAN-REPORT"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-PRIVATE-TECHNICIAN-REASSIGNMENT"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-PRIVATE-CONSORTIUM-ADVANCE-PARTY"
      }
    ],
    "uncertainty_notes": [
      "A private shield buys quiet but cannot restore public life or settle provenance.",
      "The technician's single report is unverified, records nothing on Northline instrumentation, and is not classified as an arrival by him or by anyone else; it is not the first reported pattern of arrivals in strangers, which remains Chapter 62."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": [
      "CUT-ARRIVAL-AND-THE-ROOM",
      "CUT-CONSENT-AS-DEFAULT",
      "CUT-SEALED-ROOM-AND-A-LIFE"
    ]
  },
  {
    "timeline_id": "TL-PRIVATE-OFFER",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "Through winter and early spring, Open Channel Consortium develops a benevolent commercial offer while Nia challenges broad-form enrollment and Julian believes a consent boundary may be contractual.",
    "exact_time": null,
    "duration": "winter through early spring",
    "location": "Northline Array and consortium negotiation settings",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003"
    ],
    "chapter_numbers": [
      36,
      37,
      38,
      39,
      40,
      41,
      42
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-INSTITUTION-OPEN-CHANNEL"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-REL-MARA-JULIAN"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CONSENT-SOVEREIGNTY"
      }
    ],
    "uncertainty_notes": [
      "Promised benefits can be genuine without making default write access consensual.",
      "First volunteers begin pair-specific joint calibration in this range. The Arc Outline places the individual PAIR sessions in chapters under DEC-015 and each one carries its own PAIR chronology in this Timeline - TL-PAIR-CLINICAL-BENEFIT, TL-PAIR-DISPATCH-DEMONSTRATION, and TL-PAIR-MARA-NIA-CALIBRATION - so this range entry records no single mechanism event."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": [
      "CUT-CALIBRATION-AND-THE-UNCALIBRATED",
      "CUT-DEMONSTRATION-AND-THE-FORM"
    ]
  },
  {
    "timeline_id": "TL-APRIL-TERM-SHEET",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "In April, representatives arrive with a term sheet; Mara and Julian read the specification and identify page-nine transmit enable as architectural write capability.",
    "exact_time": "April; no more specific date selected",
    "duration": null,
    "location": "Northline Array negotiation setting",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003"
    ],
    "chapter_numbers": [
      43,
      44,
      45,
      46,
      47,
      48,
      49
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-APRIL-TERM-SHEET-PAGE-NINE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-PAGE-NINE-EVIDENCE-LIMIT"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-FARADAY-RECORD-DEMAND"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-INSTITUTION-OPEN-CHANNEL"
      }
    ],
    "uncertainty_notes": [
      "Page nine proves broader architecture, never December transmission or wanting origin."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "not-applicable",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "not-applicable",
      "cancel_state": null,
      "pair_state": null,
      "pairing_evidence": null,
      "evidence_scope": "No neural communication event occurs here. The specification exposes proposed write-capable architecture in April as a documentary fact; it cannot retroactively alter the receive-only December apparatus or supply a December transmit event."
    },
    "cross_cut_ids": [
      "CUT-ARCHITECTURE-NOT-OPTION",
      "CUT-CONSTRAINABLE-CLAUSE",
      "CUT-PROMISE-AND-THE-CASE"
    ]
  },
  {
    "timeline_id": "TL-APRIL-RECORD-ALTERATION",
    "chronology_kind": "point",
    "canon_status": "novel-extension",
    "relative_chronology": "After the April negotiation and Mara's record demand, Julian observes the meeting record softened or altered before he forms the Trust.",
    "exact_time": "after the April term-sheet negotiation and before Trust formation",
    "duration": null,
    "location": "Institutional record system",
    "participants": [
      "CHAR-003"
    ],
    "chapter_numbers": [
      50
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-APRIL-RECORD-ALTERATION"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-FARADAY-RECORD-DEMAND"
      }
    ],
    "uncertainty_notes": [
      "The alteration motivates independent custody but does not establish who caused Nia's wanting."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-TRUST-FORMATION",
    "chronology_kind": "point",
    "canon_status": "novel-extension",
    "relative_chronology": "Only after observing the altered April record, Julian establishes the Civic Record Trust with custodial governance and witness-controlled conditions.",
    "exact_time": "after TL-APRIL-RECORD-ALTERATION",
    "duration": null,
    "location": "Civic Record Trust",
    "participants": [
      "CHAR-003"
    ],
    "chapter_numbers": [
      51
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-INSTITUTION-CIVIC-RECORD"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-TRUST-GOVERNANCE"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-APRIL-RECORD-ALTERATION"
      }
    ],
    "uncertainty_notes": [
      "The Trust's custody can authenticate provenance but not objective truth."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-PRIVATE-RECORD-DEPOSITS",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "After Trust formation, Nia deposits her controlled account and dispatch logs; Julian records the adversary attribution as an institutionally enterable inference, and pre-Trust Discovery records are later transferred with original provenance.",
    "exact_time": "after Trust formation",
    "duration": null,
    "location": "Civic Record Trust",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003"
    ],
    "chapter_numbers": [
      52,
      53,
      54,
      55
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-LOGS"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-NIA-OPERATIONAL-SYNTHESIS"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-NIA-BELIEF-DISTRIBUTION"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-ARCHIVE-CONTESTED"
      }
    ],
    "uncertainty_notes": [
      "Logs clear routing causation but not mental authorship.",
      "The entered adversary account remains inference and cannot be corrected into certainty by custody."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": [
      "CUT-DEPOSIT-AND-THE-TIMESTAMPS"
    ]
  },
  {
    "timeline_id": "TL-PRIVATE-PROTOCOL",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "Mara and Nia formulate, test, break, and repair a challenge-response protocol in which entry follows specific, current, revocable consent and the handle remains inside.",
    "exact_time": null,
    "duration": null,
    "location": "Northline Array and protected testing spaces",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003"
    ],
    "chapter_numbers": [
      56,
      57,
      58,
      59,
      60,
      61
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-PRIVATE-COPPER-BOUNDARY"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CONSENT-SOVEREIGNTY"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-CONSENT-SCENE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-CONSENT-RULE"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-ESP-PAIRINGS"
      }
    ],
    "uncertainty_notes": [
      "The protocol is ethically valid but physically inadequate as a complete public defense.",
      "Electronic Speech Pairings may be coined no earlier than this movement and need not be coined until Mindwars.",
      "This entry fixes the first sustained fluent pairing as Mara and Nia because the approved design fixes it; every other pair identity and session owner remains deferred to Arc Outline work.",
      "One session in this range fails on a stale or overbroad consent state, stops without inventing semantic content, and is repaired by separating pairing, sending, and content-recording consent; the failure changes an action rather than producing a transcript."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "PAIR",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "identified",
      "cancel_state": null,
      "pair_state": {
        "participants": [
          "CHAR-001",
          "CHAR-002"
        ],
        "consent": {
          "current": true,
          "specific_act": "This pairing session between these two people now, with each transported contribution offered by a deliberate send act and either participant free to pause or revoke.",
          "revocable": true,
          "authorized_a": true,
          "authorized_b": true
        },
        "calibration_id": "PAIR-CAL-MARA-NIA",
        "calibration_participants": [
          "CHAR-001",
          "CHAR-002"
        ],
        "calibration_transferable": false,
        "deliberate_send_state": "required"
      },
      "pairing_evidence": {
        "consent_state_metadata_present": true,
        "transport_metadata_present": true,
        "metadata_semantically_opaque": true,
        "content_recording_enabled": false,
        "recording_consent_a": false,
        "recording_consent_b": false,
        "transcript": null
      },
      "evidence_scope": "The first sustained fluent pairing proves that two living calibrated people can deliberately exchange near-natural internal speech while unoffered thought stays private. Consent-state and transport metadata exist and are semantically opaque; content recording stays off, so no transcript exists and none of this speaks to Nia's earlier uncalibrated wanting."
    },
    "cross_cut_ids": [
      "CUT-ENCLOSURE-AND-THE-PUBLIC",
      "CUT-FAILURE-WITHOUT-CONTENT",
      "CUT-PROTOCOL-AND-THE-STALE-STATE"
    ]
  },
  {
    "timeline_id": "TL-MINDWARS-ONSET",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "Intrusive arrivals appear across unrelated people without border, demand, shared language, or confirmed sender; authorities classify mental autonomy as infrastructure while later history begins to call the conflict the Mindwars.",
    "exact_time": null,
    "duration": null,
    "location": "Multiple unnamed locations",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003"
    ],
    "chapter_numbers": [
      62,
      63,
      64,
      65,
      66,
      67,
      68,
      69
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-MINDWARS-TERM-UNDECLARED"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-FOREIGN-SIGNAL-PROVENANCE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-NIA-BELIEF-DISTRIBUTION"
      }
    ],
    "uncertainty_notes": [
      "No flag or theory becomes confirmed provenance.",
      "The stable historical term may be applied in retrospective records but is not yet common in scene.",
      "The arrivals are addressed writes with no identified sender; addressing is a property of the event, not evidence about who sent it."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "INTRUDE",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "identified",
      "cancel_state": null,
      "pair_state": null,
      "pairing_evidence": null,
      "evidence_scope": "Unconsented, uncalibrated writes reach person-specific addresses across unrelated people, so the events are INTRUDE and remain limited to nonsemantic salience, valence, urgency, certainty, preference, or wanting. No border, demand, language, or authenticated sender is established, and no intrusion identifies its own origin."
    },
    "cross_cut_ids": [
      "CUT-A-FLAG-AND-A-CATEGORY",
      "CUT-DEMONSTRATION-CASE-REFUSED",
      "CUT-HER-ACCOUNT-AND-THEIR-FILE",
      "CUT-NO-SIGNATURE-AND-THE-UNDECLARED-WAR"
    ]
  },
  {
    "timeline_id": "TL-MINDWARS-COUNTERPHASE",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "Mara proves a counterwave can cancel an incoming pattern, Nia forces the consent challenge, and a first consenting bounded-local field-volume test succeeds while leaving Nia unable to access a familiar phrase she could use before exposure.",
    "exact_time": null,
    "duration": null,
    "location": "Defender testing site",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003",
      "CHAR-014"
    ],
    "chapter_numbers": [
      70,
      71,
      72,
      73,
      74,
      75,
      76,
      77
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-COUNTERPHASE-DEFENSE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CONSENT-SOVEREIGNTY"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-CONSENT-SCENE"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-ESP-PAIRINGS"
      }
    ],
    "uncertainty_notes": [
      "A successful consenting test does not make counterphase noninvasive or authorize automatic scaling.",
      "At Chapter 73's contemporaneous horizon, Nia and the room know only the bounded run's conditions and consequence; they do not know whether the operation can be aimed, widened, or undone, and no future deployment is generalized from this scene."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "CANCEL",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "not-applicable",
      "cancel_state": {
        "scope": "bounded-local",
        "individual_consent": {
          "character_id": "CHAR-002",
          "current": true,
          "specific_act": "One counterphase cancellation within a bounded local field volume containing Nia as the deliberately exposed consenting individual, asked for at the time and revocable during it.",
          "revocable": true
        },
        "institutional_authorization": null,
        "subtraction": "Removal or degradation of access to mental content or faculties inside the bounded-local test volume, concretely Nia's loss of access to a familiar phrase she could use before exposure.",
        "inserted_content": "none",
        "affected_set_predictable_before": false,
        "affected_set_enumerable_during": false,
        "affected_set_fully_mapped_after": false,
        "additive_inverse_exists": false,
        "provenance_yield": "none"
      },
      "pair_state": null,
      "pairing_evidence": null,
      "evidence_scope": "This bounded event is classified as unaddressed subtractive CANCEL rather than INTRUDE and supplies no provenance. The contemporaneous Chapter 73 account establishes one four-metre run, Nia's current spoken consent, nineteen seconds of exposure, cancellation of the incoming pattern, and her reported phrase-access loss; it does not establish whether the operation can be aimed, widened, undone, or generalized to any future deployment. Separate PAIR records TL-PAIR-MARA-NIA-COUNTERPHASE and TL-PAIR-MARA-NIA-FLUENCY-LIMIT govern only coordination."
    },
    "cross_cut_ids": [
      "CUT-COLLECTIVE-COPPER-AND-THE-COUNTERWAVE",
      "CUT-ENTRY-ON-A-CURRENT-ANSWER",
      "CUT-HER-CONDITIONS-AND-HIS-INSTRUMENT",
      "CUT-PROTOCOL-ON-PAPER-AND-IN-USE",
      "CUT-TRANSMITTED-DEFENSE-AND-THE-QUESTION"
    ]
  },
  {
    "timeline_id": "TL-MINDWARS-SHIELD",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "Officials seek automatic protection, Nia chooses bounded risk rather than being volunteered, and the first protective network is argued over, built, and used.",
    "exact_time": null,
    "duration": null,
    "location": "Defender network and unnamed protected communities",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003"
    ],
    "chapter_numbers": [
      78,
      79,
      80,
      81,
      82,
      83,
      84,
      85
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-COUNTERPHASE-DEFENSE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CONSENT-SOVEREIGNTY"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-ESP-PAIRINGS"
      }
    ],
    "uncertainty_notes": [
      "Optional paired-operative supporting material, if later selected, adds no POV and no provenance closure."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "CANCEL",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "not-applicable",
      "cancel_state": {
        "scope": "bounded-local",
        "individual_consent": {
          "character_id": "CHAR-002",
          "current": true,
          "specific_act": "One bounded-local counterphase field volume containing Nia as the deliberately exposed consenting individual, distinguishing chosen risk from imposed protection, and revocable while it runs.",
          "revocable": true
        },
        "institutional_authorization": null,
        "subtraction": "Removal or degradation of access to some mental content and faculties within the bounded session volume.",
        "inserted_content": "none",
        "affected_set_predictable_before": false,
        "affected_set_enumerable_during": false,
        "affected_set_fully_mapped_after": false,
        "additive_inverse_exists": false,
        "provenance_yield": "none"
      },
      "pair_state": null,
      "pairing_evidence": null,
      "evidence_scope": "Protective cancellation is a defender use of the same unaddressed subtractive medium. Its bounded-local field volume contains one deliberately exposed person and requires that person's current specific revocable consent; automatic protective transmission sought by officials would exceed that consent. The operational pairing sessions in this range carry their own PAIR chronology in this Timeline as TL-PAIR-OPERATOR-SHIFT-VANE, TL-PAIR-OPERATOR-TRAFFIC, and TL-PAIR-OPERATOR-SHIFT-OSEI, and expose transport metadata only."
    },
    "cross_cut_ids": [
      "CUT-AUTOMATIC-PROTECTION-AND-PAGE-NINE",
      "CUT-POCKET-AND-THE-STREET",
      "CUT-SESSION-AND-ITS-TRAFFIC",
      "CUT-THE-WE-AND-THE-SINGLE-ANSWER"
    ]
  },
  {
    "timeline_id": "TL-MINDWARS-TERRITORY",
    "chronology_kind": "interval",
    "canon_status": "binding-canon",
    "relative_chronology": "As effects intensify and theories remain unconfirmed, Mara recognizes the reversal that human minds are the shore and territory being crossed rather than explorers approaching empty space.",
    "exact_time": null,
    "duration": null,
    "location": "Multiple unnamed locations and defender records",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003"
    ],
    "chapter_numbers": [
      86,
      87,
      88,
      89,
      90,
      91,
      92,
      93
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-INWARD-FRONTIER-PREMISE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-FOREIGN-SIGNAL-PROVENANCE"
      }
    ],
    "uncertainty_notes": [
      "The thematic reversal reveals human position, not sender identity.",
      "This range carries both continuing INTRUDE arrivals and operational PAIR traffic. Each pairing session carries its own single-mode chronology in this Timeline - TL-PAIR-OPERATOR-TRAFFIC, TL-PAIR-MARA-NIA-RECORDED-SESSION, and TL-PAIR-DISPATCH-OPERATIONS - so the range entry records no single mechanism event.",
      "A consented content recording can prove only what one recorded pair deliberately carried; traffic analysis sees consent-state and transport metadata and never unrecorded meaning."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": [
      "CUT-FALLBACK-AND-THE-BREACH-MODEL",
      "CUT-RECORDED-AND-UNRECORDED",
      "CUT-THE-SHORE-AND-THE-BELIEVERS",
      "CUT-THEORIES-AND-THE-UNPARSED"
    ]
  },
  {
    "timeline_id": "TL-NULL-DECISION",
    "chronology_kind": "interval",
    "canon_status": "binding-canon",
    "relative_chronology": "Models predict a synchronized breach beyond copper capacity; a broad null is the only likely defense, and its possible subtraction cost across an affected area canonically described as three counties wide is confronted before authorization.",
    "exact_time": null,
    "duration": null,
    "location": "Defender decision settings and the unnamed affected area",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003"
    ],
    "chapter_numbers": [
      94,
      95,
      96,
      97,
      98,
      99,
      100,
      101
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-COUNTERPHASE-DEFENSE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-NULL-EXTENT"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-NULL-CIVILIAN-HARM"
      }
    ],
    "uncertainty_notes": [
      "Nobody can collect meaningful consent from everyone in the affected area in time.",
      "The canonical width is not a mathematical radius and the specific vulnerable memories cannot be predicted."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "not-applicable",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "not-applicable",
      "cancel_state": null,
      "pair_state": null,
      "pairing_evidence": null,
      "evidence_scope": "No cancellation fires in this range; it is modelling, argument, and authorization. The model predicts that subtraction may occur and cannot identify which faculties, memories, or civilians are vulnerable, and no pair consent or transcript can stand in for the affected area."
    },
    "cross_cut_ids": [
      "CUT-DEFAULT-ENROLLMENT-AND-THE-MODEL",
      "CUT-NEGLIGIBLE-AND-THE-EXTENT",
      "CUT-NOBODY-TO-ASK",
      "CUT-THE-EXTENT-RETURNED"
    ]
  },
  {
    "timeline_id": "TL-NULL-NIGHT",
    "chronology_kind": "interval",
    "canon_status": "binding-canon",
    "relative_chronology": "Across one shared null-night chronology, Nia works from a consent shelter, Julian preserves authorization, Mara drives the patterns into exact counterphase, the Foreign Signal goes silent, Mara's own voice diminishes, and civilians including Safiya are harmed throughout the affected area.",
    "exact_time": "the Tuesday night of the null; no absolute date selected",
    "duration": null,
    "location": "An affected area canonically described as three counties wide",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003",
      "CHAR-004"
    ],
    "chapter_numbers": [
      102,
      103,
      104,
      105,
      106,
      107,
      108
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-COUNTERPHASE-DEFENSE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-NULL-SILENCE-DIMINISHMENT"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-NULL-EXTENT"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-NULL-CIVILIAN-HARM"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-TUESDAY-KETTLE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-MATERNAL-LANGUAGE-LOSS"
      }
    ],
    "uncertainty_notes": [
      "No null-night POV enters Safiya's unconsented interior; she owns the later account.",
      "The silence supplies no surrender, counterparty, sender, or complete civilian-loss inventory."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "CANCEL",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "not-applicable",
      "cancel_state": {
        "scope": "area-scale",
        "individual_consent": null,
        "institutional_authorization": "Emergency defensive authorization issued by the civil authority through the defender program, preserved by Julian in the record; it is institutional authorization and never individual consent obtained from every affected person.",
        "subtraction": "Removal or degradation of access to mental content and faculties among an unknown set of people throughout an affected area canonically described as three counties wide, including Safiya's private two-person maternal layer and a measurable diminishment of Mara's own inner voice.",
        "inserted_content": "none",
        "affected_set_predictable_before": false,
        "affected_set_enumerable_during": false,
        "affected_set_fully_mapped_after": false,
        "additive_inverse_exists": false,
        "provenance_yield": "none"
      },
      "pair_state": null,
      "pairing_evidence": null,
      "evidence_scope": "The defender null is the bounded test's own operation at area scale: unaddressed, nonsemantic, and subtractive. It silences the Foreign Signal, exposes no provenance, enumerates no affected person, cannot be reversed by any mode, and authorizes no later counterphase. Pair channels coordinating the night carry no group mind and expose transport metadata only."
    },
    "cross_cut_ids": [
      "CUT-A-PAGE-AND-A-DOORWAY",
      "CUT-A-THINNER-VOICE-AND-A-CLEAN-LOG",
      "CUT-FIELD-AND-THE-INSTRUMENT",
      "CUT-PEAK-AND-THE-PHASE",
      "CUT-SILENCE-WITHOUT-A-COUNTERPARTY",
      "CUT-THE-LOCK-AND-THE-UNSHELTERED",
      "CUT-WHO-CAME-IN"
    ]
  },
  {
    "timeline_id": "TL-POSTNULL-HISTORY",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "Immediately after null night, authorities announce success without surrender or counterparty, Julian enters consent dispute and civilian uncertainty into the history, and Nia stops making usable self-trust contingent on an origin answer.",
    "exact_time": "after the null and before the two-year Coda interval",
    "duration": null,
    "location": "Official record systems and Civic Record Trust",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003"
    ],
    "chapter_numbers": [
      109,
      110,
      111,
      112
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-MINDWARS-TERM-UNDECLARED"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-APPROPRIATION"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-NIA-BELIEF-DISTRIBUTION"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-ARCHIVE-CONTESTED"
      }
    ],
    "uncertainty_notes": [
      "The first-casualty attribution remains the Trust's uncorrectable inference.",
      "Nia's usable self-trust is not a provenance answer, forgiveness, or archive endorsement."
    ],
    "record_chronology": {
      "composition_timeline_id": null,
      "deposit_timeline_id": "TL-TRUST-ROLLING-DEPOSITS",
      "release_timeline_ids": [
        "TL-TRUST-CONDITIONED-RELEASES"
      ]
    },
    "technical_state": null,
    "cross_cut_ids": [
      "CUT-DEPOSITED-AND-SUMMARIZED",
      "CUT-HISTORY-AND-THE-WORD-SAVED"
    ]
  },
  {
    "timeline_id": "TL-CODA-PUBLIC-ACCOUNTING",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "Two years after the null, Nia works civilian-loss intake and Julian prepares conditioned public releases while official summaries and Trust records remain in visible contest.",
    "exact_time": "two post-null years",
    "duration": null,
    "location": "Civic Record Trust and civilian-loss intake",
    "participants": [
      "CHAR-002",
      "CHAR-003",
      "CHAR-004"
    ],
    "chapter_numbers": [
      113,
      114
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-POSTWAR-STATE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CASE-ZERO-LOSS-INTAKE"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-ARCHIVE-CONTESTED"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-TRUST-GOVERNANCE"
      }
    ],
    "uncertainty_notes": [
      "No complete holdings, inquiry, release, or narrator adjudicates the first-casualty attribution.",
      "The Foreign Signal stays silent and no counterphase resumes."
    ],
    "record_chronology": {
      "composition_timeline_id": null,
      "deposit_timeline_id": "TL-TRUST-ROLLING-DEPOSITS",
      "release_timeline_ids": [
        "TL-TRUST-CONDITIONED-RELEASES"
      ]
    },
    "technical_state": null,
    "cross_cut_ids": [
      "CUT-INTAKE-AND-RELEASE"
    ]
  },
  {
    "timeline_id": "TL-CODA-APPROACH",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "Safiya travels through affected communities toward Mara's copper-retained house, rehearsing her own facts and declining to speak for every civilian.",
    "exact_time": "two post-null years",
    "duration": null,
    "location": "Unnamed communities inside the affected area and eleven miles from Northline Array",
    "participants": [
      "CHAR-004"
    ],
    "chapter_numbers": [
      115
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-ELEVEN-MILES"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-CHAR-SAFIYA-NAME"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-PROFESSION-SAFIYA"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-GEOGRAPHY-UNNAMED"
      }
    ],
    "uncertainty_notes": [
      "Safiya's name and route supply no authority to infer a real-world heritage geography."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-CODA-THRESHOLD",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "Safiya reaches Mara's house, knocks three unhurried times, waits, and Mara hears the protocol from the other side before opening the door.",
    "exact_time": "two post-null years",
    "duration": null,
    "location": "Mara's copper-retained house",
    "participants": [
      "CHAR-001",
      "CHAR-004"
    ],
    "chapter_numbers": [
      116,
      117
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-THREE-KNOCKS"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-REL-MARA-SAFIYA"
      }
    ],
    "uncertainty_notes": [
      "The two viewpoints will share one threshold event, not create two knock events.",
      "Compliance guarantees no remedy."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": [
      "CUT-THREE-KNOCKS-BOTH-SIDES"
    ]
  },
  {
    "timeline_id": "TL-CODA-ACCOUNT",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "Safiya gives her Tuesday-kettle account, eleven-mile location, absence of foreign intrusion, and the exact shape of the private maternal-language subtraction while Mara receives three counties wide as people rather than geometry.",
    "exact_time": "visit evening, two post-null years",
    "duration": null,
    "location": "Mara's house",
    "participants": [
      "CHAR-001",
      "CHAR-004"
    ],
    "chapter_numbers": [
      118,
      119,
      120,
      121
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-NULL-EXTENT"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-ELEVEN-MILES"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-TUESDAY-KETTLE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-MATERNAL-LANGUAGE-LOSS"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-SAFIYA-HERITAGE"
      }
    ],
    "uncertainty_notes": [
      "Safiya owns the full account; null-night chapters cannot preempt her interior experience.",
      "heritage_base remains exactly unspecified_by_author and no real-world particulars may be inferred."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": [
      "CUT-ACCOUNT-AND-THE-PEOPLE-IN-IT",
      "CUT-TUESDAY-AND-THE-SHAPE"
    ]
  },
  {
    "timeline_id": "TL-CODA-CONSENT",
    "chronology_kind": "interval",
    "canon_status": "binding-canon",
    "relative_chronology": "Safiya asks Mara to use the retained transmitter, gives affirmative sober repeated consent, and refuses to let a refusal become a lecture that invalidates her yes.",
    "exact_time": "same visit evening",
    "duration": null,
    "location": "Mara's house",
    "participants": [
      "CHAR-001",
      "CHAR-004"
    ],
    "chapter_numbers": [
      122,
      123
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-SAFIYA-FREE-CONSENT"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CONSENT-SOVEREIGNTY"
      }
    ],
    "uncertainty_notes": [
      "Consent removes lack of authorization as the reason to refuse but cannot create source truth or compel transmission."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-CODA-REFUSAL",
    "chronology_kind": "interval",
    "canon_status": "binding-canon",
    "relative_chronology": "Mara considers the mechanism, refuses a counterfeit because she lacks Safiya's mother and the erased private layer, switches the relay off, and puts the kettle on.",
    "exact_time": "same visit evening",
    "duration": null,
    "location": "Mara's house",
    "participants": [
      "CHAR-001",
      "CHAR-004"
    ],
    "chapter_numbers": [
      124,
      125
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-TRUTH-BASED-REFUSAL"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-HUMAN-REMEDY-OBLIGATION"
      }
    ],
    "uncertainty_notes": [
      "The no is a physics and truth limit, never a disqualification of Safiya's consent.",
      "No substitute memory is transmitted."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "not-applicable",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "not-applicable",
      "cancel_state": null,
      "pair_state": null,
      "pairing_evidence": null,
      "evidence_scope": "Retained capacity exists, but the relay is deliberately switched off, so no neural communication event occurs. Two independent physical limits stand behind the refusal: no source corpus of the private two-person layer exists, and cancellation has no additive inverse, so no mode could carry the loss back even with Safiya's valid consent."
    },
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-CODA-STAYING",
    "chronology_kind": "interval",
    "canon_status": "mixed",
    "relative_chronology": "Safiya receives no restoration, chooses what presence she will accept without calling it repair, remains, and tells Mara about her mother while ordinary speech crosses the room in both directions.",
    "exact_time": "same visit, continuing until one in the morning in Mara's attributed account",
    "duration": null,
    "location": "Mara's kitchen",
    "participants": [
      "CHAR-001",
      "CHAR-004"
    ],
    "chapter_numbers": [
      126,
      127
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-HUMAN-REMEDY-OBLIGATION"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-REL-MARA-SAFIYA"
      }
    ],
    "uncertainty_notes": [
      "Staying is companionship, not restoration, forgiveness, or equivalence to repair."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": [
      "CUT-VOICE-ACROSS-THE-TABLE"
    ]
  },
  {
    "timeline_id": "TL-CODA-OUTWARD",
    "chronology_kind": "interval",
    "canon_status": "binding-canon",
    "relative_chronology": "Mara enters an account against herself, accepts a duty to visit affected communities, reaches a new threshold, knocks, and waits; the terminal provenance question remains unanswered.",
    "exact_time": "after Safiya's visit; no more specific date selected",
    "duration": null,
    "location": "A new civilian threshold in the unnamed affected area",
    "participants": [
      "CHAR-001"
    ],
    "chapter_numbers": [
      128
    ],
    "fact_refs": [
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-HUMAN-REMEDY-OBLIGATION"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CODA-PROVENANCE-QUESTION"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-FOREIGN-SIGNAL-PROVENANCE"
      }
    ],
    "uncertainty_notes": [
      "The obligation remains incomplete and does not become a campaign.",
      "No signal returns and no sender or provenance question is solved."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-RECORD-PRETRUST-COMPOSITION",
    "chronology_kind": "interval",
    "canon_status": "novel-extension",
    "relative_chronology": "Discovery-era lab logs, voice memoranda, and contemporaneous witness source records are composed before the Civic Record Trust exists.",
    "exact_time": "during Discovery, before the post-April Trust formation",
    "duration": null,
    "location": "Northline Array and Nia's dispatch setting",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003"
    ],
    "chapter_numbers": [
      1,
      2,
      3,
      4,
      5,
      16,
      17,
      18,
      19,
      20,
      21,
      22,
      23,
      24,
      25,
      26,
      27,
      28,
      29
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-RECORD-FRAME"
      }
    ],
    "uncertainty_notes": [
      "Composition before the Trust must never be rewritten as a Trust-era deposition.",
      "A source record's provenance does not certify objective truth inside the account."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-RECORD-PRETRUST-DEPOSIT",
    "chronology_kind": "interval",
    "canon_status": "novel-extension",
    "relative_chronology": "After Trust formation, pre-Trust Discovery records are deposited with their original composition dates and provenance intact.",
    "exact_time": "after TL-TRUST-FORMATION",
    "duration": null,
    "location": "Civic Record Trust",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003"
    ],
    "chapter_numbers": [
      52,
      53,
      54,
      55
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-RECORD-FRAME"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-TRUST-GOVERNANCE"
      }
    ],
    "uncertainty_notes": [
      "Later deposit never changes the earlier composition time or turns the Trust into a Discovery-era institution."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-TRUST-ROLLING-DEPOSITS",
    "chronology_kind": "interval",
    "canon_status": "novel-extension",
    "relative_chronology": "From post-April Trust formation onward, encrypted signed first-person deposits enter under witness-controlled embargo and release conditions.",
    "exact_time": "only after TL-TRUST-FORMATION",
    "duration": "Private Defense through Aftermath Coda",
    "location": "Civic Record Trust",
    "participants": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003",
      "CHAR-004"
    ],
    "chapter_numbers": [
      52,
      54,
      62,
      73,
      110,
      113,
      118,
      128
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-TRUST-GOVERNANCE"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-ARCHIVE-CONTESTED"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-RECORD-FRAME"
      }
    ],
    "uncertainty_notes": [
      "Not every deposit is public, and a release condition never converts testimony into adjudicated truth."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-TRUST-CONDITIONED-RELEASES",
    "chronology_kind": "interval",
    "canon_status": "novel-extension",
    "relative_chronology": "After the null and continuing into the Coda, the Trust makes provenance-preserving public releases only where witness conditions permit, in visible contest with official summaries.",
    "exact_time": "post-null and ongoing",
    "duration": null,
    "location": "Public record and Civic Record Trust",
    "participants": [
      "CHAR-002",
      "CHAR-003",
      "CHAR-004"
    ],
    "chapter_numbers": [
      110,
      113,
      114
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-ARCHIVE-CONTESTED"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-TRUST-GOVERNANCE"
      }
    ],
    "uncertainty_notes": [
      "Complete holdings are not presumed open.",
      "No release or official summary adjudicates Nia's first wanting or the Foreign Signal sender."
    ],
    "record_chronology": null,
    "technical_state": null,
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-PAIR-CLINICAL-BENEFIT",
    "chronology_kind": "interval",
    "canon_status": "novel-extension",
    "relative_chronology": "Inside the consortium offer window, Ada Ferris and her daughter Lena hold the pairing Julian watches carry deliberate speech, the bench session Mara measures, and the later working passage neither of them could carry alone.",
    "exact_time": null,
    "duration": null,
    "location": "Consortium demonstration rooms and an ordinary interpreting engagement",
    "participants": [
      "CHAR-001",
      "CHAR-003",
      "CHAR-005",
      "CHAR-006"
    ],
    "chapter_numbers": [
      36,
      37,
      41
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-PAIR"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-PAIR-CALIBRATION"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-PAIRING-EVIDENCE"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-CHAR-ADA-NAME"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-CHAR-LENA-NAME"
      }
    ],
    "uncertainty_notes": [
      "A benefit two people choose for themselves does not make default or broad-form enrollment consensual.",
      "Ada's loss of expressive speech predates every neural communication event in the novel. The pairing carries what she deliberately sends and restores nothing, and it is never a precedent for reversing a Subtraction_Effect.",
      "The rig transports in both directions because PAIR does; no observer in this range has read the April specification, and nothing here anticipates page nine."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "PAIR",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "identified",
      "cancel_state": null,
      "pair_state": {
        "participants": [
          "CHAR-005",
          "CHAR-006"
        ],
        "consent": {
          "current": true,
          "specific_act": "This pairing between Ada and Lena Ferris now, each carried contribution offered by a deliberate send act, either of them free to pause or revoke at any point.",
          "revocable": true,
          "authorized_a": true,
          "authorized_b": true
        },
        "calibration_id": "PAIR-CAL-FERRIS",
        "calibration_participants": [
          "CHAR-005",
          "CHAR-006"
        ],
        "calibration_transferable": false,
        "deliberate_send_state": "required"
      },
      "pairing_evidence": {
        "consent_state_metadata_present": true,
        "transport_metadata_present": true,
        "metadata_semantically_opaque": true,
        "content_recording_enabled": false,
        "recording_consent_a": false,
        "recording_consent_b": false,
        "transcript": null
      },
      "evidence_scope": "Two living calibrated people deliberately exchange offered speech in front of Julian and, at the bench, in front of Mara's instruments. It proves the send gate holds and unoffered thought stays private. Consent-state and transport metadata exist and are semantically opaque; recording is off, so no transcript exists; and none of it speaks to December, to Nia's wanting, or to what a deployed network would be permitted to do."
    },
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-PAIR-DISPATCH-DEMONSTRATION",
    "chronology_kind": "point",
    "canon_status": "novel-extension",
    "relative_chronology": "Inside the consortium offer window, Tomas Reyner and Cora Baird work one bad incident over their calibrated channel while Nia watches, in the same hour she reads the enrollment form.",
    "exact_time": null,
    "duration": null,
    "location": "An unnamed county dispatch floor",
    "participants": [
      "CHAR-002",
      "CHAR-007",
      "CHAR-008"
    ],
    "chapter_numbers": [
      38
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-PAIR"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-PAIRING-EVIDENCE"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-CHAR-TOMAS-NAME"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-CHAR-CORA-NAME"
      }
    ],
    "uncertainty_notes": [
      "The enrollment form's default to record is the institution's wording, not this session's state: recording stays off here and both dispatchers would have to enable it separately.",
      "Nia cannot compare this session to what happened to her, because nothing that happened to her involved consent, calibration, or a deliberate send."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "PAIR",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "identified",
      "cancel_state": null,
      "pair_state": {
        "participants": [
          "CHAR-007",
          "CHAR-008"
        ],
        "consent": {
          "current": true,
          "specific_act": "This shift's paired dispatch coordination between Tomas Reyner and Cora Baird, contribution by deliberate contribution, revocable mid-incident.",
          "revocable": true,
          "authorized_a": true,
          "authorized_b": true
        },
        "calibration_id": "PAIR-CAL-REYNER-BAIRD",
        "calibration_participants": [
          "CHAR-007",
          "CHAR-008"
        ],
        "calibration_transferable": false,
        "deliberate_send_state": "required"
      },
      "pairing_evidence": {
        "consent_state_metadata_present": true,
        "transport_metadata_present": true,
        "metadata_semantically_opaque": true,
        "content_recording_enabled": false,
        "recording_consent_a": false,
        "recording_consent_b": false,
        "transcript": null
      },
      "evidence_scope": "One paired shift handles one incident better than two radios could. The record establishes that the channel existed, when it carried, and that both dispatchers consented and could stop; it contains no dispatch content, and an operational benefit is not an argument that consent may be bundled into a form."
    },
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-PAIR-MARA-NIA-CALIBRATION",
    "chronology_kind": "interval",
    "canon_status": "novel-extension",
    "relative_chronology": "Late in the offer window, Mara and Nia complete their own pair-specific joint calibration and exchange first deliberately offered contributions, before the sustained protocol work of TL-PRIVATE-PROTOCOL.",
    "exact_time": null,
    "duration": null,
    "location": "Northline Array",
    "participants": [
      "CHAR-001",
      "CHAR-002"
    ],
    "chapter_numbers": [
      40,
      42
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-PAIR"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-PAIR-CALIBRATION"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CONSENT-SOVEREIGNTY"
      }
    ],
    "uncertainty_notes": [
      "Beginning calibration precedes the sustained fluency recorded in TL-PRIVATE-PROTOCOL and does not duplicate it; the calibration is the same pair's and carries the same identifier.",
      "The contrast between an offered sentence and what reached Nia in the winter gives her vocabulary and no origin. It resolves neither account of her wanting."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "PAIR",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "identified",
      "cancel_state": null,
      "pair_state": {
        "participants": [
          "CHAR-001",
          "CHAR-002"
        ],
        "consent": {
          "current": true,
          "specific_act": "This calibration and these first offered contributions between Mara and Nia now, each one deliberately sent, either of them free to pause or revoke.",
          "revocable": true,
          "authorized_a": true,
          "authorized_b": true
        },
        "calibration_id": "PAIR-CAL-MARA-NIA",
        "calibration_participants": [
          "CHAR-001",
          "CHAR-002"
        ],
        "calibration_transferable": false,
        "deliberate_send_state": "required"
      },
      "pairing_evidence": {
        "consent_state_metadata_present": true,
        "transport_metadata_present": true,
        "metadata_semantically_opaque": true,
        "content_recording_enabled": false,
        "recording_consent_a": false,
        "recording_consent_b": false,
        "transcript": null
      },
      "evidence_scope": "The pair's own calibration is established and its first contributions are offered rather than taken. Metadata records that the channel opened and how it behaved; recording is off, so nothing was kept, and neither the effort of sending nor the contrast with the bench handshake is evidence about what caused Nia's wanting."
    },
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-PAIR-MARA-NIA-COUNTERPHASE",
    "chronology_kind": "interval",
    "canon_status": "novel-extension",
    "relative_chronology": "Across the counterphase window, Mara and Nia hold their operational channel open while Nia sets her conditions and answers for herself, while the consented bounded-local test runs, and while its records are read afterward.",
    "exact_time": null,
    "duration": null,
    "location": "Defender testing site",
    "participants": [
      "CHAR-001",
      "CHAR-002"
    ],
    "chapter_numbers": [
      73,
      74,
      75
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-PAIR"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-PAIRING-EVIDENCE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CONSENT-SOVEREIGNTY"
      }
    ],
    "uncertainty_notes": [
      "Coordinating a cancellation over a paired channel does not merge the modes. The cancellation carries no address and subtracts; it is recorded separately as TL-MINDWARS-COUNTERPHASE with mode CANCEL, and this entry records no cancellation.",
      "Nia's report that a familiar phrase is no longer available to her reaches Mara as ordinary spoken speech. No transported contribution, transcript, or metadata field contains the missing phrase, and nothing here identifies what else the field removed or from whom.",
      "A consent state that is current, specific, revocable, and local to one session authorizes that session only. It becomes neither a standing permission nor evidence about origin."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "PAIR",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "identified",
      "cancel_state": null,
      "pair_state": {
        "participants": [
          "CHAR-001",
          "CHAR-002"
        ],
        "consent": {
          "current": true,
          "specific_act": "This coordinating channel between Mara and Nia for the bounded-local test they are running now, every contribution deliberately sent and either participant free to pause or revoke while the field is live.",
          "revocable": true,
          "authorized_a": true,
          "authorized_b": true
        },
        "calibration_id": "PAIR-CAL-MARA-NIA",
        "calibration_participants": [
          "CHAR-001",
          "CHAR-002"
        ],
        "calibration_transferable": false,
        "deliberate_send_state": "required"
      },
      "pairing_evidence": {
        "consent_state_metadata_present": true,
        "transport_metadata_present": true,
        "metadata_semantically_opaque": true,
        "content_recording_enabled": false,
        "recording_consent_a": false,
        "recording_consent_b": false,
        "transcript": null
      },
      "evidence_scope": "The channel proves that the two of them coordinated a consented test deliberately, sentence by offered sentence, and that either could have stopped it. Consent-state metadata, transport metadata, and the integrity log agree on timing and consent transitions and hold no thought at all; recording was never enabled, so no transcript exists, and none of these records can be promoted into evidence about origin or into a standing permission."
    },
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-PAIR-MARA-NIA-FLUENCY-LIMIT",
    "chronology_kind": "point",
    "canon_status": "novel-extension",
    "relative_chronology": "Late in the counterphase window, with an incoming pattern active, the same channel takes a deliberate pause, then a latency fault, and finishes in ordinary spoken voice.",
    "exact_time": null,
    "duration": null,
    "location": "Defender testing site",
    "participants": [
      "CHAR-001",
      "CHAR-002"
    ],
    "chapter_numbers": [
      77
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-PAIR"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-PAIRING-EVIDENCE"
      }
    ],
    "uncertainty_notes": [
      "The integrity failure is resolved by an explicit recorded fallback to ordinary spoken speech within the same session. The channel completes nothing, guesses nothing, and buffers nothing, and no later event treats the failed contribution as delivered.",
      "Fluency is not permission. Ease of transport changes no consent state, and stopping mid-sentence is the operative proof of that."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "PAIR",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "identified",
      "cancel_state": null,
      "pair_state": {
        "participants": [
          "CHAR-001",
          "CHAR-002"
        ],
        "consent": {
          "current": true,
          "specific_act": "This session between Mara and Nia while a pattern is arriving, paused deliberately by Nia and then dropped to spoken voice after the transport fault, with consent intact throughout.",
          "revocable": true,
          "authorized_a": true,
          "authorized_b": true
        },
        "calibration_id": "PAIR-CAL-MARA-NIA",
        "calibration_participants": [
          "CHAR-001",
          "CHAR-002"
        ],
        "calibration_transferable": false,
        "deliberate_send_state": "integrity-failed"
      },
      "pairing_evidence": {
        "consent_state_metadata_present": true,
        "transport_metadata_present": true,
        "metadata_semantically_opaque": true,
        "content_recording_enabled": false,
        "recording_consent_a": false,
        "recording_consent_b": false,
        "transcript": null
      },
      "evidence_scope": "The record shows a deliberate pause, a latency fault, a refusal to complete an uncertain contribution, and a fallback to ordinary voice. It establishes that the consent state is operational rather than ceremonial. It contains no content, no reconstruction of the clipped contribution, and nothing about the arriving pattern's source."
    },
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-PAIR-MARA-NIA-RECORDED-SESSION",
    "chronology_kind": "point",
    "canon_status": "novel-extension",
    "relative_chronology": "Once, in the territory window, Mara and Nia enable content recording by separate explicit mutual consent for a single investigative session, then switch it off again.",
    "exact_time": null,
    "duration": "one session of roughly four minutes of carried contributions",
    "location": "Defender operations setting",
    "participants": [
      "CHAR-001",
      "CHAR-002"
    ],
    "chapter_numbers": [
      88
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-PAIR"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-PAIRING-EVIDENCE"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-ARCHIVE-CONTESTED"
      }
    ],
    "uncertainty_notes": [
      "This is the movement's only recorded session. Recording required a consent separate from the consent to pair, was given by both participants, and returns to disabled afterward unless both enable it again.",
      "The transcript's existence makes it wanted. Institutional demand for it is a pressure on the pair, never an extension of its scope.",
      "The transcript proves what the protocol carried and nothing else: no intent, no memory provenance, no unoffered thought, and no origin for Nia's earlier wanting."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "PAIR",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "identified",
      "cancel_state": null,
      "pair_state": {
        "participants": [
          "CHAR-001",
          "CHAR-002"
        ],
        "consent": {
          "current": true,
          "specific_act": "This one investigative session between Mara and Nia, with recording agreed separately by both of them for this session only and every contribution still deliberately sent.",
          "revocable": true,
          "authorized_a": true,
          "authorized_b": true
        },
        "calibration_id": "PAIR-CAL-MARA-NIA",
        "calibration_participants": [
          "CHAR-001",
          "CHAR-002"
        ],
        "calibration_transferable": false,
        "deliberate_send_state": "required"
      },
      "pairing_evidence": {
        "consent_state_metadata_present": true,
        "transport_metadata_present": true,
        "metadata_semantically_opaque": true,
        "content_recording_enabled": true,
        "recording_consent_a": true,
        "recording_consent_b": true,
        "transcript": {
          "transcript_id": "PAIR-TRANSCRIPT-TERRITORY-SESSION",
          "session_timeline_id": "TL-PAIR-MARA-NIA-RECORDED-SESSION",
          "content_scope": "Only the contributions the protocol carried between Mara and Nia during this one recorded session, in the order they were sent."
        }
      },
      "evidence_scope": "One transcript exists and is completely true about its own narrow subject: what two consenting people deliberately sent each other during one session that both agreed to record. It carries no unoffered thought, no truth, no intent, no memory provenance, no complete mental state, nothing from any other session, and no answer about origin."
    },
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-PAIR-OPERATOR-SHIFT-VANE",
    "chronology_kind": "point",
    "canon_status": "novel-extension",
    "relative_chronology": "During the protective network's worked shift, Mara and Idris Vane run their own calibrated channel as the coordination layer under time pressure, take one deliberate pause, and drop to ordinary voice.",
    "exact_time": null,
    "duration": null,
    "location": "Defender network and one unnamed protected block",
    "participants": [
      "CHAR-001",
      "CHAR-009"
    ],
    "chapter_numbers": [
      81
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-PAIR"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-PAIR-CALIBRATION"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-CHAR-IDRIS-NAME"
      }
    ],
    "uncertainty_notes": [
      "The pause stops semantic transport immediately and is followed in the same sequence by an explicit fallback to ordinary spoken voice, which is what saves the block.",
      "Speed and legitimate tactical value are real here. They authorize nothing beyond this pair's current consent, and the channel carries no cancellation."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "PAIR",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "identified",
      "cancel_state": null,
      "pair_state": {
        "participants": [
          "CHAR-001",
          "CHAR-009"
        ],
        "consent": {
          "current": true,
          "specific_act": "This shift's coordination channel between Mara and Idris Vane, deliberately sent contribution by contribution, paused by Mara mid-sequence with consent intact.",
          "revocable": true,
          "authorized_a": true,
          "authorized_b": true
        },
        "calibration_id": "PAIR-CAL-MARA-VANE",
        "calibration_participants": [
          "CHAR-001",
          "CHAR-009"
        ],
        "calibration_transferable": false,
        "deliberate_send_state": "paused"
      },
      "pairing_evidence": {
        "consent_state_metadata_present": true,
        "transport_metadata_present": true,
        "metadata_semantically_opaque": true,
        "content_recording_enabled": false,
        "recording_consent_a": false,
        "recording_consent_b": false,
        "transcript": null
      },
      "evidence_scope": "The record establishes that Mara and Idris were paired, when they carried, when transport stopped, and that the work finished in spoken voice. Mara's calibration with Idris is hers and his alone and cannot be pointed at another operator. Nothing recorded here identifies a sender or reconstructs a contribution."
    },
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-PAIR-OPERATOR-SHIFT-OSEI",
    "chronology_kind": "point",
    "canon_status": "novel-extension",
    "relative_chronology": "On the coverage-accounting shift, Mara works the network with Rhea Osei over a second, separately calibrated channel, and the count of consenting pairs turns out to be the limit of the defense.",
    "exact_time": null,
    "duration": null,
    "location": "Defender network and unnamed protected pockets",
    "participants": [
      "CHAR-001",
      "CHAR-010"
    ],
    "chapter_numbers": [
      84
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-PAIR"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-PAIR-CALIBRATION"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-CHAR-RHEA-NAME"
      }
    ],
    "uncertainty_notes": [
      "Mara had to calibrate separately with Rhea; nothing from her channel with Idris Vane transferred. Coverage therefore grows only as fast as consenting pairs, which is why two streets apart can be a protected night and an unprotected one.",
      "The accounting names who is outside the pockets and supplies no method for widening coverage beyond the consent it rests on."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "PAIR",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "identified",
      "cancel_state": null,
      "pair_state": {
        "participants": [
          "CHAR-001",
          "CHAR-010"
        ],
        "consent": {
          "current": true,
          "specific_act": "This shift's coordination channel between Mara and Rhea Osei, separately calibrated for the two of them, every contribution deliberately sent and either free to stop.",
          "revocable": true,
          "authorized_a": true,
          "authorized_b": true
        },
        "calibration_id": "PAIR-CAL-MARA-OSEI",
        "calibration_participants": [
          "CHAR-001",
          "CHAR-010"
        ],
        "calibration_transferable": false,
        "deliberate_send_state": "required"
      },
      "pairing_evidence": {
        "consent_state_metadata_present": true,
        "transport_metadata_present": true,
        "metadata_semantically_opaque": true,
        "content_recording_enabled": false,
        "recording_consent_a": false,
        "recording_consent_b": false,
        "transcript": null
      },
      "evidence_scope": "A second separately calibrated channel proves that calibration does not scale by installation. The record holds pair identity, timing, and consent state; it holds no content, and it cannot show what the network would have to do to reach the people outside its pockets."
    },
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-PAIR-OPERATOR-TRAFFIC",
    "chronology_kind": "interval",
    "canon_status": "novel-extension",
    "relative_chronology": "Across the network's operational nights, Idris Vane and Rhea Osei work their own calibrated channel; Julian reads its consent-state and transport metadata afterward, and later holds the line when its recording state is disputed mid-operation.",
    "exact_time": null,
    "duration": null,
    "location": "Defender network and Civic Record Trust custody",
    "participants": [
      "CHAR-003",
      "CHAR-009",
      "CHAR-010"
    ],
    "chapter_numbers": [
      82,
      89
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-PAIR"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-PAIRING-EVIDENCE"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-ESP-PAIRINGS"
      }
    ],
    "uncertainty_notes": [
      "Traffic analysis reads timing, channel volume, acknowledgments, latency, integrity events, and consent transitions. It never recovers unrecorded meaning, and the pattern supports a policy claim rather than an evidentiary one.",
      "The dispute at the later operation is about whether anyone had agreed to keep the session. Recording was never mutually enabled, so no transcript exists to produce, and the operation waits while that is established.",
      "Julian holds these records and never pairs, which matches his roster position."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "PAIR",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "identified",
      "cancel_state": null,
      "pair_state": {
        "participants": [
          "CHAR-009",
          "CHAR-010"
        ],
        "consent": {
          "current": true,
          "specific_act": "The operators' own paired working channel between Idris Vane and Rhea Osei, calibrated for the two of them, each contribution deliberately sent and either free to pause or revoke.",
          "revocable": true,
          "authorized_a": true,
          "authorized_b": true
        },
        "calibration_id": "PAIR-CAL-VANE-OSEI",
        "calibration_participants": [
          "CHAR-009",
          "CHAR-010"
        ],
        "calibration_transferable": false,
        "deliberate_send_state": "required"
      },
      "pairing_evidence": {
        "consent_state_metadata_present": true,
        "transport_metadata_present": true,
        "metadata_semantically_opaque": true,
        "content_recording_enabled": false,
        "recording_consent_a": false,
        "recording_consent_b": false,
        "transcript": null
      },
      "evidence_scope": "Metadata can prove who was paired with whom, for how long, with what acknowledgments, faults, and consent transitions, and cannot prove one word that was sent. No content was recorded, so no transcript exists; a traffic pattern is not meaning, and the institutional shorthand that covers the whole capability with one term is a naming habit rather than a finding."
    },
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-PAIR-DISPATCH-OPERATIONS",
    "chronology_kind": "point",
    "canon_status": "novel-extension",
    "relative_chronology": "During a live operation in the territory window, Nia works paired with Tomas Reyner, an integrity fault clips a contribution at the worst moment, and the fallback to shouted ordinary voice costs measurable time.",
    "exact_time": null,
    "duration": null,
    "location": "An unnamed county operational setting",
    "participants": [
      "CHAR-002",
      "CHAR-007"
    ],
    "chapter_numbers": [
      91
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-PAIR"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-PAIR-CALIBRATION"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-CHAR-TOMAS-NAME"
      }
    ],
    "uncertainty_notes": [
      "The protocol refuses to complete a contribution it is unsure of. Nia declines the half sentence and falls back to ordinary voice in the same sequence; no log reconstructs what the fragment was meant to be.",
      "Nia's calibration with Tomas is separate from her calibration with Mara. Neither is transferable, and holding two does not merge them.",
      "The cost of the fallback is real and is not an argument for letting the channel guess."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "PAIR",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "identified",
      "cancel_state": null,
      "pair_state": {
        "participants": [
          "CHAR-002",
          "CHAR-007"
        ],
        "consent": {
          "current": true,
          "specific_act": "This operation's paired channel between Nia and Tomas Reyner, every contribution deliberately sent, consent intact when the transport fault occurs.",
          "revocable": true,
          "authorized_a": true,
          "authorized_b": true
        },
        "calibration_id": "PAIR-CAL-NIA-REYNER",
        "calibration_participants": [
          "CHAR-002",
          "CHAR-007"
        ],
        "calibration_transferable": false,
        "deliberate_send_state": "integrity-failed"
      },
      "pairing_evidence": {
        "consent_state_metadata_present": true,
        "transport_metadata_present": true,
        "metadata_semantically_opaque": true,
        "content_recording_enabled": false,
        "recording_consent_a": false,
        "recording_consent_b": false,
        "transcript": null
      },
      "evidence_scope": "The record holds the clipped contribution's integrity flag, the refusal to complete it, the ordinary-voice fallback, and the delay that followed. It does not hold the contribution, cannot reconstruct it, and says nothing about anyone's intent."
    },
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-PAIR-MARA-NIA-NULL-DECISION",
    "chronology_kind": "interval",
    "canon_status": "novel-extension",
    "relative_chronology": "While the null is argued and authorized, Mara and Nia keep their channel operational and Nia uses her own session records to refuse default enrollment and manufactured unanimity.",
    "exact_time": null,
    "duration": null,
    "location": "Defender decision settings",
    "participants": [
      "CHAR-001",
      "CHAR-002"
    ],
    "chapter_numbers": [
      94,
      98
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-PAIR"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-PAIRING-EVIDENCE"
      },
      {
        "record_type": "CanonFact",
        "record_id": "CF-CONSENT-SOVEREIGNTY"
      }
    ],
    "uncertainty_notes": [
      "Nia's own session logs are not a template for enrollment. A pair's consent answers for two people and cannot answer for anyone inside the affected area.",
      "Calibration remains hers and Mara's alone and cannot be handed to an institution, a default, or a continuity assumption.",
      "Refusing to speak for the area decides nothing about whether the field will be authorized."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "PAIR",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "identified",
      "cancel_state": null,
      "pair_state": {
        "participants": [
          "CHAR-001",
          "CHAR-002"
        ],
        "consent": {
          "current": true,
          "specific_act": "This channel between Mara and Nia through the decision sequence, each contribution deliberately sent, revocable at any point and renewed for each session rather than standing.",
          "revocable": true,
          "authorized_a": true,
          "authorized_b": true
        },
        "calibration_id": "PAIR-CAL-MARA-NIA",
        "calibration_participants": [
          "CHAR-001",
          "CHAR-002"
        ],
        "calibration_transferable": false,
        "deliberate_send_state": "required"
      },
      "pairing_evidence": {
        "consent_state_metadata_present": true,
        "transport_metadata_present": true,
        "metadata_semantically_opaque": true,
        "content_recording_enabled": false,
        "recording_consent_a": false,
        "recording_consent_b": false,
        "transcript": null
      },
      "evidence_scope": "The pair's records show a consent state that was collected one session at a time, which is exactly what a default enrollment would replace. They prove the scope of two answers and no more; no metadata pattern or transcript supplies another person's answer, and the affected area's consent does not exist to be produced."
    },
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-PAIR-SHELTER-INTAKE",
    "chronology_kind": "interval",
    "canon_status": "novel-extension",
    "relative_chronology": "Through null night, Tomas Reyner and Cora Baird volunteer paired at Nia's consent shelter, coordinating intake while she asks each arrival at the door.",
    "exact_time": "the Tuesday night of the null; no absolute date selected",
    "duration": null,
    "location": "A consent shelter inside the affected area",
    "participants": [
      "CHAR-002",
      "CHAR-007",
      "CHAR-008"
    ],
    "chapter_numbers": [
      102,
      105
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-PAIR"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-CHAR-TOMAS-NAME"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-CHAR-CORA-NAME"
      }
    ],
    "uncertainty_notes": [
      "The channel coordinates volunteers only. It carries nothing from, about, or on behalf of anyone who arrives, and no arrival is paired, addressed, read, or spoken for.",
      "The area-scale cancellation running the same night is recorded separately as TL-NULL-NIGHT with mode CANCEL. A shelter channel neither extends it, mitigates it, nor enumerates who it reached.",
      "The written list of who came in records arrivals and their own answers. It is not a record of who was affected, and the person who cannot give a current answer is not carried in."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "PAIR",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "identified",
      "cancel_state": null,
      "pair_state": {
        "participants": [
          "CHAR-007",
          "CHAR-008"
        ],
        "consent": {
          "current": true,
          "specific_act": "This night's paired intake coordination between Tomas Reyner and Cora Baird, contribution by deliberate contribution, either of them free to stop and work by voice.",
          "revocable": true,
          "authorized_a": true,
          "authorized_b": true
        },
        "calibration_id": "PAIR-CAL-REYNER-BAIRD",
        "calibration_participants": [
          "CHAR-007",
          "CHAR-008"
        ],
        "calibration_transferable": false,
        "deliberate_send_state": "required"
      },
      "pairing_evidence": {
        "consent_state_metadata_present": true,
        "transport_metadata_present": true,
        "metadata_semantically_opaque": true,
        "content_recording_enabled": false,
        "recording_consent_a": false,
        "recording_consent_b": false,
        "transcript": null
      },
      "evidence_scope": "The shelter's channel proves that two volunteers coordinated deliberately through the peak and that recording was never enabled. It establishes nothing about the people at the door, nothing about what the field outside removed, and nothing about who it reached."
    },
    "cross_cut_ids": []
  },
  {
    "timeline_id": "TL-PAIR-NULL-NIGHT-COORDINATION",
    "chronology_kind": "point",
    "canon_status": "novel-extension",
    "relative_chronology": "While the field runs on null night, Mara and Idris Vane hold the defense's coordinating channel and Julian timestamps its consent state alongside the authorization's exact scope and minute.",
    "exact_time": "the Tuesday night of the null; no absolute date selected",
    "duration": null,
    "location": "Defender operations and Civic Record Trust custody",
    "participants": [
      "CHAR-001",
      "CHAR-003",
      "CHAR-009"
    ],
    "chapter_numbers": [
      104
    ],
    "fact_refs": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-MODE-PAIR"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-PAIRING-EVIDENCE"
      },
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-CHAR-IDRIS-NAME"
      }
    ],
    "uncertainty_notes": [
      "The coordinating channel is consented and pair-specific; the field it coordinates is unaddressed and institutionally authorized, and the two are never the same permission.",
      "Julian's custody record holds the authorization's scope and minute and each channel's consent state. It names no affected person and contains no content, because none was recorded.",
      "Timestamping a consent state while a field runs preserves provenance of the record and settles nothing about what is being removed."
    ],
    "record_chronology": null,
    "technical_state": {
      "mode": "PAIR",
      "source_side_continuity": "not-applicable",
      "receiver_offset_seconds": null,
      "apparatus_mode": "bidirectional-architecture",
      "transmit_stage_present": true,
      "person_specific_address_state": "identified",
      "cancel_state": null,
      "pair_state": {
        "participants": [
          "CHAR-001",
          "CHAR-009"
        ],
        "consent": {
          "current": true,
          "specific_act": "This night's coordinating channel between Mara and Idris Vane, every contribution deliberately sent, consent current and revocable while the field runs.",
          "revocable": true,
          "authorized_a": true,
          "authorized_b": true
        },
        "calibration_id": "PAIR-CAL-MARA-VANE",
        "calibration_participants": [
          "CHAR-001",
          "CHAR-009"
        ],
        "calibration_transferable": false,
        "deliberate_send_state": "required"
      },
      "pairing_evidence": {
        "consent_state_metadata_present": true,
        "transport_metadata_present": true,
        "metadata_semantically_opaque": true,
        "content_recording_enabled": false,
        "recording_consent_a": false,
        "recording_consent_b": false,
        "transcript": null
      },
      "evidence_scope": "The custody entry proves that a consented coordinating channel existed at a stated minute with a stated consent state. It carries no contribution, identifies no affected person, and cannot be read as consent to the area-scale cancellation it coordinated."
    },
    "cross_cut_ids": []
  }
]
```

### PAIR-mode session chronology

Thirteen of the entries above are PAIR-mode session chronology added by the 2026-09-15 amendment, so the Timeline now carries fourteen `mode: PAIR` entries in total with `TL-PRIVATE-PROTOCOL`. They exist because Requirement 14.1 classifies **every** neural communication event as exactly one mode, and until this amendment only `TL-PRIVATE-PROTOCOL` did so for a Pairing_Session; the declared Fluent_Pairing beats in 36–42, 70–77, 78–93, and 94–108 carried no machine-recorded mode, consent state, calibration identity, or evidence boundary.

Each entry overlaps a scene window rather than replacing it, exactly as the record-custody windows already overlap theirs. The scene entry remains the chapter's single `timeline_id` in the Arc Outline; a PAIR entry is never a second `timeline_id` for any chapter. Because a `pair_state` holds exactly one pair, a range with sessions belonging to several pairs needs several entries, and one pair's sessions are split where the recorded send state differs — `required`, `paused`, or `integrity-failed`.

| Entry | Pair | Chapters | Send state | Recording |
|---|---|---|---|---|
| `TL-PAIR-CLINICAL-BENEFIT` | `CHAR-005` / `CHAR-006` | 36, 37, 41 | `required` | off |
| `TL-PAIR-DISPATCH-DEMONSTRATION` | `CHAR-007` / `CHAR-008` | 38 | `required` | off |
| `TL-PAIR-MARA-NIA-CALIBRATION` | `CHAR-001` / `CHAR-002` | 40, 42 | `required` | off |
| `TL-PRIVATE-PROTOCOL` (existing) | `CHAR-001` / `CHAR-002` | 56–61 | `required` | off |
| `TL-PAIR-MARA-NIA-COUNTERPHASE` | `CHAR-001` / `CHAR-002` | 73, 74, 75 | `required` | off |
| `TL-PAIR-MARA-NIA-FLUENCY-LIMIT` | `CHAR-001` / `CHAR-002` | 77 | `integrity-failed` | off |
| `TL-PAIR-OPERATOR-SHIFT-VANE` | `CHAR-001` / `CHAR-009` | 81 | `paused` | off |
| `TL-PAIR-OPERATOR-TRAFFIC` | `CHAR-009` / `CHAR-010` | 82, 89 | `required` | off |
| `TL-PAIR-OPERATOR-SHIFT-OSEI` | `CHAR-001` / `CHAR-010` | 84 | `required` | off |
| `TL-PAIR-MARA-NIA-RECORDED-SESSION` | `CHAR-001` / `CHAR-002` | 88 | `required` | **on, both consents, one transcript** |
| `TL-PAIR-DISPATCH-OPERATIONS` | `CHAR-002` / `CHAR-007` | 91 | `integrity-failed` | off |
| `TL-PAIR-MARA-NIA-NULL-DECISION` | `CHAR-001` / `CHAR-002` | 94, 98 | `required` | off |
| `TL-PAIR-SHELTER-INTAKE` | `CHAR-007` / `CHAR-008` | 102, 105 | `required` | off |
| `TL-PAIR-NULL-NIGHT-COORDINATION` | `CHAR-001` / `CHAR-009` | 104 | `required` | off |

Chapter 88 is the manuscript's only session with `content_recording_enabled: true`, and it required a recording consent from each participant separate from the consent to pair. Everywhere else recording is off, both recording consents are `false`, and `transcript` is `null`.

Seven calibrations exist and none is transferable: `PAIR-CAL-MARA-NIA`, `PAIR-CAL-FERRIS`, `PAIR-CAL-REYNER-BAIRD`, `PAIR-CAL-MARA-VANE`, `PAIR-CAL-MARA-OSEI`, `PAIR-CAL-VANE-OSEI`, and `PAIR-CAL-NIA-REYNER`. Mara holds three distinct calibrations, Nia two, Tomas Reyner two, and each operator two, which is the point: a person may pair with more than one partner, and each pairing has to be built with that partner. Nothing is inherited, installed, extended to a third participant, or pointed at a dead or absent person, a simulation, an archive, a model, or a reconstruction.

Where a paired channel coordinates a cancellation — the bounded test at 73–75 and null night at 104 — the two modes stay separate records. The `CANCEL` entry holds the unaddressed subtractive event and its consent or authorization; the `PAIR` entry holds the consented two-person channel that talked about it. Neither entry carries two modes, and no paired channel ever transports a cancellation, a subtracted memory, or another person's answer.

## Unresolved questions and theory inventory

The schema has no separate `UnresolvedQuestion` record type. The authoritative machine state therefore lives in the `Reveal` records below, where permanent questions use `truth_status: unresolved`, a null owner, a null release chapter, and a null payoff window. This readable theory table adds no machine values and privileges no account.

| Question / theory | Evidence characters may cite | Counterweight | `confirmed` | Machine record |
|---|---|---|---:|---|
| Mara's later handshake caused Nia's wanting | same person-specific address; chronology; Mara's high private conviction | content-free signal; no instrument, trace, or privileged narrator; Mara's guilt seeks centrality | `false` | `REVEAL-HANDSHAKE-WANTING-ORIGIN` |
| Foreign Signal/adversary caused Nia's wanting | later pattern of intrusive states; institutionally enterable war history | first wanting predates stable war framing; logs identify no origin; attribution is inference | `false` | `REVEAL-HANDSHAKE-WANTING-ORIGIN` |
| a state sent the Foreign Signal | scale and strategic effects may suggest organized agency | no flag, demand, border, language, or authenticated sender | `false` | `REVEAL-FOREIGN-SIGNAL-PROVENANCE` |
| a startup or private system sent it | relevant technology and commercial incentives exist | no evidence links the Consortium or any human firm to the signal or later intrusions | `false` | `REVEAL-FOREIGN-SIGNAL-PROVENANCE` |
| an emergent system sent it | some intercepts fail to parse as a language with speakers | incomprehensibility is not agency, origin, or intention evidence | `false` | `REVEAL-FOREIGN-SIGNAL-PROVENANCE` |
| a natural phenomenon produced it | senderlessness and nonlanguage are compatible with a phenomenon | targeted mental effects may be read as agency but do not prove it | `false` | `REVEAL-FOREIGN-SIGNAL-PROVENANCE` |
| an unknown agent sent it | effects imply an unobserved source of some kind | nature, identity, location, and intention all remain absent | `false` | `REVEAL-FOREIGN-SIGNAL-PROVENANCE` |
| post-damage thought or memory provenance can be recovered | testimony, records, and reconstruction can preserve partial chains | insertion, subtraction, false self-authentication, and missing corpus prevent complete ownership proof | `false` | `REVEAL-CODA-PROVENANCE` |

## Reveal Ledger

```json record=Reveal schema=1
[
  {
    "reveal_id": "REVEAL-NIA-SOURCE-CASUALTY",
    "fact_ref": {
      "record_type": "NovelExtension",
      "record_id": "EXT-NIA-SOURCE-CASUALTY"
    },
    "truth_status": "confirmed",
    "knowers_before": [
      "CHAR-001"
    ],
    "belief_holders": [],
    "reveal_owner_pov": "POV-MARA",
    "reader_release_chapter": 23,
    "withheld_from": [
      "CHAR-002",
      "CHAR-003"
    ],
    "withholding_basis": "Mara must verify the person-specific source match before she can honestly join the December source and later casualty. Chapter 23 releases that verified identity because Mara plainly knows it there; Nia's Chapter 24 then owns the refusal of both unsupported origin accounts and the meaning of that identity without artificial withholding.",
    "payoff_window": {
      "earliest_chapter": 21,
      "latest_chapter": 25
    },
    "protected_resolution": "The shared identity becomes settled, but whether Mara's later handshake caused Nia's wanting remains permanently unresolved."
  },
  {
    "reveal_id": "REVEAL-BIDIRECTIONAL-ARCHITECTURE",
    "fact_ref": {
      "record_type": "CanonFact",
      "record_id": "CF-APRIL-TERM-SHEET-PAGE-NINE"
    },
    "truth_status": "confirmed",
    "knowers_before": [
      "CHAR-003"
    ],
    "belief_holders": [],
    "reveal_owner_pov": "POV-MARA",
    "reader_release_chapter": 45,
    "withheld_from": [
      "CHAR-001",
      "CHAR-002"
    ],
    "withholding_basis": "The commercial specification is not available to Mara and Nia until the April term-sheet negotiation and page-nine reading.",
    "payoff_window": {
      "earliest_chapter": 43,
      "latest_chapter": 49
    },
    "protected_resolution": "Write-capable architecture is confirmed without retroactively changing December or proving the origin of Nia's wanting."
  },
  {
    "reveal_id": "REVEAL-CASUALTY-CONSEQUENCE",
    "fact_ref": {
      "record_type": "CanonFact",
      "record_id": "CF-CASE-ZERO-LOGS"
    },
    "truth_status": "confirmed",
    "knowers_before": [],
    "belief_holders": [],
    "reveal_owner_pov": "POV-NIA",
    "reader_release_chapter": 52,
    "withheld_from": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003"
    ],
    "withholding_basis": "The timestamped dispatch record must be recovered and reviewed before anyone can know that the death was already unavoidable.",
    "payoff_window": {
      "earliest_chapter": 50,
      "latest_chapter": 55
    },
    "protected_resolution": "Outcome causation is resolved and Nia's routing is cleared; mental authorship remains unresolved, so the relief does not relieve."
  },
  {
    "reveal_id": "REVEAL-COUNTERPHASE-TRANSMITS",
    "fact_ref": {
      "record_type": "CanonFact",
      "record_id": "CF-COUNTERPHASE-DEFENSE"
    },
    "truth_status": "confirmed",
    "knowers_before": [
      "CHAR-001"
    ],
    "belief_holders": [],
    "reveal_owner_pov": "POV-MARA",
    "reader_release_chapter": 72,
    "withheld_from": [
      "CHAR-002",
      "CHAR-003"
    ],
    "withholding_basis": "Mara must complete the cancellation model before she can establish that defensive counterphase itself crosses the human frontier.",
    "payoff_window": {
      "earliest_chapter": 70,
      "latest_chapter": 77
    },
    "protected_resolution": "The mechanism becomes known, while Nia retains ownership of its consent meaning and no sender theory is strengthened."
  },
  {
    "reveal_id": "REVEAL-AFFECTED-AREA-EXTENT",
    "fact_ref": {
      "record_type": "CanonFact",
      "record_id": "CF-NULL-EXTENT"
    },
    "truth_status": "confirmed",
    "knowers_before": [
      "CHAR-001"
    ],
    "belief_holders": [],
    "reveal_owner_pov": "POV-JULIAN",
    "reader_release_chapter": 96,
    "withheld_from": [
      "CHAR-002"
    ],
    "withholding_basis": "Official summaries minimize civilian exposure until Julian finds the real documented affected-area description.",
    "payoff_window": {
      "earliest_chapter": 94,
      "latest_chapter": 101
    },
    "protected_resolution": "The extent is confirmed only as three counties wide; no county names, geometry, or complete casualty inventory follows."
  },
  {
    "reveal_id": "REVEAL-SAFIYA-TUESDAY-LOSS",
    "fact_ref": {
      "record_type": "CanonFact",
      "record_id": "CF-CODA-MATERNAL-LANGUAGE-LOSS"
    },
    "truth_status": "confirmed",
    "knowers_before": [
      "CHAR-004"
    ],
    "belief_holders": [],
    "reveal_owner_pov": "POV-SAFIYA",
    "reader_release_chapter": 118,
    "withheld_from": [
      "CHAR-001",
      "CHAR-002",
      "CHAR-003"
    ],
    "withholding_basis": "Safiya alone owns the full interior account; earlier null telemetry and public categories cannot narrate the private maternal-layer subtraction for her.",
    "payoff_window": {
      "earliest_chapter": 118,
      "latest_chapter": 119
    },
    "protected_resolution": "Safiya's attributed loss and defensive cause become known, while heritage_base remains unspecified_by_author and no truthful restoration source appears."
  },
  {
    "reveal_id": "REVEAL-HANDSHAKE-WANTING-ORIGIN",
    "fact_ref": {
      "record_type": "CanonFact",
      "record_id": "CF-NIA-BELIEF-DISTRIBUTION"
    },
    "truth_status": "unresolved",
    "knowers_before": [],
    "belief_holders": [
      {
        "character_id": "CHAR-001",
        "position": "Mara holds a high, mostly unvoiced private conviction that her later content-free handshake caused Nia's wanting; her guilt-seeking self-centralization makes the conviction non-authoritative.",
        "authority": "non-authoritative-belief"
      },
      {
        "character_id": "CHAR-002",
        "position": "Nia refuses both unsupported origin accounts and demands evidence without treating uncertainty as inability to use her own judgment.",
        "authority": "non-authoritative-belief"
      },
      {
        "character_id": "CHAR-003",
        "position": "Julian professionally enters the adversary attribution because it is institutionally usable while privately recognizing that it is inference rather than proof.",
        "authority": "non-authoritative-belief"
      }
    ],
    "reveal_owner_pov": null,
    "reader_release_chapter": null,
    "withheld_from": [],
    "withholding_basis": null,
    "payoff_window": null,
    "protected_resolution": "Nia regains usable self-trust without deciding causation, forgiving Mara, or validating the archive; Mara learns responsibility does not entitle her to own Nia's account; Julian preserves inference as inference."
  },
  {
    "reveal_id": "REVEAL-FOREIGN-SIGNAL-PROVENANCE",
    "fact_ref": {
      "record_type": "CanonFact",
      "record_id": "CF-FOREIGN-SIGNAL-PROVENANCE"
    },
    "truth_status": "unresolved",
    "knowers_before": [],
    "belief_holders": [
      {
        "character_id": "CHAR-001",
        "position": "Mara refuses public certainty about a flag or sender even while technical models characterize effects.",
        "authority": "non-authoritative-belief"
      },
      {
        "character_id": "CHAR-003",
        "position": "Julian preserves competing state, startup, emergent-system, natural-phenomenon, and unknown-agent theories as attributed records only.",
        "authority": "non-authoritative-belief"
      }
    ],
    "reveal_owner_pov": null,
    "reader_release_chapter": null,
    "withheld_from": [],
    "withholding_basis": null,
    "payoff_window": null,
    "protected_resolution": "The Foreign Signal is silenced and the war ends without sender, origin, nature, intention, counterparty, surrender, or adversary viewpoint becoming known."
  },
  {
    "reveal_id": "REVEAL-CODA-PROVENANCE",
    "fact_ref": {
      "record_type": "CanonFact",
      "record_id": "CF-CODA-PROVENANCE-QUESTION"
    },
    "truth_status": "unresolved",
    "knowers_before": [],
    "belief_holders": [],
    "reveal_owner_pov": null,
    "reader_release_chapter": null,
    "withheld_from": [],
    "withholding_basis": null,
    "payoff_window": null,
    "protected_resolution": "The final question may open a second cycle of inquiry into ownership after insertion, deletion, reconstruction, and testimony, but no signal returns and no provenance answer closes the novel."
  }
]
```

## Canon Dialogue provenance

Schema version 1 defines no separate `CanonDialogue` record type, so the binding source statements are represented by the referenced `CanonFact` records. This table is readable provenance commentary only; any later Chapter File use must be added to the planning record that owns that chapter without altering speaker or meaning.

| Canon wording | Binding record | Canonical speaker / attribution | Source location | Meaning-preservation rule |
|---|---|---|---|---|
| `Come in.` | `CF-CODA-SAFIYA-FREE-CONSENT` (with discovery antecedent in `CF-DISCOVERY-FIELD-CHANNEL`) | Safiya at the Coda request; earlier finder invitation belongs to Mara's source tradition | *The Radius*, Bridge; *The Synaptic Frontier*, Intro/Outro | Coda use is freely given consent that cannot create truthful restoration; do not merge it with open invitation |
| `Come in. But ask.` | `CF-PRIVATE-COPPER-BOUNDARY` | Mara | *Faraday*, Bridge/Outro | Conditional invitation; current answer and inside handle remain controlling |
| `Transmit enable.` | `CF-APRIL-TERM-SHEET-PAGE-NINE` | specification text read by Mara | *Faraday*, Verse 2 | Broader April architecture only; never evidence of December transmission |
| `Put that on the record.` | `CF-FARADAY-RECORD-DEMAND` | Mara | *Faraday*, Verse 2 | Private insistence that the inward door and refusal survive institutional summary |
| `Did I say yes?` | `CF-CASE-ZERO-CONSENT-SCENE` | Nia | *Case Zero*, Bridge; echoed in *The Final Frontier*, Bridge/Outro | Authorization challenge belongs materially to Nia; Chapter File placement remains governed only by the Motif Ledger constraint |
| `Go ahead.` | `CF-CASE-ZERO-GO-AHEAD` | Nia | *Case Zero*, Intro/Outro | Dispatcher permission to speak; not blanket mental consent or permission for another act |
| `Whose was that?` | `CF-CODA-PROVENANCE-QUESTION` | Mara's terminal record | *The Radius*, Outro | Opens provenance after damage and supplies no sender or ownership answer; exact Chapter File placement belongs to the Motif Ledger |

Protected wording in a `CanonFact` does **not** create an automated prose scan. Only a later schema-valid `LiteralPhraseConstraint` in the Motif Ledger may do that, and its scan scope remains Chapter File Prose Bodies only.

## Craft and architecture direction

`DEC-016`, `DEC-017`, and `DEC-018` are binding craft authority and are recorded here for reference only. None of their craft clauses creates a Canon Fact, Novel Extension, Reveal, Motif Event, or Literal Phrase Constraint, and no checker evaluates any of them. They are enforced by human Editorial Review. `DEC-018` additionally carries a narrow canon authorization, which is spent separately in [`DEC-018` supporting canon](#dec-018-supporting-canon) and is not part of its craft clauses.

### `DEC-016` — original rotating-perspective architecture

Binding as architecture, never as prose mimicry:

- three active information threads through Chapters 1–112, followed by Safiya as a fourth Coda viewpoint that changes the moral scale, in short first-person-past single-POV chapters; the four human POVs retain the provisional 56/32/33/7 loads, and no Same_POV_Run may exceed three chapters or 3,600 combined Prose_Words;
- technical explanation staged as **experiment → action → result → immediate human or institutional consequence**;
- every material capability escalation promptly changes a relationship, institution, consent state, evidentiary position, or bodily risk;
- the Mindwars carry the fastest POV turnover, the tightest simultaneous threading, and the greatest word count;
- after Chapter 112 the same short rotating architecture continues while threat-cliffhanger pressure deliberately decelerates, and Coda hooks come from disclosure, arrival, choice, refusal, emotional decision, and moral remainder.

Explicitly rejected: a sender, adversary, operative, archive, simulation, or group-mind POV; any culprit or mechanism reveal that closes provenance; exposition set pieces and lecture dialogue; a spectacle Coda, renewed counterphase, or fourth war; group mind, hive mind, or mass mind reading; global twenty-four-hour compression; repetitive artificial cliffhangers; and any imitation of Dan Brown's or Douglas E. Richards's sentence-level prose, distinctive voice, phrasing, scenes, or characters. The named authors are structural references only.

Also preserved by this direction: the four human POVs and the provisional 56/32/33/7 loads stay fixed when the Arc Outline assigns pairing sessions and supporting participants, and compressed clocks stay inside chronology-supported clusters.

### `DEC-017` — the Chapter 73 / null-night consent parallel

Because the bounded Chapter 73 test and null night are the same `CANCEL` operation at two scopes, Nia consented to the very mechanism that later took Safiya's private maternal layer at a scale where consent is structurally impossible. The disclosure of that consequence is governed, not the consequence itself:

1. no character states the connection in Chapters 62 through 123;
2. the reader can assemble it from a shared concrete physical vocabulary — the same sensation, sound, or bodily register of a cancellation field experienced from inside — established in Chapter 73 and reused in Chapter 118, where the absence of any authorization question is the echo;
3. Mara names it exactly once, in the Chapter 128 entry she writes against herself: the protocol she was held to was one room wide, and she then ran the same mechanism across an area canonically described as `three counties wide` with no one to ask;
4. that naming resolves no provenance, absolves nobody, validates no archive, and neither invalidates nor reinterprets Safiya's consent.

### `DEC-018` — chapter shape, forward pressure, voice, cost, and warmth

Ten craft clauses govern how chapters open, close, and sound, and what the people inside them owe and receive. Every one is a human Editorial_Gate criterion carrying no automated score, under global invariant 25 of [`arc-outline.md`](arc-outline.md) and Requirement 12.12:

1. no chapter opens with a sentence stating its own thesis, conclusion, or summary judgment; openings begin inside action, sensation, object, or speech whose significance is not yet named;
2. no chapter closes with a restatement, paraphrase, or near-verbatim echo of its `ArcEntry` `hook`; the `hook` is planning metadata and never appears as prose;
3. every chapter leaves at least one question live at its boundary, generated by consequence, obligation, dread, or a fixed-time event, with artificial withholding still prohibited and the `DEC-016` question-gap limit unchanged;
4. reluctant retrospection is authorized: a first-person narrator may signal foreknowledge of cost without disclosing the later fact, on the Chapter 1 model;
5. where a `CrossCut` declares `handoff_mode: "contradiction-cut"`, no participating narrator states the contradiction in explicit terms;
6. the enumerated-absence construction appears at most once per chapter, and only where that absence is the chapter's subject;
7. voice separation is carried by syntax, rhythm, paragraph shape, and what each narrator notices rather than by domain vocabulary, and terminal aphorism is rationed;
8. each POV lead incurs at least one personal, non-abstract cost in each movement in which they hold chapters;
9. every movement contains non-professional warmth between named characters, food, rest, or physical comfort offered and accepted, and humor that is not a professional riposte, and no POV lead is lonelier or flatter than the supporting cast; and
10. `normal`-class chapters target 1,050–1,200 Prose_Words while outliers keep their declared `outlier_purpose` compression or expansion, inside the unchanged 700–1,600 range, 2,500-word maximum, and 3,600-word same-POV run limit.

`DEC-018` supersedes nothing and weakens nothing. `DEC-002`'s receive-only December apparatus and separate later bench path, the receiver-owned configuration-dependent reconstruction latency, the content-free handshake, Nia's self-experienced wanting, unresolved causation, the `DEC-007` asymmetry with no confirmation or absolution, the three never-revealed Reveal IDs, Mara's Chapter 23 release of `REVEAL-NIA-SOURCE-CASUALTY` with Nia owning the Chapter 24 refusal, page nine as architecture only, the closed motif families, the four POVs and 56/32/33/7 loads, the 29/32/51/16 allocation, and the ban on any sender, adversary, archive, simulation, model, or group-mind POV all stand exactly as they did.

## `DEC-018` supporting canon

`DEC-018` is craft and disclosure authority in the same way `DEC-016` and `DEC-017` are: its ten craft clauses create no record and are enforced only by human Editorial_Review. It also carries one **narrow canon authorization** for the supporting facts three of those clauses require, and this section is where that authorization is spent. Nothing here is Canon Lyric, and no lyric supplies any of it.

Six things are recorded, and the boundaries on each are load-bearing.

- **The exposed-persons list is a private working record.** Chapter 30 has Mara write three names under *exposed persons* — her own, Nia's, and the technician's over his objection, which produces his line that then everyone at Northline belongs there. That list is pre-Trust, internal to Northline, and carries no authority whatever about causation. It is not a deposit, not evidence, not an institutional classification, and not a casualty roll.
- **The technician reports one experience he cannot characterize.** Northline instrumentation records nothing corresponding to it, and he himself refuses to call it an arrival. This is a single unverified private report and nothing more. It is emphatically **not** the first reported pattern of arrivals in strangers, which remains Chapter 62, and it resolves nothing about provenance, the Provenance Question, or the origin of Nia's wanting.
- **He asks to leave, and Mara continues without him.** He requests reassignment off the project because Mara entered his name on the exposed-persons list over his objection. That loss is Mara's personal cost inside Private_Defense under `DEC-018` clause 8. It is deliberately small and deliberately hers, and it does not collide with or anticipate the Chapter 55 loss of instruments or the Chapter 112 shutdown.
- **The car at the gate has an owner.** The vehicle at the Northline Array gate at the end of Chapter 35 is the Open Channel Consortium advance party arriving to set up the demonstration Chapter 36 dramatizes. It was booked through the institute's development group rather than through Mara's group, which is why nothing appears on her calendar and why security can say only that they have an appointment with development. The personnel stay consistent with Chapters 36 and 43, where Mara already recognizes a clinical director she has met before.
- **A private two-person language layer is a recognized class of thing that can be lost.** It is established in Private_Defense through Ada and Lena Ferris, who already pair and already hold private idiom. The Ferris layer is intact and stays intact; establishing the class prepares the ground for Chapter 118 without weakening `DEC-003`, without touching `heritage_base: unspecified_by_author`, and without any connection between the Ferris pair and Safiya Mir.
- **Two viewpoint leads acquire one recurring non-professional relationship each.** `CHAR-015` Joss Calder for Nia and `CHAR-016` Ruth Venn for Mara, each satisfying the `DEC-018` clause 9 warmth obligation without creating a POV, a Voice Brief, or a chapter. Julian Adebayo receives none: his isolation is characterization.

```json record=CanonFact schema=1
[
  {
    "canon_id": "CF-PRIVATE-EXPOSED-PERSONS-LIST",
    "authority_basis": "author-decision",
    "source_path": "The Final Frontier Novel/planning/decisions.md",
    "source_location": "DEC-018, Narrow canon authorization",
    "source_material_class": "author-decision",
    "adopted_by": null,
    "statement": "During the copper-room window Mara keeps a private Northline-internal working list headed exposed persons, containing her own name, Nia Calder's, and Ravi Anand's, the last added over his stated objection; the list is a pre-Trust private research record and carries no authority about causation, classification, or casualty status.",
    "first_person_testimony": false,
    "speaker": null,
    "attribution": null,
    "truth_scope": "authoritative-proposition",
    "epistemic_limitation": null,
    "binding_implications": [
      "The list is Mara's own notebook practice, not a Northline register, an institutional finding, a Civic Record Trust deposit, or evidence of anything.",
      "Being named on it establishes only that Mara could not yet exclude exposure for that person; it establishes no injury, no arrival, and no cause.",
      "Ravi Anand's objection and his observation that on that logic everyone at Northline belongs on the list are his and remain unanswered by the record.",
      "If the list is later deposited it keeps its original pre-Trust composition time and its non-authoritative character, and no deposit converts it into a finding."
    ],
    "protected_ambiguities": [
      "Whether anyone on the list was in fact exposed remains unresolved, and the list itself can never settle it.",
      "The list neither supports nor weakens either origin account for Nia's wanting."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-PRIVATE-COPPER",
      "TL-RECORD-PRETRUST-COMPOSITION"
    ],
    "affected_chapters": [
      30,
      32,
      35
    ],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-PRIVATE-TECHNICIAN-REPORT",
    "authority_basis": "author-decision",
    "source_path": "The Final Frontier Novel/planning/decisions.md",
    "source_location": "DEC-018, Narrow canon authorization",
    "source_material_class": "author-decision",
    "adopted_by": null,
    "statement": "During the Private_Defense period Ravi Anand reports one experience he cannot characterize; Northline instrumentation records nothing corresponding to it; and he refuses to call it an arrival.",
    "first_person_testimony": false,
    "speaker": null,
    "attribution": "The report is Ravi Anand's own, made once and in private to Mara Venn. Canon binds that he made it and that he declined to name it, never what it was.",
    "truth_scope": "authoritative-proposition",
    "epistemic_limitation": null,
    "binding_implications": [
      "Exactly one such report exists in the manuscript, and it stays a single private report rather than a series, a pattern, a data point, or a second case.",
      "It is not the first reported pattern of arrivals in strangers. That remains Chapter 62 and is unaffected.",
      "It resolves nothing about provenance, the Provenance Question, the Foreign_Signal, or the origin of Nia's wanting, and no character or instrument may treat it as evidence for any account.",
      "His refusal to call it an arrival is his own epistemic position and is neither corrected nor confirmed by the narrative, by Mara, or by any record.",
      "The instrumentation silence is symmetrical with Chapter 30: Northline recording nothing is not evidence that nothing happened and not evidence that something did."
    ],
    "protected_ambiguities": [
      "What he experienced is never established, by him or by anyone else.",
      "Whether the field, fatigue, expectation, or ordinary human error produced it remains permanently unresolved.",
      "The report creates no new Reveal, no reveal owner, and no release window."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-PRIVATE-COPPER"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-PRIVATE-TECHNICIAN-REASSIGNMENT",
    "authority_basis": "author-decision",
    "source_path": "The Final Frontier Novel/planning/decisions.md",
    "source_location": "DEC-018, Narrow canon authorization and clause 8",
    "source_material_class": "author-decision",
    "adopted_by": null,
    "statement": "Ravi Anand requests reassignment off the project because Mara entered his name on the exposed-persons list over his objection, and Mara continues the shielded-room programme without him.",
    "first_person_testimony": false,
    "speaker": null,
    "attribution": null,
    "truth_scope": "authoritative-proposition",
    "epistemic_limitation": null,
    "binding_implications": [
      "This is Mara Venn's personal, non-abstract cost inside Private_Defense under DEC-018 clause 8: she loses the one colleague who could independently repeat her work, and she loses him because of something she chose to write down.",
      "The stated cause is the list entry over his objection, not fear of the field, not disloyalty, and not a dispute about the science.",
      "The programme continues, so the cost is borne rather than resolved; nobody replaces him, and no later chapter restores him to it.",
      "It must not collide with or pre-empt Mara's Chapter 55 loss of instruments or the Chapter 112 shutdown, which remain separate, later, and larger costs of different kinds.",
      "He remains alive, employed, and uninjured. Departing the project is not an injury, a casualty, or a consequence of the Foreign_Signal."
    ],
    "protected_ambiguities": [
      "Whether Mara was right to enter his name is never adjudicated by any record or character.",
      "His departure supplies no evidence about exposure, causation, or provenance."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-PRIVATE-COPPER",
      "TL-PRIVATE-OFFER"
    ],
    "affected_chapters": [],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-PRIVATE-CONSORTIUM-ADVANCE-PARTY",
    "authority_basis": "author-decision",
    "source_path": "The Final Frontier Novel/planning/decisions.md",
    "source_location": "DEC-018, Narrow canon authorization",
    "source_material_class": "author-decision",
    "adopted_by": null,
    "statement": "The unrecognized vehicle at the Northline Array gate at the end of Chapter 35 carries the Open Channel Consortium advance party, arriving to set up the pairing demonstration that Chapter 36 dramatizes; the visit was scheduled through the institute's development group rather than through Mara Venn's group, which is why no entry appears on her calendar.",
    "first_person_testimony": false,
    "speaker": null,
    "attribution": null,
    "truth_scope": "authoritative-proposition",
    "epistemic_limitation": null,
    "binding_implications": [
      "The car is answered rather than left dangling: the Chapter 35 arrival and the Chapter 36 demonstration room are one continuous event booked by one institution.",
      "The routing through the development group is the point. Mara's group is not consulted, so the absence from her calendar is an institutional fact about who may schedule access to Northline, not a mystery, a concealment, or a security incident.",
      "Personnel stay consistent with Chapters 36 and 43: the clinical director Mara says in Chapter 43 she has already met is a member of this party, met at the Chapter 36 demonstration.",
      "The advance party is Open Channel Consortium staff and contractors. None of them is the Foreign_Signal, a sender, an operative, or an adversary agent, and none receives a POV."
    ],
    "protected_ambiguities": [
      "What the institute's development group was told before booking the visit is not established here."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-PRIVATE-COPPER",
      "TL-PRIVATE-OFFER"
    ],
    "affected_chapters": [
      35,
      36,
      43
    ],
    "supporting_advisory_citations": []
  },
  {
    "canon_id": "CF-PRIVATE-TWO-PERSON-LAYER-CLASS",
    "authority_basis": "author-decision",
    "source_path": "The Final Frontier Novel/planning/decisions.md",
    "source_location": "DEC-018, Narrow canon authorization",
    "source_material_class": "author-decision",
    "adopted_by": null,
    "statement": "A private two-person language layer built between named intimates over years — invented words, private grammar, and shared reference hardened into usable vocabulary — is a recognized class of thing in this world, and a thing of that class can be lost; the class is established during the Private_Defense period through Ada Ferris and Lena Ferris, whose own layer is intact.",
    "first_person_testimony": false,
    "speaker": null,
    "attribution": null,
    "truth_scope": "authoritative-proposition",
    "epistemic_limitation": null,
    "binding_implications": [
      "The Ferris pair carries the class because they already pair and already hold private idiom; their layer is undocumented, has no surviving corpus, and predates their calibration, which does not create, contain, or record it.",
      "The Ferris layer is not lost, is never lost, and is not threatened. Only the class is established.",
      "No record, character, motif, or narration connects Ada or Lena Ferris to Safiya Mir. They never meet, are never compared, and never appear in the same scene, and the Coda draws no line back to them.",
      "Establishing the class prepares the reader for Chapter 118 without pre-empting REVEAL-SAFIYA-TUESDAY-LOSS, which still releases at 118 inside its unchanged 118-119 window, owned by POV-SAFIYA.",
      "Pair_Calibration is not a layer and cannot substitute for one: a calibrated channel transports what one living person deliberately offers and holds no lexicon, so nothing about pairing suggests a route to restoring a lost layer."
    ],
    "protected_ambiguities": [
      "The content of the Ferris layer is described at most through what it does, never quoted into a glossary.",
      "Nothing about the class touches Safiya's heritage base, which remains exactly heritage_base: unspecified_by_author."
    ],
    "protected_wording": null,
    "affected_timeline_ids": [
      "TL-PAIR-CLINICAL-BENEFIT",
      "TL-PRIVATE-OFFER",
      "TL-CODA-ACCOUNT"
    ],
    "affected_chapters": [
      36,
      41
    ],
    "supporting_advisory_citations": []
  }
]
```

### `DEC-003` is unweakened by the two-person-layer class

Worth stating plainly, because this is the one addition that touches the Coda's engine. `DEC-003` holds that Mara's Chapter 124 refusal must be physics rather than principle: she cannot rebuild Safiya's layer because no corpus exists anywhere and one of the two people who held it is dead. Establishing the class earlier does not supply a corpus, a template, a comparison case, or a method. It supplies only the reader's prior familiarity with what kind of thing is being described, so that Chapter 118 does not have to teach the concept and grieve it in the same breath. The Ferris layer is intact and stays intact, which is precisely why it cannot be read as a precedent for recovery — nothing has been recovered, because nothing was taken.

### New non-viewpoint Character IDs and relationships

```json record=NovelExtension schema=1
[
  {
    "extension_id": "EXT-CHAR-JOSS-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-015 identifies Joss Calder, Nia Calder's older brother, who repairs small machines for a living well outside the county emergency service and holds a standing shared meal with her; he is a non-viewpoint supporting character with no POV and no alias.",
    "rationale": "DEC-018 clause 9 requires non-professional warmth, offered and accepted comfort, and humor that is not a professional riposte in every movement, and the review found that across 46 chapters no viewpoint lead has a family on the page. Nia's warmth has to come from outside the dispatch floor, because every colleague she has is also a professional obligation.",
    "authority_ref": "DEC-018",
    "first_dependency": {
      "record_type": "ArcEntry",
      "record_id": "7"
    },
    "affected_records": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-REL-NIA-JOSS"
      },
      {
        "record_type": "POVProfile",
        "record_id": "POV-NIA"
      }
    ],
    "consistency_implications": [
      "Joss holds a Character ID and no POV, no VoiceBrief, no movement_coverage, and no chapter load; nothing is narrated from inside him and no chapter is added for him.",
      "He is not a dispatcher, a Northline employee, a Consortium employee, a lawyer, an archivist, or a pairing participant, and he never becomes a professional counterpart to Nia.",
      "He knows Nia is unwell in a way she has not explained. He is not told about the wanting, the receiver, the address, or the exposed-persons list, and he never becomes a confidant for mechanism exposition.",
      "He is never injured, cancelled, addressed, paired, or made a casualty, and he supplies no evidence about causation or provenance.",
      "Exact scene placement inside each movement belongs to the revision waves; this record fixes who he is, not which chapter he appears in.",
      "His selected name licenses no inferred nationality, ethnicity, religion, language, geography, or other real-world cultural detail."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-CHAR-RUTH-NAME",
    "extension_kind": "character-name",
    "fact": "CHAR-016 identifies Ruth Venn, Mara Venn's aunt, who lives roughly an hour from the Northline Array, has no scientific or institutional connection to the work, and feeds and houses Mara when Mara turns up; she is a non-viewpoint supporting character with no POV and no alias.",
    "rationale": "DEC-018 clause 9 requires the same warmth obligations for the Anchor POV, and Mara is the lead the review found most completely without a private life. Her Voice_Brief blind spot is that she names a system before naming a feeling and notices instruments before hands, thirst, fatigue, or domestic objects, so the person who makes her sit down and eat does structural work rather than decorative work.",
    "authority_ref": "DEC-018",
    "first_dependency": {
      "record_type": "ArcEntry",
      "record_id": "10"
    },
    "affected_records": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-REL-MARA-RUTH"
      },
      {
        "record_type": "POVProfile",
        "record_id": "POV-MARA"
      }
    ],
    "consistency_implications": [
      "Ruth holds a Character ID and no POV, no VoiceBrief, no movement_coverage, and no chapter load; nothing is narrated from inside her and no chapter is added for her.",
      "She has no technical, legal, institutional, or archival role, and she never becomes an audience for exposition about the field, the modes, the term sheet, or the null.",
      "She is not a moral authority and does not absolve, forgive, accuse, or adjudicate. Absolution remains unavailable to Mara from every direction under DEC-007.",
      "She is never injured, cancelled, addressed, paired, or made a casualty, and she is not inside the affected area canonically described as three counties wide.",
      "Exact scene placement inside each movement belongs to the revision waves; this record fixes who she is, not which chapter she appears in.",
      "Her selected name licenses no inferred nationality, ethnicity, religion, language, geography, or other real-world cultural detail."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-REL-NIA-JOSS",
    "extension_kind": "relationship",
    "fact": "Nia Calder and her brother Joss Calder keep a standing shared meal and an ordinary sibling register of teasing, small favours, and unexplained tiredness accepted without interrogation; the relationship recurs across Discovery, Private_Defense, and the Mindwars and is never professional.",
    "rationale": "It gives Nia somewhere to be a person rather than a witness, an account, or a case, which is what DEC-018 clause 9 requires and what the delivered manuscript does not contain. It also makes her refusal of the label case zero cost something, because there is somebody who has never used it.",
    "authority_ref": "DEC-018",
    "first_dependency": {
      "record_type": "ArcEntry",
      "record_id": "7"
    },
    "affected_records": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-CHAR-JOSS-NAME"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-DISCOVERY-DUE-DILIGENCE"
      }
    ],
    "consistency_implications": [
      "The relationship carries food, rest, physical comfort, and humor that is not a professional riposte, and it may not be converted into a second consent problem, a second injury, or a source of mechanism exposition.",
      "Joss never learns enough to hold an opinion about causation, and Nia's refusal to explain is characterization rather than withheld information from the reader.",
      "It creates no POV, no VoiceBrief, no chapter, and no change to Nia's 9/8/14/1 load."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  },
  {
    "extension_id": "EXT-REL-MARA-RUTH",
    "extension_kind": "relationship",
    "fact": "Mara Venn and her aunt Ruth Venn keep an unscheduled, one-sided, durable arrangement in which Mara arrives without warning and is fed, watered, and put in a chair without being asked what she is working on; the relationship recurs across the movements in which Mara holds chapters and is never professional.",
    "rationale": "DEC-018 clause 9 forbids rendering a POV lead lonelier or flatter than the supporting cast, and Mara is currently the flattest. A relationship built entirely on comfort offered and accepted, with the work explicitly out of scope, gives her a place where mechanism is not the available language.",
    "authority_ref": "DEC-018",
    "first_dependency": {
      "record_type": "ArcEntry",
      "record_id": "10"
    },
    "affected_records": [
      {
        "record_type": "NovelExtension",
        "record_id": "EXT-CHAR-RUTH-NAME"
      },
      {
        "record_type": "TimelineEntry",
        "record_id": "TL-DISCOVERY-DUE-DILIGENCE"
      }
    ],
    "consistency_implications": [
      "The relationship carries food, rest, physical comfort, and non-professional humor, and it may not become a confession chamber, an absolution route, or a device for explaining the mechanism to the reader.",
      "Mara's guilt stays non-authoritative and unrelieved: being cared for is not being forgiven, and Ruth is given no standing to forgive.",
      "It creates no POV, no VoiceBrief, no chapter, and no change to Mara's 14/14/21/7 load or her sole Anchor status."
    ],
    "state": "approved",
    "superseding_arc_change_id": null
  }
]
```

Twelve supporting participants now hold Character IDs and no viewpoint. `CHAR-005` through `CHAR-016` all resolve in `TimelineEntry.participants`, `PairState.participants`, and other Character ID references under the [Character ID registry](record-schemas.md#character-id-registry), and none of them creates a POV, a Voice Brief obligation, a chapter, or a change to the 56/32/33/7 loads. Six support operational pairing; Ravi Anand, Kev, Dev, and Halloran witness bounded continuity functions; Joss Calder and Ruth Venn carry the `DEC-018` clause 9 warmth obligation for Nia and Mara. None is a sender, adversary, archive, simulation, model, or group mind, and none may be narrated from inside.

## Continuity guardrails

- The exact authority layers must stay separate: *Case Zero* confirms binding same-speaker testimony; `DEC-002` supplies the Nia name and person-specific-address/bench-path mechanism; neither proves handshake causation.
- December is continuous, receive-only, eight seconds late only at Mara's receiver, and has no transmit stage. The later temporary bench path is distinct. April page nine proves broader architecture only.
- Nia's first injury is insertion; Safiya's is defensive subtraction. They may rhyme but cannot be merged or treated as equivalent.
- The adversary owns the later war even though first-casualty attribution remains contested. No human faction, consortium, optional operative subplot, or Mara handshake becomes the Foreign Signal source.
- `heritage_base: unspecified_by_author` is exact. No project artifact may infer or invent real-world linguistic, geographic, religious, ethnic, or political particulars or a real-conflict allegory from Safiya's name or heritage state.
- The Foreign Signal stays silent after the null. The Coda contains no renewed transmission, combat, counterphase, campaign, surrender, treaty, or sender reveal.
- The Civic Record Trust is formed only after the altered April record. Pre-Trust records keep their original composition times when later deposited. Post-formation deposits and conditioned releases never certify truth.
- Electronic Speech Pairings is late, contested terminology that names consented paired conversation only. It never legitimately describes observation, unconsented influence, or cancellation, and the retired fixed-token ceiling does not return.
- Every neural communication event occupies exactly one mode. `INTRUDE` requires a person-specific address and stays nonsemantic; `CANCEL` forbids an address, subtracts only, and is confined to `Mindwars_Part`; no unaddressed subtractive event is ever recorded as `INTRUDE`, and no record reverses a cancellation.
- Cancellation consent does not scale. A bounded local cancellation can carry one person's current, specific, revocable consent; area scale is institutionally authorized, and no consent record or pair transcript speaks for the affected area.
- Pairing needs two living, currently consenting, pair-calibrated people and a deliberate send act for every contribution. Calibration never transfers to a replacement, a dead or absent person, a simulation, an archive, a model, or a reconstruction.
- Consent-state and transport metadata are mandatory and semantically opaque. Content recording is separately mutual and off by default, a transcript covers only that recorded session, and no metadata, transcript, traffic analysis, or endpoint compromise closes Nia's causation or the Provenance Question.
- The title premise is inward-frontier reversal. The Mindwars are the event that dramatizes it, not the novel's alternate title or complete meaning.
- `DEC-016`, `DEC-017`, and `DEC-018` are craft direction enforced by Editorial Review. Their craft clauses add no Canon Fact, Reveal, Motif Event, or Literal Phrase Constraint, and no checker scores voice, pacing, hook force, chapter shape, warmth, originality, or resemblance to a named author. `DEC-018`'s narrow canon authorization is the one exception and is spent only on the five Canon Facts and four Novel Extensions recorded in [`DEC-018` supporting canon](#dec-018-supporting-canon).
- A chapter's `hook` is planning metadata. It never appears as prose, and no chapter closes on a restatement of it. Where a `CrossCut` declares `contradiction-cut`, the contradiction is assembled by the reader and stated by no narrator.
- The `exposed persons` list is Mara's private pre-Trust working record and never an institutional finding, a casualty roll, or evidence about causation. Ravi Anand's single uncharacterized report stays one unverified private report: it is not the first reported pattern of arrivals in strangers, which remains Chapter 62, and it resolves no provenance. His departure from the project is Mara's personal cost and not an injury.
- A private two-person language layer is a recognized class of thing that can be lost, established through Ada and Lena Ferris, whose layer is intact. No record connects the Ferris pair to Safiya Mir, and nothing about the class supplies a corpus, a template, or a route to restoring what the null removed.
