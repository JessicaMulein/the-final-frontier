"""Principal property test for design Property 14.

Property 14: Manuscript source exclusion

Validates: Requirements 9.3
Related requirements: 9.2, 11.9, 12.8.

Owning task: 8.23. Reserved by task 7.1.

Feature: the-final-frontier-novel, Property 14: Manuscript source exclusion

What is being proved
--------------------
No Markdown at or below the resolved manuscript root is ever collected as a
reference source, and every valid song folder outside it still is. The manuscript
is a work in progress; publishing a draft chapter as a reference page would put
unfinished prose on the site, so the boundary has to hold for arbitrary trees
rather than for the ones that happened to exist when the collector was written.

What this test can and cannot establish
---------------------------------------
It asserts against the Manuscript_Exclusion_Contract's reference implementation in
`check_novel.py`, because Site_Build is external to this workspace. Passing
therefore proves **local isolation only**. It is not evidence that the real site
generator honours the contract, and Requirement 12.8 keeps external adoption an
explicitly unverified obligation — `external_adoption_verified` stays `False` and
no test here may set it.

Saying that plainly matters more than the assertions do. A green result here is
easy to mistake for "the manuscript cannot leak", and it is not that.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

PROPERTY = "Property 14: Manuscript source exclusion"
OWNING_TASK = "8.23"

PROPERTY_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.too_slow,
        HealthCheck.data_too_large,
        HealthCheck.function_scoped_fixture,
    ],
)

# Markdown filenames that a naive exclusion rule might let through: a name that
# merely resembles a song, a dotfile, a deeply nested draft, an uppercase
# extension, and a file whose name contains the manuscript root's own name.
LEAKY_NAMES: Tuple[str, ...] = (
    "notes.md",
    "Case Zero.md",
    "README.md",
    "index.md",
    ".hidden.md",
    "The Final Frontier Novel.md",
    "chapter-001.md",
    "song.MD",
)

NESTED_PREFIXES: Tuple[str, ...] = (
    "",
    "planning/",
    "chapters/",
    "chapters/discovery-part/",
    "drafts/",
    "drafts/deeply/nested/",
    "songs/",
)


def _under_manuscript(relative_path: str) -> str:
    """A path inside the manuscript root, which is where exclusion applies.

    `build_workspace` writes `extra_files` relative to the *workspace* root, so
    the manuscript root's own name has to be prepended. Without it the files land
    outside the boundary and the test would prove nothing about exclusion.
    """

    return "{0}/{1}".format(nf.MANUSCRIPT_ROOT_NAME, relative_path)


def _run(base: Path) -> Any:
    return checker.run_site_exclusion(base)


def _collected(result: Any) -> Tuple[str, ...]:
    return tuple(sorted(source.relative_path for source in result.sources))


@PROPERTY_SETTINGS
@given(
    st.lists(st.sampled_from(list(LEAKY_NAMES)), min_size=1, max_size=6, unique=True),
    st.lists(st.sampled_from(list(NESTED_PREFIXES)), min_size=1, max_size=5, unique=True),
)
def test_no_markdown_under_the_manuscript_root_is_ever_collected(
    tmp_path_factory, names, prefixes
):
    """Requirement 9.3: the whole subtree is excluded, at any depth or name."""

    base = tmp_path_factory.mktemp("property-14-exclude")
    extra = {
        _under_manuscript(prefix + name): "# Synthetic manuscript markdown\n\nBody.\n"
        for prefix in prefixes
        for name in names
    }
    workspace = nf.build_workspace(base, extra_files=extra)
    result = _run(base)
    collected = _collected(result)
    root = workspace.manuscript_root.name
    leaked = [path for path in collected if path.startswith(root + "/")]
    assert leaked == [], leaked


@PROPERTY_SETTINGS
@given(
    st.lists(
        st.sampled_from(list(nf.CANON_SOURCE_PATHS) + [nf.EXCLUDED_CANON_SOURCE_PATH]),
        min_size=1,
        max_size=6,
        unique=True,
    )
)
def test_song_folders_outside_the_manuscript_root_are_still_collected(
    tmp_path_factory, songs
):
    """Requirement 9.2: excluding the manuscript must not exclude the sources.

    A collector that solved exclusion by collecting nothing would satisfy the
    first property and fail this one, which is why both directions are here.
    """

    base = tmp_path_factory.mktemp("property-14-include")
    nf.build_workspace(
        base,
        songs={
            path: "[Verse]\nSynthetic source line.\n" for path in songs
        },
    )
    result = _run(base)
    assert result.songs, [s.relative_path for s in result.sources]


@PROPERTY_SETTINGS
@given(st.sampled_from(list(NESTED_PREFIXES)), st.sampled_from(list(LEAKY_NAMES)))
def test_one_file_at_a_time_stays_excluded(tmp_path_factory, prefix, name):
    """Shrinks to a single path, so a counterexample names one file."""

    base = tmp_path_factory.mktemp("property-14-single")
    workspace = nf.build_workspace(
        base, extra_files={_under_manuscript(prefix + name): "# Synthetic\n\nBody.\n"}
    )
    collected = _collected(_run(base))
    root = workspace.manuscript_root.name
    assert not any(path.startswith(root + "/") for path in collected), (
        prefix + name,
        collected,
    )


@PROPERTY_SETTINGS
@given(st.integers(min_value=1, max_value=6))
def test_a_manuscript_root_that_looks_like_a_song_folder_is_still_excluded(
    tmp_path_factory, depth
):
    """The boundary is the resolved root, not a name-shaped guess.

    A `songs/` directory *inside* the manuscript is manuscript material. Deciding
    by folder name rather than by resolved path would publish it.
    """

    base = tmp_path_factory.mktemp("property-14-lookalike")
    nested = "songs/" + "nested/" * depth + "Case Zero.md"
    workspace = nf.build_workspace(
        base, extra_files={_under_manuscript(nested): "[Verse]\nNot a real source.\n"}
    )
    collected = _collected(_run(base))
    root = workspace.manuscript_root.name
    assert "{0}/{1}".format(root, nested) not in collected, collected


@PROPERTY_SETTINGS
@given(st.just(None))
def test_a_missing_contract_fails_closed(tmp_path_factory, _unused):
    """Requirement 12.8: with no contract there is no permission to collect.

    Absent a contract the collector must refuse rather than fall back to a
    built-in default, because a default would be an unreviewed publication rule.
    """

    base = tmp_path_factory.mktemp("property-14-no-contract")
    nf.build_workspace(base, contract_filename=None)
    try:
        result = _run(base)
    except Exception:
        return
    assert not result.sources, _collected(result)


@PROPERTY_SETTINGS
@given(
    st.lists(st.sampled_from(list(LEAKY_NAMES)), min_size=1, max_size=4, unique=True)
)
def test_external_adoption_is_never_claimed_by_a_local_run(tmp_path_factory, names):
    """Requirement 12.8: local isolation is not external adoption.

    This is the assertion that keeps the property honest. Everything above proves
    the reference collector behaves; none of it proves the real Site_Build does,
    so no local run may report the external obligation as verified.
    """

    base = tmp_path_factory.mktemp("property-14-adoption")
    nf.build_workspace(
        base,
        extra_files={
            _under_manuscript(name): "# Synthetic\n\nBody.\n" for name in names
        },
    )
    result = _run(base)
    assert result.external_adoption_verified is False
