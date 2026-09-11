# Motif Ledger

Schema version: **1**  
Status: **provisional planning reference; not an Approved Baseline**  
Authority through: **DEC-017**  
Amended: **2026-09-12** — authority advanced from `DEC-014` to `DEC-017`; added the readable event summary required by Requirement 7.1, the chapter index that Chapter Headers and Arc Entries must match under Requirement 7.2, the declared machine-readable Final_Passage bounds, the protected-wording/scan boundary carried from the Canon Bible, and the `DEC-017` rider. No Motif_Event was added, moved, or retyped, and no third Literal_Phrase_Constraint was created.  
Authority: Requirement 7 (7.1 through 7.18), Task 4.5, the design Movement-Level Motif Map, the design Ending Design sequence, and binding author decisions through `DEC-017`

This ledger records planned dramatic events rather than keyword occurrences. A motif that persists through one sustained scene and performs one function is one `MotifEvent`; an Incidental_Mention with no planned dramatic function is not an event and never enters a count. Machine-readable values live only in the typed fenced JSON blocks below, governed by [`record-schemas.md`](record-schemas.md). Every table and paragraph outside those fences is readable commentary with no record value; a checker must never infer, repair, or override a record from it.

No Canon Facts, Novel Extensions, Timeline Entries, Arc Entries, Chapter Headers, POV Profiles, Voice Briefs, Reveals, Baselines, Arc Changes, Editorial Findings, or Gate Results are created here.

## Closed family mappings

| Family | Event IDs | Count | Closure rule |
|---|---|---:|---|
| Spectrum → wire → voice/air | `MOT-CHAIN-01..03` | 3 | Exactly Discovery spectrum-to-bone, Private Defense wire-to-bone, and Coda voice-through-air. Mindwars counterphase — defenders transmitting too — is connective context, **not** a fourth chain event. |
| Copper / quiet | `MOT-COPPER-01..03` | 3 | Exactly Private Defense private boundary, Mindwars imperfect collective defense, and Coda retained protection that cannot supply the needed remedy. Discovery copper references are unledgered foreshadowing, **not** a fourth event. |
| Come in | `MOT-COME-01..04` | 4 | Open invitation, conditional invitation, entry after freely given consent, and consent that cannot produce truthful restoration. |
| Knock / wait | `MOT-KNOCK-01..03` | 3 | Mindwars security protocol, the visitor's compliant arrival spanning Chapters 116–117 as **one** event, and the Anchor_POV's outward obligation. |
| Kettle | `MOT-KETTLE-01..02` | 2 | Exactly two Coda events, in Chapters 118 and 124 only. |
| Silence has a radius | `MOT-RADIUS-01..02` | 2 | Mindwars admission of defensive cost, then the Coda's central accounting. |
| Record progression | `MOT-RECORD-01..03` | 3 | Exactly three events: private insistence, deposition into the war's history, and an entry against the Anchor_POV. |
| Authorization question | `MOT-YES-01` | 1 | One Mindwars event carrying `LPC-DID-I-SAY-YES`. |
| Provenance question | `MOT-WHOSE-01` | 1 | One terminal Coda event carrying `LPC-WHOSE-WAS-THAT`; both in-passage occurrences comprise that single event. |
| **Total** | — | **22** | — |

Movement distribution of the 22 events: Discovery 2, Private Defense 4, Mindwars 6, Aftermath/Coda 10.

A fourth chain event, a fourth copper event, a third kettle event, a fourth Record_Progression event, or any other family extension becomes valid only when a later `ArcChange` assigns a distinct dramatic function, issues a new unreused stable ID, and synchronizes this ledger, the Arc Outline, and every affected Chapter Header in the same change. Until then those additions are objective violations, not editorial preferences.

## Event index by chapter

Every Chapter Header and Arc Entry for a chapter below must list exactly the IDs in its row, and no chapter absent from this table may list a Motif_Event ID.

