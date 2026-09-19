# Requirements Document

## Introduction

This specification governs a creative-writing project built on the world established by five song documents in this workspace: *The Synaptic Frontier*, *Faraday*, *The Final Frontier*, *The Radius*, and *Case Zero*. The deliverable is a complete chapter arc and actual novel chapters, supported by lightweight planning, continuity, review, and checking documents. The intended form is an original short-chapter, cross-cut thriller architecture: first-person testimony, rapid viewpoint alternation, withheld disclosures, and chapter-ending narrative pulls. The project does not imitate another author’s prose voice.

The trilogy forms the novel’s three Main Parts: discovery in *The Synaptic Frontier*, private refusal and defense in *Faraday*, and the Mindwars in *The Final Frontier*. *The Radius* supplies a shorter Aftermath/Coda within the same manuscript. The Aftermath/Coda opens a second cycle through consequence and accounting; the Aftermath/Coda does not extend or restart the settled war. *Case Zero* is a binding counter-deposition that adds canon without creating a fifth Story_Movement or changing that architecture.

Names are allowed. Characters, places, institutions, and products may receive stable names selected during design and arc work. This requirements phase does not choose those final names. “The Mindwars” remains an established canonical term rather than the only name available to the novel.

The lyric text in the five Canon_Sources and explicit author decisions provide binding story canon. Canon_Lyric remains subject to ordinary metaphor, compression, first-person limitation, and attributed testimony rather than being treated as automatic omniscient fact. Production notes and other non-lyric song metadata are advisory evidence for motif, tone, structure, and interpretation unless an approved requirement or later author decision expressly adopts a particular proposition. The title’s governing premise is binding in both the lyric and the author’s direction: the final frontier was not outer space but our own minds; humanity expected to cross the frontier and instead became the territory crossed. The Mindwars are an event within that argument, not another title for the novel. Objective checks verify file structure, metadata, counts, identifiers, continuity references, and explicitly protected wording. Human editorial review owns judgments about prose voice, tone, pacing, hook effectiveness, POV distinctness, and emotional truth.

## Glossary

