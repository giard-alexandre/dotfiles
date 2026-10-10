"""Exercise the default-shell hook with fake system tools and paths."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CHEZMOI = shutil.which("chezmoi")
SCRIPT = ".chezmoiscripts/run_onchange_after_100-set-zsh-default-shell.sh.tmpl"
USER = "tester"
# Real utilities the hook needs; everything system-specific is faked.
TOOLS = (
    "sed", "cut", "grep", "head", "tee", "mkdir", "mv", "rm", "dirname",
    "realpath", "readlink", "cat", "chmod", "sh",
)


@unittest.skipUnless(CHEZMOI and Path("/bin/bash").exists(), "chezmoi and bash required")
class DefaultShell(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="chezmoi-shell-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.home = self.root / "home"
        self.bin_dir = self.root / "bin with spaces"
        self.sys_dir = self.root / "system zsh"
        self.etc = self.root / "etc"
        self.log = self.root / "log"
        for directory in (self.source, self.home, self.bin_dir, self.sys_dir, self.etc, self.log):
            directory.mkdir()
        for relative in (SCRIPT, ".chezmoitemplates/run-as-root", ".chezmoitemplates/brew-executable"):
            target = self.source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((REPO / relative).read_bytes())
        for tool in TOOLS:
            found = shutil.which(tool)
            if found:
                (self.bin_dir / tool).symlink_to(found)

        self.sys_zsh = self.fake_zsh(self.sys_dir / "zsh", "5.9")
        self.getent = self.etc / "getent-passwd"
        self.passwd = self.etc / "passwd"
        self.passwd.write_text("root:x:0:0::/root:/bin/sh\n")
        self.nsswitch = self.etc / "nsswitch.conf"
        self.nsswitch.write_text("passwd: files systemd\n")
        self.shells = self.etc / "shells"
        self.shells.write_text("/bin/sh\n")
        self.sssd_dir = self.etc / "sssd" / "conf.d"
        self.sssd_dir.mkdir(parents=True)
        self.snippet = self.sssd_dir / "50-chezmoi-shell.conf"
        self.state = self.home / ".local" / "state" / "chezmoi" / "default-shell"
        self.set_login_shell("/bin/bash")

        self.executable("getent", '[ "$1" = passwd ] && cat "$FIXTURE_GETENT"\n')
        self.executable("sudo", 'exec "$@"\n')
        self.executable("chown", 'echo "$*" >> "$FIXTURE_LOG/chown"\n')
        self.executable("sss_cache", 'echo "$*" >> "$FIXTURE_LOG/sss_cache"\n')
        self.executable("chsh", 'echo "$*" >> "$FIXTURE_LOG/chsh"\n')
        self.executable(
            "systemctl",
            'echo "$*" >> "$FIXTURE_LOG/systemctl"\n'
            'case "$1" in\n'
            '    is-active) exit "${FIXTURE_SSSD_STATUS:-0}" ;;\n'
            '    restart)\n'
            '        if [ -f "$FIXTURE_SNIPPET" ]; then\n'
            '            shell=$(sed -n "s/^override_shell = //p" "$FIXTURE_SNIPPET")\n'
            '            printf "%s\\n" "tester:*:1000:1000::/home/tester:$shell" > "$FIXTURE_GETENT"\n'
            '        fi ;;\n'
            'esac\n',
        )

        self.env = dict(
            os.environ,
            HOME=str(self.home),
            PATH=str(self.bin_dir),
            FIXTURE_GETENT=str(self.getent),
            FIXTURE_LOG=str(self.log),
            FIXTURE_SNIPPET=str(self.snippet),
            DEFAULT_SHELL_PASSWD_FILE=str(self.passwd),
            DEFAULT_SHELL_NSSWITCH_FILE=str(self.nsswitch),
            DEFAULT_SHELL_SHELLS_FILE=str(self.shells),
            DEFAULT_SHELL_SSSD_CONF_DIR=str(self.sssd_dir),
            DEFAULT_SHELL_ZSH_CANDIDATES=str(self.sys_zsh),
            DEFAULT_SHELL_TTY=str(self.root / "no-tty"),
        )
        self.env.pop("XDG_STATE_HOME", None)
        self.env.pop("DEFAULT_SHELL_STATE_FILE", None)
        self.os = "linux"

    # --- fixtures -------------------------------------------------------------
    def executable(self, name, body, directory=None):
        target = (directory or self.bin_dir) / name
        target.write_text("#!/bin/sh\n" + body)
        target.chmod(0o755)
        return target

    def fake_zsh(self, path, version):
        path.write_text(f'#!/bin/sh\n[ "$1" = -c ] && echo {version}\n')
        path.chmod(0o755)
        return path

    def set_login_shell(self, shell):
        self.getent.write_text(f"{USER}:*:1000:1000::/home/{USER}:{shell}\n")

    def local_account(self):
        with self.passwd.open("a") as passwd:
            passwd.write(f"{USER}:x:1000:1000::/home/{USER}:/bin/bash\n")

    def use_sssd(self):
        self.nsswitch.write_text("passwd: files systemd sss\n")

    def logged(self, name):
        path = self.log / name
        return path.read_text() if path.exists() else ""

    def args(self):
        return [
            CHEZMOI,
            "--source", str(self.source),
            "--destination", str(self.home),
            "--config", str(self.root / "config.toml"),
            "--cache", str(self.root / "cache"),
            "--persistent-state", str(self.root / "state"),
            "--no-tty",
            "--override-data", json.dumps({
                "chezmoi": {"os": self.os, "arch": "arm64", "username": USER},
            }),
        ]

    def apply(self, tty_input=None):
        """Apply; with tty_input, stdin is a pseudo-terminal pre-filled with it."""
        command = [*self.args(), "apply", "--force"]
        if tty_input is None:
            return subprocess.run(
                command, env=self.env, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, timeout=20,
            )
        master, slave = os.openpty()
        try:
            os.write(master, tty_input.encode())
            return subprocess.run(
                command, env=self.env, stdin=slave, start_new_session=True,
                capture_output=True, text=True, timeout=20,
            )
        finally:
            os.close(slave)
            os.close(master)

    def assertApplied(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def render(self):
        return subprocess.run(
            [*self.args(), "execute-template"], env=self.env,
            input=(self.source / SCRIPT).read_text(),
            capture_output=True, text=True, timeout=20, check=True,
        ).stdout

    # --- tests --------------------------------------------------------------------
    def test_local_account_uses_chsh(self):
        self.local_account()
        result = self.apply()
        self.assertApplied(result)
        self.assertEqual(self.logged("chsh"), f"-s {self.sys_zsh}\n")
        self.assertIn(f"{self.sys_zsh}\n", self.shells.read_text())

    def test_already_correct_shell_is_noop(self):
        self.local_account()
        for shell in ("/bin/zsh", "/usr/bin/zsh"):
            if Path(shell).exists():
                break
        else:
            self.skipTest("no system zsh to compare at render time")
        self.set_login_shell(shell)
        self.assertEqual(self.render(), "")
        # The run-time check covers shells the renderer cannot know about.
        self.set_login_shell(str(self.sys_zsh))
        result = self.apply()
        self.assertApplied(result)
        self.assertIn("already", result.stdout)
        self.assertEqual(self.logged("chsh"), "")

    def test_sssd_yes_writes_snippet(self):
        self.use_sssd()
        result = self.apply(tty_input="y\n")
        self.assertApplied(result)
        self.assertIn("EVERY SSSD user", result.stdout)
        self.assertEqual(self.snippet.read_text(), f"[nss]\noverride_shell = {self.sys_zsh}\n")
        self.assertEqual(self.snippet.stat().st_mode & 0o777, 0o600)
        self.assertIn(f"root:root {self.snippet}", self.logged("chown"))
        self.assertEqual(self.logged("sss_cache"), "-E\n")
        self.assertIn("restart sssd", self.logged("systemctl"))
        self.assertIn("sssd_override=yes", self.state.read_text())
        self.assertEqual(self.logged("chsh"), "")
        self.assertNotIn("Warning", result.stderr)

    def test_sssd_snippet_removed_when_getent_unchanged(self):
        self.use_sssd()
        self.env["FIXTURE_SNIPPET"] = str(self.root / "ignored")
        result = self.apply(tty_input="y\n")
        self.assertApplied(result)
        self.assertFalse(self.snippet.exists())
        self.assertEqual(self.logged("systemctl").count("restart sssd"), 2)
        self.assertIn("getent does not report", result.stderr)

    def test_sssd_no_writes_nothing_and_is_remembered(self):
        self.use_sssd()
        result = self.apply(tty_input="n\n")
        self.assertApplied(result)
        self.assertFalse(self.snippet.exists())
        self.assertIn("sssd_override=no", self.state.read_text())
        (self.root / "state").unlink()  # force run_onchange to run again
        result = self.apply(tty_input="y\n")
        self.assertApplied(result)
        self.assertFalse(self.snippet.exists())
        self.assertIn("saved answer: no", result.stdout)
        self.assertNotIn("[y/N]", result.stderr)

    def test_sssd_without_tty_skips(self):
        self.use_sssd()
        result = self.apply()
        self.assertApplied(result)
        self.assertFalse(self.snippet.exists())
        self.assertFalse(self.state.exists())
        self.assertIn("No terminal available", result.stderr)

    def test_unsupported_directory_warns(self):
        self.nsswitch.write_text("passwd: files ldap\n")
        result = self.apply(tty_input="y\n")
        self.assertApplied(result)
        self.assertIn("not served by SSSD", result.stderr)
        self.assertFalse(self.snippet.exists())
        self.assertEqual(self.logged("chsh"), "")

    def test_inactive_sssd_is_unsupported(self):
        self.use_sssd()
        self.env["FIXTURE_SSSD_STATUS"] = "3"
        result = self.apply(tty_input="y\n")
        self.assertApplied(result)
        self.assertIn("not served by SSSD", result.stderr)
        self.assertFalse(self.snippet.exists())

    def test_chsh_failure_warns(self):
        self.local_account()
        self.executable("chsh", "exit 1\n")
        result = self.apply()
        self.assertApplied(result)
        self.assertIn(f"chsh -s '{self.sys_zsh}'", result.stderr)

    def test_multiple_candidates_list_versions_and_take_default(self):
        self.local_account()
        alias = self.sys_dir / "usr-bin-zsh"
        alias.symlink_to(self.sys_zsh)  # same binary: listed once
        self.env["DEFAULT_SHELL_ZSH_CANDIDATES"] = f"{self.sys_zsh}:{alias}"
        path_zsh = self.fake_zsh(self.bin_dir / "zsh", "5.9.2")
        self.set_login_shell(str(path_zsh))
        self.executable("chsh", 'echo "$*" >> "$FIXTURE_LOG/chsh"\n')

        result = self.apply(tty_input="\n")
        self.assertApplied(result)
        self.assertIn("Multiple zsh installations found:", result.stdout)
        lines = [line for line in result.stdout.splitlines() if line.startswith("  ")]
        self.assertEqual(len(lines), 2, result.stdout)
        self.assertRegex(lines[0], rf"1\) {self.sys_zsh}\s+5\.9\s+\(system package\) \[default\]")
        self.assertRegex(lines[1], r"2\) .*bin with spaces/zsh\s+5\.9\.2\s+\(PATH\) \(current login shell\)")
        self.assertIn("[1]:", result.stderr)
        self.assertEqual(self.logged("chsh"), f"-s {self.sys_zsh}\n")
        self.assertIn(f"zsh_path={self.sys_zsh}", self.state.read_text())

    def test_multiple_candidates_without_tty_use_default(self):
        self.local_account()
        self.fake_zsh(self.bin_dir / "zsh", "5.9.2")
        result = self.apply()
        self.assertApplied(result)
        self.assertIn(f"using the default {self.sys_zsh}", result.stdout)
        self.assertEqual(self.logged("chsh"), f"-s {self.sys_zsh}\n")
        self.assertFalse(self.state.exists())

    def test_darwin_prefers_homebrew_zsh(self):
        self.os = "darwin"
        prefix = self.root / "homebrew"
        (prefix / "bin").mkdir(parents=True)
        brew_zsh = self.fake_zsh(prefix / "bin" / "zsh", "5.9.2")
        self.env["DEFAULT_SHELL_BREW_PREFIX"] = str(prefix)
        self.executable("dscl", f'echo "UserShell: {self.sys_zsh}"\n')
        result = self.apply(tty_input="\n")
        self.assertApplied(result)
        self.assertRegex(result.stdout, rf"1\) {brew_zsh}\s+5\.9\.2\s+\(Homebrew\) \[default\]")
        self.assertRegex(result.stdout, rf"2\) {self.sys_zsh}\s+5\.9\s+\(macOS system\) \(current login shell\)")
        self.assertEqual(self.logged("chsh"), f"-s {brew_zsh}\n")

    def test_saved_path_is_reused(self):
        self.local_account()
        path_zsh = self.fake_zsh(self.bin_dir / "zsh", "5.9.2")
        self.state.parent.mkdir(parents=True)
        self.state.write_text(f"zsh_path={path_zsh}\n")
        result = self.apply(tty_input="1\n")
        self.assertApplied(result)
        self.assertNotIn("Multiple zsh", result.stdout)
        self.assertIn("Using saved zsh choice", result.stdout)
        self.assertEqual(self.logged("chsh"), f"-s {path_zsh}\n")
        # Once applied, the saved choice also makes rendering a no-op.
        self.set_login_shell(str(path_zsh))
        self.assertEqual(self.render(), "")

    def test_stale_saved_path_is_ignored(self):
        self.local_account()
        path_zsh = self.fake_zsh(self.bin_dir / "zsh", "5.9.2")
        self.state.parent.mkdir(parents=True)
        self.state.write_text("zsh_path=/nonexistent/zsh\nsssd_override=no\n")
        result = self.apply(tty_input="2\n")
        self.assertApplied(result)
        self.assertIn("no longer exists", result.stderr)
        self.assertIn("Multiple zsh", result.stdout)
        self.assertEqual(self.logged("chsh"), f"-s {path_zsh}\n")
        self.assertEqual(
            sorted(self.state.read_text().splitlines()),
            ["sssd_override=no", f"zsh_path={path_zsh}"],
        )


if __name__ == "__main__":
    unittest.main()
