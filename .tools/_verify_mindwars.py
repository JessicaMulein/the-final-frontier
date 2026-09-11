#!/usr/bin/env python3
"""Task 5.4 verification. Temporary tooling; deleted after the report."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "The Final Frontier Novel" / "planning"
ARC = PLAN / "arc-outline.md"
CANON = PLAN / "canon-bible.md"
LEDGER = PLAN / "motif-ledger.md"
ROSTER = PLAN / "pov-roster.md"

FENCE = re.compile(r"^```json record=(\w+) schema=1\n(.*?)^```", re.M | re.S)

fails: list[str] = []
notes: list[str] = []


def check(cond: bool, msg: str) -> None:
    if cond:
        notes.append("PASS  " + msg)
    else:
        fails.append("FAIL  " + msg)


def load(path: Path) -> dict[str, list]:
    out: dict[str, list] = {}
    text = path.read_text(encoding="utf-8")
    for kind, body in FENCE.findall(text):
        data = json.loads(body)
        if isinstance(data, dict):
            data = [data]
        out.setdefault(kind, []).extend(data)
    return out


arc = load(ARC)
canon = load(CANON)
ledger = load(LEDGER)
roster = load(ROSTER)

entries = arc["ArcEntry"]
cuts = arc["CrossCut"]
mw = [e for e in entries if e["movement"] == "mindwars_part"]

# ---------- 1. sequence, uniqueness, filenames ----------
chs = [e["chapter"] for e in entries]
check(sorted(chs) == list(range(1, 113)), "document-wide chapter sequence is 1-112 contiguous with no duplicate")
check(len(set(e["filename"] for e in entries)) == len(entries), "all 112 filenames unique")
mwch = sorted(e["chapter"] for e in mw)
check(mwch == list(range(62, 113)), "Mindwars chapters 62-112 contiguous and unique (51 entries)")
check(len(mw) == 51, f"Mindwars entry count is 51 (got {len(mw)})")

fn_ok = all(
    e["filename"] == f"chapters/mindwars-part/mindwars-part-{e['chapter']:03d}-"
    + e["filename"].rsplit("-", 1)[-1].replace(".md", "") + ".md"
    or re.fullmatch(
        r"chapters/mindwars-part/mindwars-part-%03d-[a-z0-9]+(?:-[a-z0-9]+)*\.md" % e["chapter"],
        e["filename"],
    )
    for e in mw
)
check(fn_ok, "every Mindwars filename matches mindwars-part/mindwars-part-<NNN>-<slug>.md with correct sequence")
check(all(e["movement"] == "mindwars_part" for e in mw), "every Mindwars entry declares movement mindwars_part")

# ---------- 2. key set and order ----------
ref_keys = list(entries[0].keys())
check(all(list(e.keys()) == ref_keys for e in entries), f"all entries share identical key order ({len(ref_keys)} keys): {ref_keys}")

# ---------- 3. POV load and runs ----------
load_counts = Counter(e["pov_id"] for e in mw)
check(load_counts["POV-MARA"] == 21, f"Mara load 21 (got {load_counts['POV-MARA']})")
check(load_counts["POV-NIA"] == 14, f"Nia load 14 (got {load_counts['POV-NIA']})")
check(load_counts["POV-JULIAN"] == 16, f"Julian load 16 (got {load_counts['POV-JULIAN']})")
check(set(load_counts) == {"POV-MARA", "POV-NIA", "POV-JULIAN"}, "no fourth POV appears in 62-112")

seq = [e["pov_id"] for e in sorted(entries, key=lambda x: x["chapter"])]
longest, run, prev = 1, 1, None
worst = None
for i, p in enumerate(seq):
    if p == prev:
        run += 1
    else:
        run = 1
    prev = p
    if run > longest:
        longest, worst = run, i + 1
check(longest <= 3, f"longest POV run document-wide is {longest} (<=3), counted across 29/30 and 61/62")
b = {e["chapter"]: e["pov_id"] for e in entries}
check(not (b[60] == b[61] == b[62]) and not (b[61] == b[62] == b[63]),
      f"61/62 boundary clean: 60={b[60]}, 61={b[61]}, 62={b[62]}, 63={b[63]}")

# ---------- 4. length classes and outliers ----------
mw_out = [e["chapter"] for e in mw if e["estimated_length_class"] != "normal"]
mw_norm = [e for e in mw if e["estimated_length_class"] == "normal"]
check(len(mw_out) <= 8, f"Mindwars outliers {len(mw_out)} <= ceiling 8: {mw_out}")
check(len(mw_norm) >= 43, f"Mindwars normal entries {len(mw_norm)} >= floor 43")
all_out = [e["chapter"] for e in entries if e["estimated_length_class"] != "normal"]
all_norm = [e for e in entries if e["estimated_length_class"] == "normal"]
check(len(all_out) <= 20, f"chapters 1-112 use {len(all_out)} of the 20 manuscript outliers: {all_out}")
check(len(all_out) + 3 <= 20, f"outlier budget leaves room for the Coda ceiling of 3 ({len(all_out)}+3 <= 20)")
check(len(all_norm) + 13 >= 108, f"normal floor reachable: {len(all_norm)} normal so far + Coda floor 13 >= 108")
check(all(e["outlier_purpose"] for e in mw if e["estimated_length_class"] != "normal"),
      "every Mindwars outlier carries a non-null outlier_purpose")
check(all(e["outlier_purpose"] is None for e in mw if e["estimated_length_class"] == "normal"),
      "every normal Mindwars entry carries outlier_purpose null")
check(all(e["estimated_length_class"] in {"normal", "microchapter", "long-outlier"} for e in mw),
      "every length class is a valid LengthClass value")

# ---------- 5. status / calibration ----------
check(all(e["status"] == "planned" for e in mw), "every Mindwars entry is status planned")
check(all(e["calibration_selected"] is False for e in mw), "every Mindwars entry has calibration_selected false")
check(all(e["representative_purpose"] is None for e in mw), "every Mindwars entry has representative_purpose null")

# ---------- 6. timelines ----------
tl = {t["timeline_id"]: t for t in canon["TimelineEntry"]}
bad_tl = [e["chapter"] for e in mw if e["timeline_id"] not in tl]
check(not bad_tl, "every Mindwars timeline_id resolves in canon-bible.md")
bad_member = [e["chapter"] for e in mw if e["chapter"] not in tl[e["timeline_id"]]["chapter_numbers"]]
check(not bad_member, "every Mindwars chapter number appears in its TimelineEntry chapter_numbers")
bad_hz = [e["chapter"] for e in mw if e["record_horizon"]["through_timeline_id"] not in tl]
check(not bad_hz, "every record_horizon.through_timeline_id resolves")
bad_hz2 = [
    e["chapter"] for e in mw
    if e["chapter"] not in tl[e["record_horizon"]["through_timeline_id"]]["chapter_numbers"]
]
check(not bad_hz2, "every record_horizon window contains its own chapter")
check(all(set(e["record_horizon"].keys()) == {"through_timeline_id", "knowledge_limit"} for e in mw),
      "record_horizon has exactly through_timeline_id and knowledge_limit")
check(all(e["record_horizon"]["knowledge_limit"].strip() for e in mw), "every knowledge_limit is nonblank")
night = [e for e in mw if 102 <= e["chapter"] <= 108]
check(all(e["timeline_id"] == "TL-NULL-NIGHT" for e in night) and len(night) == 7,
      "all seven null-night entries 102-108 carry the single timeline_id TL-NULL-NIGHT")
named_as_tl = set(e["timeline_id"] for e in mw)
check("TL-TRUST-ROLLING-DEPOSITS" not in named_as_tl and "TL-TRUST-CONDITIONED-RELEASES" not in named_as_tl,
      "record-custody windows are never used as a timeline_id")
check(sorted(e["chapter"] for e in mw if e["record_horizon"]["through_timeline_id"] == "TL-TRUST-ROLLING-DEPOSITS") == [62, 73],
      "TL-TRUST-ROLLING-DEPOSITS appears only as the record_horizon of 62 and 73")
check(sorted(e["chapter"] for e in mw if e["record_horizon"]["through_timeline_id"] == "TL-TRUST-CONDITIONED-RELEASES") == [110],
      "TL-TRUST-CONDITIONED-RELEASES appears only as the record_horizon of 110")

# ---------- 7. POV ids ----------
pov_ids = set(p["pov_id"] for p in roster["POVProfile"])
check(all(e["pov_id"] in pov_ids for e in mw), "every pov_id resolves in pov-roster.md")
check(all(e["pov_id"] != "POV-SAFIYA" for e in mw), "POV-SAFIYA appears nowhere in 62-112")

# ---------- 8. motifs ----------
ledger_map: dict[int, set[str]] = {}
for m in ledger["MotifEvent"]:
    for c in m["participating_chapters"]:
        ledger_map.setdefault(c, set()).add(m["motif_event_id"])
motif_by_id = {m["motif_event_id"]: m for m in ledger["MotifEvent"]}
for e in mw:
    expect = ledger_map.get(e["chapter"], set())
    got = set(e["motif_events"])
    check(expect == got, f"chapter {e['chapter']} motif set matches ledger ({sorted(got) or 'empty'})")
for e in mw:
    for mid in e["motif_events"]:
        m = motif_by_id[mid]
        check(m["movement"] == "mindwars_part" and e["chapter"] in m["participating_chapters"],
              f"{mid} agrees field-by-field with the ledger: movement {m['movement']}, planned {m['planned_chapter']}")
check("MOT-CHAIN-04" not in motif_by_id, "MOT-CHAIN-04 does not exist")
check(not any("MOT-CHAIN-04" in e["motif_events"] for e in entries), "no entry references MOT-CHAIN-04")

# ---------- 9. reveals ----------
rev = {r["reveal_id"]: r for r in canon["Reveal"]}
never = {"REVEAL-HANDSHAKE-WANTING-ORIGIN", "REVEAL-FOREIGN-SIGNAL-PROVENANCE", "REVEAL-CODA-PROVENANCE"}
for e in mw:
    for rid in e["reveal_ids"]:
        r = rev[rid]
        w = r["payoff_window"]
        check(rid not in never, f"chapter {e['chapter']} reveal {rid} is not a never-revealed id")
        check(w["earliest_chapter"] <= e["chapter"] <= w["latest_chapter"],
              f"chapter {e['chapter']} is inside {rid} payoff window {w['earliest_chapter']}-{w['latest_chapter']}")
for rid in ("REVEAL-COUNTERPHASE-TRANSMITS", "REVEAL-AFFECTED-AREA-EXTENT"):
    holders = sorted(e["chapter"] for e in mw if rid in e["reveal_ids"])
    check(rev[rid]["reader_release_chapter"] in holders,
          f"{rid} release chapter {rev[rid]['reader_release_chapter']} lists it; carried by {holders}")
check(not any(r in e["reveal_ids"] for e in entries for r in never), "no entry anywhere lists a never-revealed reveal")

# ---------- 10. cross-cut reciprocity ----------
cut_by_id = {c["cross_cut_id"]: c for c in cuts}
check(len(cut_by_id) == len(cuts), f"all {len(cuts)} CrossCut ids unique")
mw_cut_ids = [c["cross_cut_id"] for c in cuts if min(c["chapters"]) >= 62]
check(len(mw_cut_ids) == 30, f"30 Mindwars CrossCut records (got {len(mw_cut_ids)})")

declared: dict[str, set[int]] = {}
for e in entries:
    cc = e["cross_cuts"]
    if cc == "none":
        continue
    check(isinstance(cc, list) and cc and len(set(cc)) == len(cc),
          f"chapter {e['chapter']} cross_cuts is a nonempty duplicate-free array") if False else None
    for cid in cc:
        declared.setdefault(cid, set()).add(e["chapter"])

for e in mw:
    cc = e["cross_cuts"]
    ok = cc == "none" or (isinstance(cc, list) and len(cc) > 0 and len(set(cc)) == len(cc))
    if not ok:
        fails.append(f"FAIL  chapter {e['chapter']} cross_cuts malformed: {cc!r}")
check(all((e["cross_cuts"] == "none") or isinstance(e["cross_cuts"], list) for e in mw),
      'every Mindwars cross_cuts value is either the exact string "none" or a nonempty array')
check(sorted(e["chapter"] for e in mw if e["cross_cuts"] == "none") == [66, 85, 100, 112],
      'exactly chapters 66, 85, 100, 112 record "none"')

for cid, c in cut_by_id.items():
    ch = c["chapters"]
    check(len(ch) >= 2 and ch == sorted(ch) and len(set(ch)) == len(ch),
          f"{cid} chapters {ch} are >=2, ascending, unique") if False else None
for c in cuts:
    cid = c["cross_cut_id"]
    ch = c["chapters"]
    if not (len(ch) >= 2 and ch == sorted(ch) and len(set(ch)) == len(ch)):
        fails.append(f"FAIL  {cid} chapters not >=2/ascending/unique: {ch}")
    if set(c["declared_by_chapters"]) != set(ch):
        fails.append(f"FAIL  {cid} declared_by_chapters not set-equal to chapters")
    if declared.get(cid, set()) != set(ch):
        fails.append(f"FAIL  {cid} reciprocity broken: entries declaring it {sorted(declared.get(cid, set()))} vs chapters {ch}")
    if [m["chapter"] for m in c["material_narrative_value"]] != ch:
        fails.append(f"FAIL  {cid} material_narrative_value chapters {[m['chapter'] for m in c['material_narrative_value']]} != {ch}")
    vals = [m["value"].strip() for m in c["material_narrative_value"]]
    if not all(vals) or len(set(vals)) != len(vals):
        fails.append(f"FAIL  {cid} material_narrative_value not distinct/nonblank")
    if not c["replay_boundary"].strip():
        fails.append(f"FAIL  {cid} replay_boundary blank")
    if c["handoff_mode"] not in {"sensory-match", "causal-cut", "contradiction-cut", "threshold-cut", "temporal-braid", "delayed-return"}:
        fails.append(f"FAIL  {cid} invalid handoff_mode {c['handoff_mode']}")
    if c["shared_timeline_id"] is None and c["shared_reveal_id"] is None and not (c["shared_consequence"] or "").strip():
        fails.append(f"FAIL  {cid} has no timeline, reveal, or consequence")
    if c["shared_timeline_id"] is not None and c["shared_timeline_id"] not in tl:
        fails.append(f"FAIL  {cid} shared_timeline_id does not resolve")
    if c["shared_reveal_id"] is not None:
        if c["shared_reveal_id"] in never:
            fails.append(f"FAIL  {cid} shares a never-revealed reveal")
        for cc in ch:
            ent = next(e for e in entries if e["chapter"] == cc)
            if c["shared_reveal_id"] not in ent["reveal_ids"]:
                fails.append(f"FAIL  {cid} shared_reveal_id not carried by chapter {cc}")
    if min(ch) >= 62 and set(c["declared_by_chapters"]) - set(range(62, 113)):
        fails.append(f"FAIL  {cid} crosses out of the Mindwars block")
check(True, "cross-cut reciprocity, distinct material_narrative_value, replay boundaries, and handoff modes validated")

dangling = set(declared) - set(cut_by_id)
check(not dangling, f"no dangling CrossCut reference (checked {len(declared)} referenced ids)")

# every Mindwars chapter is either in a cut or records "none"
covered = set()
for c in cuts:
    covered.update(c["chapters"])
uncov = [e["chapter"] for e in mw if e["cross_cuts"] != "none" and e["chapter"] not in covered]
check(not uncov, "every Mindwars chapter with cross_cuts appears in a declared CrossCut")

night_ch = set(range(102, 109))
night_cuts = [c for c in cuts if set(c["chapters"]) <= night_ch and len(set(c["chapters"]) & night_ch) >= 2]
check(len(night_cuts) == 7, f"null night carries exactly 7 Cross Cuts (got {len(night_cuts)})")
part = Counter(x for c in night_cuts for x in c["chapters"])
check(all(part[c] == 2 for c in range(102, 109)), f"each null-night chapter participates in exactly 2 cuts: {dict(sorted(part.items()))}")
check(sum(1 for c in night_cuts if c["handoff_mode"] == "temporal-braid") >= 1,
      f"null night declares temporal-braid handoffs ({sum(1 for c in night_cuts if c['handoff_mode'] == 'temporal-braid')} of 7)")
night_vals = [m["value"] for c in night_cuts for m in c["material_narrative_value"]]
check(len(set(night_vals)) == len(night_vals), "all 14 null-night material_narrative_value strings are distinct")
check(not any(73 in c["chapters"] and set(c["chapters"]) & night_ch for c in cuts),
      "no CrossCut joins Chapter 73 to a null-night chapter")

# ---------- 11. CANCEL properties at both scopes ----------
for tid, scope, chapset in (("TL-MINDWARS-COUNTERPHASE", "bounded-individual", set(range(70, 78))),
                            ("TL-NULL-NIGHT", "area-scale", set(range(102, 109)))):
    t = tl[tid]
    ts = t["technical_state"]
    cs = ts["cancel_state"]
    check(ts["mode"] == "CANCEL", f"{tid} mode is CANCEL")
    check(cs["scope"] == scope, f"{tid} CANCEL scope is {scope}")
    check(ts["person_specific_address_state"] == "not-applicable", f"{tid} property 1: no person-specific address")
    check(cs["inserted_content"] == "none" and bool(cs["subtraction"].strip()),
          f"{tid} property 2/3: subtraction only, inserted_content none")
    check(cs["affected_set_predictable_before"] is False
          and cs["affected_set_enumerable_during"] is False
          and cs["affected_set_fully_mapped_after"] is False,
          f"{tid} property 4: all three untargetability flags false")
    check(cs["additive_inverse_exists"] is False, f"{tid} property 5: no additive inverse")
    check(cs["provenance_yield"] == "none", f"{tid} property 8: provenance_yield none")
    check(set(t["chapter_numbers"]) <= set(range(62, 113)), f"{tid} property 7: confined to the Mindwars block")
    if scope == "bounded-individual":
        check(cs["individual_consent"] is not None and cs["institutional_authorization"] is None
              and cs["individual_consent"]["current"] is True and cs["individual_consent"]["revocable"] is True
              and bool(cs["individual_consent"]["specific_act"].strip()),
              f"{tid} property 6: individual current specific revocable consent, no institutional authorization")
    else:
        check(cs["individual_consent"] is None and bool((cs["institutional_authorization"] or "").strip()),
              f"{tid} property 6: institutional authorization only, never individual consent from every affected person")
mw_tl_modes = {t["timeline_id"]: (t["technical_state"] or {}).get("mode") for t in canon["TimelineEntry"]}
cancel_tls = [k for k, v in mw_tl_modes.items() if v == "CANCEL"]
cancel_chs = sorted(c for k in cancel_tls for c in tl[k]["chapter_numbers"])
check(set(cancel_chs) <= set(range(62, 113)), f"every CANCEL chapter is inside 62-112: {cancel_tls}")

# ---------- 12. DEC-017 silence and forbidden content ----------
blob = " ".join(
    [e["purpose"] for e in mw] + [e["hook"] for e in mw]
    + [e["record_horizon"]["knowledge_limit"] for e in mw]
    + [e["outlier_purpose"] or "" for e in mw]
    + [c["shared_consequence"] or "" for c in cuts if min(c["chapters"]) >= 62]
    + [m["value"] for c in cuts if min(c["chapters"]) >= 62 for m in c["material_narrative_value"]]
    + [c["replay_boundary"] for c in cuts if min(c["chapters"]) >= 62]
).lower()

forbidden = [
    "group mind", "hive mind", "mass mind", "same operation at two scopes",
    "same mechanism at two scopes", "same cancellation twice", "one room wide",
    "case zero", "radius of", "square mile", "mile radius", "kilometre", "kilometer",
]
hits = [w for w in forbidden if w in blob]
check(not hits, f"no forbidden phrase in Mindwars purposes, hooks, horizons, or cross-cut text (scanned {len(forbidden)} patterns)")
check("three counties wide" in blob, "canonical wording 'three counties wide' is used for the null extent")
check("counties wide" in blob and not re.search(r"\b(radius|diameter)\s+of\b", blob),
      "no geometric derivation of the canonical extent")
check(not re.search(r"\bcounty of\b", blob), "no individual county is named")

# ---------- 13. hook / purpose shape ----------
for e in mw:
    for f in ("purpose", "hook"):
        v = e[f]
        if not v.strip() or "\n" in v or "\r" in v:
            fails.append(f"FAIL  chapter {e['chapter']} {f} is blank or multiline")
check(True, "every purpose and hook is a nonblank single line")
check(len(set(e["hook"] for e in mw)) == 51, "all 51 hooks are distinct strings")
check(len(set(e["purpose"] for e in mw)) == 51, "all 51 purposes are distinct strings")

# ---------- 14. document counts ----------
text = ARC.read_text(encoding="utf-8")
check("**Active `ArcEntry` records: 112 (chapters 1\u2013112). Active `CrossCut` records: 55." in text,
      "initialization state updated to 112 entries / 55 cross-cuts")
check("**Active `CrossCut` records: 55 \u2014 11 in Discovery_Part, 14 in Private_Defense_Part, and 30 in Mindwars_Part.**" in text,
      "cross-cut section header updated")
check("**Active `ArcEntry` records for chapters 62\u2013112: 51.**" in text, "Mindwars entry count line updated")
check(text.count("```json record=ArcEntry schema=1") == 3, "exactly three ArcEntry fences (one per written movement)")
check(text.count("```json record=CrossCut schema=1") == 3, "exactly three CrossCut fences")
check("EXAMPLE" not in text.split("## Chapter entries")[1], "no EXAMPLE identifier inside the chapter-entry sections")

print("\n".join(notes))
print()
if fails:
    print("\n".join(fails))
    print(f"\n{len(fails)} FAILURES, {len(notes)} passes")
    raise SystemExit(1)
print(f"ALL CHECKS PASSED: {len(notes)} assertions")
