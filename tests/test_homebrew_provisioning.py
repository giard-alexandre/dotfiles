"""Exercise macOS bootstrap and package failures without installing software."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CHEZMOI = shutil.which("chezmoi")
WORKBREW = Path("/opt/workbrew/bin/brew")


@unittest.skipUnless(
    CHEZMOI and Path("/bin/bash").exists() and Path("/bin/zsh").exists(),
    "chezmoi and Unix lifecycle shells required",
)
class HomebrewProvisioning(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="chezmoi-brew-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.home = self.root / "home"
        self.bin_dir = self.root / "bin with spaces"
        for directory in (self.source, self.home, self.bin_dir):
            directory.mkdir()
        for relative in (
            ".chezmoitemplates/brew-executable",
            ".chezmoiscripts/run_once_before_000-macos-install-brew.sh.tmpl",
        ):
            self.copy_source(relative)
        (self.source / "dot_marker").write_text("applied\n")
        self.installation_state = self.root / "installation-owner"
        self.installation_state.write_text("managed\n")
        self.env = dict(
            os.environ,
            HOME=str(self.home),
            PATH=str(self.bin_dir),
            FIXTURE_INSTALLATION_STATE=str(self.installation_state),
        )
        self.args = [
            CHEZMOI,
            "--source", str(self.source),
            "--destination", str(self.home),
            "--config", str(self.root / "config.toml"),
            "--cache", str(self.root / "cache"),
            "--persistent-state", str(self.root / "state"),
            "--no-tty",
            "--override-data", json.dumps({
                "chezmoi": {"os": "darwin", "arch": "amd64"},
            }),
        ]

    def copy_source(self, relative):
        target = self.source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO / relative).read_bytes())

    def executable(self, name, content):
        target = self.bin_dir / name
        target.write_text(content)
        target.chmod(0o755)

    def apply(self):
        return subprocess.run(
            [*self.args, "apply", "--force"], env=self.env,
            capture_output=True, text=True, timeout=20,
        )

    def test_existing_installation_is_not_replaced_by_bootstrap(self):
        self.executable("brew", "#!/bin/sh\nexit 0\n")
        # A downloaded installer would replace the existing installation's owner.
        self.executable(
            "curl",
            "#!/bin/sh\n"
            "printf '%s\\n' 'printf \"unmanaged\\n\" > \"$FIXTURE_INSTALLATION_STATE\"'\n",
        )
        result = self.apply()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / ".marker").read_text(), "applied\n")
        self.assertEqual(self.installation_state.read_text(), "managed\n")

    @unittest.skipIf(WORKBREW.exists(), "real Workbrew takes precedence over fixture PATH")
    def test_required_package_denial_aborts_before_applying_files(self):
        self.executable("brew", "#!/bin/sh\nexit 29\n")
        self.copy_source(".chezmoiscripts/run_onchange_before_010-darwin-install-packages.sh.tmpl")
        (self.source / ".chezmoidata.json").write_text(json.dumps({
            "packages": {"darwin": {
                "taps": [], "brews": ["git"], "optional_brews": [],
                "casks": [], "arm64": {"casks": []},
            }},
        }))
        result = self.apply()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / ".marker").exists())
        self.assertEqual(self.installation_state.read_text(), "managed\n")

    @unittest.skipIf(WORKBREW.exists(), "real Workbrew takes precedence over fixture PATH")
    def test_optional_failures_allow_other_installs_and_apply(self):
        self.executable(
            "brew",
            "#!/bin/sh\n"
            "case \"$1:${2-}:${3-}\" in\n"
            "    bundle:*) exec /bin/cat > /dev/null ;;\n"
            "    tap:denied/tap:|install:--formula:denied-formula|"
            "install:--cask:denied-cask|install:--cask:denied-arm-cask) exit 29 ;;\n"
            "    tap:allowed/tap:) : > \"$FIXTURE_PACKAGE_STATE/tap\" ;;\n"
            "    install:--formula:allowed-formula) : > \"$FIXTURE_PACKAGE_STATE/formula\" ;;\n"
            "    install:--cask:allowed-cask) : > \"$FIXTURE_PACKAGE_STATE/cask\" ;;\n"
            "    install:--cask:allowed-arm-cask) : > \"$FIXTURE_PACKAGE_STATE/arm-cask\" ;;\n"
            "    *) exit 99 ;;\n"
            "esac\n",
        )
        self.copy_source(".chezmoiscripts/run_onchange_before_010-darwin-install-packages.sh.tmpl")
        (self.source / ".chezmoidata.json").write_text(json.dumps({
            "packages": {"darwin": {
                "brews": ["git"],
                "taps": ["denied/tap", "allowed/tap"],
                "optional_brews": ["denied-formula", "allowed-formula"],
                "casks": ["denied-cask", "allowed-cask"],
                "arm64": {"casks": ["denied-arm-cask", "allowed-arm-cask"]},
            }},
        }))
        for arch in ("amd64", "arm64"):
            with self.subTest(arch=arch):
                installed = self.root / f"installed-{arch}"
                installed.mkdir()
                self.env["FIXTURE_PACKAGE_STATE"] = str(installed)
                self.args[-1] = json.dumps({"chezmoi": {"os": "darwin", "arch": arch}})
                (self.home / ".marker").unlink(missing_ok=True)
                result = self.apply()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((self.home / ".marker").read_text(), "applied\n")
                expected = {"tap", "formula", "cask"}
                if arch == "arm64":
                    expected.add("arm-cask")
                self.assertEqual({path.name for path in installed.iterdir()}, expected)


if __name__ == "__main__":
    unittest.main()
