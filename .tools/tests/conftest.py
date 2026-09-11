"""Pytest wiring for the novel checker suite.

Created by task 7.1. This file stays deliberately thin. Every synthetic-fixture
builder lives in `novel_fixtures.py`, an ordinary importable module, for two
reasons:

* other test modules must import the builders directly, and importing a
  `conftest.py` from a test module is a pytest anti-pattern; and
* the repository also runs `python3 -m unittest discover -s .tools/tests`, which
  never loads `conftest.py` at all.

So `conftest.py` owns only what pytest owns: making the helper importable no
matter which rootdir or import mode pytest picks, and exposing a few thin
fixtures that wrap the builders.
"""

from __future__ import annotations

import sys
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    # `.tools/` is not a package. Pytest's default prepend import mode already
    # adds this directory, but the guard keeps `import novel_fixtures` working
    # under `--import-mode=importlib` and under a different rootdir.
    sys.path.insert(0, str(TESTS_ROOT))

import pytest  # noqa: E402  (import follows the sys.path guard by necessity)

import novel_fixtures  # noqa: E402


@pytest.fixture(scope="session")
def checker():
    """The loaded `check_novel.py` module."""

    return novel_fixtures.load_checker()


@pytest.fixture
def fixtures():
    """The shared synthetic-fixture builder module."""

    return novel_fixtures


@pytest.fixture
def workspace(tmp_path):
    """A default synthetic workspace: contract, manuscript tree, control song."""

    return novel_fixtures.build_workspace(
        tmp_path / "workspace",
        planning=novel_fixtures.default_planning_documents(),
        chapters=(
            novel_fixtures.chapter_fixture(chapter=1),
            novel_fixtures.chapter_fixture(
                chapter=2, slug="second-fixture", pov_id="POV-TWO"
            ),
        ),
    )
