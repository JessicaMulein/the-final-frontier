#!/usr/bin/env python3
"""Task 5.4 generator: build the Mindwars_Part ArcEntry and CrossCut fences.

Temporary tooling. Deleted after the arc-outline splice is verified.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARC = ROOT / "The Final Frontier Novel" / "planning" / "arc-outline.md"

M, N, J = "POV-MARA", "POV-NIA", "POV-JULIAN"
ONSET = "TL-MINDWARS-ONSET"
CTR = "TL-MINDWARS-COUNTERPHASE"
SHIELD = "TL-MINDWARS-SHIELD"
TERR = "TL-MINDWARS-TERRITORY"
DEC = "TL-NULL-DECISION"
NIGHT = "TL-NULL-NIGHT"
POST = "TL-POSTNULL-HISTORY"
ROLL = "TL-TRUST-ROLLING-DEPOSITS"
REL = "TL-TRUST-CONDITIONED-RELEASES"

RC = "REVEAL-COUNTERPHASE-TRANSMITS"
RA = "REVEAL-AFFECTED-AREA-EXTENT"

# chapter, slug, timeline, pov, purpose, hook, cross_cuts, motifs,
# length_class, outlier_purpose, horizon_timeline, knowledge_limit, reveals
RAW = [
    (
        62, "not-only-me", ONSET, N,
        "Nia reads the first reports of arrivals in strangers, recognizes her own winter inside them, and writes her own account into custody on her own conditions rather than let a summary speak for her.",
        "She attaches her conditions to the deposit, and the reports have already proved the one thing she never wanted proved, that she was not the only one.",
        ["CUT-HER-ACCOUNT-AND-THEIR-FILE"], [], "normal", None,
        ROLL,
        "Nia knows her own experience, the scattered reports she has read, and the conditions she attaches to her deposit; she has no count, no pattern, and no sender, and she still refuses both accounts of where her certainty came from.",
        [],
    ),
    (
        63, "name-a-flag", ONSET, M,
        "Mara is asked to name an attacker and refuses to convert her measurements into public certainty, which is the one thing an emergency actually wants from a scientist.",
        "She gives them the physics and declines the flag, and the room decides she is being difficult rather than accurate.",
        ["CUT-A-FLAG-AND-A-CATEGORY"], [], "normal", None,
        ONSET,
        "Mara knows what her instruments show about addressed nonsemantic writes and nothing at all about who sends them; her private conviction about her own later handshake stays out of the room, and no measurement she holds supports it.",
        [],
    ),
    (
        64, "an-infrastructure-problem", ONSET, J,
        "Julian watches emergency authorities open a file that treats mental autonomy as infrastructure, and finds the file will accept only one account of who is doing this.",
        "The form has a field for the adversary and no field for uncertainty, and he fills it in anyway.",
        ["CUT-HER-ACCOUNT-AND-THEIR-FILE", "CUT-DEMONSTRATION-CASE-REFUSED"], [], "normal", None,
        ONSET,
        "Julian knows how the emergency classification is written and which account it will hold; he privately knows the attribution he enters is inference rather than proof, and he has no evidence about any sender.",
        [],
    ),
    (
        65, "not-a-demonstration", ONSET, N,
        "The emergency program asks Nia to stand as its demonstration case, and her refusal costs her the standing that cooperating would have bought.",
        "They want the case and not the person, so she keeps the person and loses the access.",
        ["CUT-DEMONSTRATION-CASE-REFUSED"], [], "normal", None,
        ONSET,
        "Nia knows what the program is asking of her and what refusing costs; she does not know what it has measured, and she will not let either origin account be presented as settled on her behalf.",
        [],
    ),
    (
        66, "no-border-no-demand", ONSET, M,
        "Mara compares arrivals across unrelated people for a shared border, language, or demand, and establishes that the events carry addressed nonsemantic pressure and nothing anyone can answer.",
        "Every arrival has an address and not one of them has a sentence, so there is nobody to negotiate with and nothing to negotiate about.",
        "none", [], "normal", None,
        ONSET,
        "Mara knows the arrivals are addressed writes limited to salience, urgency, certainty, and wanting, and knows addressing is a property of the event rather than evidence about its origin; she has no sender, no border, and no message.",
        [],
    ),
    (
        67, "a-category-with-a-budget", ONSET, J,
        "The classification hardens into a funded policy category assembled out of accounts like Nia's, and Julian learns that a category with a budget is harder to correct than a mistake.",
        "The category passes with a line item attached, and the people it was built out of are cited in it without having been asked.",
        ["CUT-A-FLAG-AND-A-CATEGORY"], [], "normal", None,
        ONSET,
        "Julian knows the funded category, its citations, and its exact wording; he cannot say who is causing the arrivals, and the attribution inside the category remains an inference he entered rather than a finding anyone made.",
        [],
    ),
    (
        68, "a-property-of-the-event", ONSET, M,
        "Mara runs the experiment that could have produced a sender signature, gets nothing, and the second request for a flag arrives as an instruction instead of a question.",
        "The addressing is real and tells her nothing about who is doing the addressing, and the next request does not have a question mark in it.",
        ["CUT-NO-SIGNATURE-AND-THE-UNDECLARED-WAR"], [], "normal", None,
        ONSET,
        "Mara knows the experiment's negative result and what it forecloses; she has no provenance, no carrier signature, and no way to distinguish one origin from another, and she has been told what her next answer is expected to be.",
        [],
    ),
    (
        69, "nobody-says-the-word", ONSET, J,
        "Doctrine is issued without a declaration, and Julian records a war being fought under a category name because the record has no other name available.",
        "He files the doctrine under the only heading the system offers, and in the room where it is signed nobody says the word war.",
        ["CUT-NO-SIGNATURE-AND-THE-UNDECLARED-WAR"], [], "normal", None,
        ONSET,
        "Julian knows the issued doctrine, the absence of any declaration, and the vocabulary available to him; no stable name for the conflict exists yet in the rooms he works in, and no sender has been established.",
        [],
    ),
    (
        70, "copper-for-everybody", CTR, J,
        "Julian audits collective copper as public policy and establishes that it buys real defensive time by sealing people away from the public life it was meant to protect.",
        "The shielding works, the waiting rooms are quiet, and the quiet is where everyone now has to live.",
        ["CUT-COLLECTIVE-COPPER-AND-THE-COUNTERWAVE"], ["MOT-COPPER-02"], "normal", None,
        CTR,
        "Julian knows the enclosure programs, their attenuation claims, and what they cost the people inside them; he knows of no active defense, and nothing in the enclosure record speaks to origin.",
        [],
    ),
    (
        71, "an-inverted-copy", CTR, M,
        "Mara builds an inverted copy of a captured pattern, cancels it inside a measured volume, and turns defense from enclosure into something that can be aimed at a space rather than held around a person.",
        "The pattern goes to nothing inside the volume, and nothing is exactly what comes back out of it.",
        ["CUT-COLLECTIVE-COPPER-AND-THE-COUNTERWAVE"], [], "normal", None,
        CTR,
        "Mara knows the counterwave cancels a captured pattern inside a bounded volume and that the result is removal rather than insertion; she has not yet worked out what the emission requires of the space between the emitter and the pattern, and the pattern supplies no provenance.",
        [RC],
    ),
    (
        72, "the-defense-transmits", CTR, M,
        "Mara states the result she cannot design around: to cancel a pattern inside a person's field the counterwave has to be transmitted through minds, so the defense is the same kind of act as the attack.",
        "It works because it transmits, which means there is no version of it that stays outside anybody.",
        ["CUT-TRANSMITTED-DEFENSE-AND-THE-QUESTION"], [], "microchapter",
        "Compression to the single result and its immediate ethical consequence, so the reversal lands in the time it takes her to finish the sentence.",
        CTR,
        "Mara knows that counterphase cancellation carries no address, inserts nothing, and must be transmitted through minds; she does not know what it does to a person who has agreed to it, and it identifies no sender.",
        [RC],
    ),
    (
        73, "did-i-say-yes", CTR, N,
        "Nia forces the working defense apart from its authorization, sets the terms on which she will be inside a cancellation field at all, answers for herself, and learns from the inside exactly what the field does to a person.",
        "She says yes to one bounded field on her own conditions, and then finds out what her own head sounds like while it is running.",
        ["CUT-TRANSMITTED-DEFENSE-AND-THE-QUESTION", "CUT-HER-CONDITIONS-AND-HIS-INSTRUMENT"],
        ["MOT-KNOCK-01", "MOT-YES-01"], "long-outlier",
        "Expansion to hold the whole authorization question asked and answered in one room, including the conditions Nia sets, the knock-and-wait challenge, and the concrete bodily register of a cancellation field experienced from inside.",
        ROLL,
        "Nia knows what she was asked, what she required, what she answered, and what the field felt like in her own body; she does not know whether the same operation can be aimed, widened, or undone, and nothing in the test speaks to where her earlier certainty came from.",
        [RC],
    ),
    (
        74, "only-on-the-answer", CTR, M,
        "Mara runs the consented bounded test only on Nia's current answer, coordinating it over the fluent paired channel where every contribution has to be deliberately sent, and it succeeds while taking something out of her own inner speech.",
        "The pattern is gone, the room is quiet, and a phrase she thinks with does not come back.",
        ["CUT-ENTRY-ON-A-CURRENT-ANSWER"], ["MOT-COME-03"], "normal", None,
        CTR,
        "Mara knows the test's measured success, the consent state it ran under, and the gap left in her own inner speech; she knows the field inserted nothing and cannot be run backward, and she cannot say what else it removed or from whom.",
        [],
    ),
    (
        75, "timing-and-no-content", CTR, N,
        "Nia holds the afterimage, the session's consent-state and transport metadata, and the integrity log against one another, and establishes that none of them can be promoted into evidence about origin or into a standing permission.",
        "Three records agree on when everything happened, and not one of them contains a single thing that was thought.",
        ["CUT-ENTRY-ON-A-CURRENT-ANSWER"], [], "normal", None,
        CTR,
        "Nia knows the timings, the consent states, the integrity events, and her own experience; content recording was never enabled, so no transcript exists, and the metadata is semantically opaque and silent about causes.",
        [],
    ),
    (
        76, "current-local-revocable", CTR, J,
        "Julian drafts the trial-consent instrument out of Nia's stated conditions and finds a scaled version already circulating that keeps the wording and drops the conditions.",
        "His instrument requires a current answer from a named person, and the draft on the next desk requires neither.",
        ["CUT-HER-CONDITIONS-AND-HIS-INSTRUMENT", "CUT-PROTOCOL-ON-PAPER-AND-IN-USE"], [], "normal", None,
        CTR,
        "Julian knows the conditions Nia set, the instrument he wrote from them, and the scaled draft he has seen; he does not know whether the scaled version will be authorized, and consent to a field remains distinct from consent to record content.",
        [],
    ),
    (
        77, "fluency-is-not-permission", CTR, N,
        "Nia runs a fluent paired channel while an incoming pattern is active, and a pause, a latency fault, and a fallback to spoken voice prove the consent state is operational rather than ceremonial.",
        "The channel is easy and she stops it mid-sentence anyway, because easy is not the same as allowed.",
        ["CUT-PROTOCOL-ON-PAPER-AND-IN-USE"], [], "normal", None,
        CTR,
        "Nia knows what she chose to send, when she paused, and that transport stopped where she stopped it; she cannot know what her partner did not offer, and fluency has given her access to nothing unoffered.",
        [],
    ),
    (
        78, "protection-nobody-asked-for", SHIELD, N,
        "Officials propose automatic protective transmission for whole populations, and Nia establishes that protection nobody was asked about is the same act as the thing it defends against.",
        "They call it a shield because it points the other way, and she makes them say out loud who they intend to ask.",
        ["CUT-AUTOMATIC-PROTECTION-AND-PAGE-NINE"], [], "normal", None,
        SHIELD,
        "Nia knows the proposal's wording and what it does not require of anyone; she does not know whether it will be adopted, and she will not describe anybody else's exposure as consent.",
        [],
    ),
    (
        79, "the-capability-we-condemned", SHIELD, J,
        "Julian sets the page-nine record beside the automatic-protection proposal and shows defenders requesting the capability they condemned, while refusing to let the resemblance be read as evidence about who sent anything.",
        "The same architecture, the same sentence, a different letterhead, and none of it says where the signal came from.",
        ["CUT-AUTOMATIC-PROTECTION-AND-PAGE-NINE"], [], "normal", None,
        SHIELD,
        "Julian knows what page nine printed, what the defender proposal asks for, and that the resemblance is architectural; the comparison establishes no provenance, and a party's capability is not evidence that the party transmitted.",
        [],
    ),
    (
        80, "the-first-we", SHIELD, M,
        "Mara argues the first protective network into existence and begins speaking for a public in the first person plural, which is the register the work now demands of her.",
        "She hears herself say we in a room full of strangers and does not correct it.",
        ["CUT-THE-WE-AND-THE-SINGLE-ANSWER"], [], "normal", None,
        SHIELD,
        "Mara knows what the network can hold, what it costs to run, and whose consent it currently rests on; she does not know how far it can be extended, and she is speaking for people she has never met.",
        [],
    ),
    (
        81, "two-living-people-at-a-time", SHIELD, M,
        "The protective network is worked under time pressure with fluent pairing as its coordination layer, and one deliberate pause and one drop to ordinary voice change what happens to people on the ground.",
        "The channel hands her back her own mouth at the worst possible second, and the fallback is what saves the block.",
        ["CUT-SESSION-AND-ITS-TRAFFIC"], [], "normal", None,
        SHIELD,
        "Mara knows the session's timing, what she deliberately sent, and where the protocol refused to complete; the channel carried two living people at a time and nothing that was not offered, and none of it identifies a sender.",
        [],
    ),
    (
        82, "timing-traffic-and-nothing", SHIELD, J,
        "Julian reads the night back out of consent-state and transport metadata, establishes that the pattern supports a policy claim and no evidentiary one, and watches the institutional shorthand for the whole capability harden into one term.",
        "He can prove who was paired with whom and for how long and cannot prove one word, and the briefing calls all of it Electronic Speech Pairings anyway.",
        ["CUT-SESSION-AND-ITS-TRAFFIC"], [], "normal", None,
        SHIELD,
        "Julian knows session timing, pauses, integrity events, and pairing traffic, and knows the metadata is semantically opaque; no content was recorded, so no transcript exists, and the traffic pattern establishes nothing about meaning or origin.",
        [],
    ),
    (
        83, "chosen-risk", SHIELD, N,
        "Nia takes one bounded counterphase session she chooses for herself, revocable while it runs, and fixes the difference between risk a person accepts and protection applied to her.",
        "She keeps her hand on the revocation the whole time and never uses it, and the not using is the part that is hers.",
        ["CUT-THE-WE-AND-THE-SINGLE-ANSWER", "CUT-POCKET-AND-THE-STREET"], [], "normal", None,
        SHIELD,
        "Nia knows the session she agreed to, its bounds, and that she could have stopped it at any second; she cannot speak for anyone else's exposure, and the session tells her nothing about origins.",
        [],
    ),
    (
        84, "inside-the-pocket", SHIELD, M,
        "The network holds a handful of local pockets, and Mara does the accounting that shows the defense reaches the people who could be asked and nobody else.",
        "Two streets apart, one block gets a protected night and the other gets the same night without it.",
        ["CUT-POCKET-AND-THE-STREET"], [], "normal", None,
        SHIELD,
        "Mara knows how many pockets the network holds, what each consumes in operators and consent, and who is outside them; she does not know how to widen coverage without exceeding the consent it rests on.",
        [],
    ),
    (
        85, "single-answers-do-not-scale", SHIELD, M,
        "Mara reaches the limit of a defense assembled out of individual answers and one-to-one channels, and states the arithmetic that makes the next proposal inevitable.",
        "A defense made of single yeses covers exactly as many people as have been asked, and the count is not rising fast enough.",
        "none", [], "normal", None,
        SHIELD,
        "Mara knows the coverage arithmetic, the operator limit, and the pace of the arrivals; she has no wider mechanism, no authorization for one, and no model of what a wider field would do.",
        [],
    ),
    (
        86, "theories-with-believers", TERR, J,
        "Julian catalogues the archive's competing origin theories with each one attributed to the person who holds it, and refuses the institutional request to rank them into a finding.",
        "Six accounts, six believers, no evidence, and a request to put one of them at the top of the page.",
        ["CUT-THEORIES-AND-THE-UNPARSED"], [], "normal", None,
        TERR,
        "Julian knows which people hold which theories and what each one rests on; none is confirmed, the record contains no authenticated sender, and his own filed attribution remains an inference.",
        [],
    ),
    (
        87, "not-a-language", TERR, M,
        "Half the intercepts fail to parse as any spoken language, and Mara's analytic frame collapses because she has been hunting a message inside something that was only ever structure aimed at people.",
        "There is nothing to translate, which is worse than a code, because a code would mean somebody wanted to be understood.",
        ["CUT-THEORIES-AND-THE-UNPARSED"], [], "normal", None,
        TERR,
        "Mara knows the parse failures and what they rule out; she cannot infer intent, identity, or origin from unparseable structure, and the arrivals remain nonsemantic pressure with an address on them.",
        [],
    ),
    (
        88, "recorded-once-on-purpose", TERR, N,
        "Nia and her partner enable content recording once, by separate explicit mutual consent, for a single investigative session, and the resulting transcript proves exactly what was carried and immediately becomes something other people want.",
        "The transcript is four minutes long and completely true, and by evening two institutions have asked her for it.",
        ["CUT-RECORDED-AND-UNRECORDED"], [], "normal", None,
        TERR,
        "Nia knows what she agreed to record, what the transcript contains, and that it covers only that session's deliberately sent contributions; it proves no intent, no memory, and no origin, and recording is off again unless both of them turn it on.",
        [],
    ),
    (
        89, "a-disputed-recording-state", TERR, J,
        "A disputed recording state stops an operation mid-decision, and Julian holds the line that a transcript covers one recorded session while metadata covers timing and nothing else.",
        "The operation waits while two people establish whether anybody had agreed to keep it, and the waiting costs something real.",
        ["CUT-RECORDED-AND-UNRECORDED"], [], "normal", None,
        TERR,
        "Julian knows the consent states in dispute, the integrity flags, and what a recorded session does and does not cover; he cannot recover unrecorded content and will not let a traffic pattern be entered as meaning.",
        [],
    ),
    (
        90, "the-shore-was-us", TERR, M,
        "Mara turns the inherited map around and reaches the reversal the whole event has been demonstrating: the frontier was never the distance outward, human minds are the ground being crossed, and people are the shore rather than the explorers.",
        "Every map she was raised on points away from the planet, and the only territory anyone has actually entered is the inside of a person's head.",
        ["CUT-THE-SHORE-AND-THE-BELIEVERS"], [], "long-outlier",
        "Expansion to earn the reversal in full: the inherited outward maps, the measurements that contradict them, and the position of being the crossed rather than the crosser, without letting it become a thesis about the war.",
        TERR,
        "Mara knows the measurements, the parse failures, and her own position inside the event; the reversal describes where people are standing and supplies no sender, no motive, and no provenance.",
        [],
    ),
    (
        91, "integrity-fault", TERR, N,
        "An integrity fault clips a contribution at the worst moment of a live operation, the protocol refuses to complete it, and the fallback to ordinary voice costs a measurable amount of somebody's safety.",
        "The channel offers her half a sentence it is not sure of, she refuses the half, and shouting works but not fast enough.",
        ["CUT-FALLBACK-AND-THE-BREACH-MODEL"], [], "normal", None,
        TERR,
        "Nia knows the clipped contribution, the integrity flag, and what the delay cost; she cannot know what the fragment was meant to be, and no log will reconstruct it.",
        [],
    ),
    (
        92, "ranked-by-belief", TERR, J,
        "The archive's theories are ranked under institutional pressure and Julian records the ranking as belief rather than finding, while the first-casualty attribution sets into something no later correction can reach.",
        "He writes believed by beside every line, and the summary that quotes him drops those two words.",
        ["CUT-THE-SHORE-AND-THE-BELIEVERS"], [], "normal", None,
        TERR,
        "Julian knows the ranking, its basis in belief, and the wording he used; custody warrants provenance and not truth, and the first-casualty attribution he entered stays an inference he cannot correct into fact.",
        [],
    ),
    (
        93, "one-synchronized-night", TERR, M,
        "The network holds its pockets while Mara's model predicts one synchronized event past the capacity of copper, operators, and one-to-one channels, which turns the defense question from coverage into scale.",
        "The model puts the whole thing on a single night, and every defense she has is built one room and one answer at a time.",
        ["CUT-FALLBACK-AND-THE-BREACH-MODEL"], [], "normal", None,
        TERR,
        "Mara knows the model's prediction, its confidence, and the capacity of every defense she holds; she does not know what a wider field would remove, and she has no authorization to find out.",
        [],
    ),
    (
        94, "enrolled-by-default", DEC, N,
        "Institutional pressure moves to default pairing enrollment, centralized metadata, and standing continuity assumptions, and Nia names each one as a claim that reaches past a current local answer.",
        "Their word for it is enrollment and hers is default, and she refuses to let her own session logs be the template.",
        ["CUT-DEFAULT-ENROLLMENT-AND-THE-MODEL"], [], "normal", None,
        DEC,
        "Nia knows what the enrollment proposal assumes and what her own consent state actually permits; calibration remains hers and her partner's alone and cannot be handed to anyone, and she does not know whether the proposal will pass.",
        [],
    ),
    (
        95, "the-only-defense-in-the-model", DEC, M,
        "Mara's model returns one defense likely to stop a synchronized event, a single broad unaddressed field, together with the prediction that it will subtract from people it cannot identify beforehand.",
        "The model gives her one answer that works and cannot give her the name of a single person it will take something from.",
        ["CUT-DEFAULT-ENROLLMENT-AND-THE-MODEL"], [], "normal", None,
        DEC,
        "Mara knows the model predicts both silence and subtraction and that it cannot identify which faculties, memories, or people are vulnerable; nothing the field removes has an additive inverse, and no authorization exists yet.",
        [RA],
    ),
    (
        96, "three-counties-wide", DEC, J,
        "Official summaries call the field's civilian effects negligible, and Julian finds the working annex that describes the affected area as three counties wide.",
        "The summary says negligible in one clause, and the annex beneath it describes an affected area three counties wide.",
        ["CUT-NEGLIGIBLE-AND-THE-EXTENT", "CUT-THE-EXTENT-RETURNED"], [], "normal", None,
        DEC,
        "Julian knows the summary's wording and the annex's description of the affected area as three counties wide; the description is an extent rather than a geometry, it names no county, and it carries no casualty inventory.",
        [RA],
    ),
    (
        97, "it-will-not-take-a-list", DEC, M,
        "Mara tries to aim, bound, and enumerate the field's effects, and establishes the properties that make the decision unbearable: nothing predictable before, nothing enumerable during, nothing fully mapped after, and nothing that can be put back.",
        "She spends the night trying to hand the field a list of names, and it will not take one.",
        ["CUT-NEGLIGIBLE-AND-THE-EXTENT"], [], "normal", None,
        DEC,
        "Mara knows the field carries no address, inserts nothing, and cannot be reversed by any mode she has; she cannot predict, enumerate, or afterwards fully map who it affects, and cancelling a pattern yields nothing about where the pattern came from.",
        [],
    ),
    (
        98, "nobody-can-be-asked", DEC, N,
        "Nia refuses the manufactured unanimity the decision wants and establishes that neither a pair's consent nor a recorded transcript can answer for everyone inside the affected area.",
        "They ask her to say the affected area agrees, and she tells them exactly how many people she is entitled to answer for.",
        ["CUT-NOBODY-TO-ASK"], [], "normal", None,
        DEC,
        "Nia knows what consent she can give and for whom, and knows how long real consent takes to collect; she does not know whether the field will be authorized without it, and no transcript or metadata can supply another person's answer.",
        [],
    ),
    (
        99, "authorized-not-consented", DEC, J,
        "Julian writes the emergency authorization and makes its exact character permanent in the record: an institutional instrument standing where individual consent cannot be obtained, and never a substitute for it.",
        "He writes authorized in the box and refuses to let the word consented appear anywhere on the page.",
        ["CUT-NOBODY-TO-ASK"], [], "normal", None,
        DEC,
        "Julian knows which body authorized the field, under which instrument, and what the instrument does not claim; no individual consent was collected from the affected area, and the authorization establishes nothing about origin.",
        [],
    ),
    (
        100, "my-name-in-the-operator-field", DEC, M,
        "Mara takes the emission herself instead of assigning it, which fixes responsibility on one named person before anything is switched on.",
        "She puts her own name in the operator field, and the argument about who is responsible ends in one line of a form.",
        "none", [], "normal", None,
        DEC,
        "Mara knows the authorization, the model, and what she is choosing to be responsible for; she does not know what the field will take, from whom, or whether the predicted silence will arrive at all.",
        [],
    ),
    (
        101, "silence-has-a-radius", DEC, M,
        "The decision is spent at full cost in Mara's own words: the defense will work, its reach is the same reach that will take things from civilians across an affected area three counties wide, and she says so before it runs rather than after.",
        "She admits on the record that the silence she is about to make has a reach, and that people she will never meet are inside it.",
        ["CUT-THE-EXTENT-RETURNED"], ["MOT-RADIUS-01"], "long-outlier",
        "Expansion to spend the decision at full cost in one place: the modeled benefit, the admitted civilian reach of a defensive silence, and the refusal to convert the canonical extent into a comforting figure.",
        DEC,
        "Mara knows the model, the authorization, and the canonical description of the affected area as three counties wide; the extent is not a geometry she can compute, she cannot name anyone inside it, and nothing has been emitted yet.",
        [RA],
    ),
    (
        102, "a-room-with-a-door", NIGHT, N,
        "As the arrivals peak, Nia runs a consent shelter where every entry is one person's own current answer, and keeps a written list of who came in.",
        "The peak is loud enough that people arrive already certain of things they never decided, and she asks each of them at the door anyway.",
        ["CUT-PEAK-AND-THE-PHASE", "CUT-WHO-CAME-IN"], [], "normal", None,
        NIGHT,
        "Nia knows who came through her door, what each of them agreed to, and how the night sounds from inside the shelter; she does not know what the defense is doing outside it and cannot account for anyone who never arrived.",
        [],
    ),
    (
        103, "into-phase", NIGHT, M,
        "Mara reads the same peak as a measurable phase, matches it, and starts the emission.",
        "She holds the two patterns against each other until they cancel, and then she does not stop.",
        ["CUT-PEAK-AND-THE-PHASE", "CUT-FIELD-AND-THE-INSTRUMENT"], [], "microchapter",
        "Compression to the single act of matching phase and starting the field, so the operation begins in about the time it takes to do it.",
        NIGHT,
        "Mara knows the incoming phase, the counterphase she is emitting, and that the field carries no address; she cannot see what it is subtracting, from whom, or how far it has already reached.",
        [],
    ),
    (
        104, "timestamped-while-it-runs", NIGHT, J,
        "Julian timestamps the authorization, its scope, and the consent state of every coordinating channel while the field is running, so the night will have a custody record nobody can soften later.",
        "He writes down the exact minute a page of paper began removing things from people, and the page does not contain one name.",
        ["CUT-FIELD-AND-THE-INSTRUMENT", "CUT-A-PAGE-AND-A-DOORWAY"], [], "normal", None,
        NIGHT,
        "Julian knows the authorization's exact scope, the minute the field started, and the consent state of each coordinating channel; the instrument names no affected person, no content is recorded, and he cannot know what is being removed.",
        [],
    ),
    (
        105, "one-answer-at-the-door", NIGHT, N,
        "One arrival at the shelter door is in no condition to answer for herself, and Nia has thirty seconds to decide what that permits her to do.",
        "She cannot get a current answer out of the woman on the step, so she stands in the doorway with her and does not carry her in.",
        ["CUT-A-PAGE-AND-A-DOORWAY", "CUT-THE-LOCK-AND-THE-UNSHELTERED"], [], "microchapter",
        "Compression to a single interruption inside the night, so one person's unobtainable answer arrives at the pace it actually arrives.",
        NIGHT,
        "Nia knows what she can and cannot obtain from the person in front of her and what her own rule requires of her; she does not know what is happening across the rest of the area, and she will not answer for anyone who cannot answer.",
        [],
    ),
    (
        106, "quieter-in-here", NIGHT, M,
        "The lock holds across everyone the field reaches, and Mara notices her own inner speech has gone measurably thinner while she is still holding it.",
        "She reaches for the phrase she checks her own work with, finds a flat place where it used to be, and keeps her hand on the emitter.",
        ["CUT-THE-LOCK-AND-THE-UNSHELTERED", "CUT-A-THINNER-VOICE-AND-A-CLEAN-LOG"], [], "normal", None,
        NIGHT,
        "Mara knows the lock is holding, knows what she can no longer reach in her own inner speech, and knows the field inserted nothing; she cannot enumerate who else it has reached and cannot undo any of it.",
        [],
    ),
    (
        107, "clean-silence", NIGHT, J,
        "The carrier stops, and Julian records a clean silence that contains no surrender, no counterparty, and no sender.",
        "The trace goes flat at a minute he can name, and he writes down that nobody said anything, because nobody ever did.",
        ["CUT-A-THINNER-VOICE-AND-A-CLEAN-LOG", "CUT-SILENCE-WITHOUT-A-COUNTERPARTY"], [], "microchapter",
        "Compression to the instant the carrier stops, so the silence arrives without commentary and the custody entry is the only thing in the room.",
        NIGHT,
        "Julian knows the exact time the carrier stopped and that nothing accompanied it; there is no surrender, counterparty, or authenticated sender, and the stop resolves no provenance.",
        [],
    ),
    (
        108, "what-it-took", NIGHT, M,
        "Mara shuts the field down into a silence covering an affected area three counties wide, and the first reports arrive of things it removed from people no list will ever hold.",
        "The defense worked, the reports start before morning, and there is no procedure anywhere for putting any of it back.",
        ["CUT-SILENCE-WITHOUT-A-COUNTERPARTY", "CUT-WHO-CAME-IN"], [], "long-outlier",
        "Expansion to hold the operational end of the night and the beginning of its cost in one place, including the canonical extent and the absent inverse, without resolving what was lost.",
        NIGHT,
        "Mara knows the field ran across an affected area canonically described as three counties wide, knows the incoming patterns stopped, and knows the first reports of loss; the affected set cannot be enumerated, nothing removed can be restored, and no report tells her who sent anything.",
        [],
    ),
    (
        109, "into-the-history", POST, J,
        "Authorities announce a success with no surrender and no counterparty, and Julian enters the consent dispute and the uncounted civilian uncertainty into the history the event is now named by.",
        "The announcement runs one paragraph with no absences in it, so he files the absences into the history under a heading of their own.",
        ["CUT-HISTORY-AND-THE-WORD-SAVED", "CUT-DEPOSITED-AND-SUMMARIZED"], ["MOT-RECORD-02"], "normal", None,
        POST,
        "Julian knows the announcement, the authorization trail, the consent dispute, and that the civilian losses are uncounted; there is no counterparty and no authenticated sender, and the attribution he entered earlier remains an inference custody cannot correct.",
        [],
    ),
    (
        110, "not-the-word-saved", POST, N,
        "Nia refuses saved as a complete description of what happened to the area, and takes a live decision on her own judgment without first settling where her old certainty began.",
        "She makes the call, stands behind it, and stops requiring an origin before she is allowed to trust herself.",
        ["CUT-HISTORY-AND-THE-WORD-SAVED"], [], "normal", None,
        REL,
        "Nia knows the official summary, the first conditioned release beside it, and her own judgment on the call she has just made; both accounts of her earlier certainty remain unverified, and nothing she has done forgives anyone or endorses any archive.",
        [],
    ),
    (
        111, "provenance-not-truth", POST, J,
        "Official summaries begin smoothing inference into fact while the first conditioned, provenance-preserving releases go out to compete with them, and Julian establishes that nobody is going to adjudicate between the two.",
        "Two accounts of the same night are public, both are properly sourced, and there is no body anywhere whose job it is to decide.",
        ["CUT-DEPOSITED-AND-SUMMARIZED"], [], "normal", None,
        POST,
        "Julian knows what the summaries assert, what the conditioned releases contain, and that embargoes hold while complete holdings stay closed; custody warrants provenance rather than truth, and the first-casualty attribution stands uncorrected.",
        [],
    ),
    (
        112, "the-line-held", POST, M,
        "Mara shuts down active counterphase for good, withdraws behind the copper she kept, and closes the war on a held line and an accounting nobody has started.",
        "The last thing she does as a defender is disconnect the emitter, and the silence she is left standing in is the one she made.",
        "none", [], "normal", None,
        POST,
        "Mara knows the emitter is down, knows the line held, and knows reports of loss are still arriving without a count; she cannot restore anything the field removed and has no accounting to offer anyone who asks.",
        [],
    ),
]

entries = []
for (ch, slug, tl, pov, purpose, hook, cuts, motifs, lc, op, hz, kl, rev) in RAW:
    entries.append({
        "chapter": ch,
        "filename": f"chapters/mindwars-part/mindwars-part-{ch:03d}-{slug}.md",
        "movement": "mindwars_part",
        "timeline_id": tl,
        "pov_id": pov,
        "purpose": purpose,
        "hook": hook,
        "cross_cuts": cuts,
        "motif_events": motifs,
        "estimated_length_class": lc,
        "outlier_purpose": op,
        "status": "planned",
        "calibration_selected": False,
        "representative_purpose": None,
        "record_horizon": {
            "through_timeline_id": hz,
            "knowledge_limit": kl,
        },
        "reveal_ids": rev,
    })

# cross_cut_id, chapters, shared_timeline_id, shared_reveal_id, shared_consequence,
# handoff_mode, [(chapter, value)...], replay_boundary
CUTS = [
    (
        "CUT-HER-ACCOUNT-AND-THEIR-FILE", [62, 64], ONSET, None,
        "One woman's account written on her own conditions and an emergency file that will hold only one account of who is doing this are created in the same week, and both cannot be honored.",
        "contradiction-cut",
        [
            (62, "Nia supplies her own first-person account of the first casualty, the conditions she attaches to it, and her refusal of both origin accounts."),
            (64, "Julian supplies the classification form itself, the single field it reserves for an adversary, and the absence of any field for uncertainty."),
        ],
        "Chapter 64 begins in the authorities' room with the form already drafted and never restates Nia's account, her conditions, or her deposit.",
    ),
    (
        "CUT-A-FLAG-AND-A-CATEGORY", [63, 67], ONSET, None,
        "A refusal to supply public certainty leaves a vacuum that policy fills with a funded category, so declining to name an enemy does not prevent one from being written down.",
        "causal-cut",
        [
            (63, "Mara supplies the refusal itself, the measurements she offers in its place, and the cost of being accurate in a room that wants a name."),
            (67, "Julian supplies the approved category, its appropriation line, and the cited accounts of people nobody asked."),
        ],
        "Chapter 67 opens on the approved text and its budget line and does not re-narrate Mara's meeting or repeat her refusal.",
    ),
    (
        "CUT-DEMONSTRATION-CASE-REFUSED", [64, 65], ONSET, None,
        "One institutional decision is experienced as a procedural need for a demonstrable case on one side of the door and as a demand to become one on the other.",
        "threshold-cut",
        [
            (64, "Julian supplies the program's need for one nameable demonstration case and the moment he realizes the file has started looking for a person."),
            (65, "Nia supplies the refusal from the other side of that request, including what cooperating would have bought her and what declining takes away."),
        ],
        "Chapter 65 begins with the request already made to her and repeats none of Julian's procedural reasoning or his view of the file.",
    ),
    (
        "CUT-NO-SIGNATURE-AND-THE-UNDECLARED-WAR", [68, 69], ONSET, None,
        "The last experiment that could have produced an attributable sender returns nothing, and doctrine is issued days later with no declaration under it.",
        "causal-cut",
        [
            (68, "Mara supplies the experiment, its negative result, and the second request for a flag arriving as an instruction."),
            (69, "Julian supplies the signing room, the issued doctrine, and the fact that nobody in it uses the word war."),
        ],
        "Chapter 69 begins at the signing with the doctrine already drafted and never restates Mara's method, her result, or her refusal.",
    ),
    (
        "CUT-COLLECTIVE-COPPER-AND-THE-COUNTERWAVE", [70, 71], CTR, None,
        "Enclosure buys exactly the interval in which an active defense becomes thinkable, and the interval is paid for by the people sealed inside it.",
        "causal-cut",
        [
            (70, "Julian supplies the policy audit of collective copper: what it attenuates, what it costs in ordinary life, and how little of a public it can hold."),
            (71, "Mara supplies the bench result that ends the enclosure era, an inverted copy of a captured pattern taken to nothing inside a measured volume."),
        ],
        "Chapter 71 begins at Mara's bench with the captured pattern already in hand and never restates the enclosure programs or Julian's audit.",
    ),
    (
        "CUT-TRANSMITTED-DEFENSE-AND-THE-QUESTION", [72, 73], CTR, RC,
        "Establishing that the defense has to be transmitted through minds is what makes the authorization question unavoidable, so the physics creates the consent problem rather than following it.",
        "causal-cut",
        [
            (72, "Mara supplies the result and its immediate consequence: cancellation is unaddressed, subtractive, and cannot be run from outside anybody."),
            (73, "Nia supplies the challenge, the conditions she requires, her own answer, and the bodily register of the field from inside it."),
        ],
        "Chapter 73 begins with Nia hearing the finished result rather than watching it derived, and Mara's bench reasoning is not restated.",
    ),
    (
        "CUT-HER-CONDITIONS-AND-HIS-INSTRUMENT", [73, 76], CTR, None,
        "Conditions one person states aloud in a test room become the written trial-consent instrument, and a scaled draft is already circulating that keeps the wording and drops the conditions.",
        "delayed-return",
        [
            (73, "Nia supplies the conditions as she sets them: current, specific, local, revocable, and separate from any consent to record content."),
            (76, "Julian supplies the instrument drafted from those conditions and the scaled version on the next desk that requires none of them."),
        ],
        "Chapter 76 opens on the drafting and the competing document and does not replay the test, the challenge, or Nia's answer.",
    ),
    (
        "CUT-ENTRY-ON-A-CURRENT-ANSWER", [74, 75], CTR, None,
        "One bounded consented run is the same event from the emitter side and from inside the volume, and neither side produces any record of what was removed.",
        "threshold-cut",
        [
            (74, "Mara supplies the operational side: the current answer she waited for, the deliberate sends that coordinated the run, and the gap left in her own inner speech."),
            (75, "Nia supplies the record side: an afterimage held against consent-state metadata, transport metadata, and an integrity log that contain no content whatever."),
        ],
        "Chapter 75 begins after the run with the logs in front of her and does not re-narrate the emission, the count-in, or Mara's coordination.",
    ),
    (
        "CUT-PROTOCOL-ON-PAPER-AND-IN-USE", [76, 77], CTR, None,
        "A written consent instrument and the same consent state under live pressure disagree about what fluency permits, and the live session is the one that decides.",
        "contradiction-cut",
        [
            (76, "Julian supplies the drafted rule, its separations, and his assumption that a written current-answer requirement will hold in an emergency."),
            (77, "Nia supplies the session itself, where a pause, a latency fault, and a fallback to spoken voice show the requirement enforced by a person rather than by a page."),
        ],
        "Chapter 77 begins mid-session under active pressure and never restates the instrument's clauses or Julian's drafting.",
    ),
    (
        "CUT-AUTOMATIC-PROTECTION-AND-PAGE-NINE", [78, 79], SHIELD, None,
        "A proposal to protect populations without asking them sends the old specification back into the room, and the defenders turn out to be requesting the capability they condemned.",
        "causal-cut",
        [
            (78, "Nia supplies the proposal's wording, what it does not require of anyone, and the demand that somebody name who will be asked."),
            (79, "Julian supplies the page-nine comparison, its architectural exactness, and the limit that it establishes nothing about who sent anything."),
        ],
        "Chapter 79 begins in the record room with both documents open and does not replay the meeting or Nia's objection.",
    ),
    (
        "CUT-THE-WE-AND-THE-SINGLE-ANSWER", [80, 83], SHIELD, None,
        "A collective register is adopted to argue a network into existence, and the only authorization the network actually runs on is one named person's revocable yes.",
        "delayed-return",
        [
            (80, "Mara supplies the argument, the network it produces, and the first time she hears herself speak for a public she has never met."),
            (83, "Nia supplies the single answer that register cannot supply: chosen, bounded, and revocable for as long as it runs."),
        ],
        "Chapter 83 begins with Nia's own session already scheduled and repeats neither Mara's argument nor the network's design.",
    ),
    (
        "CUT-SESSION-AND-ITS-TRAFFIC", [81, 82], SHIELD, None,
        "One coordinated night exists twice, as lived speech with a fallback in it and as timing, pauses, and integrity flags with no meaning anywhere in them.",
        "sensory-match",
        [
            (81, "Mara supplies the session as it was worked: deliberate sends under time pressure, one pause, and a drop to her own voice that changes what happens on a street."),
            (82, "Julian supplies the same hours as metadata, the policy claim the pattern supports, the evidentiary claim it does not, and the term the briefing uses for all of it."),
        ],
        "Chapter 82 begins from the metadata rather than the street and may not supply any content the protocol never recorded.",
    ),
    (
        "CUT-POCKET-AND-THE-STREET", [83, 84], SHIELD, None,
        "The defense that makes one person's chosen night survivable is the same reason a street two blocks away has the identical night without any of it.",
        "contradiction-cut",
        [
            (83, "Nia supplies what being inside a protected pocket actually covers and what it costs to be asked properly."),
            (84, "Mara supplies the coverage accounting: how many pockets hold, what each consumes, and who is outside every one of them."),
        ],
        "Chapter 84 opens on the accounting rather than inside a session and does not re-narrate Nia's night or her hand on the revocation.",
    ),
    (
        "CUT-THEORIES-AND-THE-UNPARSED", [86, 87], TERR, None,
        "An archive full of competing origin theories is answered by a measurement showing half the intercepts parse as no language at all, which leaves every theory intact and none of them supportable.",
        "contradiction-cut",
        [
            (86, "Julian supplies the theories with their believers attached and his refusal to rank belief into a finding."),
            (87, "Mara supplies the parse failures and the collapse of the frame that assumed a message was there to read."),
        ],
        "Chapter 87 begins at the analysis rather than in the archive and restates none of Julian's catalogue or its holders.",
    ),
    (
        "CUT-RECORDED-AND-UNRECORDED", [88, 89], TERR, None,
        "One deliberately recorded session and every unrecorded one around it fix the exact boundary of what a pairing can ever prove, and institutions immediately press on both sides of it.",
        "threshold-cut",
        [
            (88, "Nia supplies the single session she and her partner chose to record, what the transcript contains, and how quickly other people want it."),
            (89, "Julian supplies the disputed recording state that stops an operation, the flags he can read, and the content he refuses to infer."),
        ],
        "Chapter 89 begins with the dispute already stopping the operation and does not reproduce Nia's transcript or her decision to record.",
    ),
    (
        "CUT-THE-SHORE-AND-THE-BELIEVERS", [90, 92], TERR, None,
        "While an institution ranks candidate crossers, the position that actually changed is the one everybody is standing in, and neither account converts into the other.",
        "contradiction-cut",
        [
            (90, "Mara supplies the reversal: inherited outward maps, measurements that contradict them, and human minds as the ground being crossed rather than the vantage point."),
            (92, "Julian supplies the ranking, the words believed by that he writes beside every line, and the summary that removes them."),
        ],
        "Chapter 92 begins inside the institutional process, never restates Mara's reversal, and does not adopt it as a finding.",
    ),
    (
        "CUT-FALLBACK-AND-THE-BREACH-MODEL", [91, 93], TERR, None,
        "The delay one integrity fault costs on one street is the same limit the model scales into a single synchronized night, so the protocol's honesty and the defense's insufficiency are one fact.",
        "causal-cut",
        [
            (91, "Nia supplies the clipped contribution, the refusal to complete it, and the measurable cost of shouting instead."),
            (93, "Mara supplies the model that puts the whole event on one night and the capacity arithmetic that cannot meet it."),
        ],
        "Chapter 93 begins at the model rather than on the street and does not re-narrate the fault, the fallback, or its outcome.",
    ),
    (
        "CUT-DEFAULT-ENROLLMENT-AND-THE-MODEL", [94, 95], DEC, None,
        "A modeled emergency makes default enrollment, centralized metadata, and standing continuity look reasonable in the same week they are proposed, so the physics supplies the argument for abandoning a current answer.",
        "causal-cut",
        [
            (94, "Nia supplies each proposed assumption named exactly, and her refusal to let her own session logs become the template."),
            (95, "Mara supplies the model's single working answer and its second prediction, that the field will subtract from people it cannot identify beforehand."),
        ],
        "Chapter 95 begins at the model output and does not restate the enrollment proposal or Nia's objections to it.",
    ),
    (
        "CUT-NEGLIGIBLE-AND-THE-EXTENT", [96, 97], DEC, None,
        "An official summary calling civilian effects negligible and a mechanism that refuses to accept a list of names describe the same operation, and only one of them can be true.",
        "contradiction-cut",
        [
            (96, "Julian supplies the summary's wording and the working annex describing the affected area as three counties wide."),
            (97, "Mara supplies the attempt to aim or bound the field and the properties that defeat it: unpredictable before, unenumerable during, incompletely mapped after, and no way back."),
        ],
        "Chapter 97 begins at the bench with the extent already known and does not re-narrate Julian's search or quote his annex.",
    ),
    (
        "CUT-THE-EXTENT-RETURNED", [96, 101], DEC, RA,
        "A width found in a working annex returns as an admission spoken on the record by the person who will emit the field, and it stays an extent rather than becoming a figure.",
        "delayed-return",
        [
            (96, "Julian supplies the discovery of the documented extent and the summary language it contradicts."),
            (101, "Mara supplies the same extent as accepted cost, said aloud before the field runs and never converted into geometry."),
        ],
        "Chapter 101 speaks the extent as her own admission, does not re-narrate Julian's discovery, and re-derives nothing from the description.",
    ),
    (
        "CUT-NOBODY-TO-ASK", [98, 99], DEC, None,
        "Consent that cannot be collected in time and an authorization written to stand where it is missing meet at one decision, and the record has to say which of the two it holds.",
        "threshold-cut",
        [
            (98, "Nia supplies the refusal of manufactured unanimity and the exact limit of whom a pair's consent or a transcript can answer for."),
            (99, "Julian supplies the instrument, the body that issued it, and his refusal to let the word consented appear anywhere on it."),
        ],
        "Chapter 99 begins at the drafting with the decision already taken and does not replay Nia's refusal or argue it again.",
    ),
    (
        "CUT-PEAK-AND-THE-PHASE", [102, 103], NIGHT, None,
        "The same peak minute is a doorway full of people arriving certain of things they never chose and a measurable phase that has to be matched, and each is happening while the other is.",
        "temporal-braid",
        [
            (102, "Nia supplies the peak as it arrives in people: what they say at the door and the answer she takes from each of them anyway."),
            (103, "Mara supplies the peak as a phase: the match, the moment the two patterns cancel, and the decision not to stop."),
        ],
        "Chapter 103 stays at the emitter for its whole length and contains nothing of the shelter, the doorway, or anyone arriving.",
    ),
    (
        "CUT-WHO-CAME-IN", [102, 108], NIGHT, None,
        "The shelter's intake list is the only enumerated set of people the night produces, and the field's affected set is never enumerable at all.",
        "delayed-return",
        [
            (102, "Nia supplies the written list, with times and what each person agreed to, kept because somebody in this night should be countable."),
            (108, "Mara supplies the completed operation and the fact that no equivalent list can be made for the area the field crossed."),
        ],
        "Chapter 108 returns to the question of who can be counted from the operator's end, and it does not enter the shelter or reproduce Nia's list.",
    ),
    (
        "CUT-FIELD-AND-THE-INSTRUMENT", [103, 104], NIGHT, None,
        "The field runs on a page, and the page is being timestamped in the same minutes the field is removing things, so the authority and the effect are simultaneous rather than sequential.",
        "temporal-braid",
        [
            (103, "Mara supplies the emission itself and the fact that she is running it on an authorization she did not write."),
            (104, "Julian supplies the custody record made while it runs: the exact minute, the instrument's scope, and the consent state of every coordinating channel."),
        ],
        "Chapter 104 stays with the record and the clock and never re-narrates the phase match or the emitter.",
    ),
    (
        "CUT-A-PAGE-AND-A-DOORWAY", [104, 105], NIGHT, None,
        "One page authorizes an area and names nobody; one doorway can take exactly one person's answer at a time; together they are the night's whole account of permission.",
        "contradiction-cut",
        [
            (104, "Julian supplies what the instrument authorizes, what it deliberately does not claim, and the absence of any affected-person list inside it."),
            (105, "Nia supplies the doorway case the instrument cannot reach, an arrival who cannot give a current answer and thirty seconds in which to decide what that permits."),
        ],
        "Chapter 105 stays on the step with one person and contains none of the authorization, the clock, or Julian's record.",
    ),
    (
        "CUT-THE-LOCK-AND-THE-UNSHELTERED", [105, 106], NIGHT, None,
        "In the same hour one defense reaches only the people who came and were asked, and the other reaches everyone in the area without asking any of them.",
        "temporal-braid",
        [
            (105, "Nia supplies the people she cannot reach, the ones with no room to come to, and her refusal to speak for them."),
            (106, "Mara supplies the lock holding across the whole area, including everyone who never came to a door."),
        ],
        "Chapter 106 stays at the emitter through the hour and does not enter the shelter or restate the doorway decision.",
    ),
    (
        "CUT-A-THINNER-VOICE-AND-A-CLEAN-LOG", [106, 107], NIGHT, None,
        "A flat place where a phrase used to be and an instrument trace with nothing in it are the same silence arriving in two registers inside the same minutes.",
        "sensory-match",
        [
            (106, "Mara supplies the subjective register of the loss, reaching for the phrase she checks her own work with and finding a flat place, with her hand still on the emitter."),
            (107, "Julian supplies the instrumental register, the trace going flat at a time he can name to the minute."),
        ],
        "Chapter 107 is the stop and the custody entry only; it reports nothing of Mara's interior state and does not re-narrate the lock.",
    ),
    (
        "CUT-SILENCE-WITHOUT-A-COUNTERPARTY", [107, 108], NIGHT, None,
        "The carrier's stop is the whole of the victory and produces no surrender, no counterparty, and no sender, so the only thing that follows it is cost.",
        "causal-cut",
        [
            (107, "Julian supplies the aftermath of the stop: no surrender, no counterparty, no claim, and a record that has to say so."),
            (108, "Mara supplies the shutdown, the affected area the silence covers, and the first reports of what it removed."),
        ],
        "Chapter 108 begins with the shutdown from the operator's position and does not repeat the custody entry or the timing of the stop.",
    ),
    (
        "CUT-HISTORY-AND-THE-WORD-SAVED", [109, 110], POST, None,
        "One night is deposited into history as a consent dispute with uncounted losses and refused in person as a word that describes what happened to nobody.",
        "contradiction-cut",
        [
            (109, "Julian supplies the deposition itself, the consent dispute, the civilian uncertainty, and the heading he files them under."),
            (110, "Nia supplies the refusal of the word saved and the live decision she makes on her own judgment with no origin under it."),
        ],
        "Chapter 110 stays with her own call and her own reading of the two public accounts and does not re-narrate Julian's deposition.",
    ),
    (
        "CUT-DEPOSITED-AND-SUMMARIZED", [109, 111], POST, None,
        "What is deposited with its uncertainty intact comes back as a summary with the uncertainty smoothed out, and no institution exists whose job is to choose between them.",
        "delayed-return",
        [
            (109, "Julian supplies the deposit as made, with the dispute and the uncounted losses under a heading of their own."),
            (111, "Julian supplies the public contest that follows: summaries hardening inference into fact, conditioned releases keeping provenance, and no body anywhere to adjudicate."),
        ],
        "Chapter 111 begins after publication, treats the deposit as already made, and neither re-narrates the act nor reopens the heading.",
    ),
]

cuts = []
for (cid, chs, tl, rev, cons, mode, mnv, replay) in CUTS:
    cuts.append({
        "cross_cut_id": cid,
        "chapters": list(chs),
        "shared_timeline_id": tl,
        "shared_reveal_id": rev,
        "shared_consequence": cons,
        "handoff_mode": mode,
        "material_narrative_value": [{"chapter": c, "value": v} for (c, v) in mnv],
        "replay_boundary": replay,
        "declared_by_chapters": list(chs),
    })

entry_json = json.dumps(entries, indent=2, ensure_ascii=False)
cut_json = json.dumps(cuts, indent=2, ensure_ascii=False)

ENTRY_PLACEHOLDER = (
    "**Active `ArcEntry` records for chapters 62\u2013112: 0.** Task 5.4 replaces this line with one "
    "typed `json record=ArcEntry schema=1` fence holding chapters 62 through 112 as an ascending JSON array."
)

ENTRY_BLOCK = """**Active `ArcEntry` records for chapters 62\u2013112: 51.** Written by task 5.4. POV load Mara 21 / Nia 14 / Julian 16, longest POV run 2 counting across the 61/62 boundary, eight outliers (72, 103, 105, and 107 compressed; 73, 90, 101, and 108 expanded) against a 43-entry normal floor, `MOT-COPPER-02` at 70, `MOT-KNOCK-01` and `MOT-YES-01` at 73, `MOT-COME-03` at 74, `MOT-RADIUS-01` at 101, and `MOT-RECORD-02` at 109, `REVEAL-COUNTERPHASE-TRANSMITS` advanced at 71, released at 72, and completed at 73 inside its 70\u201377 window, and `REVEAL-AFFECTED-AREA-EXTENT` advanced at 95, released at 96, and completed at 101 inside its 94\u2013101 window. All seven null-night entries name `TL-NULL-NIGHT` and each participates in exactly two of that cluster's seven Cross Cuts. `TL-TRUST-ROLLING-DEPOSITS` appears only as the `record_horizon` of chapters 62 and 73 and `TL-TRUST-CONDITIONED-RELEASES` only as the `record_horizon` of chapter 110; neither is ever named as a `timeline_id`. Four entries record `"none"`: 66, 85, 100, and 112.