- **Canon_Source**: One of exactly five reference song documents: `songs/The Synaptic Frontier.md`, `songs/Faraday.md`, `songs/The Final Frontier.md`, `songs/The Radius.md`, and `songs/Case Zero.md`. `DEC-014` authorizes *Case Zero* publication in progress and promotes it to this set. The *One-Time Pad* draft is preserved in git history and removed from the working tree; it is unpublished, noncanonical for book purposes, is not a Canon_Source, and supplies no novel continuity. Each Canon_Source contains Canon_Lyric plus non-story rights/credit metadata and Production_Notes. The lyrics-site tooling and canonical release sources live in a separate repository.
- **Canon_Lyric**: The lyric text of a Canon_Source. It is inherently binding story canon, subject only to higher-authority explicit author decisions and approved requirements; ordinary metaphor, compression, first-person limitation, and attributed testimony do not require every image or speaker inference to be literal or omniscient fact.
- **Production_Notes**: Style prompts, exclude-style lists, generation workflow, trilogy/cycle commentary, carried-motif analysis, credits, rights metadata, and other non-lyric material associated with a song. Production_Notes and non-lyric metadata are non-story/advisory unless a specific proposition is expressly ratified by an approved requirement or author decision. Unratified material cannot independently establish a Binding_Canon_Fact, Literal_Phrase_Constraint, identity, name rule, chronology, continuity obligation, or literal diegetic production event.
- **Canon_Authority**: The precedence defined by `DEC-011` and updated source inventory in `DEC-014`: explicit author decisions; approved requirements/design decisions; Canon_Lyric from the five Canon_Sources; expressly ratified note material whose authority comes from its identified adopter; then approved compatible Novel_Extensions. Unratified Production_Notes and other non-lyric metadata sit outside this precedence order, remain advisory/non-story, and cannot defeat a Novel_Extension. Rights, performance, recording, and credit metadata are not story canon.
- **Manuscript_Project**: The complete creative-writing process governed by this specification, including planning, calibration, drafting, review, and acceptance.
- **Manuscript**: The complete novel deliverable: Front_Matter, Arc_Outline, Canon_Bible, POV_Roster, Voice_Briefs, Motif_Ledger, and every Chapter_File.
- **Chapter_File**: One markdown file containing exactly one chapter, composed of a Chapter_Header followed by a Prose_Body.
- **Chapter_Header**: The delimited metadata block at the top of a Chapter_File.
- **Prose_Body**: Everything in a Chapter_File after the Chapter_Header.
- **Narration**: A POV character’s narrative discourse in the Prose_Body, excluding direct dialogue and explicitly quoted matter.
- **Prose_Word**: One whitespace-separated token in a Prose_Body; Chapter_Header content is excluded from prose word counts.
- **Story_Movement**: One structural division of the Manuscript: a Main_Part or the Aftermath_Coda.
- **Main_Part**: One of the trilogy’s three coequal structural divisions.
- **Discovery_Part**: Main Part One, mapped to *The Synaptic Frontier*.
- **Private_Defense_Part**: Main Part Two, mapped to *Faraday*.
- **Mindwars_Part**: Main Part Three, mapped to *The Final Frontier*.
- **Aftermath_Coda**: The shorter postwar movement mapped to *The Radius*; the Aftermath_Coda belongs to this Manuscript but is not a fourth Main_Part.
- **Arc_Outline**: The living chapter-arc document listing every planned chapter, structural placement, narrative function, and drafting status.
- **Provisional_Arc**: The complete pre-drafting version of the Arc_Outline used to select and draft the Calibration_Batch.
- **Calibration_Batch**: The first delivered set of 6–8 Chapter_Files, selected to test the opening sequence and any explicitly identified representative material before baseline approval.
- **Baseline_Revision_Pass**: The single dedicated post-calibration review of the complete Arc_Outline in which every recorded calibration finding receives an arc change or a rationale for no arc change.
- **Approved_Baseline**: The author-approved Arc_Outline established after Calibration_Batch review and the Baseline_Revision_Pass.
- **Final_Targets**: The exact planned chapter count and inclusive minimum-to-maximum total Prose_Word range recorded in the Approved_Baseline.
- **Arc_Change**: A documented post-baseline change that records the prior state, revised state, rationale, affected chapters, and affected reference documents.
- **Cross_Cut**: A reciprocal declared relationship between chapters that present the same timeline event, consequence, or withheld disclosure from different positions.
- **Timeline_ID**: A stable identifier for a chronology point or interval defined in the Canon_Bible.
- **Hook**: A planned chapter-ending narrative pull, such as an unanswered question, reversal, withheld disclosure, consequential image, or interrupted action.
- **Normal_Chapter_Range**: The inclusive range of 700–1,600 Prose_Words.
- **Hard_Chapter_Maximum**: The maximum permitted length of 2,500 Prose_Words for one Chapter_File.
- **Length_Class**: One of `microchapter`, `normal`, or `long-outlier`, determined from the final Prose_Word count.
- **Length_Outlier**: A deliberately planned `microchapter` or `long-outlier` that remains at or below the Hard_Chapter_Maximum.
- **Microchapter**: A purposeful Length_Outlier below 700 Prose_Words.
- **Character_ID**: A stable internal identifier for one novel character, independent of the character’s selected name or alias.
- **Character_Name**: A stable narrative name or alias selected during design or arc work and associated with one Character_ID.
- **POV**: One human viewpoint used by a Chapter_File.
- **POV_ID**: A stable identifier assigned to one POV in the POV_Roster and Chapter_Header.
- **Same_POV_Run**: A maximal uninterrupted sequence of Chapter_Files assigned to one POV_ID, counted on the global chapter sequence so that Story_Movement boundaries are counted like any other adjacency. A Same_POV_Run is limited to three Chapter_Files and 3,600 Prose_Words. The word limit is evaluated from estimated values during planning and from declared `words` values in the completed Manuscript.
- **Anchor_POV**: The finder/defender who discovers the field, leads the private refusal and defense, participates in the Mindwars, and faces the accounting in the Aftermath_Coda.
- **POV_Roster**: The document defining the selected POVs, Character_ID and POV_ID mappings, selected names and aliases, distinctive narrative contributions, and Story_Movement coverage.
- **Material_Narrative_Value**: New or materially reframed knowledge, moral pressure, consequence, or interpretive position contributed by a POV transition.
- **Voice_Brief**: A qualitative guide for one POV covering syntax and rhythm, image families and sensory attention, emotional distance, characteristic omissions or evasions, delayed notice, and movement-specific evolution.
- **Voice_Briefs**: The complete set of Voice_Brief entries, stored in the POV_Roster or in a linked manuscript reference document.
- **Reverb_Profile**: A qualitative Voice_Brief device that translates the Canon_Source’s spatial production language into narrative distance and interiority without numerical prose metrics.
- **Coda_Turn**: The identified Aftermath_Coda beat after which the Anchor_POV’s voice becomes markedly drier and narrower.
- **Foreign_Signal**: The intruding transmission whose origin and sender the Canon_Source leaves unestablished.
- **Neural_Communication_Mode**: Exactly one of `RECEIVE`, `INTRUDE`, `CANCEL`, or `PAIR`; the modes share an addressable field but differ in direction, semantic capacity, addressing, consent, calibration, and evidentiary meaning. `RECEIVE`, `INTRUDE`, and `PAIR` are insertive or observational; `CANCEL` is the only subtractive mode.
- **RECEIVE**: Passive observation of high-dimensional structure already present in one living person's field. `RECEIVE` performs no write and requires no transmit stage.
- **INTRUDE**: An active person-specific addressed write performed without the complete conditions for `PAIR`. `INTRUDE` may affect only nonsemantic salience, valence, urgency, certainty, preference, or wanting; `INTRUDE` cannot carry language, propositions, commands, a voice, or arbitrary memories.
- **CANCEL**: An active unaddressed counterphase cancellation field whose only effect is subtraction. `CANCEL` carries no person-specific address, transports no language, proposition, order, voice, or memory in either direction, and inserts nothing. Its effect is the removal or degradation of access to mental content and faculties. `CANCEL` covers both a bounded local field volume containing one deliberately exposed consenting individual and an area-scale field volume; these are one mode at two scopes.
- **Subtraction_Effect**: The removal or degradation of a person's access to mental content or faculties produced by `CANCEL`. A Subtraction_Effect has no additive inverse and is distinct in kind from the insertion produced by `INTRUDE`.
- **Pair_Calibration**: A jointly established semantic encode/decode mapping unique to exactly two living participants. Pair_Calibration may mature over repeated consensual sessions and cannot transfer to another person, a dead or absent person, a simulation, an archive, a model, or a reconstruction.
- **Deliberate_Send_Act**: A participant's conscious act of offering one contribution for transport during `PAIR`; unoffered thought, imagery, memory, emotion, and background mentation are excluded.
- **PAIR**: A Neural_Communication_Mode providing near-natural internal speech between exactly two living participants who hold current, specific, revocable mutual consent and matching Pair_Calibration. Every contribution requires a Deliberate_Send_Act.
- **Pairing_Session**: One bounded `PAIR` interaction with identifiable participants, consent state, start, pause, revocation, timing, channel volume, and integrity or error events.
- **Fluent_Pairing**: A mature `PAIR` interaction in which repeated Pair_Calibration permits near-natural conversational exchange while preserving Deliberate_Send_Acts, immediate pause or revocation, and private unoffered mentation.
- **Consent_State_Metadata**: A nonsemantic record of Pairing_Session authorization, participant and pair addresses, consent state, pause, and revocation.
- **Transport_Metadata**: A nonsemantic record of Pairing_Session operation, including timing, channel volume, acknowledgments, latency, integrity, and error events.
- **Content_Recording**: A separate, explicit, mutual, default-off authorization to preserve protocol-carried semantic content from one Pairing_Session.
- **Pairing_Transcript**: The content record produced only when Content_Recording is authorized. A Pairing_Transcript represents only contributions transported by the protocol during the recorded Pairing_Session and does not establish truth, intent, memory provenance, unoffered thought, or a complete mental state.
- **Provenance_Question**: The unresolved question of the Foreign_Signal’s origin and sender, including the question opened by “Whose was that?”.
- **The_Mindwars**: The established canonical term “the Mindwars,” used for the undeclared war over mindspace.
- **Binding_Canon_Fact**: A fact that affects plot, chronology, characterization, motif function, or ethical logic and derives from an explicit author decision, an approved requirement, Canon_Lyric, or expressly ratified Production_Notes. Its Canon_Bible record identifies that authority basis; unratified Production_Notes cannot supply one.
- **Novel_Extension**: A fact added by the novel that affects later continuity, including selected names, relationships, chronology details, locations, institutions, or products.
- **Canon_Dialogue**: Dialogue inherited or closely adapted from Canon_Lyric and attributed to its canonical speaker.
- **Canon_Bible**: The reference document recording Binding_Canon_Facts with authority basis, Novel_Extensions, Timeline_IDs, selected names that affect continuity, unresolved questions, and other context useful for continuity.
- **Motif_Event**: A planned dramatic beat in which a carried phrase, object, image, sound, or action performs a specified narrative function.
- **Incidental_Mention**: A repeated token or object reference that adds no new dramatic function and is not counted as a separate Motif_Event.
- **Literal_Phrase_Constraint**: A ledgered constraint on exact wording, count, or placement that is explicitly established by this specification or an author decision, normally protecting wording drawn from Canon_Lyric. Unratified Production_Notes cannot establish one.
- **Record_Progression**: The three-event movement of the “put this on the record” motif from private insistence, to historical deposition, to an entry against the Anchor_POV.
- **Motif_Ledger**: The document recording each Motif_Event’s stable ID, dramatic function, Story_Movement, planned Chapter_File, representation mode, and any Literal_Phrase_Constraint.
- **Final_Passage**: The closing prose span of the final Aftermath_Coda Chapter_File identified for the terminal Provenance_Question event in the Motif_Ledger.
- **Rhetorical_Collective_Declaration**: A heightened choral or declarative use of collective voice comparable to the “I” to “we” turn in *The Final Frontier*; ordinary grammatical uses of “we” are excluded.
- **Refused_Swell**: The ending’s deliberate movement away from triumph, moral victory, renewed campaign, or anthemic escalation and toward quiet human obligation.
- **Editorial_Review**: Human review of subjective craft that records qualitative evidence and a `pass` or `revision` finding.
- **Editorial_Gate**: A recorded `pass` or `revision` decision from Editorial_Review for a chapter, batch, or complete Manuscript.
- **Objective_Check**: A deterministic check of metadata, identifiers, ordering, counts, broad length limits, ledgered literal constraints, timeline references, arc/file agreement, or Site_Build exclusion.
- **Manuscript_Checker**: The lightweight utility that performs Objective_Checks and reports violations without judging prose artistry.
- **Direct_Planning_References**: The Arc_Outline entry, Canon_Bible timeline entries, POV_Roster entry, Voice_Brief, and Motif_Ledger entries directly assigned to one Chapter_File.
- **Chapter_Local_Gate**: The objective and editorial completion criteria evaluated from one current Chapter_File and its Direct_Planning_References.
- **Manuscript_Global_Gate**: The whole-book objective acceptance criteria evaluated only when the complete Manuscript is presented for final review.
- **Final_Prerequisites**: A recorded Approved_Baseline, readable required reference documents and Front_Matter, every planned Chapter_File, and a passed Chapter_Local_Gate for each Chapter_File.
- **Front_Matter**: The novel-specific authorship, prose copyright, and optional source acknowledgment document.
- **Site_Build**: The lyrics-site generation process and its generated song index. Site_Build is **external to this workspace**: it lives in a separate lyrics repository and is not present here, so it cannot be edited or executed from this project. Requirements 9.2, 9.3, 11.9, and 12.8 are therefore satisfied by the Manuscript_Exclusion_Contract rather than by modifying Site_Build source directly.
- **Manuscript_Exclusion_Contract**: The machine-readable declaration in this workspace that names the manuscript root as an excluded source directory, together with the checker mode and tests that verify a discovery routine honoring the contract returns zero Manuscript paths. The contract is the artifact the external lyrics repository consumes; it does not prove the external Site_Build has adopted it.
- **Drafting_Batch**: A reviewable set of 4–8 Chapter_Files drafted and evaluated together after the Calibration_Batch.
- **Drafting_Process**: The sequence of arc creation, calibration, baseline approval, incremental drafting, checking, editorial review, and revision.
- **Substantive_Prose_Change**: A Prose_Body edit that changes narration, dialogue, scene action, characterization, continuity, motif function, or a chapter ending rather than correcting formatting or metadata alone.
- **Chapter_Status**: One of `planned`, `exploratory`, `draft`, `revised`, `approved`, or `final`.
- **Batch_Status**: One of `draft`, `revised`, `approved`, or `final`.

