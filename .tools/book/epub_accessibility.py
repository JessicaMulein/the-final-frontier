#!/usr/bin/env python3
"""Add EPUB Accessibility 1.1 metadata and cover alt text to a built EPUB.

Why this is a post-processing step
---------------------------------
Accessibility metadata lives in the package document as `<meta property="schema:...">`
entries. Pandoc's EPUB writer has no option for them: `--epub-metadata` accepts Dublin
Core, and these are not Dublin Core. Rather than hope a future pandoc passes unknown
elements through, this edits the package document directly and verifiably.

Why it matters
--------------
This book is meant to be read along with its narration by low-vision readers. Reading
systems, library platforms and stores use this metadata to tell a reader whether a book
is usable *before* they acquire it, and screen-reader users routinely filter on it.
Without it a perfectly navigable EPUB is indistinguishable from an unusable one.

It is also the machine-readable half of an accessibility claim that the EU Accessibility
Act expects of ebooks.

What is claimed, and what is not
--------------------------------
Only what is true of this file:

  accessMode                 textual, visual -- the prose is text; the cover is an image
  accessModeSufficient       textual -- the whole work can be consumed as text alone,
                             which is the claim that matters to a screen-reader user
  accessibilityFeature       structuralNavigation, tableOfContents, readingOrder,
                             alternativeText, unlocked
  accessibilityHazard        none -- no flashing, no motion, no sound
  accessibilitySummary       plain prose, including the known limitation

Deliberately NOT claimed: `synchronizedAudioText`, until Media Overlays actually ship,
and no WCAG conformance level, because that requires testing with assistive technology
rather than a self-assessment by the tool that generated the file. Overclaiming here is
worse than silence: a reader who filters on a false claim wastes money and time.

Safety
------
Never writes in place. EPUB requires `mimetype` to be the first archive entry and
stored uncompressed, which a naive rezip breaks, so the archive is rebuilt in order.
Idempotent: existing accessibility metadata is replaced rather than duplicated.
"""

from __future__ import annotations

import argparse
import re
import shutil
import zipfile
from pathlib import Path

ACCESSIBILITY_SUMMARY = (
    "This publication is reflowable text with a full table of contents and a "
    "structured reading order, so it can be resized, reflowed, and read with a "
    "screen reader or refreshable braille display. Headings identify each part and "
    "chapter, and the cover image carries a text alternative. There is no audio, "
    "video, motion, or flashing content, and the file is not restricted by DRM. "
    "Chapter titles are provided as text and match the spoken chapter announcements "
    "in the audiobook edition. This edition does not yet include synchronised "
    "text-and-audio playback."
)

#: Ordered so a human reading the OPF can follow it. Multiple values for one property
#: are separate `<meta>` elements, as the specification requires.
ACCESSIBILITY_META: tuple[tuple[str, str], ...] = (
    ("schema:accessMode", "textual"),
    ("schema:accessMode", "visual"),
    ("schema:accessModeSufficient", "textual"),
    ("schema:accessibilityFeature", "structuralNavigation"),
    ("schema:accessibilityFeature", "tableOfContents"),
    ("schema:accessibilityFeature", "readingOrder"),
    ("schema:accessibilityFeature", "alternativeText"),
    ("schema:accessibilityFeature", "unlocked"),
    ("schema:accessibilityHazard", "none"),
    ("schema:accessibilitySummary", ACCESSIBILITY_SUMMARY),
)

MANAGED_PROPERTIES = {
    "schema:accessMode",
    "schema:accessModeSufficient",
    "schema:accessibilityFeature",
    "schema:accessibilityHazard",
    "schema:accessibilitySummary",
    "a11y:certifiedBy",
}


def escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def strip_managed(opf: str) -> str:
    """Remove any accessibility metadata already present, so reruns do not duplicate."""
    pattern = re.compile(
        r"[ \t]*<meta[^>]*\bproperty=\"(" + "|".join(re.escape(p) for p in MANAGED_PROPERTIES) + r")\"[^>]*>.*?</meta>[ \t]*\n?|"
        r"[ \t]*<meta[^>]*\bproperty=\"(" + "|".join(re.escape(p) for p in MANAGED_PROPERTIES) + r")\"[^>]*/>[ \t]*\n?",
        re.DOTALL,
    )
    return pattern.sub("", opf)


def inject(opf: str, certified_by: str | None) -> str:
    opf = strip_managed(opf)
    entries = list(ACCESSIBILITY_META)
    if certified_by:
        entries = entries + [("a11y:certifiedBy", certified_by)]

    block = "".join(
        f'    <meta property="{name}">{escape(value)}</meta>\n'
        for name, value in entries
    )

    # The a11y prefix is not in the default EPUB vocabulary, so it must be declared.
    if "a11y:" in block and "prefix=" not in opf:
        opf = re.sub(
            r"(<package\b[^>]*?)(\s*>)",
            r'\1 prefix="a11y: http://www.idpf.org/epub/vocab/package/a11y/#"\2',
            opf,
            count=1,
        )
    elif "a11y:" in block and "a11y:" not in re.search(r"<package\b[^>]*>", opf).group(0):
        opf = re.sub(
            r'(<package\b[^>]*?prefix=")',
            r"\1a11y: http://www.idpf.org/epub/vocab/package/a11y/# ",
            opf,
            count=1,
        )

    match = re.search(r"</metadata>", opf)
    if match is None:
        raise SystemExit("package document has no </metadata>; cannot inject")
    return opf[: match.start()] + block + opf[match.start() :]


