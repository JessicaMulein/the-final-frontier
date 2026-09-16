# File and Directory Conventions

The fixed naming and layout rules for this manuscript, recorded by task 2.1 of the
`The-Final-Frontier-novel` spec. These are mechanical conventions, not creative decisions: they exist
so that a filename, a directory, a Chapter_Header, and an ArcEntry can be checked against each other
without a human reading prose.

Authority: Requirements 9.1, 9.4, 9.5, 9.8, and the design's *Manuscript Organization and Site
Isolation* section. `DEC-010` fixes the root directory name. Nothing here judges voice, pacing, or
quality; those belong to the Voice_Briefs and the Editorial_Gate.

---

## Manuscript root

`The Final Frontier Novel/` — a visible, dedicated, non-dot-prefixed directory that is a direct child
of the workspace root (Requirement 9.1, `DEC-010`).

It does not collide with the source song `songs/The Final Frontier.md`: the songs sit one level down
in `songs/`, and the `Novel` suffix separates the two by name alone. The
Manuscript_Exclusion_Contract (task 3.1) declares this exact root string, so the root name and the
contract must be changed together or not at all.

## Layout

```text
The Final Frontier Novel/
├── front-matter.md                  (task 2.2)
├── back-matter.md                   (`DEC-023`)
├── exclusion-contract.json          (task 3.1)
├── planning/
│   ├── decisions.md                 author decisions, dated       (task 1)
│   ├── file-conventions.md          this file                     (task 2.1)
│   ├── record-schemas.md            (task 4.1)
│   ├── canon-bible.md               (task 4.2)
│   ├── pov-roster.md                (task 4.3)
│   ├── voice-briefs.md              (task 4.4)
│   ├── motif-ledger.md              (task 4.5)
│   ├── editorial-log.md             (task 4.6)
│   ├── arc-changes.md               (task 4.6)
│   └── arc-outline.md               (task 5.1)
└── chapters/
    ├── discovery-part/
    ├── private-defense-part/
    ├── mindwars-part/
    └── aftermath-coda/
```

`planning/` keeps the Arc_Outline, Canon_Bible, POV_Roster, and Motif_Ledger as four separate
documents, never merged into one reference file (Requirement 9.8). The design's planning tree lists
seven files; `decisions.md` (task 1), this file (task 2.1), and `record-schemas.md` (task 4.1) are
additions the tasks introduce. The four documents Requirement 9.8 names are unchanged. Voice_Briefs
live outside the POV_Roster, so `pov-roster.md` must link to `voice-briefs.md` (Requirement 9.9).

Empty movement directories carry a `.gitkeep` placeholder so the tree survives a clone. The
placeholders are deliberately **not** Markdown: a `README.md` inside a movement directory would be
picked up by any chapter-file glob and then fail the naming rule below. Remove a `.gitkeep` once that
directory holds its first chapter file.

`back-matter.md` is the reader-facing document that follows the last chapter, added by `DEC-023`. Like
`front-matter.md` it is a root file, uses `#` for the title and `##` per section, carries no
Chapter_Header, and is never a Chapter_File. Root Markdown is outside every chapter glob and outside
the Chapter File Prose Body literal scan, so no back-matter section satisfies or violates a
Literal_Phrase_Constraint. The two root documents are the only Markdown permitted at this level;
anything else belongs in `planning/` or in a movement directory under its chapter name.

## Chapter files

One chapter per file (Requirement 9.4). The fixed convention, and the only one permitted
(Requirement 9.5):

```text
<movement>-<three-digit-global-sequence>-<descriptive-slug>.md
```

In that order, always. The file lives in `chapters/<movement>/`.

| Part | Directory and filename prefix | Header `movement` value | Provisional chapters |
|---|---|---|---|
| Discovery_Part | `discovery-part` | `discovery_part` | 001–029 |
| Private_Defense_Part | `private-defense-part` | `private_defense_part` | 030–061 |
| Mindwars_Part | `mindwars-part` | `mindwars_part` | 062–112 |
| Aftermath_Coda | `aftermath-coda` | `aftermath_coda` | 113–128 |

Paths and filenames use hyphens; the `movement` header value uses underscores. A checker comparing
the two must translate rather than string-match. The chapter ranges are provisional at the 128-chapter
scale and move only through a recorded ArcChange.

### Sequence

- Three digits, zero-padded: `001`, `045`, `104`, `128`.
- Global across the whole book. It **never resets** at a movement boundary — Private Defense opens at
  `030`, not `001`.
- Unique and contiguous from `001` through the final chapter, with no gaps and no reuse.

### Slug

- Lowercase ASCII words separated by single hyphens; no spaces, underscores, punctuation, or
  diacritics.
- Descriptive of the chapter's function so the directory is readable at a glance. It is a handle, not
  a title, and it is not required to match any text in the prose.
- A slug may be revised; the sequence number may not, absent an ArcChange.

### Examples

```text
chapters/discovery-part/discovery-part-001-noise-floor.md
chapters/private-defense-part/private-defense-part-045-page-nine.md
chapters/mindwars-part/mindwars-part-104-null-night.md
chapters/aftermath-coda/aftermath-coda-128-knock-and-wait.md
```

## The four-way agreement rule

For every chapter, these four must agree. Any disagreement is an objective violation, not a matter of
interpretation:

1. **Directory** — `chapters/<movement>/`
2. **Filename** — `<movement>-<NNN>-<slug>.md`
3. **Chapter_Header** — the `movement` and `chapter` keys inside the file
4. **ArcEntry** — the `movement`, `chapter`, and `filename` fields in `planning/arc-outline.md`

So `chapters/mindwars-part/mindwars-part-104-null-night.md` requires header `movement: mindwars_part`
and `chapter: 104`, and an ArcEntry whose `chapter` is `104`, whose `movement` is `mindwars_part`, and
whose `filename` is that exact filename. Each ArcEntry maps to exactly one chapter file and each
chapter file to exactly one ArcEntry.

The header's remaining keys, their allowed values, and the Length_Class boundaries are fixed by
`planning/record-schemas.md` (task 4.1) and the design's `ChapterHeader` table. This file governs
names and locations only.

## Renaming

Changing a movement directory name, the filename convention, or a chapter's sequence number touches
the filename, the header, the ArcEntry, the Motif_Ledger's planned-chapter fields, and any editorial
record that cites the old path. Record it as an ArcChange in `planning/arc-changes.md` with every
affected reference listed; the change is not valid until all of them are synchronized. Renaming the
manuscript root additionally requires updating `exclusion-contract.json`.