| Chapter | Movement | Motif_Event IDs |
|---:|---|---|
| 13 | Discovery | `MOT-CHAIN-01` |
| 16 | Discovery | `MOT-COME-01` |
| 31 | Private Defense | `MOT-COPPER-01` |
| 45 | Private Defense | `MOT-CHAIN-02` |
| 51 | Private Defense | `MOT-RECORD-01` |
| 61 | Private Defense | `MOT-COME-02` |
| 70 | Mindwars | `MOT-COPPER-02` |
| 73 | Mindwars | `MOT-KNOCK-01`, `MOT-YES-01` |
| 74 | Mindwars | `MOT-COME-03` |
| 101 | Mindwars | `MOT-RADIUS-01` |
| 109 | Mindwars | `MOT-RECORD-02` |
| 116 | Coda | `MOT-KNOCK-02` |
| 117 | Coda | `MOT-KNOCK-02` |
| 118 | Coda | `MOT-KETTLE-01` |
| 120 | Coda | `MOT-RADIUS-02` |
| 124 | Coda | `MOT-COPPER-03`, `MOT-COME-04`, `MOT-KETTLE-02` |
| 127 | Coda | `MOT-CHAIN-03` |
| 128 | Coda | `MOT-KNOCK-03`, `MOT-RECORD-03`, `MOT-WHOSE-01` |

`MOT-KNOCK-02` is one event listed by both Chapters 116 and 117: the three unhurried knocks heard from Safiya's side and then from Mara's side of one threshold. Two chapters listing it is required agreement, not duplication.

The Chapter 124 header fixture in [`record-schemas.md`](record-schemas.md) shows two IDs because schema examples carry no continuity authority. The authoritative Chapter 124 set is the three IDs above.

## Readable event summary

Columns restate the fenced records for human review. In the records themselves an absent literal constraint is JSON `null` and an empty change history is `[]`; the word `none` below is commentary and is never a stored value.

