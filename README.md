# The Final Frontier

A novel by Jessica Mulein. **v0.9.0** — all 128 chapters delivered, none finalised.

> Somewhere behind the eyes there's a country with no army,
> and one small question standing in the door.

About 150,000 words in 128 chapters. This repository holds the manuscript, the
songs its world grew out of, a fully narrated audiobook, the specification the book
was built from, and the complete audit trail of every decision that produced them.

I treated the novel like a software project: specification, verification harness,
reviewed increments, recorded decisions. The prose was drafted by large language
models against that specification. [METHOD.md](METHOD.md) is the full account, with
commands so you can check every claim in it yourself.

## Start here

- **Project site** — [jessicamulein.github.io/the-final-frontier](https://jessicamulein.github.io/the-final-frontier/), with downloads and the music
- **Read it** — download the [EPUB](https://jessicamulein.github.io/the-final-frontier/downloads/the-final-frontier.epub) or [PDF](https://jessicamulein.github.io/the-final-frontier/downloads/the-final-frontier.pdf), read it [chapter by chapter](The%20Final%20Frontier%20Novel/chapters/), or build it yourself (below)
- **Listen** — the AI-narrated audiobook (M4B and MP3s) is in the [latest release](https://github.com/JessicaMulein/the-final-frontier/releases/latest); all 128 chapters, licensed the same as the prose
- **Or start with the music** — [`songs/`](songs/), lyrics and production notes, and *The Synaptic Frontier* [on SoundCloud](https://soundcloud.com/jessicamulein/sets/the-synaptic-frontier). Four minutes instead of 150,000 words, and the songs came first
- **How it was built** — [METHOD.md](METHOD.md), and the [specs](.kiro/specs/The-Final-Frontier-novel/) and [planning records](The%20Final%20Frontier%20Novel/planning/) behind it
- **What's wrong with it** — [KNOWN-ISSUES.md](KNOWN-ISSUES.md)

```sh
python3 .tools/build_book.py all      # needs Pandoc, plus XeLaTeX for the PDF
```

That assembles front matter, chapters, and back matter, then writes
`book/dist/the-final-frontier.epub` and `.pdf`. Build output isn't tracked in git,
so the manuscript in `chapters/` is the canonical text.

## What `v0.9.0` means

It's a real claim, not a hedge. Under this project's own acceptance rules a chapter
reaches `final` only when two independent gates pass: an objective checker and a
human editorial review, neither able to overrule the other.

All 128 chapters are delivered and sit at `revised`. **Zero are `approved` or
`final`.** The manuscript-global gate currently exits 2. You can confirm that in
one command:

```sh
python3 .tools/check_novel.py --scope global
```

All 129 errors it reports are that refusal: 128 chapters not yet final, and one
missing finalisation gate. There are currently no objective content defects in any
chapter. What's missing is the editing, and that's itemised in
[KNOWN-ISSUES.md](KNOWN-ISSUES.md).

So: read this as a complete draft with a published defect list, not as a finished
book. If you find something broken that isn't on the list, open an issue.

## What's in here

| Path | Contents |
| --- | --- |
| [`The Final Frontier Novel/`](The%20Final%20Frontier%20Novel/) | The manuscript. `chapters/` in four parts, plus front matter, back matter, and `planning/` |
| [`.kiro/specs/`](.kiro/specs/) | Requirements, design, and task breakdown |
| [`songs/`](songs/) | Lyrics and production notes |
| `audiobook/` | Where narrated renders land locally. Derived audio isn't committed; the finished M4B and MP3s ship in the [release](https://github.com/JessicaMulein/the-final-frontier/releases/latest) |
| [`docs/`](docs/) | The project [site](https://jessicamulein.github.io/the-final-frontier/), including direct EPUB/PDF downloads |
| `.tools/` | Manuscript checker, EPUB/PDF build, and release packaging |
| `audiobook-studio/` | Narration pipeline, patch assets, and the committed voice reference |
| `book/` | Build output, untracked |
| [`cover.jpg`](cover.jpg) | Cover art |

The novel runs in four parts: **Discovery** (29 chapters), **Private Defense**
(32), **Mindwars** (51), and an **Aftermath** coda (16).

The source songs are *The Synaptic Frontier*, *Faraday*, *The Final Frontier*,
*The Radius*, *Case Zero*, and *The Final Frontier (Is Up Here)*, a retelling.
Most exist twice — an orchestral version and an electronic remix — and the album
[*The Synaptic Frontier*](https://soundcloud.com/jessicamulein/sets/the-synaptic-frontier)
runs the orchestral set, then the remixes, then *Writable*, the lead-in to the
sequel. Lyrics are mine; composition and performance are Suno.

## Where the idea came from

I'm a lifetime software engineer. Early on I worked in signals, and I came away
fascinated by how interchangeable bits and waves are: wiggle a bit over here and
a bit wiggles over there, as though the air in the middle didn't matter.

From there it isn't much of a reach. Look at fMRI and EEG and you can see that a
thought and a bit are already partly interchangeable, and will be more so soon,
with technology we may already have. fMRI demonstrates thought to bit. Bit to
voice is a stretch at present, but only time will tell how much of one — what
gets revealed to us, and when. Some things stay classified long after they are
invented.

The novel is fiction. The premise underneath it is not far-fetched. The
[afterword](The%20Final%20Frontier%20Novel/back-matter.md) is where I separate
what I invented from what has already been published, with sources.

## What it's actually about

Consent.

If a thought can be read, there is probably no way to enforce a consent protocol
on the reading of it. No cryptography, no permissions model, no standards body.
What's left is politeness: asking, waiting for an answer, and then choosing to
respect it. That's a thin thing to hang a civilisation on, and the book is
largely an exercise in thinking about what happens when it's all you have.

The rule the novel runs on is that entry requires a current answer from the
person behind the door. A known sender is not an authorised one. A defence that
enters uninvited is still an entry. Provenance is not truth.

## Disclosure

The prose was drafted by Claude Opus 5 and GPT 5.6 Sol against the specification
in [`.kiro/specs/`](.kiro/specs/The-Final-Frontier-novel/). The first full draft
cost about $600 in model spend, on top of a great deal of human effort. The songs
are my lyrics with Suno composition and performance. The narration is synthesised.
The cover is generated.

The audiobook was rendered locally on one laptop — an Apple M4 Max with
64 GB of unified memory — using Fish S2 Pro on the Mac's own GPU, with no cloud
spend. It runs at roughly 1.3–1.5× real time per chapter and peaks around
21–30 GB of memory; building the finished ~13.4-hour book (render, announcements,
repairs, and MP3/M4B encoding) took about a day of machine time. See
[METHOD.md](METHOD.md) for detail.

I wrote the requirements, the design, the arc, the POV roster, the motif ledger,
the canon, and all 23 recorded decisions. No model chose the premise, set the
mechanism, decided what the book refuses to resolve, or held the consent line
through 128 chapters. Every one of those calls is dated and sits in
[`planning/decisions.md`](The%20Final%20Frontier%20Novel/planning/decisions.md)
with the alternatives I rejected written down beside it.

I'd rather be judged on that record than on the word count, and
[METHOD.md](METHOD.md) is where I make the case — including the parts where the
method failed and I had to catch it.

## Why I worked this way

I have cancer and chronic fatigue. That's most of why I reached for these tools: I
don't have the time, the energy, or on some days the brain to do all of this
myself, and I wanted the idea out in the world while I could still put it there.

It's also why the gap in this project is editing rather than drafting. Drafting
turned out to be the cheap part. There is no professional line edit, because I
don't have an editor and I can't reliably be one. That's the honest reason the
prose still has the flaws it has, and it's the first thing I'd spend help on.

## License

The novel prose and the planning documents are Creative Commons BY-NC-SA 4.0.
Share them, translate them, build on them, with attribution and
non-commercially. The build tooling is MIT.

The songs, the cover art, and the audio recordings are fully reserved, as are
commercial rights to the novel. Want to do something commercial, or use the
lyrics, the cover, or a recording? Ask.

See [LICENSE](LICENSE) for the specifics.

— Jessica Mulein, 2026
