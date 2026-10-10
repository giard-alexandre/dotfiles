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
    "realpath", "readlink", "cat", "chmod", "sh", "true", "tr", "cp",
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
        # Fake SSSD directory: the user's domain and the shell the directory returns.
        self.directory = self.etc / "directory"
        self.directory.write_text("domain=CORP.EXAMPLE.COM\ndirectory_shell=\n")
        self.sssd_conf = self.etc / "sssd" / "sssd.conf"
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

        self.executable(
            "getent",
            '[ "$1" = passwd ] || exit 2\n'
            'domain=$(sed -n "s/^domain=//p" "$FIXTURE_DIRECTORY")\n'
            'case "$2" in\n'
            '    tester) cat "$FIXTURE_GETENT" ;;\n'
            '    tester@*)\n'
            '        want=$(printf "%s" "${2#*@}" | tr "[:upper:]" "[:lower:]")\n'
            '        have=$(printf "%s" "$domain" | tr "[:upper:]" "[:lower:]")\n'
            '        [ -n "$have" ] && [ "$want" = "$have" ] && cat "$FIXTURE_GETENT" || exit 2 ;;\n'
            '    *) exit 2 ;;\n'
            'esac\n',
        )
        self.executable(
            "sudo",
            # One line per call, even when an argument is a multi-line sh -c script.
            'printf "%s\\n" "$*" | tr "\\n" " " >> "$FIXTURE_LOG/sudo"; echo >> "$FIXTURE_LOG/sudo"\n'
            'printf "%s\\n" "${SUDO_PROMPT-}" >> "$FIXTURE_LOG/sudo-prompts"\n'
            'exec "$@"\n',
        )
        self.executable("chown", 'echo "$*" >> "$FIXTURE_LOG/chown"\n')
        self.executable("sss_cache", 'echo "$*" >> "$FIXTURE_LOG/sss_cache"\n')
        self.executable("chsh", 'echo "$*" >> "$FIXTURE_LOG/chsh"\n')
        self.executable(
            "systemctl",
            'echo "$*" >> "$FIXTURE_LOG/systemctl"\n'
            'case "$1" in\n'
            '    is-active) exit "${FIXTURE_SSSD_STATUS:-0}" ;;\n'
            '    reset-failed) ;;\n'
            '    restart)\n'
            # FIXTURE_RESTART_FAILURES=N: the next N restarts fail without reloading.
            '        left=$(cat "$FIXTURE_LOG/restart-failures" 2>/dev/null || echo "${FIXTURE_RESTART_FAILURES:-0}")\n'
            '        if [ "$left" -gt 0 ]; then echo $((left - 1)) > "$FIXTURE_LOG/restart-failures"; exit 1; fi\n'
            # Model SSSD precedence: override_shell > directory shell > default_shell.
            # [nss] settings apply to every domain; [domain/X] only to domain X.
            '        domain=$(sed -n "s/^domain=//p" "$FIXTURE_DIRECTORY")\n'
            '        shell=$(sed -n "s/^directory_shell=//p" "$FIXTURE_DIRECTORY")\n'
            '        if [ -f "$FIXTURE_SNIPPET" ]; then\n'
            '            override=$(sed -n "s/^override_shell = //p" "$FIXTURE_SNIPPET")\n'
            '            section=$(sed -n "s/^\\[domain\\/\\(.*\\)\\]$/\\1/p" "$FIXTURE_SNIPPET" | tr "[:upper:]" "[:lower:]")\n'
            '            default=$(sed -n "s/^default_shell = //p" "$FIXTURE_SNIPPET")\n'
            '            mine=$(printf "%s" "$domain" | tr "[:upper:]" "[:lower:]")\n'
            '            [ -z "$section" ] || [ "$section" = "$mine" ] || override=\n'
            '            if [ -n "$override" ]; then shell=$override\n'
            '            elif [ -z "$shell" ] && [ -n "$default" ] && [ "$section" = "$mine" ]; then shell=$default; fi\n'
            '        fi\n'
            '        printf "%s\\n" "tester:*:1000:1000::/home/tester:$shell" > "$FIXTURE_GETENT" ;;\n'
            'esac\n',
        )

        self.env = dict(
            os.environ,
            HOME=str(self.home),
            PATH=str(self.bin_dir),
            FIXTURE_GETENT=str(self.getent),
            FIXTURE_LOG=str(self.log),
            FIXTURE_SNIPPET=str(self.snippet),
            FIXTURE_DIRECTORY=str(self.directory),
            DEFAULT_SHELL_PASSWD_FILE=str(self.passwd),
            DEFAULT_SHELL_NSSWITCH_FILE=str(self.nsswitch),
            DEFAULT_SHELL_SHELLS_FILE=str(self.shells),
            DEFAULT_SHELL_SSSD_CONF_DIR=str(self.sssd_dir),
            DEFAULT_SHELL_SSSD_CONF=str(self.sssd_conf),
            DEFAULT_SHELL_KRB5_CONF=str(self.etc / "krb5.conf"),
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

    def use_sssd(self, domains=("OTHER.EXAMPLE.COM", "CORP.EXAMPLE.COM"), directory_shell=""):
        """SSSD serves the user; sssd.conf lists `domains`, the user is in CORP."""
        self.nsswitch.write_text("passwd: files systemd sss\n")
        self.sssd_conf.write_text(
            f"[sssd]\nservices = nss\ndomains = {', '.join(domains)}\n\n[nss]\n\n"
            + "".join(f"[domain/{d}]\nid_provider = ldap\ndefault_shell = /bin/bash\n\n" for d in domains)
        )
        self.directory.write_text(f"domain=CORP.EXAMPLE.COM\ndirectory_shell={directory_shell}\n")

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
            # Trailing Ctrl-D: an unexpected extra prompt reads EOF instead of hanging.
            os.write(master, tty_input.encode() + b"\x04")
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

    def snippet_text(self):
        return self.snippet.read_text() if self.snippet.exists() else None

    def test_sssd_default_shell_in_users_domain(self):
        self.use_sssd()
        # A passing validator: the success path must run sssctl config-check.
        self.executable("sssctl", 'echo "$*" >> "$FIXTURE_LOG/sssctl"\n')
        result = self.apply(tty_input="y\n")
        self.assertApplied(result)
        self.assertEqual(self.logged("sssctl"), "config-check\n")
        self.assertIn("Your account belongs to SSSD domain CORP.EXAMPLE.COM", result.stdout)
        self.assertEqual(
            self.snippet_text(), f"[domain/CORP.EXAMPLE.COM]\ndefault_shell = {self.sys_zsh}\n",
        )
        self.assertEqual(self.snippet.stat().st_mode & 0o777, 0o600)
        self.assertIn(f"root:root {self.snippet}", self.logged("chown"))
        self.assertEqual(self.logged("sss_cache"), "-E\n")
        self.assertIn("restart sssd", self.logged("systemctl"))
        self.assertIn("sssd_default_shell=yes", self.state.read_text())
        self.assertNotIn("Set override_shell", result.stderr)  # never offered
        self.assertEqual(self.logged("chsh"), "")
        self.assertNotIn("Warning", result.stderr)

    def test_sudo_reasons_are_explained(self):
        self.use_sssd()
        result = self.apply(tty_input="y\n")
        self.assertApplied(result)
        self.assertIn("needs sudo: SSSD's configuration is root-only", result.stdout)
        reasons = [line[line.index("Using sudo to "):] for line in result.stderr.splitlines() if "Using sudo to " in line]
        self.assertTrue(any("read the root-only SSSD configuration" in r for r in reasons), reasons)
        self.assertTrue(any(f"add {self.sys_zsh} to {self.shells}" in r for r in reasons), reasons)
        self.assertTrue(any(f"write the SSSD setting to {self.snippet}" in r for r in reasons), reasons)
        self.assertTrue(any("restart sssd" in r for r in reasons), reasons)
        # Each reason is printed once, even though it covers several sudo calls.
        self.assertEqual(len(reasons), len(set(reasons)), reasons)
        # The sudo password prompt itself repeats the reason.
        prompts = self.logged("sudo-prompts").splitlines()
        self.assertEqual(len(prompts), len(self.logged("sudo").splitlines()))
        self.assertTrue(all(p.startswith("[sudo] password for %u (to ") for p in prompts), prompts)

    def test_sssd_directory_shell_uses_domain_override(self):
        self.use_sssd(directory_shell="/bin/bash")
        result = self.apply(tty_input="y\ny\n")
        self.assertApplied(result)
        self.assertIn("default_shell had no effect: the directory sets a shell", result.stdout)
        self.assertIn("EVERY user in CORP.EXAMPLE.COM", result.stdout)
        self.assertIn("Users of other SSSD domains and local accounts are unaffected", result.stdout)
        self.assertIn("for every user in CORP.EXAMPLE.COM? [y/N]", result.stderr)
        self.assertNotIn("for every SSSD user?", result.stderr)  # [nss] never offered
        self.assertEqual(
            self.snippet_text(), f"[domain/CORP.EXAMPLE.COM]\noverride_shell = {self.sys_zsh}\n",
        )
        state = self.state.read_text()
        self.assertIn("sssd_default_shell=ineffective", state)
        self.assertIn("sssd_domain_override=yes", state)
        self.assertNotIn("sssd_override=", state)

    def test_sssd_domain_override_declined_is_remembered(self):
        self.use_sssd(directory_shell="/bin/bash")
        result = self.apply(tty_input="y\nn\n")
        self.assertApplied(result)
        self.assertIsNone(self.snippet_text())
        self.assertIn("Declined; login shell left unchanged", result.stderr)
        self.assertIn("[domain/CORP.EXAMPLE.COM]\\noverride_shell", result.stderr)  # manual fix
        self.assertIn("sssd_domain_override=no", self.state.read_text())
        # Next run skips straight past both, without prompting.
        (self.root / "state").unlink()
        result = self.apply(tty_input="y\ny\n")
        self.assertApplied(result)
        self.assertIn("Skipping default_shell: an earlier run found", result.stdout)
        self.assertIn("saved answer for sssd_domain_override is no", result.stdout)
        self.assertNotIn("[y/N]", result.stderr)
        self.assertIsNone(self.snippet_text())

    def test_sssd_ineffective_default_goes_straight_to_domain_override(self):
        self.use_sssd(directory_shell="/bin/bash")
        self.state.parent.mkdir(parents=True)
        self.state.write_text("sssd_default_shell=ineffective\n")
        result = self.apply(tty_input="y\n")
        self.assertApplied(result)
        self.assertNotIn("Set default_shell", result.stderr)
        self.assertNotIn("default_shell had no effect", result.stdout)
        self.assertEqual(
            self.snippet_text(), f"[domain/CORP.EXAMPLE.COM]\noverride_shell = {self.sys_zsh}\n",
        )
        # Writes the snippet once: no default_shell attempt before the override.
        self.assertEqual(self.logged("systemctl").count("restart sssd"), 1)

    def test_sssd_domain_override_only_affects_users_domain(self):
        # The fake sssd ignores a [domain/X] override when the user is not in X.
        self.use_sssd(directory_shell="/bin/bash")
        self.directory.write_text("domain=CORP.EXAMPLE.COM\ndirectory_shell=/bin/bash\n")
        self.snippet.write_text("[domain/OTHER.EXAMPLE.COM]\noverride_shell = /bin/zsh\n")
        subprocess.run(
            [str(self.bin_dir / "systemctl"), "restart", "sssd"], env=self.env, check=True,
        )
        self.assertTrue(self.getent.read_text().rstrip().endswith(":/bin/bash"))
        self.snippet.unlink()

    def test_sssd_guessed_domain_never_gets_domain_override(self):
        # A Kerberos realm that is not an SSSD section: default_shell may be tried,
        # but the per-domain override is skipped in favour of the [nss] question.
        self.use_sssd(domains=("OTHER.EXAMPLE.COM",), directory_shell="/bin/bash")
        (self.etc / "krb5.conf").write_text("[libdefaults]\n    default_realm = CORP.EXAMPLE.COM\n")
        result = self.apply(tty_input="y\ny\n")
        self.assertApplied(result)
        self.assertIn("not a section in the SSSD configuration", result.stdout)
        self.assertNotIn("for every user in", result.stderr)
        self.assertEqual(self.snippet_text(), f"[nss]\noverride_shell = {self.sys_zsh}\n")
        self.assertNotIn("sssd_default_shell=ineffective", self.state.read_text())

    def test_sssd_domain_detected_case_insensitively(self):
        self.use_sssd(domains=("corp.example.com",))
        result = self.apply(tty_input="y\n")
        self.assertApplied(result)
        self.assertEqual(
            self.snippet_text(), f"[domain/corp.example.com]\ndefault_shell = {self.sys_zsh}\n",
        )

    def test_sssd_domain_from_kerberos_when_config_lacks_it(self):
        self.use_sssd(domains=("OTHER.EXAMPLE.COM",))
        (self.etc / "krb5.conf").write_text("[libdefaults]\n    default_realm = CORP.EXAMPLE.COM\n")
        result = self.apply(tty_input="y\n")
        self.assertApplied(result)
        self.assertEqual(
            self.snippet_text(), f"[domain/CORP.EXAMPLE.COM]\ndefault_shell = {self.sys_zsh}\n",
        )

    def test_sssd_unknown_domain_offers_override(self):
        self.use_sssd(domains=("OTHER.EXAMPLE.COM",))
        result = self.apply(tty_input="y\ny\n")
        self.assertApplied(result)
        self.assertIn("Could not determine which SSSD domain", result.stdout)
        self.assertIn("EVERY SSSD user of EVERY domain", result.stdout)
        self.assertEqual(self.snippet_text(), f"[nss]\noverride_shell = {self.sys_zsh}\n")
        # Unknown domain is not proof the directory sets a shell: ask again next time.
        self.assertNotIn("sssd_default_shell=ineffective", self.state.read_text())

    def test_sssd_snippet_removed_when_getent_unchanged(self):
        self.use_sssd()
        self.env["FIXTURE_SNIPPET"] = str(self.root / "ignored")
        result = self.apply(tty_input="y\ny\n")
        self.assertApplied(result)
        self.assertIsNone(self.snippet_text())
        self.assertIn("getent does not report", result.stderr)
        self.assertIn("for CORP.EXAMPLE.COM; reverted", result.stderr)
        # default_shell, then the domain override: each restarts twice (apply + undo).
        self.assertEqual(self.logged("systemctl").count("restart sssd"), 4)

    def test_sssd_sudo_denied_warns_once(self):
        self.use_sssd()
        self.executable("sudo", 'echo "$*" >> "$FIXTURE_LOG/sudo"; exit 1\n')
        result = self.apply(tty_input="y\n")
        self.assertApplied(result)
        self.assertEqual(len(self.logged("sudo").splitlines()), 1, self.logged("sudo"))
        self.assertIn("sudo is unavailable or was denied", result.stderr)
        self.assertIsNone(self.snippet_text())

    def test_sssd_config_check_failure_removes_snippet(self):
        self.use_sssd()
        self.executable("sssctl", "exit 1\n")
        result = self.apply(tty_input="y\n")
        self.assertApplied(result)
        self.assertIn("sssctl config-check rejected", result.stderr)
        self.assertIsNone(self.snippet_text())

    def test_sssd_no_writes_nothing_and_is_remembered(self):
        self.use_sssd()
        result = self.apply(tty_input="n\n")
        self.assertApplied(result)
        self.assertIsNone(self.snippet_text())
        self.assertIn("sssd_default_shell=no", self.state.read_text())
        self.assertEqual(self.logged("sudo"), "")  # declining needs no sudo
        (self.root / "state").unlink()  # force run_onchange to run again
        result = self.apply(tty_input="y\n")
        self.assertApplied(result)
        self.assertIsNone(self.snippet_text())
        self.assertIn("saved answer for sssd_default_shell is no", result.stdout)
        self.assertNotIn("[y/N]", result.stderr)

    def test_sssd_without_tty_skips(self):
        self.use_sssd()
        result = self.apply()
        self.assertApplied(result)
        self.assertIsNone(self.snippet_text())
        self.assertFalse(self.state.exists())
        self.assertIn("No terminal available", result.stderr)
        self.assertEqual(self.logged("sudo"), "")

    # --- review findings ------------------------------------------------------------
    def test_render_survives_unreadable_or_odd_state_file(self):
        # A state file that cannot be read (or is a directory) must not fail the apply.
        self.local_account()
        self.state.parent.mkdir(parents=True)
        self.state.write_text("zsh_path=/bin/zsh\n")
        self.state.chmod(0)
        self.addCleanup(self.state.chmod, 0o600)
        self.assertTrue(self.render().startswith("#!/bin/bash"))
        result = self.apply()
        self.assertApplied(result)
        self.state.chmod(0o600)
        self.state.unlink()
        self.state.mkdir()
        self.assertTrue(self.render().startswith("#!/bin/bash"))
        self.assertApplied(self.apply())

    def test_render_ignores_saved_zsh_that_no_longer_runs(self):
        # The login shell equals a saved path that exists but is no longer a working
        # zsh: the script must still render (and pick a working zsh at run time).
        self.local_account()
        broken = self.executable("broken-zsh", "exit 1\n", directory=self.sys_dir)
        self.state.parent.mkdir(parents=True)
        self.state.write_text(f"zsh_path={broken}\n")
        self.set_login_shell(str(broken))
        self.assertTrue(self.render().startswith("#!/bin/bash"))
        result = self.apply()
        self.assertApplied(result)
        self.assertIn("no longer exists or does not run", result.stderr)
        self.assertEqual(self.logged("chsh"), f"-s {self.sys_zsh}\n")
        # A working saved zsh as login shell still renders nothing.
        self.state.write_text(f"zsh_path={self.sys_zsh}\n")
        self.set_login_shell(str(self.sys_zsh))
        self.assertEqual(self.render(), "")

    def test_sssd_restart_failure_is_not_saved_as_ineffective(self):
        self.use_sssd(directory_shell="/bin/bash")
        self.env["FIXTURE_RESTART_FAILURES"] = "1"
        result = self.apply(tty_input="y\ny\n")
        self.assertApplied(result)
        self.assertIn("sssd failed to restart with the new setting", result.stderr)
        self.assertNotIn("default_shell had no effect", result.stdout)
        self.assertNotIn("for every user in", result.stderr)  # domain override not offered
        self.assertIsNone(self.snippet_text())
        self.assertNotIn("ineffective", self.state.read_text())
        # The rollback restarted sssd (restart #2 succeeds).
        self.assertEqual(self.logged("systemctl").count("restart sssd"), 2)

    def test_sssd_existing_snippet_restored_after_failed_attempt(self):
        # A working snippet from an earlier run must survive a failed new attempt.
        self.use_sssd()
        previous = "[domain/CORP.EXAMPLE.COM]\ndefault_shell = /bin/previous-zsh\n"
        self.snippet.write_text(previous)
        self.snippet.chmod(0o600)
        self.executable("sssctl", "exit 1\n")
        result = self.apply(tty_input="y\n")
        self.assertApplied(result)
        self.assertIn("sssctl config-check rejected", result.stderr)
        self.assertEqual(self.snippet_text(), previous)
        self.assertFalse(Path(f"{self.snippet}.chezmoi-backup").exists())

    def test_sssd_existing_snippet_replaced_on_success_without_leftovers(self):
        self.use_sssd()
        self.snippet.write_text("[domain/CORP.EXAMPLE.COM]\ndefault_shell = /bin/previous-zsh\n")
        result = self.apply(tty_input="y\n")
        self.assertApplied(result)
        self.assertEqual(
            self.snippet_text(), f"[domain/CORP.EXAMPLE.COM]\ndefault_shell = {self.sys_zsh}\n",
        )
        self.assertFalse(Path(f"{self.snippet}.chezmoi-backup").exists())

    def test_sssd_ambiguous_domain_changes_nothing(self):
        # The same short name and uid resolve in two configured domains.
        self.use_sssd()
        self.executable(
            "getent",
            '[ "$1" = passwd ] || exit 2\n'
            'case "$2" in tester|tester@*) cat "$FIXTURE_GETENT" ;; *) exit 2 ;; esac\n',
        )
        result = self.apply(tty_input="y\ny\ny\n")
        self.assertApplied(result)
        self.assertIn("matches more than one SSSD domain (OTHER.EXAMPLE.COM, CORP.EXAMPLE.COM)", result.stderr)
        self.assertIsNone(self.snippet_text())
        self.assertEqual(self.logged("systemctl").count("restart"), 0)
        self.assertNotIn("for every", result.stderr)

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