The fluent pair carried forward from Private_Defense is Mara and Nia, whose channel is operational at 74 and 77 under counterphase pressure and supplies the movement's one recorded session at 88, enabled by separate explicit mutual consent and switched off again afterward. Every other pairing belongs to supporting participants inside an existing POV chapter: network operators separately calibrated with Mara at 81 and 84, paired analysts whose traffic Julian reads at 82 and whose recording state he disputes at 89, a working dispatcher partnered with Nia at 91, and shelter volunteers at 102 and 105. No calibration is inherited, transferred, or extended to a third participant, Julian holds records and never pairs, and no operative, sender, adversary, archive, or simulation POV is created. Each session is dramatized inside the cluster chronology its own chapter owns; if the Canon Bible later declares per-session Timeline_IDs for these ranges, aligning them is a task 5.6 synchronization and never a second `timeline_id` here.

Under `DEC-017` no `purpose`, `hook`, or `knowledge_limit` in this block has Mara, Nia, or Julian connect the consented bounded cancellation of Chapter 73 to the area-scale null of 102\u2013108. Chapter 73 carries the concrete inside-the-field vocabulary and the question asked and answered; Chapter 108 carries the same operation with nobody to ask and no question anywhere in it. No Cross Cut joins 73 to any null-night chapter, and no Motif_Event, Literal_Phrase_Constraint, or `Reveal` is created for the parallel.