## Requirements

### Requirement 1: Provisional Arc, Calibration, and Baseline Approval

**User Story:** As the author, I want a complete provisional chapter arc tested against representative prose before approval, so that the book’s architecture can respond to actual voice and pacing evidence.

#### Acceptance Criteria

1. THE Drafting_Process SHALL establish a complete Provisional_Arc before drafting any Prose_Body.
2. THE Provisional_Arc SHALL contain exactly one complete Arc_Outline entry for every planned Chapter_File.
3. THE Provisional_Arc SHALL assign every planned Chapter_File one unique integer sequence number in an uninterrupted range beginning at 1.
4. THE Arc_Outline SHALL record for each chapter the sequence number, Story_Movement, Timeline_ID, POV_ID, one-sentence purpose, nonblank Hook, Cross_Cut reference or explicit absence, estimated Length_Class, and Chapter_Status.
5. THE Arc_Outline SHALL assign each planned chapter to exactly one Story_Movement, one Timeline_ID, and one POV_ID.
6. WHERE two or more chapters share a timeline event, consequence, or withheld disclosure, THE Arc_Outline SHALL record reciprocal Cross_Cut references in each chapter participating in the relationship.
7. WHERE a chapter has no Cross_Cut relationship, THE Arc_Outline SHALL record the Cross_Cut value as `none`.
8. THE Provisional_Arc SHALL identify 6–8 chapters as the Calibration_Batch.
9. WHERE a Calibration_Batch chapter is outside the opening sequence, THE Arc_Outline SHALL record the representative purpose served by that selection.
10. WHEN the Provisional_Arc is complete, THE Drafting_Process SHALL draft and review the Calibration_Batch before establishing the Approved_Baseline.
11. WHEN Calibration_Batch review is complete, THE Editorial_Review SHALL record qualitative findings and either a requested-revision or no-revision conclusion for voice separation, opening momentum, Cross_Cut clarity, pacing, and Hook effectiveness.
12. WHEN the Calibration_Batch findings are recorded, THE Drafting_Process SHALL perform one dedicated Baseline_Revision_Pass before requesting author approval.
13. THE Baseline_Revision_Pass SHALL record for every calibration finding the resulting Arc_Outline change or the rationale for making no Arc_Outline change.
14. WHEN the author approves the revised Arc_Outline, THE Approved_Baseline SHALL record the author’s approval.
15. WHEN the author approves the revised Arc_Outline, THE Final_Targets SHALL record one exact planned chapter count and one inclusive bounded total Prose_Word range.
16. WHEN a post-baseline Arc_Change is proposed, THE Arc_Change SHALL identify the prior state, revised state, rationale, affected Chapter_Files, and affected reference documents.
17. WHEN a post-baseline Arc_Change affects continuity or motif placement, THE Drafting_Process SHALL synchronize every affected entry in the Arc_Outline, Chapter_Files, Canon_Bible, Motif_Ledger, POV_Roster, and Voice_Briefs within the same recorded change.
18. THE Approved_Baseline SHALL permit later changes only through documented Arc_Changes.

### Requirement 2: Provisional Scale and Short-Chapter Form

**User Story:** As a reader, I want a fast, legible sequence of short first-person chapters with purposeful variation, so that rotating viewpoints and withheld disclosures create momentum without flattening important moments.

#### Acceptance Criteria

1. THE Provisional_Arc SHALL use the inclusive range of 120–135 Chapter_Files and the inclusive range of 130,000–150,000 Prose_Words as provisional planning targets.
2. WHEN the Approved_Baseline is established, THE Final_Targets SHALL replace the provisional scale with one exact planned chapter count and an inclusive minimum-to-maximum total Prose_Word range.
3. WHERE the exact planned chapter count falls outside the inclusive range of 120–135 Chapter_Files, or either inclusive Prose_Word bound falls outside the inclusive range of 130,000–150,000 Prose_Words, THE Approved_Baseline SHALL record the narrative or calibration rationale for the difference.
4. THE Prose_Body of each Chapter_File SHALL use exactly one labeled POV.
5. THE Narration of each Chapter_File SHALL use first-person past tense as testimony placed on the record.
6. WHERE a Prose_Body contains direct dialogue or explicitly quoted matter, THE Manuscript SHALL permit the grammatical person and tense required by the speaker or quoted source.
7. THE Arc_Outline SHALL place no more than three consecutive Chapter_Files under the same POV_ID, which is the Chapter_File-count limit on a Same_POV_Run.
8. WHEN every final Chapter_File is present, THE Manuscript_Global_Gate SHALL verify that at least 80 percent of final Chapter_Files fall within the Normal_Chapter_Range, using all final Chapter_Files as the denominator.
9. THE Prose_Body of each Chapter_File SHALL contain no more than the Hard_Chapter_Maximum.
10. WHERE a planned chapter is a Length_Outlier, THE Arc_Outline SHALL label the Length_Class and record the chapter’s narrative purpose.
11. WHERE a planned chapter is a Microchapter, THE Arc_Outline SHALL identify the specific compression, interruption, revelation, aftermath, or other short-form function.
12. THE Chapter_Header of each Chapter_File SHALL contain a nonblank single-line Hook description.
13. WHEN a Chapter_File reaches Editorial_Review, THE Editorial_Review SHALL record whether the final beat performs the Hook described in the Chapter_Header.
14. WHEN the complete Manuscript reaches final Editorial_Review, THE Editorial_Review SHALL assess POV voice originality and distinctness qualitatively, including whether the prose avoids deliberate imitation of another author, without numeric style scoring.
15. THE Arc_Outline SHALL place no more than 3,600 estimated Prose_Words in any Same_POV_Run.
16. WHERE an Arc_Outline entry belongs to a Same_POV_Run containing two or more Chapter_Files, THE Arc_Outline SHALL record an estimated Prose_Word value for that entry.

### Requirement 3: Three Main Parts and an Aftermath/Coda

**User Story:** As the author, I want the trilogy to retain its three-part dramatic shape while the shorter Coda delivers the bill for the war, so that *The Radius* opens a second cycle without becoming a fourth installment of the conflict.

#### Acceptance Criteria