| ID | Family | Dramatic function in one line | Movement | Planned ch. | Participating ch. | Mode | Literal constraint | ArcChange history |
|---|---|---|---|---:|---|---|---|---|
| `MOT-CHAIN-01` | spectrum / wire / voice | Spectrum reaches bone and proves a living mind occupies the channel. | discovery_part | 13 | 13 | image | none | none |
| `MOT-CHAIN-02` | spectrum / wire / voice | Wire reaches bone; page nine exposes bidirectionality as architectural danger. | private_defense_part | 45 | 45 | image | none | none |
| `MOT-CHAIN-03` | spectrum / wire / voice | Ordinary voice crosses air into a consenting ear instead of machine restoration. | aftermath_coda | 127 | 127 | action | none | none |
| `MOT-COPPER-01` | copper / quiet | Copper builds a private boundary whose first quiet is relief and proof of permeability. | private_defense_part | 31 | 31 | image | none | none |
| `MOT-COPPER-02` | copper / quiet | Collective copper buys time and stays an imperfect answer. | mindwars_part | 70 | 70 | image | none | none |
| `MOT-COPPER-03` | copper / quiet | Retained protection still holds and still cannot supply Safiya's remedy. | aftermath_coda | 124 | 124 | image | none | none |
| `MOT-COME-01` | come in | Content-free open invitation exposes wonder without an adequate boundary. | discovery_part | 16 | 16 | adapted | none | none |
| `MOT-COME-02` | come in | Invitation becomes conditional: ask, and leave the handle inside. | private_defense_part | 61 | 61 | scene-structure | none | none |
| `MOT-COME-03` | come in | Protective entry follows freely given, current, specific, revocable consent. | mindwars_part | 74 | 74 | action | none | none |
| `MOT-COME-04` | come in | Consent removes the authorization objection and still cannot create truthful restoration. | aftermath_coda | 124 | 124 | action | none | none |
| `MOT-KNOCK-01` | knock / wait | Security challenge becomes knock, then wait for the addressed person's answer. | mindwars_part | 73 | 73 | action | none | none |
| `MOT-KNOCK-02` | knock / wait | The visitor follows the threshold protocol exactly and is guaranteed no remedy. | aftermath_coda | 116 | 116, 117 | action | none | none |
| `MOT-KNOCK-03` | knock / wait | Private accounting becomes outward obligation: go, knock, wait. | aftermath_coda | 128 | 128 | action | none | none |
| `MOT-KETTLE-01` | kettle | The visitor's account of the null anchors in an ordinary Tuesday. | aftermath_coda | 118 | 118 | image | none | none |
| `MOT-KETTLE-02` | kettle | The relay goes off and the kettle goes on as the available human response. | aftermath_coda | 124 | 124 | action | none | none |
| `MOT-RADIUS-01` | silence has a radius | Defensive reach is admitted as civilian cost, never a slogan or derived geometry. | mindwars_part | 101 | 101 | adapted | none | none |
| `MOT-RADIUS-02` | silence has a radius | Abstract scale becomes named human debt in the central accounting. | aftermath_coda | 120 | 120 | adapted | none | none |
| `MOT-RECORD-01` | record progression | Private insistence that transmit enable and the refusal be preserved. | private_defense_part | 51 | 51 | literal | none | none |
| `MOT-RECORD-02` | record progression | Deposition of the consent dispute into the history of the war. | mindwars_part | 109 | 109 | adapted | none | none |
| `MOT-RECORD-03` | record progression | An entry against the Anchor_POV turns the record toward accountability. | aftermath_coda | 128 | 128 | adapted | none | none |
| `MOT-YES-01` | authorization question | Technical success is forced apart from authorization by the consent question. | mindwars_part | 73 | 73 | literal | `LPC-DID-I-SAY-YES` | none |
| `MOT-WHOSE-01` | provenance question | The twice-stated terminal question leaves provenance unresolved without reviving the signal. | aftermath_coda | 128 | 128 | literal | `LPC-WHOSE-WAS-THAT` | none |

Record_Progression marking under Requirement 7.18: `MOT-RECORD-01` is `literal`, so the canonical wording `Put that on the record.` may appear in that scene; `MOT-RECORD-02` and `MOT-RECORD-03` are `adapted` and are carried by the act of deposition and the act of entry rather than by quotation. Because none of the three carries a `literal_constraint_id`, the `literal` marking permits exact wording without creating an automated rule, and no additional repetition of the phrase is required anywhere else in the manuscript.

Every event without a `literal_constraint_id` may be realized as literal quotation, paraphrase, image, action, or scene structure at drafting discretion. Only the two constraints below receive exact-word, count, or placement checks.

## Motif events

