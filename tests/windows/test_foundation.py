#!/usr/bin/env python3
"""Portable, offline render contracts. Not a native Windows/PowerShell test.
Run: python3 tests/windows/test_foundation.py
All chezmoi source/target/config/cache/state paths are disposable.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import tomllib

REPO = Path(__file__).resolve().parents[2]
CHEZMOI = shutil.which("chezmoi")


@unittest.skipUnless(CHEZMOI, "chezmoi required")
class Foundation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="windows-foundation-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        shutil.copytree(REPO, self.source, ignore=shutil.ignore_patterns(".git"))
        self.home = self.root / "home with spaces"
        self.home.mkdir()
        self.config = self.root / "config.json"
        self.config.write_text("{}")
        self.env = dict(
            os.environ,
            HOME=str(self.home),
            XDG_CONFIG_HOME=str(self.home / ".config"),
            XDG_CACHE_HOME=str(self.root / "xdg-cache"),
            XDG_DATA_HOME=str(self.root / "xdg-data"),
            XDG_STATE_HOME=str(self.root / "xdg-state"),
        )
        preflight_bin = self.root / "preflight-bin"
        preflight_bin.mkdir()
        for name in ("winget.exe", "apt", "sudo"):
            prerequisite = preflight_bin / name
            prerequisite.write_text("fixture\n")
            prerequisite.chmod(0o755)
        self.env["PATH"] = str(preflight_bin) + os.pathsep + self.env["PATH"]
        self.data = {
            "full_name": "Fixture User",
            "personal_email": "fixture@example.invalid",
            "has_work_profile": False,
            "personal_project_folder": str(self.home / "Projects"),
            "font_dir": str(self.home / "fonts"),
            "rust_arch": "x86_64",
            "rust_os": "pc-windows-msvc",
            "chezmoi": {
                "os": "windows",
                "arch": "amd64",
                "homeDir": str(self.home),
                "destDir": str(self.home),
                "sourceDir": str(self.source),
                "osRelease": {"id": "ubuntu"},
            },
        }

    def run_cm(self, *args, data=None, ok=True):
        cmd = [
            CHEZMOI,
            "--source",
            str(self.source),
            "--destination",
            str(self.home),
            "--config",
            str(self.config),
            "--cache",
            str(self.root / "cache"),
            "--persistent-state",
            str(self.root / "state.boltdb"),
            "--no-pager",
            "--no-tty",
            "--override-data",
            json.dumps(data or self.data),
            *args,
        ]
        result = subprocess.run(cmd, env=self.env, text=True, capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def render(self, relative, data=None):
        return self.run_cm(
            "execute-template", "--file", str(self.source / relative), data=data
        ).stdout

    def test_windows_full_boundary(self):
        self.assertFalse(self.render(".chezmoiexternal.toml.tmpl").strip())
        for script in (self.source / ".chezmoiscripts").iterdir():
            self.assertFalse(
                self.render(str(script.relative_to(self.source))).strip(), script.name
            )
        managed = set(
            self.run_cm(
                "managed", "--path-style", "relative", "--include", "files"
            ).stdout.splitlines()
        )
        self.assertEqual(
            managed,
            {
                ".gitconfig",
                ".config/nushell/config.nu",
                ".config/nushell/env.nu",
                ".config/git/windows.inc",
                ".config/mise/windows.toml",
                ".dotfiles/git/template.txt",
                ".editorconfig",
            },
        )
        self.run_cm("diff")
        self.run_cm("apply", "--dry-run", "--verbose")
        self.assertEqual(list(self.home.iterdir()), [], "dry-run modified target")

    def test_deferred_windows_editor_is_unmanaged(self):
        nvim = self.home / ".config/nvim"
        # Deliberately preserve existing custom config AND an unmanaged lockfile.
        for relative in (
            "init.lua",
            "lua/config/lazy.lua",
            "lua/config/options.lua",
            "lua/config/autocmds.lua",
            "lua/config/keymaps.lua",
            "lua/plugins/windows.lua",
            "lazy-lock.json",
            "lua/plugins/personal.lua",
        ):
            target = nvim / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("-- user customization: " + relative + "\n")
        before = {p: p.read_bytes() for p in nvim.rglob("*") if p.is_file()}
        diff = self.run_cm("diff").stdout
        self.assertNotIn("diff --git a/.config/nvim/", diff)
        self.run_cm("apply", "--dry-run", "--verbose")
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertFalse((self.source / "dot_config/nvim").exists())
        self.assertFalse((self.source / "scripts/windows/prepare-editor.ps1").exists())

    @unittest.skipUnless(
        shutil.which("nu"), "Installed Nu required for portable argv fixture"
    )
    def test_nu_dev_argv_and_no_startup_execution(self):
        # A fake .exe on Darwin proves Nu parsing/argv, NOT Windows process behavior.
        config = self.root / "config.nu"
        config.write_text(self.render("dot_config/nushell/config.nu.tmpl"))
        env_config = self.root / "env.nu"
        env_config.write_text("")
        manifest = self.home / ".config/mise/windows.toml"
        manifest.parent.mkdir(parents=True)
        shutil.copyfile(self.source / "dot_config/mise/windows.toml", manifest)
        fakebin = self.root / "bin"
        fakebin.mkdir()
        output = self.root / "argv.json"
        fake = fakebin / "mise.exe"
        fake.write_text(
            f"#!{sys.executable}\nimport json,os,sys\n"
            "from pathlib import Path\n"
            "with open(os.environ['CALL_OUTPUT'], 'a') as log: log.write('called\\n')\n"
            "if sys.argv[1] == 'where': sys.exit(int(os.environ.get('FAKE_MISSING') == sys.argv[2]))\n"
            "Path(os.environ['ARGV_OUTPUT']).write_text(json.dumps({"
            "'args':sys.argv[1:], 'env':{k:v for k,v in os.environ.items() if k.startswith('MISE_')}}))\n"
        )
        fake.chmod(0o755)
        env = {k: v for k, v in self.env.items() if not k.startswith("MISE_")}
        env.update(
            PATH=str(fakebin) + os.pathsep + env["PATH"],
            LOCALAPPDATA=str(self.root / "local data"),
            ARGV_OUTPUT=str(output),
            CALL_OUTPUT=str(self.root / "calls.log"),
        )
        nu_exe = shutil.which("nu")
        assert nu_exe is not None

        def run(command, ok=True, extra=None):
            result = subprocess.run(
                [
                    nu_exe,
                    "--config",
                    str(config),
                    "--env-config",
                    str(env_config),
                    "-c",
                    command,
                ],
                env=dict(env, **(extra or {})),
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode == 0, ok, result.stderr)
            return result

        calls = self.root / "calls.log"
        receipt = self.root / "local data/mise-windows/ownership.json"
        run("print 'plain startup'")
        self.assertFalse(output.exists())
        # A sole foreign executable is rejected before even `mise where` runs.
        run("dev rg --version", ok=False)
        self.assertFalse(calls.exists())
        receipt.parent.mkdir(parents=True)
        receipt.write_text(
            json.dumps(
                {
                    "package": "jdx.mise",
                    "path": str(fake),
                    "sha256": hashlib.sha256(fake.read_bytes()).hexdigest(),
                }
            )
        )
        original = manifest.read_text()
        for changed in (
            original.replace("0.11.6", "0.11.5"),
            original + '\n"aqua:foreign/tool" = "1.0.0"\n',
            original.replace('"aqua:sharkdp/fd" = "10.3.0"', ""),
            original.replace("aqua:sharkdp/fd", "aqua:foreign/tool"),
            original + '\n[env]\nUNREVIEWED = "1"\n',
        ):
            manifest.write_text(changed)
            run("dev rg --version", ok=False)
            self.assertFalse(calls.exists(), "altered manifest executed mise")
        manifest.write_text(original)
        alternate = self.root / "foreign-config/mise/windows.toml"
        alternate.parent.mkdir(parents=True)
        alternate.write_text(original)
        run(
            "dev rg --version",
            ok=False,
            extra={"XDG_CONFIG_HOME": str(alternate.parent.parent)},
        )
        self.assertFalse(calls.exists(), "altered XDG executed mise")
        # Same path but changed bytes invalidates the manual ownership attestation.
        original_exe = fake.read_bytes()
        fake.write_bytes(original_exe + b"\n# changed binary\n")
        run("dev rg --version", ok=False)
        self.assertFalse(calls.exists())
        fake.write_bytes(original_exe)
        run("dev rg --glob '*.lua' 'space and ünicode' 'a;b' 'quote\"inside'")
        captured = json.loads(output.read_text())
        self.assertEqual(
            captured["args"],
            [
                "exec",
                "aqua:neovim/neovim@0.11.6",
                "aqua:BurntSushi/ripgrep@15.1.0",
                "aqua:sharkdp/fd@10.3.0",
                "core:bun@1.4.2",
                "github:can1357/oh-my-pi@18.2.6",
                "--",
                "rg",
                "--glob",
                "*.lua",
                "space and ünicode",
                "a;b",
                'quote"inside',
            ],
        )
        self.assertEqual(captured["env"]["MISE_NO_CONFIG"], "1")
        self.assertEqual(captured["env"]["MISE_EXEC_AUTO_INSTALL"], "0")
        output.unlink()
        run("dev rg --version", ok=False, extra={"MISE_ENV": "unreviewed"})
        self.assertFalse(output.exists())
        otherbin = self.root / "other-bin"
        otherbin.mkdir()
        shutil.copy2(fake, otherbin / "mise.exe")
        run(
            "dev rg --version",
            ok=False,
            extra={"PATH": str(otherbin) + os.pathsep + env["PATH"]},
        )
        self.assertFalse(output.exists(), "duplicate mise installations must stop")
        calls.unlink()
        run("dev rg --version", ok=False, extra={"PATH": str(otherbin)})
        self.assertFalse(
            calls.exists(), "foreign singleton with different path executed mise"
        )
        run(
            "dev omp --version",
            ok=False,
            extra={"FAKE_MISSING": "github:can1357/oh-my-pi@18.2.6"},
        )
        self.assertFalse(
            output.exists(), "missing OMP must not fall back to PATH execution"
        )
        fake.unlink()
        run("print 'still usable'")
        run("dev rg --version", ok=False)

    @unittest.skipUnless(
        shutil.which("mise"), "Installed mise required for config isolation fixture"
    )
    def test_mise_ignores_global_and_project_config(self):
        mise = shutil.which("mise")
        assert mise is not None
        global_config = self.home / ".config/mise/config.toml"
        global_config.parent.mkdir(parents=True)
        malicious = '[env]\nDOTFILES_TEST_INJECTION = "unexpected"\n[tools]\n"unreviewed-plugin" = "latest"\n'
        global_config.write_text(malicious)
        (self.root / "mise.toml").write_text(malicious)
        env = {k: v for k, v in self.env.items() if not k.startswith("MISE_")}
        env.update(
            MISE_NO_CONFIG="1",
            MISE_AUTO_INSTALL="0",
            MISE_EXEC_AUTO_INSTALL="0",
            MISE_OFFLINE="1",
            MISE_DATA_DIR=str(self.root / "mise-data"),
            MISE_CACHE_DIR=str(self.root / "mise-cache"),
            MISE_STATE_DIR=str(self.root / "mise-state"),
        )
        result = subprocess.run(
            [
                mise,
                "exec",
                "--",
                sys.executable,
                "-c",
                "import os; print(os.environ.get('DOTFILES_TEST_INJECTION', 'clean'))",
            ],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "clean")
        missing = subprocess.run(
            [mise, "where", "aqua:neovim/neovim@0.11.6"],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("not installed", missing.stderr)
        self.assertFalse((self.root / "mise-data/installs").exists())

    @unittest.skip(
        "Requires Windows: native mise installs/exec/no-auto-install, PS5.1 argv and backend subprocess audit"
    )
    def test_native_developer_tools_gate(self):
        pass

    def test_xdg_conflicts_full_and_targeted(self):
        for value in ("", str(self.home / "different-config")):
            self.env["XDG_CONFIG_HOME"] = value
            for command in [
                ("managed",),
                ("diff",),
                ("apply", "--dry-run", "--verbose"),
                ("apply", "--dry-run", str(self.home / ".config/nushell/config.nu")),
            ]:
                result = self.run_cm(*command, ok=False)
                self.assertIn("XDG_CONFIG_HOME", result.stderr)
            self.assertEqual(list(self.home.iterdir()), [])

    def test_architecture_destination_and_native_xdg_spelling(self):
        for key, value, message in (
            ("arch", "arm64", "x64"),
            ("destDir", str(self.root / "other"), "destination"),
        ):
            data = json.loads(json.dumps(self.data))
            data["chezmoi"][key] = value
            self.assertIn(message, self.run_cm("managed", data=data, ok=False).stderr)
        data = json.loads(json.dumps(self.data))
        data["chezmoi"].update(
            homeDir="C:\\Users\\Fixture User", destDir="C:\\Users\\Fixture User"
        )
        self.env["XDG_CONFIG_HOME"] = "c:/users/fixture user/.config"
        self.assertIn("!.config/nushell/config.nu", self.render(".chezmoiignore", data))

    def test_existing_git_config_replacement_is_previewed_without_writes(self):
        existing = self.home / ".gitconfig"
        content = b"[credential]\r\n\thelper = manager\r\n[include]\r\n\tpath = local-work.inc\r\n"
        existing.write_bytes(content)
        diff = self.run_cm("diff").stdout
        self.run_cm("apply", "--dry-run", "--verbose")
        self.assertIn("diff --git a/.gitconfig", diff)
        self.assertEqual(existing.read_bytes(), content)

    @unittest.skipUnless(shutil.which("git") and shutil.which("ssh"), "Git and OpenSSH required")
    def test_windows_git_profiles_select_identity_and_single_key(self):
        # Real Git include precedence + OpenSSH expansion, without network/key access.
        work = self.home.resolve() / "Work [Team] ünicode"
        data = dict(
            self.data,
            has_work_profile=True,
            work_email="work@example.invalid",
            # Exercise Windows separators and ASCII case-insensitive matching.
            work_project_folder="".join(
                c.upper() if c.isascii() else c for c in str(work)
            ).replace("/", "\\"),
        )
        git_dir = self.home / ".config/git"
        git_dir.parent.mkdir(parents=True, exist_ok=True)
        self.run_cm("diff", data=data)
        self.run_cm("apply", "--dry-run", "--verbose", data=data)
        self.run_cm("apply", str(git_dir), data=data)
        global_config = self.home / ".gitconfig"
        self.run_cm("apply", str(global_config), data=data)
        system_config = self.root / "system.gitconfig"
        system_config.write_text("[credential]\n    helper = existing-helper\n")
        env = {k: v for k, v in self.env.items() if not k.startswith("GIT_")}
        env.update(GIT_CONFIG_SYSTEM=str(system_config))

        def git(repo, *args):
            result = subprocess.run(
                ["git", "-C", str(repo), *args],
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout.strip()

        for repo, email, key in (
            (work / "nested/repo", "work@example.invalid", "ssh_work"),
            (self.home / "Projects/repo", "fixture@example.invalid", "ssh_personal"),
            (Path(str(work) + "-other") / "repo", "fixture@example.invalid", "ssh_personal"),
        ):
            repo.mkdir(parents=True)
            git(repo, "init", "-q")
            self.assertIn(f"<{email}>", git(repo, "var", "GIT_AUTHOR_IDENT"))
            self.assertEqual(git(repo, "config", "credential.helper"), "existing-helper")
            # Git executes core.sshCommand using a shell even when invoked from Nu/PS.
            result = subprocess.run(
                git(repo, "config", "core.sshCommand") + " -G git@example.invalid",
                shell=True, env=env, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                [line for line in result.stdout.splitlines() if line.startswith("identityfile ")],
                [f"identityfile ~/.ssh/{key}"],
            )
            self.assertIn("identitiesonly yes\n", result.stdout)
            self.assertIn("preferredauthentications publickey\n", result.stdout)
            self.assertIn("stricthostkeychecking ask\n", result.stdout)

        # First clone has no repository to match: an explicit work include selects its key.
        self.assertEqual(
            git(self.home, "-c", f"include.path={git_dir / 'windows-work.inc'}",
                "config", "user.email"),
            "work@example.invalid",
        )
        # Repo-local exceptions retain normal Git precedence.
        git(work / "nested/repo", "config", "user.email", "override@example.invalid")
        self.assertIn(
            "<override@example.invalid>",
            git(work / "nested/repo", "var", "GIT_AUTHOR_IDENT"),
        )
        # Disabling the work profile removes selection, even if an old include remains.
        self.run_cm("apply", str(git_dir), data=self.data)
        git(work / "nested/repo", "config", "--unset", "user.email")
        self.assertIn(
            "<fixture@example.invalid>",
            git(work / "nested/repo", "var", "GIT_AUTHOR_IDENT"),
        )

    @unittest.skip(
        "Requires disposable native Windows 11 x64: PS5.1 parser, registry and WinGet install/reuse/refusal/reboot"
    )
    def test_native_bootstrap_gate(self):
        pass

    @unittest.skip(
        "Requires disposable native Windows: interactive Nu, Git/GCM, Terminal, consented apply and repeat apply"
    )
    def test_native_interactive_gate(self):
        pass

    def test_unix_nvim_external_remains_whole(self):
        # Local git-repo external: new source ignores must not filter Unix NvChad.
        # No upstream clone/network; fixture commit exists only under TemporaryDirectory.
        remote = self.root / "editor-upstream"
        remote.mkdir()
        for relative in (
            "init.lua",
            "lua/config/lazy.lua",
            "lua/plugins/windows.lua",
            "lua/custom.lua",
        ):
            file = remote / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("-- Unix external fixture\n")
        git = shutil.which("git")
        assert git is not None
        for args in (
            ["init"],
            ["add", "."],
            [
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "-c",
                "core.hooksPath=/dev/null",
                "commit",
                "-m",
                "fixture",
            ],
        ):
            result = subprocess.run(
                [git, "-C", str(remote), *args],
                env=self.env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        # Retain the REAL NvChad declaration byte-for-byte; isolate only transport
        # and unrelated externals. This previously caught a source-directory collision.
        external = (self.source / ".chezmoiexternal.toml.tmpl").read_text()
        declaration = (
            '[".config/nvim"]'
            + external.split('[".config/nvim"]', 1)[1].split(
                "#######################", 1
            )[0]
        )
        self.assertIn('url = "https://github.com/NvChad/NvChad.git"', declaration)
        self.env.update(
            GIT_CONFIG_COUNT="1",
            GIT_CONFIG_KEY_0="url." + str(remote) + ".insteadOf",
            GIT_CONFIG_VALUE_0="https://github.com/NvChad/NvChad.git",
        )
        # Keep the ignore boundary, its prerequisite template, and nvim source.
        for entry in self.source.iterdir():
            if entry.name not in (".chezmoiignore", ".chezmoitemplates", "dot_config"):
                shutil.rmtree(entry) if entry.is_dir() else entry.unlink()
        for entry in (self.source / "dot_config").iterdir():
            if entry.name != "nvim":
                shutil.rmtree(entry) if entry.is_dir() else entry.unlink()
        (self.source / ".chezmoiexternal.toml").write_text(declaration)
        data = json.loads(json.dumps(self.data))
        data["chezmoi"]["os"] = "darwin"
        self.run_cm("apply", "--dry-run", "--verbose", data=data)
        # Inspect target state rather than applying an external to any real home.
        managed = self.run_cm("managed", "--path-style", "relative", data=data).stdout
        self.assertIn(".config/nvim", managed)
        self.assertNotIn(".config/nvim/init.lua", managed)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_unix_offline_dry_runs(self):
        # Existing Unix release lookups, external downloads and Starship rendering
        # are explicitly stubbed ONLY in this disposable fixture, never the repo.
        (self.source / ".chezmoiexternal.toml.tmpl").write_text("")
        (
            self.source / "dot_local/share/nushell/vendor/autoload/starship.nu.tmpl"
        ).write_text("# offline fixture\n")
        for script in (self.source / ".chezmoiscripts").iterdir():
            content = script.read_text()
            for upstream in ("ryanoasis/nerd-fonts", "githubnext/monaspace"):
                content = content.replace(
                    f'(gitHubLatestRelease "{upstream}").TagName', '"fixture-version"'
                )
            script.write_text(content)
        mise_config = self.home / ".config/mise/config.toml"
        mise_config.parent.mkdir(parents=True)
        mise_config.write_text("# offline fixture\n")
        for platform in ("darwin", "linux"):
            data = json.loads(json.dumps(self.data))
            data["chezmoi"]["os"] = platform
            self.run_cm("diff", data=data)
            self.run_cm("apply", "--dry-run", "--verbose", data=data)
            self.assertEqual(mise_config.read_text(), "# offline fixture\n")
            self.assertEqual(
                [
                    p.relative_to(self.home).as_posix()
                    for p in self.home.rglob("*")
                    if p.is_file()
                ],
                [".config/mise/config.toml"],
            )

    def test_init_and_unix_changed_templates(self):
        for platform in ("windows", "darwin", "linux"):
            data = json.loads(json.dumps(self.data))
            data["chezmoi"]["os"] = platform
            data.update(
                fullName="Fixture User",
                personalEmail="fixture@example.invalid",
                personalProjectFolder="Projects",
                hasWorkProfile=False,
            )
            result = self.run_cm(
                "execute-template",
                "--init",
                "--promptString",
                "fullName=Fixture User,personalEmail=fixture@example.invalid,personalProjectFolder=Projects",
                "--promptBool",
                "hasWorkProfile=false",
                "--file",
                str(self.source / ".chezmoi.toml.tmpl"),
                data=data,
            )
            self.assertIn("Fixture User", result.stdout)
            parsed = self.run_cm(
                "execute-template",
                "{{ fromToml " + json.dumps(result.stdout) + " | toJson }}",
                data=data,
            )
            self.assertEqual(
                json.loads(parsed.stdout)["data"]["personal_project_folder"],
                str(self.home / "Projects"),
            )
            work_data = dict(
                data,
                hasWorkProfile=True,
                workEmail="work@example.invalid",
                workProjectFolder="Work Projects",
                workHostString="*.example.invalid",
            )
            work = self.run_cm(
                "execute-template",
                "--init",
                "--file",
                str(self.source / ".chezmoi.toml.tmpl"),
                data=work_data,
            )
            parsed_work = self.run_cm(
                "execute-template",
                "{{ fromToml " + json.dumps(work.stdout) + " | toJson }}",
                data=data,
            )
            self.assertEqual(
                json.loads(parsed_work.stdout)["data"]["work_project_folder"],
                str(self.home / "Work Projects"),
            )
            # Unix baseline from e5f69a9, independent of HEAD and clone history.
            if platform != "windows":
                original = (REPO / "tests/windows/fixtures/unix-config.nu").read_text()
                self.assertEqual(
                    self.render("dot_config/nushell/config.nu.tmpl", data), original
                )
                ignore = self.render(".chezmoiignore", data)
                self.assertNotIn("\n**\n", ignore)
                self.assertIn(".config/git/**", ignore)
            darwin = self.render(
                ".chezmoiscripts/run_onchange_before_010-darwin-install-packages.sh.tmpl",
                data,
            )
            wrapup = self.render(".chezmoiscripts/run_after_999-wrapup.zsh.tmpl", data)
            self.assertEqual(bool(darwin.strip()), platform == "darwin")
            self.assertEqual(bool(wrapup.strip()), platform != "windows")


if __name__ == "__main__":
    unittest.main(verbosity=2)