1. THE Manuscript SHALL contain exactly four Story_Movements in this order: Discovery_Part, Private_Defense_Part, Mindwars_Part, and Aftermath_Coda.
2. THE Discovery_Part SHALL dramatize in its Chapter_Files the mind as a field, the unfound frequency, and the certainty that somebody alive will find the channel.
3. THE Private_Defense_Part SHALL dramatize in its Chapter_Files the uninvited arrival, the copper room, the page-nine transmit-enable line, and the conditional invitation.
4. THE Mindwars_Part SHALL dramatize in its Chapter_Files the undeclared war, active defense by counterphase, the turn from explorer to territory, and the null.
5. THE Aftermath_Coda SHALL dramatize in its Chapter_Files the armistice without a counterparty, the knock two years after the null, the accounting owed to the visitor, and the physics-based refusal.
6. THE Arc_Outline SHALL label the movement mapped to *The Radius* as the Aftermath_Coda rather than as a fourth Main_Part.
7. THE Mindwars_Part SHALL contain more Prose_Words than every other Story_Movement in the completed Manuscript.
8. THE Aftermath_Coda SHALL contain fewer Prose_Words than every Main_Part in the completed Manuscript.
9. THE Manuscript SHALL confine active defender counterphase transmission to the Mindwars_Part.
10. WHEN the Mindwars_Part ends, THE Manuscript SHALL preserve the Foreign_Signal as silenced and the defending voice as diminished by the same null.
11. THE Aftermath_Coda SHALL depict the post-null Foreign_Signal as silent and defender activity as postwar consequence and accounting, with no renewed Foreign_Signal transmission, renewed combat, or defender counterphase.
12. THE Aftermath_Coda SHALL open the second cycle through consequence and accounting without extending or restarting the settled war.
13. THE Manuscript SHALL preserve the Provenance_Question as unconfirmed across every narrative and reference component.

### Requirement 4: Named Human POV Architecture

**User Story:** As a reader, I want a small set of clearly identified human viewpoints with materially distinct dramatic functions, so that each shift adds knowledge, pressure, consequence, or perspective.

#### Acceptance Criteria

1. THE POV_Roster SHALL define between 3 and 5 human POVs selected by the Arc_Outline.
2. THE POV_Roster SHALL assign each POV one unique stable Character_ID and one unique stable POV_ID in a one-to-one mapping.
3. WHEN a Character_Name or alias is selected, THE POV_Roster SHALL associate the Character_Name or alias with exactly one Character_ID.
4. THE Manuscript SHALL use each selected Character_Name and alias consistently with the POV_Roster mapping.
5. THE Manuscript SHALL identify people, places, institutions, and products with stable names or descriptive references chosen for narrative clarity.
6. THE POV_Roster SHALL establish each POV’s material distinction through the combined profile of knowledge, moral pressure, and plot function while permitting individual facts and moral concerns to overlap.
7. IF two POVs duplicate one another’s combined knowledge position, moral pressure, and plot function, THEN THE POV_Roster SHALL merge or remove one of the duplicative POVs before Approved_Baseline approval.
8. THE POV_Roster SHALL define the Anchor_POV as the finder/defender who discovers the field, leads the private refusal and defense, participates in the Mindwars, and faces the accounting in the Aftermath_Coda.
9. THE Arc_Outline SHALL assign the Anchor_POV at least one Chapter_File in every Story_Movement.
10. THE POV_Roster SHALL reserve no POV for the Foreign_Signal or for an actual, alleged, or hypothesized adversary behind the Foreign_Signal.
11. THE Canon_Bible SHALL keep every proposed Foreign_Signal origin or sender account narratively unconfirmed.
12. WHEN Editorial_Review evaluates a transition between POV_IDs, THE Editorial_Review SHALL record whether the transition adds Material_Narrative_Value.

### Requirement 5: Qualitative Voice and Interiority Design

**User Story:** As a reader, I want each POV to carry a recognizable inner register that changes under pressure, so that viewpoint shifts feel human and consequential rather than mechanically labeled.

#### Acceptance Criteria

1. WHEN Calibration_Batch drafting begins, THE Voice_Briefs SHALL contain one provisional Voice_Brief for every POV in the POV_Roster.
2. THE Voice_Brief for each POV SHALL describe characteristic syntax and rhythm tendencies.
3. THE Voice_Brief for each POV SHALL describe recurring image families and sensory attention.
4. THE Voice_Brief for each POV SHALL describe emotional distance from narrated events.
5. THE Voice_Brief for each POV SHALL describe characteristic omission, evasion, and delayed notice.
6. THE Voice_Brief for each POV SHALL describe movement-specific evolution across every Story_Movement in which the POV appears.
7. THE Reverb_Profile for each POV SHALL translate spatial production terms into qualitative expectations for narrative distance and interiority without numerical sentence or style metrics.
8. THE Voice_Brief for the Anchor_POV SHALL permit distinct registers across the three Main_Parts according to dramatic context.
9. THE Voice_Brief for the Anchor_POV SHALL identify the Coda_Turn and describe the qualitative drying and narrowing of the voice before and after that turn.
10. WHEN the Calibration_Batch is reviewed, THE Editorial_Review SHALL record representative prose evidence and a `pass` or `revision` finding for every represented POV against that POV’s Voice_Brief.
11. WHEN a POV first appears after the Calibration_Batch, THE Editorial_Review SHALL record the same evidence and finding before approving that POV’s first Drafting_Batch.
12. WHEN a new POV is added to the POV_Roster, THE Drafting_Process SHALL require a completed provisional Voice_Brief before drafting that POV’s first Prose_Body.
13. THE Editorial_Review SHALL record qualitative voice findings without reducing voice quality to numeric prose metrics.

### Requirement 6: Binding Canon and Continuity

**User Story:** As the author, I want binding facts and continuity-changing inventions recorded without restricting the Canon Bible’s usefulness as a reference, so that the novel can expand the world without contradicting the songs.

#### Acceptance Criteria

1. THE Canon_Bible SHALL record every Binding_Canon_Fact and every Novel_Extension that affects later continuity.
2. THE Canon_Bible SHALL assign one stable Timeline_ID to every chronology point or interval used by more than one Chapter_File.
3. THE Canon_Bible SHALL record the December discovery, the stranger’s morning arriving eight seconds late, the April term-sheet arrival, and the page-nine transmit-enable line as Binding_Canon_Facts.
4. THE Canon_Bible SHALL record “three counties wide” as the canonical description of the null’s affected area, the visitor’s location eleven miles from the array, the two post-null years, the Tuesday kettle, and the three unhurried knocks as Binding_Canon_Facts.
5. THE Canon_Bible SHALL record The_Mindwars as an established canonical term for the undeclared war over mindspace.
6. THE Canon_Bible SHALL record the origin and sender identity of the Foreign_Signal as unestablished.
7. WHERE a Chapter_File presents an origin or sender account for the Foreign_Signal, THE Prose_Body SHALL attribute the account to a character and preserve the account as an unverified belief, theory, or claim.
8. THE Manuscript SHALL preserve consent as the rule that distinguishes a shield from an occupier.
9. THE Manuscript SHALL preserve the first casualty’s experience as an arriving thought that felt like her own.
10. THE Manuscript SHALL preserve the null as a successful defense that silences the Foreign_Signal, diminishes the defending voice, and harms civilians within the affected area canonically described as three counties wide.
11. THE Manuscript SHALL preserve the visitor’s loss as the maternal language she alone shared with her dead mother and as harm caused by the null rather than by foreign intrusion.
12. THE Manuscript SHALL portray the visitor’s affirmative consent as freely and genuinely given.
13. THE Manuscript SHALL portray the Anchor_POV’s refusal as a limit of physics and truth because a fabricated replacement would be a counterfeit capable of feeling like the visitor’s own memory.
14. WHEN the Manuscript establishes a continuity-changing fact absent from binding canon under Canon_Authority, THE Canon_Bible SHALL record the fact as a Novel_Extension before an approved later chapter depends on the fact.
15. WHEN Canon_Dialogue appears in a chapter narrated by a different POV, THE Chapter_File SHALL attribute the dialogue to the canonical speaker and preserve the dialogue’s established meaning.
16. WHEN a selected name affects continuity, THE Canon_Bible SHALL record the Character_Name, place name, institution name, or product name as a Novel_Extension.
17. THE Canon_Bible SHALL record an `authority_basis` for every Binding_Canon_Fact; SHALL recognize Canon_Lyric only from the exact five-file Canon_Source set defined by `DEC-014`; SHALL preserve speaker attribution and first-person limitation rather than silently converting testimony into omniscient fact; SHALL exclude `songs/One-Time Pad.md` from binding novel authority; and SHALL NOT promote a proposition from unratified Production_Notes, style prompts, exclude lists, generation workflow, credits, or rights metadata into binding continuity; WHERE the basis is a ratified note, THE Canon_Bible SHALL identify the approved requirement or author decision that ratified it.
18. THE Canon_Bible SHALL record as a Binding_Canon_Fact that “the final frontier” means human minds rather than outer space: people expected to cross it as explorers, but the inward frontier crossed them and made their minds the contested territory.
19. THE Manuscript SHALL treat The_Mindwars as an event that dramatizes the inward-frontier revelation rather than as the title or whole meaning of the novel.

