#!/usr/bin/env python3
"""Render-only path checks: python3 tests/worktrunk/test_config.py."""

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[2]
CHEZMOI = shutil.which("chezmoi")
WT = shutil.which("wt")


@unittest.skipUnless(CHEZMOI and WT, "chezmoi and Worktrunk required")
class WorktrunkConfig(unittest.TestCase):
    def render(self, personal, work=None):
        with tempfile.TemporaryDirectory(prefix="worktrunk-config-") as directory:
            config = Path(directory) / "chezmoi.json"
            config.write_text("{}", encoding="utf-8")
            data = {"personal_project_folder": personal, "has_work_profile": work is not None}
            if work is not None:
                data["work_project_folder"] = work
            result = subprocess.run(
                [CHEZMOI, "--source", str(ROOT), "--config", str(config),
                 "--cache", str(Path(directory) / "cache"),
                 "--persistent-state", str(Path(directory) / "state.boltdb"),
                 "--no-tty", "--override-data", json.dumps(data),
                 "execute-template", "--file", str(ROOT / "dot_config/worktrunk/config.toml.tmpl")],
                text=True, capture_output=True, check=True,
            )
            parsed = tomllib.loads(result.stdout)
            self.assertEqual(set(parsed), {"worktree-path"})
            return parsed["worktree-path"]

    def evaluate(self, layout, repo_path, repo="repo1", branch="feature/search"):
        # Worktrunk's own template engine validates the exact expression and filter.
        context = ("{% set repo_path = " + json.dumps(repo_path) + " %}"
                   "{% set repo = " + json.dumps(repo) + " %}"
                   "{% set branch = " + json.dumps(branch) + " %}")
        result = subprocess.run([WT, "-C", str(ROOT), "step", "eval", context + layout],
                                text=True, capture_output=True, check=True)
        return result.stdout.strip()

    def test_personal_and_optional_work_roots(self):
        for work in (None, "/home/test/work"):
            layout = self.render("/home/test/dev", work)
            with self.subTest(work=work):
                self.assertEqual(self.evaluate(layout, "/home/test/dev/repo1"),
                                 "/home/test/dev/.worktrees/repo1/feature-search")
                self.assertEqual(self.evaluate(layout, "/home/test/dev/group/repo1"),
                                 "/home/test/dev/.worktrees/repo1/feature-search")
                expected = ("/home/test/work/.worktrees/repo1/feature-search" if work else
                            "/home/test/work/repo1/../repo1.feature-search")
                self.assertEqual(self.evaluate(layout, "/home/test/work/repo1"), expected)

    def test_boundary_and_outside_fallback(self):
        layout = self.render("/home/test/dev", "/home/test/work")
        for path in ("/home/test/dev-other/repo1", "/home/test/work-other/repo1", "/elsewhere/repo1"):
            with self.subTest(path=path):
                self.assertEqual(self.evaluate(layout, path), path + "/../repo1.feature-search")

    def test_nested_roots_and_paths_with_spaces(self):
        for personal, work, root in [
            ("/home/test/dev", "/home/test/dev/work", "/home/test/dev/work"),
            ("/home/test/work/personal", "/home/test/work", "/home/test/work/personal"),
            ("/home/test/Personal Code", "/home/test/Work Code", "/home/test/Work Code"),
        ]:
            with self.subTest(personal=personal, work=work):
                layout = self.render(personal, work)
                self.assertEqual(self.evaluate(layout, root + "/repo1"),
                                 root + "/.worktrees/repo1/feature-search")

    def test_quoted_paths_and_trailing_slashes(self):
        root = '/home/test/"Personal" Code'
        layout = self.render(root + "/")
        self.assertEqual(self.evaluate(layout, root + "/repo1", branch="fix/path"),
                         root + "/.worktrees/repo1/fix-path")


if __name__ == "__main__":
    unittest.main()