```json record=ArcEntry schema=1
__ENTRIES__
```"""

CUT_PLACEHOLDER_OLD = (
    "**Active `CrossCut` records: 25 \u2014 11 in Discovery_Part and 14 in Private_Defense_Part.** "
    "Movements 3 and 4 hold none yet, because their entries do not exist."
)
CUT_HEADER_NEW = (
    "**Active `CrossCut` records: 55 \u2014 11 in Discovery_Part, 14 in Private_Defense_Part, and 30 in "
    "Mindwars_Part.** Movement 4 holds none yet, because its entries do not exist."
)

INIT_OLD = "**Active `ArcEntry` records: 61 (chapters 1\u201361). Active `CrossCut` records: 25. Active `Baseline` records: 1 (`provisional`).**"
INIT_NEW = "**Active `ArcEntry` records: 112 (chapters 1\u2013112). Active `CrossCut` records: 55. Active `Baseline` records: 1 (`provisional`).**"

MW_CUT_SECTION = """
### Mindwars_Part cross-cuts \u2014 chapters 62\u2013112

Thirty records, ordered by first participating chapter, then by second. This is the movement with the manuscript's tightest converging-thread pattern, so most chapters carry a relationship; chapters 66, 85, 100, and 112 record `"none"` because no shared moment, consequence, or withheld disclosure exists for them. Chapters 64, 73, 76, 83, 96, 109, and all seven null-night chapters participate in two relationships each, which is where the movement's reversals and its compressed night sit.