```json record=MotifEvent schema=1
[
  {
    "motif_event_id": "MOT-CHAIN-01",
    "family": "spectrum / wire / voice",
    "dramatic_function": "Mathematical spectrum reaches bone and proves that a living mind occupies the discovered channel.",
    "movement": "discovery_part",
    "planned_chapter": 13,
    "participating_chapters": [13],
    "representation_mode": "image",
    "literal_constraint_id": null,
    "scene_scope": "Mara's person-specific channel proof in Chapter 13.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-CHAIN-02",
    "family": "spectrum / wire / voice",
    "dramatic_function": "Wire reaches bone while mediating reception and exclusion, and the page-nine discovery exposes bidirectionality as architectural danger.",
    "movement": "private_defense_part",
    "planned_chapter": 45,
    "participating_chapters": [45],
    "representation_mode": "image",
    "literal_constraint_id": null,
    "scene_scope": "Mara's page-nine interface-specification reading in Chapter 45.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-CHAIN-03",
    "family": "spectrum / wire / voice",
    "dramatic_function": "Mara's ordinary spoken voice crosses air into a consenting ear, replacing machine restoration with truthful and insufficient human presence.",
    "movement": "aftermath_coda",
    "planned_chapter": 127,
    "participating_chapters": [127],
    "representation_mode": "action",
    "literal_constraint_id": null,
    "scene_scope": "Mara listens and speaks with Safiya through ordinary air in Chapter 127.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-COPPER-01",
    "family": "copper / quiet",
    "dramatic_function": "The copper room creates a private boundary whose first measured quiet gives Nia relief and proves ordinary space is permeable.",
    "movement": "private_defense_part",
    "planned_chapter": 31,
    "participating_chapters": [31],
    "representation_mode": "image",
    "literal_constraint_id": null,
    "scene_scope": "Nia's first experience of measured quiet inside the copper room in Chapter 31.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-COPPER-02",
    "family": "copper / quiet",
    "dramatic_function": "Collective copper buys defensive time but remains an imperfect answer because sealed private life cannot restore public freedom.",
    "movement": "mindwars_part",
    "planned_chapter": 70,
    "participating_chapters": [70],
    "representation_mode": "image",
    "literal_constraint_id": null,
    "scene_scope": "The opening assessment of copper's collective limits in Chapter 70.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-COPPER-03",
    "family": "copper / quiet",
    "dramatic_function": "Retained copper still protects Mara's house, but that protection cannot provide Safiya's truthful maternal-language remedy.",
    "movement": "aftermath_coda",
    "planned_chapter": 124,
    "participating_chapters": [124],
    "representation_mode": "image",
    "literal_constraint_id": null,
    "scene_scope": "Mara's mechanism review and truthful refusal inside the retained protection in Chapter 124.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-COME-01",
    "family": "come in",
    "dramatic_function": "Mara sends a content-free open invitation through the temporary bench path, exposing wonder without an adequate boundary.",
    "movement": "discovery_part",
    "planned_chapter": 16,
    "participating_chapters": [16],
    "representation_mode": "adapted",
    "literal_constraint_id": null,
    "scene_scope": "Mara's deliberate bench-path handshake in Chapter 16.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-COME-02",
    "family": "come in",
    "dramatic_function": "Invitation becomes conditional: ask for a current answer and leave the person behind the door in control of the handle.",
    "movement": "private_defense_part",
    "planned_chapter": 61,
    "participating_chapters": [61],
    "representation_mode": "scene-structure",
    "literal_constraint_id": null,
    "scene_scope": "The repaired challenge-response protocol and movement-ending conditional invitation in Chapter 61.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-COME-03",
    "family": "come in",
    "dramatic_function": "Protective entry occurs only after freely given, current, specific, and revocable consent to the bounded counterphase test.",
    "movement": "mindwars_part",
    "planned_chapter": 74,
    "participating_chapters": [74],
    "representation_mode": "action",
    "literal_constraint_id": null,
    "scene_scope": "The first consenting counterphase test in Chapter 74.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-COME-04",
    "family": "come in",
    "dramatic_function": "Safiya's freely given consent removes lack of authorization as an objection, but it cannot make Mara possess a truthful restoration.",
    "movement": "aftermath_coda",
    "planned_chapter": 124,
    "participating_chapters": [124],
    "representation_mode": "action",
    "literal_constraint_id": null,
    "scene_scope": "The consent motif completes in Mara's truth-based refusal in Chapter 124.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-KNOCK-01",
    "family": "knock / wait",
    "dramatic_function": "A Mindwars security challenge becomes a protocol of asking and waiting for the addressed person's answer rather than declaring friend or foe.",
    "movement": "mindwars_part",
    "planned_chapter": 73,
    "participating_chapters": [73],
    "representation_mode": "action",
    "literal_constraint_id": null,
    "scene_scope": "Nia's consent-centered security challenge in Chapter 73.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-KNOCK-02",
    "family": "knock / wait",
    "dramatic_function": "Safiya follows the threshold protocol exactly by knocking three unhurried times and waiting, without gaining a guaranteed remedy.",
    "movement": "aftermath_coda",
    "planned_chapter": 116,
    "participating_chapters": [116, 117],
    "representation_mode": "action",
    "literal_constraint_id": null,
    "scene_scope": "One visitor-arrival threshold event heard from Safiya's side in Chapter 116 and Mara's side in Chapter 117.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-KNOCK-03",
    "family": "knock / wait",
    "dramatic_function": "Mara converts private accounting into outward obligation by going to another civilian threshold, knocking, and waiting for that person's answer.",
    "movement": "aftermath_coda",
    "planned_chapter": 128,
    "participating_chapters": [128],
    "representation_mode": "action",
    "literal_constraint_id": null,
    "scene_scope": "Mara's first outward visit and threshold action in Chapter 128.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-KETTLE-01",
    "family": "kettle",
    "dramatic_function": "Safiya anchors her null-night account in the ordinary Tuesday moment when access to the private maternal-language layer disappeared.",
    "movement": "aftermath_coda",
    "planned_chapter": 118,
    "participating_chapters": [118],
    "representation_mode": "image",
    "literal_constraint_id": null,
    "scene_scope": "Safiya's continuous Tuesday-null account in Chapter 118.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-KETTLE-02",
    "family": "kettle",
    "dramatic_function": "After refusing counterfeit restoration, Mara switches off the relay and puts on the kettle as the honest human response available to her.",
    "movement": "aftermath_coda",
    "planned_chapter": 124,
    "participating_chapters": [124],
    "representation_mode": "action",
    "literal_constraint_id": null,
    "scene_scope": "The relay-off and kettle-on Coda Turn in Chapter 124.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-RADIUS-01",
    "family": "silence has a radius",
    "dramatic_function": "The broad null's reach becomes an admission of defensive civilian cost across an area canonically described as three counties wide, never a victory slogan or derived geometry.",
    "movement": "mindwars_part",
    "planned_chapter": 101,
    "participating_chapters": [101],
    "representation_mode": "adapted",
    "literal_constraint_id": null,
    "scene_scope": "Mara's closing admission in the affected-area decision sequence in Chapter 101.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-RADIUS-02",
    "family": "silence has a radius",
    "dramatic_function": "Safiya's account turns abstract affected-area scale into named human debt without converting the canonical width into a mathematical radius.",
    "movement": "aftermath_coda",
    "planned_chapter": 120,
    "participating_chapters": [120],
    "representation_mode": "adapted",
    "literal_constraint_id": null,
    "scene_scope": "Mara receives the affected-area extent as people through Safiya's testimony in Chapter 120.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-RECORD-01",
    "family": "record progression",
    "dramatic_function": "Mara privately insists that transmit enable and her refusal be preserved rather than softened into an institutional summary.",
    "movement": "private_defense_part",
    "planned_chapter": 51,
    "participating_chapters": [51],
    "representation_mode": "literal",
    "literal_constraint_id": null,
    "scene_scope": "Mara's first preservation demand after refusing the Consortium deal in Chapter 51.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-RECORD-02",
    "family": "record progression",
    "dramatic_function": "Julian deposits the consent dispute and unresolved civilian uncertainty into the public history of the Mindwars.",
    "movement": "mindwars_part",
    "planned_chapter": 109,
    "participating_chapters": [109],
    "representation_mode": "adapted",
    "literal_constraint_id": null,
    "scene_scope": "Julian's war-history deposition in Chapter 109.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-RECORD-03",
    "family": "record progression",
    "dramatic_function": "Mara makes an entry against herself so the record turns from private insistence and public history toward accountable outward obligation.",
    "movement": "aftermath_coda",
    "planned_chapter": 128,
    "participating_chapters": [128],
    "representation_mode": "adapted",
    "literal_constraint_id": null,
    "scene_scope": "Mara's self-implicating record entry in Chapter 128.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-YES-01",
    "family": "authorization question",
    "dramatic_function": "Nia forces the defense to distinguish technical success from authorization by asking whether she consented.",
    "movement": "mindwars_part",
    "planned_chapter": 73,
    "participating_chapters": [73],
    "representation_mode": "literal",
    "literal_constraint_id": "LPC-DID-I-SAY-YES",
    "scene_scope": "Nia's counterphase-consent confrontation in Chapter 73.",
    "arc_change_history": []
  },
  {
    "motif_event_id": "MOT-WHOSE-01",
    "family": "provenance question",
    "dramatic_function": "The twice-stated terminal question leaves provenance after insertion, deletion, reconstruction, and testimony unresolved without reviving the Foreign Signal.",
    "movement": "aftermath_coda",
    "planned_chapter": 128,
    "participating_chapters": [128],
    "representation_mode": "literal",
    "literal_constraint_id": "LPC-WHOSE-WAS-THAT",
    "scene_scope": "The declared Final Passage at the end of Chapter 128.",
    "arc_change_history": []
  }
]
```

