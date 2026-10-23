#!/usr/bin/env python3
"""Offline compatibility checks: python3 tests/atuin/test_config.py."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[2]
CHEZMOI = shutil.which("chezmoi")
NU = shutil.which("nu")
PLATFORMS = [("darwin", "amd64"), ("darwin", "arm64"),
             ("linux", "amd64"), ("linux", "arm64"), ("windows", "amd64")]


@unittest.skipUnless(CHEZMOI, "chezmoi required")
class AtuinConfig(unittest.TestCase):
    def render_text(self, path, system, arch, sync=False, home=None):
        with tempfile.TemporaryDirectory(prefix="atuin-config-") as directory:
            config = Path(directory) / "chezmoi.json"
            config.write_text("{}", encoding="utf-8")
            data = {"chezmoi": {"os": system, "arch": arch},
                    "atuin_sync": sync,
                    "atuin_sync_address": "https://history.example.invalid"}
            if home is not None:
                data["chezmoi"]["homeDir"] = str(home)
            result = subprocess.run(
                [CHEZMOI, "--source", str(ROOT), "--config", str(config),
                 "--cache", str(Path(directory) / "cache"),
                 "--persistent-state", str(Path(directory) / "state.boltdb"),
                 "--no-tty", "--override-data", json.dumps(data),
                 "execute-template", "--file", str(ROOT / path)],
                text=True, capture_output=True, check=True,
            )
            return result.stdout

    def render(self, path, system, arch, sync=False):
        return tomllib.loads(self.render_text(path, system, arch, sync))

    def test_features_match_installed_version_and_platform(self):
        for system, arch in PLATFORMS:
            with self.subTest(os=system, arch=arch):
                tools = self.render("dot_config/mise/conf.d/tools.toml.tmpl", system, arch)
                config = self.render("dot_config/atuin/config.toml.tmpl", system, arch)
                version = tools["tools"]["atuin"]
                if version != "latest":
                    # Verified against upstream tagged settings/init sources:
                    # daemon.autostart first appears in 18.13.0;
                    # config-driven pty_proxy.enabled first appears in 18.19.0.
                    pinned = tuple(map(int, version.split(".")))
                    if pinned < (18, 13, 0):
                        self.assertNotIn("ai", config)
                        self.assertNotIn("search_mode", config)
                        self.assertNotIn("daemon", config)
                    if pinned < (18, 19, 0):
                        self.assertNotIn("pty_proxy", config)
                else:
                    self.assertEqual(config["ai"], {"enabled": False})
                    self.assertEqual(config["search_mode"], "daemon-fuzzy")
                    self.assertEqual(config["daemon"], {"enabled": True, "autostart": True})
                    if system in ("darwin", "linux"):
                        self.assertEqual(config["pty_proxy"], {"enabled": True})
                if system == "windows":
                    self.assertNotIn("pty_proxy", config)
                self.assertNotIn("output", config)

    def test_sync_remains_opt_in(self):
        for system, arch in PLATFORMS:
            for sync in (False, True):
                with self.subTest(os=system, arch=arch, sync=sync):
                    config = self.render("dot_config/atuin/config.toml.tmpl", system, arch, sync)
                    self.assertIs(config["auto_sync"], sync)
                    self.assertEqual(config.get("sync_address"),
                                     "https://history.example.invalid" if sync else None)

    def test_shell_init_order_and_platform_gates(self):
        for system, arch in PLATFORMS:
            with self.subTest(os=system, arch=arch):
                unix = system in ("darwin", "linux")
                proxy = unix and (system, arch) != ("darwin", "amd64")
                zsh = self.render_text("dot_zshrc.tmpl", system, arch)
                config = self.render_text("dot_config/nushell/config.nu.tmpl", system, arch)
                env = self.render_text("dot_config/nushell/env.nu.tmpl", system, arch)
                hook = self.render_text(".chezmoiscripts/run_after_107-init-atuin.zsh.tmpl", system, arch)
                self.assertEqual("atuin pty-proxy init zsh" in zsh, proxy)
                self.assertEqual("atuin init zsh --disable-ai" in zsh, (system, arch) != ("darwin", "amd64"))
                self.assertEqual("atuin_proxy_source" in config, proxy)
                self.assertEqual("atuin_init_source" in config, proxy)
                self.assertEqual("ATUIN_CONFIG_DIR" in env, proxy)
                self.assertEqual("exec -- atuin pty-proxy init nu" in hook, proxy)
                if proxy:
                    self.assertLess(zsh.index("atuin pty-proxy init zsh"), zsh.index("# Load Dotfile defaults"))
                    self.assertLess(config.index("source $atuin_proxy_source"), config.index("$env.config.show_banner"))
                    self.assertLess(config.index("source $atuin_proxy_source"), config.index("source $atuin_init_source"))
                subprocess.run(["zsh", "-n"], input=zsh, text=True, check=True)
                subprocess.run(["zsh", "-n"], input=hook, text=True, check=True)

    @unittest.skipUnless(NU, "Nushell required")
    def test_nu_missing_files_and_single_ordered_initialization(self):
        with tempfile.TemporaryDirectory(prefix="atuin-nu-") as directory:
            home = Path(directory) / "home with spaces"
            home.mkdir()
            config = home / "config.nu"
            config.write_text(self.render_text("dot_config/nushell/config.nu.tmpl", "linux", "amd64", home=home))
            command = f'$env.ATUIN_TEST_ORDER = []; source {json.dumps(str(config))}; $env.ATUIN_TEST_ORDER | to json --raw'
            result = subprocess.run([NU, "--no-config-file", "-c", command], text=True, capture_output=True, check=True)
            self.assertEqual(json.loads(result.stdout), [])
            init_dir = home / ".local/share/atuin/init"
            init_dir.mkdir(parents=True)
            for filename, marker in [("pty-proxy.nu", "proxy"), ("init.nu", "history")]:
                (init_dir / filename).write_text(f'$env.ATUIN_TEST_ORDER = ($env.ATUIN_TEST_ORDER | append "{marker}")\n')
            result = subprocess.run([NU, "--no-config-file", "-c", command], text=True, capture_output=True, check=True)
            self.assertEqual(json.loads(result.stdout), ["proxy", "history"])

    @unittest.skipUnless(NU, "Nushell required")
    def test_standalone_nu_environment(self):
        for system, arch in PLATFORMS:
            with self.subTest(os=system, arch=arch), tempfile.TemporaryDirectory(prefix="atuin-env-") as directory:
                path = Path(directory) / "env.nu"
                path.write_text(self.render_text("dot_config/nushell/env.nu.tmpl", system, arch))
                command = f'source {json.dumps(str(path))}; {{node_ca: $env.NODE_USE_SYSTEM_CA, config: $env.ATUIN_CONFIG_DIR?, path: $env.PATH}} | to json --raw'
                result = subprocess.run([NU, "--no-config-file", "-c", command], text=True, capture_output=True, check=True)
                env = json.loads(result.stdout)
                self.assertEqual(env["node_ca"], "1")
                if system in ("linux", "darwin") and (system, arch) != ("darwin", "amd64"):
                    self.assertEqual(env["config"], str(Path.home() / ".config/atuin"))
                    self.assertEqual(env["path"][0], str(Path.home() / ".local/share/mise/shims"))

    def test_generation_restores_files_and_preserves_them_on_failure(self):
        for system, arch in [("linux", "amd64"), ("darwin", "amd64")]:
            with self.subTest(os=system, arch=arch), tempfile.TemporaryDirectory(prefix="atuin-hook-") as directory:
                home = Path(directory) / "home with spaces"
                mise = home / ".local/bin/mise"
                mise.parent.mkdir(parents=True)
                mise.write_text('''#!/bin/sh
case "$*" in
    *"pty-proxy init nu")
        [ "${ATUIN_TEST_FAIL_PROXY:-0}" = 0 ] || exit 1
        printf '# proxy\n' ;;
    *"atuin init nu") printf '# history\n' ;;
    *) exit 2 ;;
esac
''')
                mise.chmod(0o755)
                script = self.render_text(".chezmoiscripts/run_after_107-init-atuin.zsh.tmpl", system, arch, home=home)
                subprocess.run(["zsh"], input=script, text=True, check=True)
                if system == "darwin":
                    self.assertEqual(script.strip(), "")
                    self.assertFalse((home / ".local/share/atuin/init").exists())
                    continue
                init_dir = home / ".local/share/atuin/init"
                init = init_dir / "init.nu"
                proxy = init_dir / "pty-proxy.nu"
                self.assertEqual(init.read_text(), "# history\n")
                self.assertEqual(proxy.read_text(), "# proxy\n")
                init.unlink()
                subprocess.run(["zsh"], input=script, text=True, check=True)
                self.assertTrue(init.exists())
                if system == "linux":
                    init.write_text("# last good history\n")
                    result = subprocess.run(["zsh"], input=script, text=True,
                                            env=os.environ | {"ATUIN_TEST_FAIL_PROXY": "1"})
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(init.read_text(), "# last good history\n")
                    self.assertEqual(proxy.read_text(), "# proxy\n")
                self.assertEqual(sorted(p.name for p in init_dir.iterdir()), ["init.nu", "pty-proxy.nu"])


if __name__ == "__main__":
    unittest.main()