Null night is the book's tightest compressed-clock cluster and its seven records form a closed ring: `CUT-PEAK-AND-THE-PHASE`, `CUT-FIELD-AND-THE-INSTRUMENT`, `CUT-A-PAGE-AND-A-DOORWAY`, `CUT-THE-LOCK-AND-THE-UNSHELTERED`, `CUT-A-THINNER-VOICE-AND-A-CLEAN-LOG`, `CUT-SILENCE-WITHOUT-A-COUNTERPARTY`, and `CUT-WHO-CAME-IN` join 102\u2013108 in sequence and close 108 back to 102. Three carry `handoff_mode: "temporal-braid"` because the declared `TL-NULL-NIGHT` chronology supports genuine simultaneity there; the rest convert simultaneity into consequence so the night reads as convergence rather than repetition. Every `material_narrative_value` covers a different action, and Nia's shelter, Julian's custody record, and Mara's emitter never re-narrate one another.

Four others carry a standing continuity load. `CUT-TRANSMITTED-DEFENSE-AND-THE-QUESTION` fixes the order that matters most in this movement: the finding that cancellation must be transmitted through minds comes first, and the authorization question follows from the physics rather than the reverse. `CUT-AUTOMATIC-PROTECTION-AND-PAGE-NINE` is deliberately a `causal-cut` about adoption and not about origin, and its replay boundary forbids either participant from reading the resemblance as evidence that the consortium sent anything. `CUT-THE-SHORE-AND-THE-BELIEVERS` holds the title's reversal against the institutional ranking of sender theories without letting either become the other, so the reversal stays a statement about human position and never a provenance claim. `CUT-DEPOSITED-AND-SUMMARIZED` opens `DEC-005`'s public contest and declares its own limit: two properly sourced accounts, no adjudicating body, and no correction of the first-casualty attribution.

```json record=CrossCut schema=1
__CUTS__
```
"""

text = ARC.read_text(encoding="utf-8")

assert text.count(ENTRY_PLACEHOLDER) == 1, "entry placeholder not found exactly once"
assert text.count(CUT_PLACEHOLDER_OLD) == 1, "cross-cut header not found exactly once"
assert text.count(INIT_OLD) == 1, "init state line not found exactly once"

text = text.replace(ENTRY_PLACEHOLDER, ENTRY_BLOCK.replace("__ENTRIES__", entry_json))
text = text.replace(CUT_PLACEHOLDER_OLD, CUT_HEADER_NEW)
text = text.replace(INIT_OLD, INIT_NEW)

# Append the Mindwars cross-cut section immediately after the Private_Defense CrossCut fence.
marker = '''    "declared_by_chapters": [
      60,
      61
    ]
  }
]
```
'''
assert text.count(marker) == 1, "private defense cross-cut fence terminator not unique"
text = text.replace(marker, marker + MW_CUT_SECTION)

ARC.write_text(text, encoding="utf-8")
print("wrote", ARC)
print("entries:", len(entries), "cuts:", len(cuts))
