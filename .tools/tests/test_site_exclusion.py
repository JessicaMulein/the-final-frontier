"""Focused tests for task 3.2's contract reference collector."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CHECKER_PATH = TOOLS_ROOT / "check_novel.py"
COMMITTED_CONTRACT = (
    REPOSITORY_ROOT
    / "The Final Frontier Novel"
    / "exclusion-contract.json"
)

SPEC = importlib.util.spec_from_file_location("novel_site_exclusion", CHECKER_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError(f"Unable to load checker module from {CHECKER_PATH}")
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


class SiteExclusionFixtureTests(unittest.TestCase):
    """Exercise the exclusion-first collector against real filesystem trees."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_text(self, relative_path: str, content: str) -> Path:
        path = self.workspace / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def create_valid_fixture(self) -> tuple[Path, Path]:
        manuscript_root = self.workspace / "The Final Frontier Novel"
        (manuscript_root / "planning").mkdir(parents=True)
        (manuscript_root / "chapters" / "discovery-part").mkdir(parents=True)
        shutil.copy2(
            COMMITTED_CONTRACT,
            manuscript_root / "exclusion-contract.json",
        )
        self.write_text(
            "The Final Frontier Novel/front-matter.md",
            "# The Final Frontier\n\nManuscript front matter.\n",
        )
        self.write_text(
            "The Final Frontier Novel/planning/arc-outline.md",
            "# Arc Outline\n\nPlanning content.\n",
        )
        self.write_text(
            (
                "The Final Frontier Novel/chapters/discovery-part/"
                "discovery-part-001-noise-floor.md"
            ),
            "---\nchapter: 1\n---\n\nManuscript prose.\n",
        )
        self.write_text(
            "songs/control-song.md",
            "[Verse]\nA valid control song remains collectible.\n",
        )

        visibility_plan = self.write_text(
            "reference-visibility.json",
            json.dumps(
                {
                    "schema": "reference-song-visibility/v1",
                    "default_visible": True,
                    "rows": [
                        {
                            "source": "songs/control-song.md",
                            "visible": True,
                            "title": "Control Song",
                            "slug": "control-song",
                        },
                        {
                            "source": (
                                "The Final Frontier Novel/front-matter.md"
                            ),
                            "visible": True,
                            "title": "Must Never Become a Song",
                            "slug": "must-never-become-a-song",
                        },
                    ],
                },
                indent=2,
            ),
        )
        return manuscript_root / "exclusion-contract.json", visibility_plan

    def assert_no_manuscript_provenance(
        self, result: "CHECKER.SiteExclusionResult"
    ) -> None:
        manuscript_prefix = "The Final Frontier Novel/"
        for song in result.songs:
            self.assertFalse(song.source_path.startswith(manuscript_prefix))
        for artifact in result.artifacts:
            for source_path in artifact.source_paths:
                self.assertFalse(source_path.startswith(manuscript_prefix))
            self.assertNotIn(manuscript_prefix, artifact.content)

    def test_fixture_collects_only_control_song_and_no_manuscript_artifact(self) -> None:
        contract_path, visibility_plan = self.create_valid_fixture()

        result = CHECKER.run_site_exclusion(
            self.workspace,
            contract_path=contract_path,
            visibility_plan_path=visibility_plan,
        )

        self.assertNotIn(
            "The Final Frontier Novel", result.scanned_direct_children
        )
        self.assertEqual(
            [source.relative_path for source in result.sources],
            ["songs/control-song.md"],
        )
        self.assertEqual(
            result.songs,
            (
                CHECKER.Song(
                    source_path="songs/control-song.md",
                    title="Control Song",
                    slug="control-song",
                ),
            ),
        )
        self.assertEqual(
            {artifact.kind for artifact in result.artifacts},
            {"lyrics", "search", "index"},
        )
        self.assert_no_manuscript_provenance(result)
        self.assertFalse(result.external_adoption_verified)

    def test_resolved_direct_child_alias_into_manuscript_is_excluded(self) -> None:
        contract_path, visibility_plan = self.create_valid_fixture()
        alias = self.workspace / "manuscript-alias"
        try:
            alias.symlink_to(
                self.workspace / "The Final Frontier Novel",
                target_is_directory=True,
            )
        except (NotImplementedError, OSError) as exc:
            self.skipTest(f"directory symlinks unavailable: {exc}")

        result = CHECKER.run_site_exclusion(
            self.workspace,
            contract_path=contract_path,
            visibility_plan_path=visibility_plan,
        )

        self.assertNotIn("manuscript-alias", result.scanned_direct_children)
        self.assertEqual(
            [source.relative_path for source in result.sources],
            ["songs/control-song.md"],
        )
        self.assert_no_manuscript_provenance(result)

    def test_committed_contract_names_and_resolves_real_manuscript_root(self) -> None:
        contract = CHECKER.load_exclusion_contract(REPOSITORY_ROOT)

        self.assertEqual(contract.contract_path, COMMITTED_CONTRACT.resolve())
        self.assertEqual(len(contract.excluded_roots), 1)
        excluded_root = contract.excluded_roots[0]
        self.assertEqual(excluded_root.relative_path, "The Final Frontier Novel")
        self.assertEqual(
            excluded_root.resolved_path,
            (REPOSITORY_ROOT / "The Final Frontier Novel").resolve(),
        )
        self.assertTrue((excluded_root.resolved_path / "planning").is_dir())
        self.assertTrue((excluded_root.resolved_path / "chapters").is_dir())

    def test_missing_contract_fails_closed(self) -> None:
        with self.assertRaises(CHECKER.SiteExclusionError) as raised:
            CHECKER.run_site_exclusion(
                self.workspace,
                contract_path=self.workspace / "missing-contract.json",
            )

        self.assertEqual(raised.exception.code, "CONTRACT_MISSING")
        self.assertNotEqual(raised.exception.exit_status, 0)

    def test_malformed_contract_fails_closed(self) -> None:
        malformed = self.write_text("malformed-contract.json", "{not json")

        with self.assertRaises(CHECKER.SiteExclusionError) as raised:
            CHECKER.run_site_exclusion(
                self.workspace,
                contract_path=malformed,
            )

        self.assertEqual(raised.exception.code, "CONTRACT_MALFORMED")
        self.assertNotEqual(raised.exception.exit_status, 0)

    def test_stale_contract_with_missing_root_evidence_fails_closed(self) -> None:
        manuscript_root = self.workspace / "The Final Frontier Novel"
        (manuscript_root / "planning").mkdir(parents=True)
        contract_path = manuscript_root / "exclusion-contract.json"
        shutil.copy2(COMMITTED_CONTRACT, contract_path)
        # The required chapters/ directory is deliberately absent.

        with self.assertRaises(CHECKER.SiteExclusionError) as raised:
            CHECKER.run_site_exclusion(
                self.workspace,
                contract_path=contract_path,
            )

        self.assertEqual(raised.exception.code, "CONTRACT_STALE")
        self.assertIn("chapters", str(raised.exception.path))
        self.assertNotEqual(raised.exception.exit_status, 0)

    def test_cli_success_states_external_adoption_limit(self) -> None:
        contract_path, visibility_plan = self.create_valid_fixture()
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_status = CHECKER.main(
                [
                    "--site-exclusion",
                    "--workspace-root",
                    str(self.workspace),
                    "--contract",
                    str(contract_path),
                    "--visibility-plan",
                    str(visibility_plan),
                ]
            )

        self.assertEqual(exit_status, 0)
        self.assertIn("PASS site-exclusion", output.getvalue())
        self.assertIn("manuscript_entries=0", output.getvalue())
        self.assertIn(CHECKER.EXTERNAL_ADOPTION_LIMIT, output.getvalue())

    def test_cli_missing_contract_returns_nonzero(self) -> None:
        error_output = io.StringIO()

        with contextlib.redirect_stderr(error_output):
            exit_status = CHECKER.main(
                [
                    "--site-exclusion",
                    "--workspace-root",
                    str(self.workspace),
                    "--contract",
                    "missing-contract.json",
                ]
            )

        self.assertNotEqual(exit_status, 0)
        self.assertIn("CONTRACT_MISSING", error_output.getvalue())
        self.assertIn(CHECKER.EXTERNAL_ADOPTION_LIMIT, error_output.getvalue())


if __name__ == "__main__":
    unittest.main()
