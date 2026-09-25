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
            ".chezmoitemplates/windows-xdg-check",
        ):
            target = self.source / relative
            target.write_bytes((REPO / relative).read_bytes())
        (self.source / "dot_marker").write_text("applied\n")
        self.home = self.root / "home"
        self.home.mkdir()
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), PATH=str(self.bin_dir))
        self.env["XDG_CONFIG_HOME"] = str(self.home / ".config")
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


    @unittest.skipUnless(shutil.which("git"), "Git required to exercise successful init")
    def test_windows_winget_blocks_init_template_and_apply_before_writing(self):
        (self.source / "dot_editorconfig").write_text("windows preflight marker\n")
        windows = json.dumps({"chezmoi": {"os": "windows", "arch": "amd64"}})
        init_template = (
            "--override-data", windows, "execute-template", "--init",
            "--file", str(self.source / ".chezmoi.toml.tmpl"),
        )

        missing_both = self.run_cm(*init_template)
        self.assertNotEqual(missing_both.returncode, 0)
        self.assertIn("git (source checkout and Git externals)", missing_both.stderr)
        self.assertIn("winget.exe (Windows package provisioning)", missing_both.stderr)

        self.make_available("git", shutil.which("git"))
        missing_init = self.run_cm(*init_template)
        self.assertNotEqual(missing_init.returncode, 0)
        self.assertIn("winget.exe (Windows package provisioning)", missing_init.stderr)
        self.assertNotIn("Full Name?", missing_init.stdout + missing_init.stderr)
        self.assertFalse((self.root / "config.toml").exists())

        self.make_available("winget.exe")
        ready = json.dumps({
            "chezmoi": {"os": "windows", "arch": "amd64"},
            "fullName": "Fixture User",
            "personalEmail": "fixture@example.invalid",
            "personalProjectFolder": "Projects",
            "hasWorkProfile": False,
            "has_work_profile": False,
        })
        initialized = self.run_cm(
            "--override-data", ready, "execute-template", "--init",
            "--file", str(self.source / ".chezmoi.toml.tmpl"),
        )
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        self.assertIn("Fixture User", initialized.stdout)

        (self.bin_dir / "winget.exe").unlink()
        missing_apply = self.run_cm("--override-data", ready, "apply")
        self.assertNotEqual(missing_apply.returncode, 0)
        self.assertIn("winget.exe (Windows package provisioning)", missing_apply.stderr)
        self.assertFalse((self.home / ".editorconfig").exists())

        self.make_available("winget.exe")
        applied = self.run_cm("--override-data", ready, "apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertEqual((self.home / ".editorconfig").read_text(), "windows preflight marker\n")


if __name__ == "__main__":
    unittest.main()