### Requirement 7: Motif Events and Literal Phrase Discipline

**User Story:** As the author, I want carried motifs to progress through deliberate scene functions without forcing repeated lyric quotation, so that each return changes meaning instead of becoming a catchphrase.

#### Acceptance Criteria

1. THE Motif_Ledger SHALL assign every planned Motif_Event one stable unique ID and record its dramatic function, Story_Movement, planned Chapter_File, representation mode, and any Literal_Phrase_Constraint.
2. THE Chapter_Header of each Chapter_File SHALL list every Motif_Event ID assigned to that chapter.
3. WHEN a Motif_Event moves, changes function, or changes representation mode, THE Drafting_Process SHALL synchronize the Motif_Ledger, Arc_Outline, and affected Chapter_Header in the same Arc_Change or chapter revision.
4. WHEN a motif-bearing phrase, object, image, sound, or action persists within one scene, THE Motif_Ledger SHALL count the passage as one Motif_Event unless the motif gains a distinct dramatic function.
5. WHEN an Incidental_Mention adds no planned dramatic function, THE Motif_Ledger SHALL exclude the Incidental_Mention from Motif_Event counts.
6. THE Motif_Ledger SHALL permit literal quotation, paraphrase, image, action, or scene structure for a Motif_Event that carries no Literal_Phrase_Constraint.
7. THE Manuscript_Checker SHALL apply exact-word, count, and placement checks only to constraints identified in the Motif_Ledger as Literal_Phrase_Constraints.
8. THE Manuscript SHALL carry the “Come in” motif through open invitation in the Discovery_Part, conditional invitation in the Private_Defense_Part, entry after freely given consent in the Mindwars_Part, and freely given consent that cannot produce truthful restoration in the Aftermath_Coda.
9. THE Manuscript SHALL carry copper and quiet from private boundary, to imperfect collective defense, to retained protection that no longer supplies the needed human remedy.
10. THE Manuscript SHALL carry the transmission chain from spectrum-to-bone in the Discovery_Part, to wire-to-bone in the Private_Defense_Part, to voice-through-air finding a consensual human home in the Aftermath_Coda.
11. THE Manuscript SHALL carry the knock from security protocol in the Mindwars_Part, to the visitor’s compliant arrival, to the Anchor_POV’s obligation to go out and ask in the Aftermath_Coda.
12. THE Motif_Ledger SHALL record exactly two kettle Motif_Events in the Aftermath_Coda: the visitor’s account of the null and the Anchor_POV’s available human remedy.
13. THE Manuscript SHALL carry “silence has a radius” from an admission of defensive cost in the Mindwars_Part to the central accounting of the Aftermath_Coda.
14. THE Motif_Ledger SHALL designate the exact question “Did I say yes?” as a Literal_Phrase_Constraint scoped to the Mindwars_Part without fixing a total occurrence count.
15. IF the exact question “Did I say yes?” appears outside the Mindwars_Part, THEN THE Manuscript_Checker SHALL report a violation.
16. THE Manuscript SHALL place the exact question “Whose was that?” exactly twice within the Final_Passage of the final Aftermath_Coda Chapter_File and zero times elsewhere.
17. THE Record_Progression SHALL contain exactly three Motif_Events: private insistence in the Private_Defense_Part, deposition into the history of the war in the Mindwars_Part, and an entry against the Anchor_POV in the Aftermath_Coda.
18. THE Motif_Ledger SHALL mark each Record_Progression event as literal or adapted according to its scene function without requiring additional repetitions elsewhere in the Manuscript.

### Requirement 8: Ending, Tone, and the Refused Swell

**User Story:** As the author, I want the ending to become intimate, quiet, and unresolved, so that the novel answers large-scale conflict with human obligation rather than triumph.

#### Acceptance Criteria

1. THE Manuscript SHALL sustain a tender and unresolved register that grieves without self-pity.
2. THE Aftermath_Coda SHALL move from public civilian consequence toward the visitor-and-anchor encounter and the Anchor_POV’s outward obligation.
3. THE Manuscript SHALL close with the visitor’s requested restoration unmet and the broader obligation incomplete.
4. THE Manuscript SHALL express the final obligation through a quiet threshold action associated with knocking, waiting, answering, staying, or crossing a threshold.
5. THE Aftermath_Coda SHALL frame conflict as postwar accounting and attempted repair rather than renewed battle.
6. THE Manuscript SHALL resolve its final movement through restraint and continued obligation instead of renewed combat, campaign, triumphalism, moral victory, or anthemic swell.
7. THE Manuscript SHALL confine Rhetorical_Collective_Declaration to the Mindwars_Part.
8. THE Manuscript SHALL present the Foreign_Signal through effects on human characters rather than through an adversary viewpoint.
9. WHEN a Calibration_Batch or Drafting_Batch reaches Editorial_Review, THE Editorial_Review SHALL record a `pass` or `revision` finding for tenderness, restraint, emotional truth, human cost, and consistency with the Refused_Swell.
10. WHEN the final Aftermath_Coda batch reaches Editorial_Review, THE Editorial_Review SHALL record whether the ending becomes quieter and more human-scale through public consequence, intimate encounter, and outward obligation without using chapter length, room count, or numeric prose metrics as proxies.

### Requirement 9: Manuscript Organization, Site Exclusion, and Rights

**User Story:** As the author, I want the novel stored visibly and safely with prose-specific front matter, so that the manuscript remains easy to work on and cannot leak into the lyrics catalog.

#### Acceptance Criteria

1. THE Manuscript SHALL reside in a visible, dedicated manuscript directory whose name is not dot-prefixed and whose exact workspace path is selected during design.
2. THE Site_Build SHALL explicitly exclude every Manuscript markdown file from song discovery.
3. WHEN the Site_Build exclusion test runs, THE Manuscript SHALL contribute zero entries to the generated song index.
4. THE Manuscript SHALL store each chapter in its own Chapter_File.
5. THE Chapter_File SHALL use a filename that encodes the Story_Movement, zero-padded sequence number, and descriptive slug in that order under one fixed convention selected during design.
6. THE Chapter_Header SHALL contain exactly one instance of each key: `movement`, `chapter`, `title`, `pov_id`, `timeline_id`, `motif_events`, `hook`, `words`, `length_class`, and `status`; `title` SHALL be the canonical reader-facing chapter title and SHALL NOT be inferred from the filename slug.
7. THE Chapter_Header SHALL report a `words` value equal to the Prose_Word count of the Chapter_File’s Prose_Body.
8. THE Manuscript SHALL store the Arc_Outline, Canon_Bible, POV_Roster, and Motif_Ledger as distinct reference documents.
9. WHERE Voice_Briefs are stored outside the POV_Roster, THE POV_Roster SHALL link to the Voice_Briefs document.
10. THE Front_Matter SHALL identify the author and copyright holder for the novel prose.
11. THE Front_Matter SHALL state rights in the prose independently and exclude sound-recording or performance ownership claims from the novel copyright notice.
12. WHERE the author includes a source-song acknowledgment, THE Front_Matter SHALL identify all five source-song titles—*The Synaptic Frontier*, *Faraday*, *The Final Frontier*, *The Radius*, and *Case Zero*—and their relationship to the novel without importing performance or sound-recording ownership language; THE acknowledgment SHALL NOT include *One-Time Pad* as a Canon_Source.