## Literal phrase constraints

Exactly two constraints exist, and this ledger is the only place that may create one. `LPC-DID-I-SAY-YES` restricts `Did I say yes?` to Mindwars Chapter Files and fixes no in-scope total, so one legal occurrence and several legal occurrences are equally acceptable while any occurrence outside the Mindwars movement is a violation. `LPC-WHOSE-WAS-THAT` requires `Whose was that?` exactly twice inside the declared Final Passage of Chapter 128 and zero times in every other prose span.

### Declared Final_Passage bounds

`MOT-WHOSE-01` owns the Final_Passage declaration, and the bounds are stored machine-readably in `LPC-WHOSE-WAS-THAT.allowed_span` so a checker locates the span deterministically instead of inferring a literary passage from typography, blank lines, or scene breaks.

| Span field | Declared value |
|---|---|
| `span_id` | `SPAN-FINAL-PASSAGE` |
| `chapter` | 128 |
| File | `chapters/aftermath-coda/aftermath-coda-128-knock-and-wait.md` |
| `start_boundary.kind` | `literal-marker` |
| `start_boundary.value` | `<!-- final-passage:start -->` |
| `end_boundary.kind` | `end-of-prose` |
| `end_boundary.value` | `null` |

Resolution rules for that span:

- The span begins immediately after the single start marker in the Chapter 128 Prose Body and ends at end-of-prose. Everything before the marker is out-of-span prose where `Whose was that?` must not appear.
- The marker is a machine boundary. It is not part of the protected phrase, not dialogue, not permission to scan Chapter Headers or non-chapter files, and it must appear exactly once in that Prose Body.
- A missing marker, a second marker, or a marker in any other chapter makes the requested gate `incomplete` rather than `revision`. The checker reports incomplete input and never guesses a Final Passage.
- Chapter 128 remains subject to the ordinary header contract, so the span lives entirely after the closing header delimiter.

