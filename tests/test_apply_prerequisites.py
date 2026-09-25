"""Exercise the real init/apply preflight without touching the current home."""

import json
import os
import platform
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CHEZMOI = shutil.which("chezmoi")


@unittest.skipUnless(CHEZMOI, "chezmoi required")
class ApplyPrerequisites(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="chezmoi-preflight-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / ".git").mkdir()  # No network or Git initialization.
        (self.source / ".chezmoitemplates").mkdir()
        for relative in (
            ".chezmoi.toml.tmpl",
            ".chezmoiignore",
            ".chezmoitemplates/apply-prerequisites",
        ):
            target = self.source / relative
            target.write_bytes((REPO / relative).read_bytes())
        (self.source / "dot_marker").write_text("applied\n")
        self.home = self.root / "home"
        self.home.mkdir()
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), PATH=str(self.bin_dir))
        self.args = [
            CHEZMOI,
            "--source", str(self.source),
            "--destination", str(self.home),
            "--config", str(self.root / "config.toml"),
            "--cache", str(self.root / "cache"),
            "--persistent-state", str(self.root / "state"),
            "--no-tty",
        ]

    def run_cm(self, *command, input=None):
        return subprocess.run(
            [*self.args, *command], env=self.env, input=input,
            capture_output=True, text=True, timeout=20,
        )

    def make_available(self, name, executable=None):
        target = self.bin_dir / name
        if executable is None:
            target.write_text("#!/bin/sh\nexit 0\n")
            target.chmod(0o755)
        else:
            target.symlink_to(executable)

    def test_missing_commands_abort_init_before_first_prompt(self):
        result = self.run_cm("init", "--apply", input="Fixture User\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("error calling fail: Cannot apply dotfiles:", result.stderr)
        self.assertIn("git (source checkout and Git externals)", result.stderr)
        self.assertNotIn("Full Name?", result.stdout + result.stderr)
        self.assertFalse((self.root / "config.toml").exists())

    def test_linux_package_manager_is_checked_for_selected_distribution(self):
        self.make_available("git")
        for distribution, manager in (("ubuntu", "apt"), ("arch", "pacman")):
            data = json.dumps({
                "chezmoi": {
                    "os": "linux", "osRelease": {"id": distribution},
                    "username": "fixture",
                },
            })
            result = self.run_cm(
                "--override-data", data, "execute-template",
                "--file", str(self.source / ".chezmoiignore"),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(f"{manager} (package provisioning)", result.stderr)
            self.assertIn("sudo (non-root package provisioning)", result.stderr)

            self.make_available(manager)
            root_data = json.dumps({
                "chezmoi": {
                    "os": "linux", "osRelease": {"id": distribution},
                    "username": "root",
                },
            })
            root_result = self.run_cm(
                "--override-data", root_data, "execute-template",
                "--file", str(self.source / ".chezmoiignore"),
            )
            self.assertEqual(root_result.returncode, 0, root_result.stderr)
            (self.bin_dir / manager).unlink()

    @unittest.skipUnless(shutil.which("git"), "Git required to exercise successful init")
    def test_apply_checks_again_before_writing_and_recovers(self):
        self.make_available("git", shutil.which("git"))
        if platform.system() == "Darwin":
            self.make_available("curl")
        elif platform.system() == "Linux":
            for manager in ("apt", "pacman", "sudo"):
                self.make_available(manager)

        answers = "Fixture User\nfixture@example.invalid\nProjects\nn\n"
        result = self.run_cm("init", input=answers)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Full Name?", result.stdout)

        (self.bin_dir / "git").unlink()
        missing = self.run_cm("apply")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("git (source checkout and Git externals)", missing.stderr)
        self.assertFalse((self.home / ".marker").exists())

        self.make_available("git", shutil.which("git"))
        applied = self.run_cm("apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertEqual((self.home / ".marker").read_text(), "applied\n")


if __name__ == "__main__":
    unittest.main()