### Requirement 10: Chapter-Local Definition of Done

**User Story:** As the author, I want a chapter-local completion gate, so that one chapter can be judged on its current text and direct references without pretending to satisfy whole-book constraints.

#### Acceptance Criteria

1. THE Chapter_Local_Gate SHALL evaluate only the current Chapter_File and its Direct_Planning_References.
2. WHEN a Chapter_Status becomes `approved` or `final`, THE Chapter_Local_Gate SHALL require zero Objective_Check violations attributable to that Chapter_File.
3. THE Chapter_Local_Gate SHALL verify required Chapter_Header metadata, Prose_Word count, Length_Class, Story_Movement, Timeline_ID, POV_ID, and Motif_Event IDs.
4. THE Chapter_Local_Gate SHALL verify agreement among the filename, Chapter_Header, Arc_Outline entry, and Direct_Planning_References for the current Chapter_File.
5. THE Chapter_Local_Gate SHALL verify each Motif_Event assignment and each Literal_Phrase_Constraint whose complete scope lies within the current Chapter_File.
6. WHEN a Chapter_Status becomes `approved` or `final`, THE Editorial_Gate SHALL record a pass for POV clarity, Voice_Brief fidelity, continuity, and Hook effectiveness.
7. WHEN a Chapter_Status becomes `approved` or `final`, THE Arc_Outline SHALL record the same Chapter_Status for that sequence number.
8. IF an `approved` or `final` Chapter_File receives a Substantive_Prose_Change, THEN THE Drafting_Process SHALL set the Chapter_Status to `revised` in both the Chapter_Header and Arc_Outline until the Chapter_Local_Gate passes again.
9. THE Chapter_Local_Gate SHALL exclude Final_Targets, whole-book POV distribution, cross-manuscript motif totals, Story_Movement length relationships, and final-ending acceptance.

### Requirement 11: Manuscript-Global Acceptance

**User Story:** As the author, I want whole-book acceptance evaluated only when the manuscript is complete, so that global structure and emotional resolution are judged at the correct scale.

#### Acceptance Criteria

1. WHEN final objective evaluation begins, THE Manuscript_Global_Gate SHALL verify every Final_Prerequisite.
2. IF a Final_Prerequisite is missing, unreadable, or incomplete, THEN THE Manuscript_Global_Gate SHALL return an `incomplete` or `revision` result rather than a pass.
3. WHEN every planned Chapter_File is present, THE Manuscript_Global_Gate SHALL verify that every Arc_Outline entry has exactly one matching Chapter_File and every Chapter_File has exactly one matching Arc_Outline entry.
4. THE Manuscript_Global_Gate SHALL verify that Chapter_Files form contiguous Story_Movement blocks in the order Discovery_Part, Private_Defense_Part, Mindwars_Part, and Aftermath_Coda.
5. THE Manuscript_Global_Gate SHALL verify that the completed chapter count equals the exact planned chapter count and that the total Prose_Word count falls within the inclusive range in the Final_Targets.
6. THE Manuscript_Global_Gate SHALL verify that the Mindwars_Part is the longest Story_Movement and the Aftermath_Coda is the shortest Story_Movement by Prose_Words.
7. THE Manuscript_Global_Gate SHALL verify that the final POV_Roster contains 3–5 human POVs and that the Anchor_POV has at least one Chapter_File in every Story_Movement.
8. THE Manuscript_Global_Gate SHALL verify every whole-book Literal_Phrase_Constraint and the synchronization of Motif_Event IDs among the Motif_Ledger and Chapter_Headers.
9. THE Manuscript_Global_Gate SHALL verify that the Site_Build produces zero Manuscript entries in the song index.
10. WHEN the complete Manuscript reaches final Editorial_Review, THE Editorial_Gate SHALL record a `pass` or `revision` finding for POV distinctness, Cross_Cut clarity, Hook effectiveness, tonal coherence, emotional truth, and the ending’s unmet obligation.
11. WHEN the Manuscript_Global_Gate and final Editorial_Gate both pass, THE Manuscript_Project SHALL permit the Manuscript to be marked `final`.
12. WHEN every final Chapter_File is present, THE Manuscript_Global_Gate SHALL verify that no Same_POV_Run exceeds three Chapter_Files or 3,600 Prose_Words, using each Chapter_File's declared `words` value.

### Requirement 12: Lightweight Objective Manuscript Checker

**User Story:** As the author, I want a lightweight automated audit of objective manuscript facts, so that preventable bookkeeping drift is caught without turning style into a score.

#### Acceptance Criteria

1. WHEN invoked, THE Manuscript_Checker SHALL report missing, duplicate, or malformed required Chapter_Header fields.
2. WHEN invoked, THE Manuscript_Checker SHALL report duplicate, missing, or out-of-order chapter sequence numbers.
3. WHEN invoked, THE Manuscript_Checker SHALL report each Chapter_File’s observed Prose_Word count, declared `words` value, observed and declared Length_Class, and compliance with the Hard_Chapter_Maximum.
4. WHEN invoked, THE Manuscript_Checker SHALL validate each `movement`, Timeline_ID, POV_ID, and Motif_Event ID against the Arc_Outline, Canon_Bible, POV_Roster, and Motif_Ledger.
5. WHEN invoked, THE Manuscript_Checker SHALL report Arc_Outline and Chapter_File disagreements in filename sequence, header sequence, Story_Movement, Timeline_ID, POV_ID, Motif_Event assignment, Hook metadata, or Chapter_Status.
6. WHEN invoked, THE Manuscript_Checker SHALL report every violation of a Literal_Phrase_Constraint, including the protected wording, count, and placement defined by that constraint.
7. WHEN invoked against the complete Manuscript, THE Manuscript_Checker SHALL report the observed chapter count and total Prose_Word count against the Final_Targets.
8. WHEN invoked with the Site_Build exclusion check, THE Manuscript_Checker SHALL verify that the generated song index contains zero Manuscript entries.
9. IF a required Manuscript input is missing, incomplete, or unreadable, THEN THE Manuscript_Checker SHALL report a clear failure and exit with a nonzero status.
10. WHEN the Manuscript_Checker reports a violation, THE Manuscript_Checker SHALL identify the affected item, observed condition, and expected condition.
11. THE Manuscript_Checker SHALL exclude name choice and capitalization from automated scoring and pass/fail evaluation.
12. THE Manuscript_Checker SHALL exclude prose voice, sentence-length artistry, emotional tone, Hook quality, POV distinctness, rhetorical force, and emotional truth from automated scoring and pass/fail evaluation.
13. THE Editorial_Review SHALL own every subjective craft judgment excluded from the Manuscript_Checker.
14. IF the Manuscript_Checker finds one or more Objective_Check violations, THEN THE Manuscript_Checker SHALL exit with a nonzero status.
15. IF the Manuscript_Checker finds zero Objective_Check violations and every required input for the requested scope is readable and complete, THEN THE Manuscript_Checker SHALL exit with a zero status.
16. WHEN invoked, THE Manuscript_Checker SHALL report each Same_POV_Run whose Chapter_File count exceeds three or whose combined Prose_Word count exceeds 3,600, identifying the run's chapters, the observed total, and the expected limit.

### Requirement 13: Incremental Delivery and Review

**User Story:** As the author, I want the novel delivered in reviewable batches with an early calibration checkpoint, so that voice and architecture can improve without making exploratory work impossible.

#### Acceptance Criteria