```json record=LiteralPhraseConstraint schema=1
[
  {
    "constraint_id": "LPC-DID-I-SAY-YES",
    "motif_event_id": "MOT-YES-01",
    "exact_phrase": "Did I say yes?",
    "scan_scope": "chapter-prose-body-only",
    "allowed_movements": ["mindwars_part"],
    "allowed_chapters": [],
    "allowed_files": [],
    "allowed_span": null,
    "minimum_in_scope": null,
    "maximum_in_scope": null,
    "exact_in_scope": null,
    "maximum_outside_scope": 0,
    "normalization": {
      "unicode": "NFC",
      "line_endings": "LF",
      "case_sensitive": true,
      "punctuation_sensitive": true,
      "word_order_sensitive": true,
      "match_mode": "non-overlapping-literal"
    },
    "scope_exclusions": [
      "canon-source-songs",
      "other-song-files",
      "planning-documents",
      "chapter-headers",
      "front-matter",
      "editorial-records",
      "checker-output"
    ],
    "diagnostic_code": "LITERAL_DID_I_SAY_YES_SCOPE"
  },
  {
    "constraint_id": "LPC-WHOSE-WAS-THAT",
    "motif_event_id": "MOT-WHOSE-01",
    "exact_phrase": "Whose was that?",
    "scan_scope": "chapter-prose-body-only",
    "allowed_movements": ["aftermath_coda"],
    "allowed_chapters": [128],
    "allowed_files": ["chapters/aftermath-coda/aftermath-coda-128-knock-and-wait.md"],
    "allowed_span": {
      "span_id": "SPAN-FINAL-PASSAGE",
      "chapter": 128,
      "start_boundary": {
        "kind": "literal-marker",
        "value": "<!-- final-passage:start -->"
      },
      "end_boundary": {
        "kind": "end-of-prose",
        "value": null
      }
    },
    "minimum_in_scope": null,
    "maximum_in_scope": null,
    "exact_in_scope": 2,
    "maximum_outside_scope": 0,
    "normalization": {
      "unicode": "NFC",
      "line_endings": "LF",
      "case_sensitive": true,
      "punctuation_sensitive": true,
      "word_order_sensitive": true,
      "match_mode": "non-overlapping-literal"
    },
    "scope_exclusions": [
      "canon-source-songs",
      "other-song-files",
      "planning-documents",
      "chapter-headers",
      "front-matter",
      "editorial-records",
      "checker-output"
    ],
    "diagnostic_code": "LITERAL_WHOSE_WAS_THAT_PLACEMENT"
  }
]
```