def add_cover_alt(xhtml: str, alt: str) -> tuple[str, bool]:
    """Give the cover a text alternative. Returns (xhtml, whether one is now present).

    Pandoc wraps an EPUB cover in SVG -- `<svg><image xlink:href=.../></svg>` -- not in
    an `<img>`. An SVG `<image>` has no `alt` attribute, so the plain-HTML approach
    silently does nothing and leaves the cover unlabelled while the package document
    claims `alternativeText`. That false claim is worse than making no claim, because a
    reader filtering on it is misled.

    For the SVG case the fix is a `<title>` child plus `role="img"` and
    `aria-labelledby`, which is what screen readers actually consult.
    """
    if re.search(r"<img\b", xhtml):
        if re.search(r"<img[^>]*\balt=", xhtml):
            return (
                re.sub(
                    r'(<img[^>]*\balt=")[^"]*(")',
                    lambda m: m.group(1) + escape(alt) + m.group(2),
                    xhtml,
                    count=1,
                ),
                True,
            )
        return re.sub(r"(<img\b)", r'\1 alt="' + escape(alt) + '"', xhtml, count=1), True

    svg = re.search(r"<svg\b[^>]*>", xhtml)
    if svg is None:
        return xhtml, False

    if 'id="cover-title"' in xhtml:
        return (
            re.sub(
                r'(<title id="cover-title">).*?(</title>)',
                lambda m: m.group(1) + escape(alt) + m.group(2),
                xhtml,
                count=1,
                flags=re.DOTALL,
            ),
            True,
        )

    opening = svg.group(0)
    updated = opening
    if "role=" not in opening:
        updated = updated[:-1].rstrip() + ' role="img"' + opening[-1]
    if "aria-labelledby=" not in updated:
        updated = updated[:-1].rstrip() + ' aria-labelledby="cover-title"' + updated[-1]
    xhtml = xhtml.replace(opening, updated, 1)
    return (
        xhtml.replace(
            updated,
            updated + f'\n<title id="cover-title">{escape(alt)}</title>',
            1,
        ),
        True,
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("epub", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument(
        "--certified-by",
        default=None,
        help="who assessed accessibility. Omit rather than name someone who did not.",
    )
    p.add_argument(
        "--cover-alt",
        default=(
            "Cover of The Final Frontier by Jessica Mulein: the title over a dark "
            "field suggesting radio noise."
        ),
    )
    args = p.parse_args()

    if not args.epub.is_file():
        raise SystemExit(f"no EPUB at {args.epub}")

    with zipfile.ZipFile(args.epub) as archive:
        names = archive.namelist()
        payload = {name: archive.read(name) for name in names}

    opf_names = [n for n in names if n.endswith(".opf")]
    if len(opf_names) != 1:
        raise SystemExit(f"expected exactly one package document, found {opf_names}")
    opf_name = opf_names[0]

    original_opf = payload[opf_name].decode("utf-8")
    payload[opf_name] = inject(original_opf, args.certified_by).encode("utf-8")

    cover_pages = [
        n for n in names if n.endswith((".xhtml", ".html")) and "cover" in n.lower()
    ]
    labelled = 0
    for name in cover_pages:
        text = payload[name].decode("utf-8")
        updated, ok = add_cover_alt(text, args.cover_alt)
        payload[name] = updated.encode("utf-8")
        labelled += 1 if ok else 0

    # Do not claim a feature that is not present. If no cover could be labelled, the
    # alternativeText claim is withdrawn rather than left as a false advertisement.
    if labelled == 0:
        opf_text = payload[opf_name].decode("utf-8")
        payload[opf_name] = opf_text.replace(
            '    <meta property="schema:accessibilityFeature">alternativeText</meta>\n',
            "",
        ).encode("utf-8")
        print("  WARNING: no cover image could be labelled; withdrew alternativeText")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.resolve() == args.epub.resolve():
        raise SystemExit("refusing to write in place")

    # mimetype must be first and stored, or the result is not a valid EPUB.
    ordered = ["mimetype"] + [n for n in names if n != "mimetype"]
    with zipfile.ZipFile(args.output, "w") as out:
        for name in ordered:
            if name not in payload:
                continue
            if name == "mimetype":
                out.writestr(name, payload[name], compress_type=zipfile.ZIP_STORED)
            else:
                out.writestr(name, payload[name], compress_type=zipfile.ZIP_DEFLATED)

    added = sum(1 for _ in ACCESSIBILITY_META) + (1 if args.certified_by else 0)
    print(f"{args.epub.name} -> {args.output}")
    print(f"  package document: {opf_name}")
    print(f"  accessibility meta entries: {added}")
    print(f"  cover pages labelled: {labelled} of {len(cover_pages)}")
    with zipfile.ZipFile(args.output) as check:
        first = check.infolist()[0]
        print(
            f"  first entry: {first.filename} "
            f"({'stored' if first.compress_type == zipfile.ZIP_STORED else 'deflated'})"
        )
        opf = check.read(opf_name).decode("utf-8")
    for name in sorted(MANAGED_PROPERTIES):
        needle = 'property="' + name + '"'
        print(f"  {name}: {opf.count(needle)}")


if __name__ == "__main__":
    main()