1. THE Drafting_Process SHALL make the 6–8 Chapter_File Calibration_Batch the first delivered review checkpoint.
2. WHEN the Approved_Baseline is established, THE Drafting_Process SHALL use subsequent Drafting_Batches of 4–8 Chapter_Files.
3. WHEN a Calibration_Batch or Drafting_Batch is delivered for approval, THE Manuscript_Checker SHALL audit the batch files and every changed cross-document reference affected by the batch.
4. WHEN a Calibration_Batch or Drafting_Batch is delivered for approval, THE Editorial_Review SHALL evaluate every chapter-level and batch-level craft gate assigned to the delivered files.
5. WHILE a delivered batch has unresolved objective or editorial findings, THE Batch_Status SHALL remain `draft` or `revised`.
6. WHILE a delivered batch has unresolved objective or editorial findings, THE Drafting_Process SHALL permit separately labeled `exploratory` drafting outside that batch.
7. WHEN a Calibration_Batch or Drafting_Batch becomes `approved`, THE Drafting_Process SHALL synchronize the Chapter_Status in every affected Chapter_Header and Arc_Outline entry.
8. WHEN a Calibration_Batch or Drafting_Batch becomes `approved`, THE Drafting_Process SHALL synchronize every changed Canon_Bible, Motif_Ledger, POV_Roster, and Voice_Brief record established by the batch.
9. WHEN author feedback changes a delivered chapter or planned arc beat, THE Drafting_Process SHALL set the affected work and batch records to `revised`.
10. WHEN author feedback sets affected work to `revised`, THE Drafting_Process SHALL apply the feedback and rerun every objective and editorial gate affected by the feedback before marking the affected work `final`.

### Requirement 14: Four-Mode Neural Communication, Consent, and Evidence

**User Story:** As a reader, I want observation, coercive influence, defensive cancellation, and consensual speech to remain technically and ethically distinct, so that neural communication creates dramatic possibility without erasing consent, privacy, evidence limits, or unresolved loss.

#### Acceptance Criteria

1. THE Canon_Bible SHALL classify every neural communication event as exactly one Neural_Communication_Mode.
2. WHEN the December discovery is represented, THE Manuscript SHALL present the event as live passive `RECEIVE` with an eight-second receiver-side offset and no transmit stage.
3. WHERE an active write carries a person-specific address and lacks current specific revocable mutual consent or matching Pair_Calibration, THE Canon_Bible SHALL classify the event as `INTRUDE`.
4. WHILE a neural communication event is classified as `INTRUDE`, THE Manuscript SHALL limit the represented effect to nonsemantic salience, valence, urgency, certainty, preference, or wanting.
5. WHERE an active transmission carries no person-specific address AND is counterphase/subtractive, THE Canon_Bible SHALL classify the event as `CANCEL` and THE Arc_Outline SHALL place the event within the Mindwars_Part.
6. WHILE a neural communication event is classified as `CANCEL`, THE Manuscript SHALL limit the represented effect to a Subtraction_Effect and SHALL represent no inserted language, proposition, order, voice, or memory.
7. WHERE a `CANCEL` event occurs, THE Canon_Bible SHALL record the affected faculties, memories, and persons as unpredictable before the event, unenumerable during the event, and incompletely mapped after the event.
8. THE Canon_Bible SHALL record every Subtraction_Effect as having no additive inverse and as unrecoverable by a further `CANCEL`, by `PAIR`, or by any combination of Neural_Communication_Modes.
9. WHERE a `CANCEL` event operates within a bounded local field volume containing one deliberately exposed consenting individual, THE Canon_Bible SHALL record that individual's current specific revocable consent; WHERE a `CANCEL` event operates at area scale, THE Canon_Bible SHALL record the authorization as institutional rather than as individual consent obtained from every affected person.
10. WHERE a Pairing_Session is authorized, THE Manuscript SHALL restrict `PAIR` to exactly two living participants with current specific revocable mutual consent and matching Pair_Calibration, SHALL associate every transported semantic contribution with a Deliberate_Send_Act, SHALL preserve unoffered thought, imagery, memory, emotion, and background mentation as private, SHALL stop semantic transport immediately when either participant pauses or revokes consent, and SHALL require confirmation, retry, or ordinary-speech fallback after clipping, latency, or integrity failure.
11. THE Pair_Calibration SHALL remain unique to one pair of living participants and unavailable for transfer to another person, a dead or absent person, a simulation, an archive, a model, or a reconstruction.
12. WHEN an authorized Pairing_Session occurs, THE Manuscript_Project SHALL preserve semantically opaque Consent_State_Metadata and Transport_Metadata that cannot reconstruct unrecorded content, SHALL initialize Content_Recording as disabled, SHALL require explicit mutual recording consent separate from consent to `PAIR` before enabling Content_Recording, and SHALL limit any resulting Pairing_Transcript to contributions transported by the protocol during that recorded Pairing_Session.
13. THE Manuscript SHALL preserve Safiya's corpus-less private maternal language as unavailable to `CANCEL` reversal, `PAIR`, Content_Recording, simulation, archive, model, and reconstruction.
14. THE Manuscript SHALL preserve the causal origin of Nia's wanting and the Provenance_Question as unconfirmed despite `CANCEL` of the Foreign_Signal, Pairing_Session metadata, Pairing_Transcripts, traffic analysis, or endpoint compromise.

### Requirement 15: Mandatory Fluent Pairing and Original Thriller Architecture

**User Story:** As a reader, I want fluent pairing to matter repeatedly inside an original, accelerating thriller with three active information threads through Chapters 1–112, followed by Safiya as a fourth Coda viewpoint that changes the moral scale, so that the mechanism drives action and ethical consequence before the story contracts to ordinary voice and obligation.

The structural obligations below are objectively checkable from Arc_Outline and Canon_Bible records. The craft obligations they used to duplicate — how a scene dramatizes benefit, whether exposition is staged as experiment and consequence, whether the Coda decelerates — are assigned to Editorial_Review by criterion 6 and by the movement Editorial_Gates, because Requirement 12.12 excludes them from automated evaluation.

#### Acceptance Criteria