## Protected wording is not a scan rule

The Canon Bible's Canon Dialogue provenance table records canonical speakers and meaning-preservation rules for wording such as `Come in.`, `Come in. But ask.`, `Transmit enable.`, `Put that on the record.`, `Go ahead.`, `Did I say yes?`, and `Whose was that?`. Those `CanonFact.protected_wording` values fix attribution and meaning; they create **no** automated prose scan. Only a schema-valid `LiteralPhraseConstraint` in this ledger creates one, and its scan scope is Chapter File Prose Bodies only.

Two consequences follow. First, five of the seven protected wordings have no constraint here, so they carry no count, placement, or exact-wording check anywhere in the manuscript. Second, the song files are outside scan scope under `DEC-014` and the schema's literal scan boundary: `Did I say yes?` in *Case Zero* and its echo in *The Final Frontier*, and `Whose was that?` in *The Radius* outro, neither satisfy nor violate the constraints above. The same exclusion covers planning documents including this file, Chapter Headers, front matter, editorial records, and checker output.

## `DEC-017` rider

The Chapter 73 / null-night consent parallel is disclosure and craft direction enforced by human Editorial Review. It rides entirely on three events that already exist — `MOT-YES-01` in Chapter 73, `MOT-KETTLE-01` in Chapter 118, and `MOT-RECORD-03` in Chapter 128 — and it creates no Motif_Event ID, no Literal_Phrase_Constraint, no Reveal, and no fourth event in any family. Chapter 73 establishes the concrete physical vocabulary for a cancellation field experienced from inside and has the authorization question asked and answered; Chapter 118 reuses that vocabulary with no authorization question anywhere near it, and the absence of the question is the echo; Mara names the parallel exactly once inside the existing `MOT-RECORD-03` entry against herself. Nothing in this rider is checkable, and no checker may score it.

## Persistence, incidental mentions, and change control