1. THE Arc_Outline SHALL assign one or more mandatory Fluent_Pairing beats within each chapter range: 36–42, 56–61, 70–77, 78–93, and 94–108.
2. THE Arc_Outline SHALL assign every Pairing_Session to an existing POV chapter without creating a sender, operative, adversary, archive, simulation, or group-mind POV.
3. THE Arc_Outline SHALL preserve the four selected POVs and the provisional 56/32/33/7 chapter loads when assigning Pairing_Sessions and supporting participants.
4. WHILE Chapters 78–93 are represented, THE Manuscript SHALL limit traffic-analysis discoveries to Consent_State_Metadata and Transport_Metadata patterns rather than unrecorded semantic content.
5. WHERE compressed-clock sequencing is used, THE Arc_Outline SHALL limit compression to chronology-supported clusters without placing the complete Manuscript inside one global twenty-four-hour frame.
6. WHEN Editorial_Review evaluates a Drafting_Batch or Story_Movement containing a Fluent_Pairing beat, a technical capability introduction, or a technical capability escalation, THE Editorial_Review SHALL record representative prose evidence and a `pass` or `revision` finding for the freely chosen benefit and beginning Pair_Calibration of Chapters 36–42, the sustained on-page Fluent_Pairing conversation and consent-protocol failure and repair of Chapters 56–61, the counterphase consent challenge of Chapters 70–77, operational Fluent_Pairing as a principal engine in Chapters 78–93, ethical and infrastructural escalation in Chapters 94–108, Nia's movement toward usable self-trust in Chapters 109–112, the receding neural channel of Chapters 113–128, experiment-action-result-consequence staging of technical explanation, immediate human or institutional consequence for each capability escalation, the Mindwars_Part's fastest chapter turnover and tightest converging-thread pattern, the Aftermath_Coda's deceleration through disclosure, arrival, refusal, emotional choice, and moral remainder, and evidentiary claims no broader than the records supporting them.
7. IF Editorial_Review finds recognizable imitation of Dan Brown's or Douglas E. Richards's sentence-level prose, distinctive voice, phrasing, scenes, or characters, THEN THE Editorial_Review SHALL record a `revision` finding.
8. IF Editorial_Review finds repetitive artificial cliffhangers, exposition set pieces, a culprit reveal, renewed Coda spectacle, or neural communication presented as group mind, THEN THE Editorial_Review SHALL record a `revision` finding.
9. WHEN Editorial_Review evaluates any Drafting_Batch, THE Editorial_Review SHALL record representative prose evidence and a `pass` or `revision` finding for whether the `DEC-020` propulsion architecture works without a repeated batch formula: whether clocks used as forward engines carry credible external consequence while deliberation deadlines remain subordinate; whether endings, scene forms, chapter lengths, and settings vary for dramatic reasons rather than settling into a predictable default; whether interrupted cuts and short chapters are used only where earned rather than inserted as required tokens; whether document, drafting, or deliberation architecture accumulates into a momentum trough; and whether every chapter materially changes a fact somebody holds, a document that exists, a relationship, an access right, a physical state, or a decision that is now irreversible. THE Editorial_Review SHALL judge accumulation in batch, movement, and manuscript context and SHALL NOT determine `pass` or `revision` from a fixed occurrence count, adjacency limit, ending-kind rotation, chapter-length quota, or setting quota.
10. WHEN Editorial_Review evaluates a Story_Movement, THE Editorial_Review SHALL record a `pass` or `revision` finding for whether the movement placed characters in physical situations with bodily stakes, whether the recurring institutional counterforce took actions with material consequence rather than only arguments, and whether the movement's strongest dramatic viewpoint was allocated proportionately to its flattest; and for Chapters 62–112 specifically, whether the movement contains physical danger to a named person, a place someone should not be, movement between locations under pressure, and a consequence arriving in a body rather than in a file.
11. IF Editorial_Review finds the `DEC-020` clause 10 named tics accumulating — the self-correcting sentence, the complicity subordinate clause, the negative finding as climax, the restated technical disclaimer, or the aphoristic thesis coda — THEN THE Editorial_Review SHALL record a `revision` finding identifying the specific instances. These remain human Editorial_Gate criteria and THE Checker SHALL NOT score them, consistent with Requirement 12.12.
12. THE Manuscript SHALL NOT satisfy criteria 9 through 11 by concealing from the reader any fact a narrating viewpoint holds; Requirements 2.13 and 2.14 continue to govern, and an interrupted act is expressly not concealment.

## Approved Decisions and Deferred Design Choices

1. **Creative deliverable**: The project produces a chapter arc and finished novel chapters. Automation remains a lightweight support tool rather than the product.
2. **Structure**: The trilogy supplies exactly three Main Parts. *The Radius* supplies a shorter Aftermath/Coda in the same Manuscript, opens the second cycle through consequence and accounting, and does not extend the war.
3. **Provisional scale**: Planning begins at 120–135 chapters and 130,000–150,000 prose words, an implied average of roughly 1,000–1,200 prose words per chapter, consistent with genre precedent for short-chapter, rotating-POV, cross-cut thrillers. The post-calibration Approved_Baseline records one exact planned chapter count and an inclusive bounded word target.
4. **Chapter form**: At least 80 percent of final chapters fall within 700–1,600 words, purposeful Microchapters and longer outliers are identified in the Arc_Outline, and no chapter exceeds 2,500 words.
5. **POV count**: The arc selects 3–5 human POVs. Each POV adds material narrative value through its combined knowledge, moral pressure, and plot function. The finder/defender remains the Anchor_POV, and the Foreign_Signal and any proposed adversary receive no viewpoint.
6. **Names**: Characters, places, institutions, and products may be named. Stable Character_IDs and POV_IDs support planning, and selected names or aliases remain consistently mapped.
7. **Tense and frame**: First-person past tense governs narration, with testimony and “on the record” as the structural frame; direct dialogue and explicitly quoted matter retain their own grammatical requirements.
8. **Voice method**: Reverb remains a qualitative characterization tool expressed through Voice_Briefs and representative sample review. Sentence-length thresholds and automated style scoring are outside acceptance.
9. **Arc approval**: The complete Provisional_Arc precedes prose. A 6–8 chapter Calibration_Batch informs one dedicated Baseline_Revision_Pass before author approval. Later documented Arc_Changes remain allowed.
10. **Motif method**: The Motif_Ledger tracks dramatic events and functions rather than incidental token mentions. Automated literal checking is limited to ledgered Literal_Phrase_Constraints.
11. **Ending**: The Aftermath/Coda moves toward a quiet, unresolved threshold action and an outward obligation without renewed combat, restoration, triumph, or anthemic swell.
12. **Manuscript location**: Design selects a visible dedicated manuscript directory and an explicit Site_Build exclusion mechanism.
13. **Rights**: Front_Matter uses novel-specific authorship and prose copyright language. A concise acknowledgment of the five source songs is optional, and sound-recording or performance ownership claims do not govern the prose. *Case Zero* publication/canon status does not resolve its contradictory nonlegal rights metadata.
14. **Craft acceptance**: Tone, POV distinctness, Hook effectiveness, pacing, restraint, and emotional truth are Editorial_Gates. The Manuscript_Checker evaluates only objective manuscript facts.
15. **Delivery**: The Calibration_Batch is the first checkpoint; later batches contain 4–8 chapters, and approval synchronizes chapter and reference-document status.
16. **Canon authority**: Explicit author decisions and approved requirements outrank Canon_Lyric; Canon_Lyric in the exact five Canon_Sources is inherently binding while retaining metaphor, compression, first-person limitation, and attributed-testimony boundaries; Production_Notes and non-lyric metadata are advisory unless expressly ratified; rights and recording metadata are not story canon. `DEC-014` promotes *Case Zero* and supersedes `DEC-013`; the *One-Time Pad* draft is preserved in git history, removed from the working tree, and outside canon. Every Binding_Canon_Fact records its authority basis.
17. **Title premise**: *The Final Frontier* means the frontier was not outer space but humanity’s own minds. The trilogy moves from looking outward to recognizing people as the territory crossed. The Mindwars dramatize that revelation but do not name or exhaust the novel.
18. **Neural communication and evidence**: `DEC-012` names Electronic Speech Pairings, while `DEC-015`, as amended on 2026-09-11, fixes four non-overlapping modes: passive live `RECEIVE`; nonsemantic unconsented or uncalibrated person-specific `INTRUDE`; unaddressed subtractive `CANCEL`; and deliberately sent near-natural `PAIR` between exactly two living, currently consenting, pair-specifically calibrated participants. `CANCEL` was added because the null is an unaddressed transmission whose canonical effect is subtraction rather than the crude insertion `INTRUDE` permits; it is confined to the Mindwars_Part, has no additive inverse, cannot be aimed, and supplies no provenance. Mandatory consent/transport metadata remains semantically opaque; Content_Recording is separately mutual and disabled by default; Pairing_Transcripts prove only recorded protocol-carried content. Pair_Calibration cannot transfer, connect to the dead or absent, or reconstruct Safiya's corpus-less maternal layer, and no mode can reverse what `CANCEL` removed. Neural evidence cannot close Nia's causation or the Provenance_Question.
19. **Original thriller architecture**: `DEC-016` fixes mandatory Fluent_Pairing beats from Private Defense through late Mindwars inside the existing four POVs and 56/32/33/7 loads. The original craft architecture uses short rotating information threads, experiment/action/result/consequence exposition, immediate human stakes for capability escalation, the fastest Mindwars threading, and post-112 deceleration. Dan Brown and Douglas E. Richards are structural references only; imitation of either author's prose, voice, phrasing, scenes, or characters is rejected. Requirement 15 states the structurally checkable half of that architecture; the craft half is assigned to Editorial_Review rather than duplicated as automated acceptance criteria. As amended on 2026-09-13, `DEC-016` also caps continuous same-POV exposure by word count as well as chapter count: a Same_POV_Run may contain at most three Chapter_Files and at most 3,600 Prose_Words, because a chapter break otherwise disguises an overlong stay in one viewpoint.