- **One sustained scene and function is one event.** Repetition inside a ledgered scene never creates a second event. The three knocks in Chapters 116–117 are one arrival event seen from two positions; repeated kettle references inside Chapter 118 or Chapter 124 remain one kettle event each; multiple legal occurrences of `Did I say yes?` inside the Chapter 73 confrontation remain `MOT-YES-01`; and both in-passage occurrences of `Whose was that?` comprise `MOT-WHOSE-01`. A second event requires a distinct dramatic function, not additional repetitions.
- **Incidental_Mentions are excluded.** Discovery copper foreshadowing, Mindwars counterphase as connective context, `record` used as an ordinary noun, an unfreighted kettle in an unledgered kitchen, and any other mention that performs no planned dramatic function stay out of this ledger and out of every count. Excluding them is required, not optional, and drafting may still use them.
- **Change control.** Every `arc_change_history` is `[]` because no event has moved or changed function, movement, or representation mode. Any later move or change must update this ledger, the Arc Outline, and every affected Chapter Header in the same Arc_Change or chapter revision, and after baseline approval the change stays invalid until every listed reference is synchronized. Stable IDs are immutable and are never reused for a different event.

## Requirement 7 coverage

| Criterion | Where it is satisfied |
|---|---|
| 7.1 | 22 `MotifEvent` records with unique stable IDs, family, dramatic function, movement, planned chapter, representation mode, and literal constraint or `null`; restated in the readable event summary. |
| 7.2 | Event index by chapter fixes the exact ID set each Chapter Header and Arc Entry must list, including the two-chapter `MOT-KNOCK-02` agreement. |
| 7.3 | Change-control rule requiring same-change synchronization of ledger, outline, and header, with `arc_change_history` per event. |
| 7.4 | Persistence rule: one sustained scene and function is one event. |
| 7.5 | Incidental_Mention exclusion rule with named non-events. |
| 7.6 | Readable event summary note permitting literal, paraphrase, image, action, or scene structure for the 20 events without a constraint. |
| 7.7 | Exactly two `LiteralPhraseConstraint` records; the protected-wording section confirms nothing else is scanned. |
| 7.8 | `MOT-COME-01` (16) open, `MOT-COME-02` (61) conditional, `MOT-COME-03` (74) entry after consent, `MOT-COME-04` (124) consent without truthful restoration. |
| 7.9 | `MOT-COPPER-01` (31) private boundary, `MOT-COPPER-02` (70) imperfect collective defense, `MOT-COPPER-03` (124) retained protection without the needed remedy. |
| 7.10 | `MOT-CHAIN-01` (13) spectrum-to-bone, `MOT-CHAIN-02` (45) wire-to-bone, `MOT-CHAIN-03` (127) voice-through-air into a consenting ear. |
| 7.11 | `MOT-KNOCK-01` (73) security protocol, `MOT-KNOCK-02` (116–117) compliant arrival, `MOT-KNOCK-03` (128) outward obligation. |
| 7.12 | Exactly two kettle events, `MOT-KETTLE-01` in 118 and `MOT-KETTLE-02` in 124, both in the Coda and nowhere else. |
| 7.13 | `MOT-RADIUS-01` (101) admission of defensive cost, `MOT-RADIUS-02` (120) central Coda accounting. |
| 7.14 | `LPC-DID-I-SAY-YES` scoped to `mindwars_part` with `exact_in_scope`, `minimum_in_scope`, and `maximum_in_scope` all `null`. |
| 7.15 | Same constraint sets `maximum_outside_scope: 0` with diagnostic `LITERAL_DID_I_SAY_YES_SCOPE`. |
| 7.16 | `LPC-WHOSE-WAS-THAT` sets `exact_in_scope: 2` inside `SPAN-FINAL-PASSAGE` in Chapter 128 and `maximum_outside_scope: 0`, with declared machine-readable bounds. |
| 7.17 | Exactly three Record_Progression events: `MOT-RECORD-01` (51) private insistence, `MOT-RECORD-02` (109) deposition into the war's history, `MOT-RECORD-03` (128) entry against the Anchor_POV. |
| 7.18 | Record_Progression marking note: `literal` for `MOT-RECORD-01`, `adapted` for the later two, with no constraint and no required repetition elsewhere. |
