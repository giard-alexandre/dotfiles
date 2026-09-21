# Native Windows foundation and developer tools (preview)

This is an implementation slice, **not yet a native-tested release**. Start with
Windows 11 x64, a standard user and built-in Windows PowerShell 5.1. No WSL, Git
Bash, MSYS, Scoop or Chocolatey is required. Never run the README's Unix cleanup.
Do not bypass execution policy or elevate the whole setup. Corporate policy,
WinGet registration, installer UAC and offline failures require explicit resolution.

## Contract and current scope

Set **user and process `XDG_CONFIG_HOME=<absolute user home>/.config`**, e.g. `C:\Users\Example\.config`, **before** starting chezmoi, Nushell or
Neovim. The bootstrap constructs the path; do not set it inside `config.nu`.
Canonical managed targets are existing `dot_config` destinations. Never relocate
`APPDATA` globally. `XDG_DATA_HOME` is neither required nor set by this work.
Changing XDG config discovery affects other applications: inspect existing configs
first. Conflicting process/user/machine values stop setup, not overwrite them.

The target is managed-file parity with macOS/Linux wherever Windows supports the
application and behavior. The current allowlist is an incremental safety boundary,
not a permanent minimal/opt-in Windows design. Remaining portable files and settings
are pending ports; only genuinely incompatible behavior should stay excluded.

Only these Windows files are currently managed:

- `~/.config/nushell/config.nu` and `env.nu`: plain prompt, `ll`/`lla`, SQLite history.
- `~/.gitconfig` and `~/.config/git/windows.inc`: automatically loaded Git defaults.
- `~/.config/git/windows-work.inc`: conditional work identity/key, when enabled.
- `~/.dotfiles/git/template.txt` and `~/.editorconfig`.
- `~/.config/mise/windows.toml`: explicit, pinned Windows tool inventory only.

Nu history is explicitly separate at `$env.LOCALAPPDATA\nushell\history.sqlite3`;
the runtime directory is created whenever Nu loads this configuration, never by
template rendering. Nu's plugin registry and vendor/data paths retain upstream defaults;
no plugins/integrations are provisioned. Verify discovery on the installed Nu
version. No Starship/mise command runs during rendering or startup.

Windows `.gitconfig` is managed by chezmoi, like macOS/Linux. Review and back up
existing contents before applying: the new file replaces them, not merges them.
Credential stores, private SSH keys, `.ssh/config` and `.gitignore` remain unmanaged
in this slice. System Git Credential Manager settings are not overridden; existing
user-level credential configuration must be reconciled before replacement. The mise stage
below is implemented, but **not native-validated**. The user explicitly deferred
LazyVim deployment after a source/external collision was identified (section 7).
Windows Neovim configs remain unmanaged; Unix NvChad stays unchanged. Other tools,
themes, runtimes and optional terminals remain pending. No editor migration or
package/plugin installation occurs during chezmoi apply.

## 1. Acquire and inspect before execution

A reviewed immutable bootstrap URL and trusted SHA-256 have **not** been published
yet. Public unattended onboarding is blocked until they exist. During review, obtain
the reviewed repository snapshot/archive through a trusted channel, inspect it,
and run its local `scripts\windows\bootstrap.ps1`. The script is self-contained
and does not need Git to exist. Do not trust a hash fetched alongside an untrusted
script; never pipe downloads to an interpreter.

Once a maintainer publishes real reviewed provenance, PS5.1 acquisition can use:

```powershell
# Replace both placeholders with independently trusted, reviewed release values.
$url = '<immutable reviewed HTTPS URL>'
$expectedHash = '<trusted SHA-256>'
$file = Join-Path $env:TEMP 'dotfiles-bootstrap-reviewed.ps1'
if (Test-Path -LiteralPath $file) { throw 'Choose a new file; preserve the existing download.' }
Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $file
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $file).Hash -ine $expectedHash) {
    throw 'Hash mismatch: do not execute.'
}
notepad.exe $file
# Only after inspection, from an ordinary non-elevated PowerShell session:
& $file -EstablishXdg -InstallCore
```

Do not use `ExecutionPolicy Bypass`; consult your administrator if policy blocks a
reviewed script. Script execution is always explicit and local, not network-executed.

## 2. Preflight, XDG and core packages

From the reviewed local snapshot in the same PowerShell process:

```powershell
& .\scripts\windows\bootstrap.ps1 -EstablishXdg -InstallCore
```

Default invocation without switches is read-only preflight; on a fresh machine it
stops explaining what is missing. `-EstablishXdg` requests exact typed consent to
set only the user/process config variable. `-InstallCore` requests per-package
consent after `winget show`. WinGet owns `Git.Git`, `twpayne.chezmoi`,
`Nushell.Nushell` and stable `Microsoft.WindowsTerminal`; existing executables are
reused and version-reported, not upgraded. Multiple PATH installations stop for
manual ownership review. Non-PATH installations/disabled aliases may still exist:
inspect WinGet/Installed Apps rather than install a duplicate. Installer scope is
reviewed, not indiscriminately forced to user scope. Agreements stay interactive.
`--no-upgrade` prevents this bootstrap from being an upgrade workflow; nonzero native
exit codes stop setup, including refusal or reboot-required results.

The script does not install WinGet itself. For missing or pending App Installer,
use the Microsoft Store App Installer page and [Microsoft WinGet installation and
registration guidance](https://learn.microsoft.com/en-us/windows/package-manager/winget/).
Check app execution aliases, sign out/in, and resolve policy/source/network errors.
Do not substitute another manager or silently elevate/retry. Only process PATH is
refreshed; no persistent PATH overwrite or `setx`. Reruns may reuse earlier approved
installs; no rollback uninstalls packages or resets user environment.

Existing `%APPDATA%\nushell` or `%LOCALAPPDATA%\nvim` configuration stops the
preflight: copy/back up and manually reconcile it into the canonical XDG tree
before proceeding. Do not erase old configs to bypass the check; archive them only
after review. Existing managed files are reported for conflict review, and known
managed-path reparse points/junctions are refused. Redirected/nonstandard home,
ARM64 and elevated deployment are outside this first gate.

## 3. Explicit init, preview, then consented apply

Choose the reviewed repository/branch yourself (currently `feat/windows`). Never
use `init --apply`, `update`, `--force` or an unattended apply during onboarding.
Back up any existing chezmoi config/source and target files outside managed paths;
stop if the chosen source already exists or is dirty. Preserve identity answers
locally. After the first init, reuse the source rather than repeatedly initializing.

```powershell
$source = Join-Path $env:USERPROFILE '.local\share\chezmoi'
$config = Join-Path $env:XDG_CONFIG_HOME 'chezmoi\chezmoi.toml'
# Review these paths first. Stop and reconcile if either already exists.
if ((Test-Path -LiteralPath $source) -or (Test-Path -LiteralPath $config)) {
    throw 'Existing chezmoi source/config: inspect and reuse, do not overwrite.'
}
chezmoi.exe --source $source --config $config init --branch feat/windows https://github.com/heuristicAL/dotfiles.git
if ($LASTEXITCODE -ne 0) { throw 'init failed; inspect partial state before retry.' }
# Inspect source provenance/diff before continuing; this branch is not immutable.
```

Before **each** documented apply route, including targeted apply, rerun the local
read-only preflight. **Stop immediately on any preflight error; do not continue
the remaining commands.** Then review both previews in order:

```powershell
$ErrorActionPreference = 'Stop'
& (Join-Path $source 'scripts\windows\bootstrap.ps1')
if (-not $?) { throw 'preflight failed' }
chezmoi.exe --source $source --config $config diff
if ($LASTEXITCODE -ne 0) { throw 'diff failed' }
chezmoi.exe --source $source --config $config apply --dry-run --verbose
if ($LASTEXITCODE -ne 0) { throw 'dry-run failed' }
# Back up existing differing files byte-for-byte OUTSIDE the managed tree.
# Resolve each conflict; do not accept replacements that discard local settings.
if ((Read-Host 'After reviewing every diff, type APPLY') -cne 'APPLY') { throw 'Stopped' }
chezmoi.exe --source $source --config $config apply --interactive
if ($LASTEXITCODE -ne 0) { throw 'apply failed; inspect partial state' }
chezmoi.exe --source $source --config $config apply --dry-run --verbose
if ($LASTEXITCODE -ne 0) { throw 'repeat dry-run failed' }
```

Template-time XDG/destination/architecture guards also reject unsafe Windows target
rendering, including full and targeted dry-runs. They do **not** replace the native
preflight's registry/reparse-point checks or conflict review. Chezmoi may initialize
its own cache/state even in a dry-run; no zero-internal-writes guarantee is made.
Do not customize the destination or bypass the normal source ignore/template flow.

## 4. Git: personal/work identity and SSH keys

The existing chezmoi prompts supply `full_name`, `personal_email`,
`has_work_profile`, `work_email` and `work_project_folder`. Windows no longer asks
for work host patterns: the repository directory selects both identity and key.
Personal identity is the default everywhere; repositories under the work folder
use the work email and key. `personal_project_folder` is your organizational
default, not a restriction on personal repositories.

Chezmoi installs the root `~/.gitconfig` automatically during the normal reviewed
apply. It loads `~/.config/git/windows.inc`, which conditionally loads
`windows-work.inc`. No manual include or separate activation is required.

Before applying, inspect `git.exe config --show-origin --list` locally (do not
publish identity or credential values). Back up the existing `.gitconfig` exactly
and review the replacement in `chezmoi diff`. This is a replacement, **not a merge**:
custom user-level settings, credential-helper declarations and old includes are
not automatically carried forward. Reconcile anything still required before apply;
do not commit credentials or machine-only settings to the shared source tree.
System/repo-local configuration and credential stores are not changed.

The Windows defaults do not set a credential helper, so an existing system-level
Git Credential Manager remains effective; Unix's `cache` helper is not deployed.
Repo-local settings and `git -c` retain normal precedence. The baseline still
avoids uninstalled delta, merge GUI and shell-helper dependencies; it uses Notepad,
no pager, and the commit template. Those integration gaps remain future ports,
not a permanent opt-in ownership policy.

| Repository | Commit email | SSH identity file |
| --- | --- | --- |
| Outside the work folder (or work profile disabled) | `personal_email` | `~/.ssh/ssh_personal` |
| Under `work_project_folder`, including nested repos | `work_email` | `~/.ssh/ssh_work` |

Git's `gitdir/i` match uses forward slashes, a directory boundary and
case-insensitive matching. Keep non-ASCII characters' spelling/case consistent:
Git's case folding is not full Unicode case folding. Linked worktrees follow the
original repository's Git metadata location, not necessarily the worktree folder.
Moving a repository across the work-folder boundary changes its selected profile.

**SSH isolation:** `core.sshCommand` invokes OpenSSH with `-F none`, one
`IdentityFile`, `IdentitiesOnly=yes`, and public-key-only authentication.
It does not read user/system SSH configuration, so their extra identities cannot
accumulate; host-key checking remains enabled. The same `git@github.com:...` host
can therefore serve both accounts without aliases. Existing `~/.ssh/config` is
not modified, and ordinary non-Git SSH is unaffected. Git SSH aliases, proxies,
ports and other options previously supplied by that config will not be inherited:
review any required repo-local `core.sshCommand` exception before applying.
Keys/passphrases are never provisioned, imported or stored by chezmoi.
`GIT_SSH_COMMAND` can override this selection; inspect inherited overrides and
ensure Git uses OpenSSH, not PuTTY/plink. HTTPS remotes use the existing credential
helper, not these keys.

### Create machine-local keys explicitly

On Windows, inspect the existing `.ssh` directory and permissions first. Reuse
already-approved keys at the expected paths, or generate separate machine-local
keys. Do not copy private keys into the source tree or overwrite existing files.
In PowerShell, for a **new personal key**:

```powershell
$keygen = (Get-Command ssh-keygen.exe -CommandType Application -ErrorAction Stop).Source
$key = Join-Path $env:USERPROFILE '.ssh\ssh_personal'
if ((Test-Path -LiteralPath $key) -or (Test-Path -LiteralPath "$key.pub")) {
    throw 'Existing key material: review/reuse it, do not overwrite.'
}
$null = New-Item -ItemType Directory -Force -Path (Split-Path -Parent $key)
& $keygen -t ed25519 -f $key -C 'personal-windows'
if ($LASTEXITCODE -ne 0) { throw 'Key generation failed' }
```

Choose a passphrase when prompted. For work, repeat with `ssh_work` and a
`work-windows` comment only if the work profile is enabled and employer policy
permits that key type. Register **only the `.pub` file** with the corresponding
account; approve organizational SSO if required. Keep private-key ACLs restricted
to your user; never relax them to bypass an SSH permissions error. Agent setup
is optional and not automated: absent a compatible agent, SSH asks for the key's
passphrase. `IdentitiesOnly` restricts agent use to the selected identity.

### Clone and verify

The initial clone may run before Git has repository metadata to match. Explicitly
select the work include for that operation (replace the example URL/destination):

```powershell
git.exe -c "include.path=$env:XDG_CONFIG_HOME/git/windows-work.inc" clone git@github.com:WORK-ORG/REPO.git "$env:USERPROFILE/Work/REPO"
if ($LASTEXITCODE -ne 0) { throw 'Clone failed' }
```

Use your configured work folder as the destination. Do not persist a separate
`core.sshCommand` in each cloned repo: future fetch/push operations use the
conditional include. Personal clones need no explicit include. From each repo:

```powershell
git.exe config --show-origin --get user.email
git.exe config --show-origin --get core.sshCommand
git.exe var GIT_AUTHOR_IDENT
git.exe remote -v
git.exe ls-remote origin
```

Verify the expected account, repository access and host fingerprint before use.
Authentication failures are not permission to disable host-key checking or offer
the other profile's key. Disabling the work profile and reapplying the baseline
removes its conditional include; any old work include is left unmanaged, not deleted.
Native Windows OpenSSH/agent/ACL and actual account authentication remain acceptance
checks; portable tests exercise real Git selection and offline OpenSSH expansion.

## 5. Terminal launch: manual UI, preserve settings

Sign out/in after establishing user XDG so a **genuinely new** Terminal process
inherits it. Closing a tab is insufficient; an existing Terminal/server or Explorer
can retain stale environment. In fresh PowerShell verify `$env:XDG_CONFIG_HOME`,
then `(Get-Command nu.exe -CommandType Application).Source`.

In Windows Terminal Settings, add a **new empty profile** named Nushell. Set its
command line to that absolute native `nu.exe` path, enclosed in double quotes if
needed (for example `"C:\Program Files\nu\bin\nu.exe"`; use discovery, not this
example as a hardcoded path). Do not add `-n`, `--no-config-file` or a PowerShell/Bash
wrapper. Select this profile as the default profile through Settings > Startup.
Choose Windows Terminal as the default terminal application separately if desired.
Preserve existing profiles, startup actions, restored layouts and JSONC comments.
No JSONC rewriting or fragment installation occurs in this delivery.

Start a real interactive Nu tab and inspect:

```nu
$env.XDG_CONFIG_HOME
$nu.config-path
$nu.env-path
$nu.data-dir
$nu.history-path
$env.config.history
which git
ll
```

Verify config is `~/.config/nushell/config.nu`, history is under LocalAppData and
persists across tabs, default/plus-button tabs launch Nu, Ctrl-C/paste/resizing work,
and native `.exe`/`.cmd`, spaced/Unicode paths and arguments behave correctly.
Test `nu -c` and an explicit `nu --config <config-path> -c <command>` separately
on the selected version, recording whether config loads and creates the history
directory. Neither alone proves interactive startup behavior. Recovery remains
built-in PowerShell; do not modify COMSPEC or pretend the default profile changes SSH/IDE
interpreters. To roll back, select the prior Terminal profile and remove only your
added profile; restore backed-up files manually. Reconcile chezmoi source ownership
before reapplying, or the managed Git defaults will return. Revert XDG only after reviewing
all affected apps and restarting them; never delete runtime data as rollback.

## Validation and pending gates

Portable: `python3 tests/windows/test_foundation.py` runs offline in disposable
source/target/config/cache/state trees. It renders all Windows lifecycle templates,
checks the allowlist and XDG rejection, and runs `chezmoi diff` and
`chezmoi apply --dry-run --verbose`. Unix dry-runs use explicitly stubbed release,
external and Starship fixtures (not real network/editor installation tests).
The Unix Nu baseline is a checked-in fixture from `e5f69a9`, not a lookup against
moving HEAD; the suite also works after the original source file is renamed.

Both PowerShell entry points query `Win32_Processor.Architecture` through CIM
before configuration/package work, in addition to checking process architecture.
Only a nonempty set of x64 processors (9) is accepted; ARM64 (12), unknown values
and unavailable CIM stop setup. This rejects x64 emulation on an ARM64 host.
`powershell.exe -NoProfile -File tests/windows/test_architecture.ps1` exercises
both entry points with mocked platform results. It also runs under `pwsh`;
12 scenarios passed on disposable PowerShell 7.5.4 on Darwin, and removing the
host guard reproduced the ARM64 acceptance bug. This proves guard control flow,
not the native CIM provider or PS5.1 runtime. Validate those on Windows.

**Skipped on the Darwin implementation host:** PS5.1 parsing/execution, WinGet
stock-machine install/reuse/refusal/reboot, registry persistence, native Nu parse
and interactive startup, native path discovery/reparse behavior, Git/GCM, Terminal
UI, real consented apply and idempotence. These must pass on a disposable Windows
11 x64 VM before a support/release claim. A disposable PowerShell 7 runtime was
used only for the mocked architecture regression, not native acceptance.

Native validation and immutable reviewed provenance remain release gates, including
the new mise stage below. Other runtime/CLI expansion, Starship, Alacritty
and external alternatives are separate work. See [the durable plan](windows-support-plan.md).

Current authoritative references rechecked for this slice:
[chezmoi ignore precedence](https://www.chezmoi.io/reference/special-files/chezmoiignore/),
[script dry-run behavior](https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/),
[Nu startup discovery](https://www.nushell.sh/book/configuration.html),
[Nu history path implementation](https://github.com/nushell/nushell/blob/main/crates/nu-protocol/src/config/history.rs),
[WinGet install controls](https://learn.microsoft.com/en-us/windows/package-manager/winget/install),
[Neovim standard paths](https://neovim.io/doc/user/starting.html#standard-path).

## 6. Explicit developer-tool provisioning (after reviewed apply)

WinGet owns **only** Git, chezmoi, Nu, Terminal and `jdx.mise` in this stage.
The shared Unix mise `latest` inventory, conf.d settings and trusted paths remain
excluded. The five Windows tools have one owner, **mise**, using built-in backends:

| Tool / executable | Exact specification | Reviewed Windows x64 artifact |
| --- | --- | --- |
| Neovim / `nvim.exe` | `aqua:neovim/neovim@0.11.6` | `nvim-win64.zip`, `nvim-win64/bin/nvim.exe` |
| ripgrep / `rg.exe` | `aqua:BurntSushi/ripgrep@15.1.0` | `ripgrep-15.1.0-x86_64-pc-windows-msvc.zip` |
| fd / `fd.exe` | `aqua:sharkdp/fd@10.3.0` | `fd-v10.3.0-x86_64-pc-windows-msvc.zip` |
| Bun / `bun.exe` | `core:bun@1.4.2` | `bun-windows-x64.zip` (baseline variant selected when needed) |
| OMP / `omp.exe` | `github:can1357/oh-my-pi@18.2.6` | `omp-windows-x64.exe` |

Aqua here is built into mise: no Aqua CLI, asdf plugin, Bash, compiler or custom
archive installer. Neovim's archive also bundles its runtime/support files; keep
that archive installation intact. No Node, Python, Go, fzf, native compiler or
language server is installed implicitly. Git is sufficient for plugin acquisition;
rg/fd are useful standalone CLIs and future picker dependencies. No LazyVim,
plugins, compiler or font is provisioned by this slice.

Bun supports native Windows; OMP publishes a native Windows x64 executable.
OMP uses its upstream-documented mise GitHub backend rather than the Unix npm
backend. No npm global install, Node dependency, Bun-global PATH entry or shared
`npm.package_manager` setting is needed. Bun remains separately available for
projects and OMP's Bun-backed functionality.
Sources: [Bun installation](https://bun.sh/docs/installation),
[OMP installation](https://github.com/can1357/oh-my-pi#install),
[mise GitHub backend](https://mise.jdx.dev/dev-tools/backends/github.html).

From a clean, non-activated PowerShell process, after section 3's preflight,
diff/dry-run/conflict review and consented apply:

```powershell
& (Join-Path $source 'scripts\windows\bootstrap.ps1') -InstallDeveloperTools
if (-not $?) { throw 'mise bootstrap failed' }
# Above installs/reuses jdx.mise only (core must already be present).
# Inspect winget list / Installed Apps for non-PATH duplicate tool installations.
& (Join-Path $source 'scripts\windows\developer-tools.ps1') -Install
if (-not $?) { throw 'tool provisioning failed' }
```

WinGet shows the current `jdx.mise` manifest and asks installation consent; it does
not force upgrades. **A sole PATH executable is not proof of WinGet ownership.**
Before running mise (even `--version`), bootstrap requires successful
`winget list --id jdx.mise --exact --source winget`, displays the resolved absolute
executable path and SHA-256, and asks for `CONFIRM jdx.mise OWNERSHIP`. Inspect the
actual registered installation location/publisher and verify the displayed file
belongs to it; reject portable/foreign copies. Registration alone is insufficient.
Record the resolved version/installer scope in the VM acceptance log.

This explicit manual attestation is recorded as package ID, absolute executable
path and SHA-256 in `%LOCALAPPDATA%\mise-windows\ownership.json`. Both Nu and the
PowerShell runner require the matching receipt **before any mise invocation**.
Missing receipt, changed path or changed bytes stops execution. After an intentional
upgrade/path change rerun bootstrap `-InstallDeveloperTools` and repeat ownership
review; never edit the receipt to bypass it. Reconfirmation explicitly replaces the
old attestation. The bootstrap refuses reparse-point receipt paths. This is a
human ownership decision, **not** automated signature/package-path verification or
protection against a malicious same-user process rewriting both config and receipt. The mutable WinGet
manifest is **not** an immutable bootstrap release. An older reused mise may lack
reviewed settings/registry metadata: stop on failure and review an explicit mise
upgrade, never change backend or disable verification as a workaround.

`windows.toml` is intentionally **not** an auto-loaded mise configuration. The
PowerShell runner compares its bytes with the reviewed source, accepts only the
small literal tools table, then passes explicit specs to mise. Nu reads the same
reviewed table only when `dev` is invoked, requires exact canonical XDG path spelling
(embedded from the rendering home), and compares the complete parsed manifest with
the table embedded from reviewed source at rendering. Additional/replaced tools,
changed versions, missing keys or extra sections are rejected before invoking mise.
A pin update therefore requires reviewing/applying both windows.toml **and** the
rendered Nu config. Both use `MISE_NO_CONFIG=1` so parent
project configs, tasks, hooks and broad trust are never required; both disable
`MISE_AUTO_INSTALL` and `MISE_EXEC_AUTO_INSTALL` for command execution. There is no
activation module, persistent PATH edit or prompt/startup install. Existing
`MISE_*` overrides are rejected instead of silently inheriting unrelated settings.

Both runners first require `mise where` to succeed for every exact pin before
executing a command: `mise exec` alone with automatic installs disabled can silently
fall through to unrelated PATH commands when a tool is missing. This failure mode
was reproduced using installed mise 2026.8.4 on Darwin and is regression-covered.

Both routes use `%LOCALAPPDATA%\mise-windows\{data,cache,state}`, not the shared
Unix store or another global mise installation. Explicit `-Install` alone permits
package downloads. Failed downloads stop; reruns reuse the exact installed
versions. Tools are intentionally **not** bare PATH commands in a plain shell:

```nu
# In a fresh real Nu tab using the managed config:
dev nvim -u NONE # plain Neovim; LazyVim deployment is explicitly deferred
dev rg --version
dev fd --version
dev bun --version
dev omp --version
dev omp
dev rg --glob '*.lua' 'two words' .
```

For automation (without Nu config/interactive activation):

```powershell
& (Join-Path $source 'scripts\windows\developer-tools.ps1') -Run rg -ToolArguments @('--version')
if (-not $?) { throw 'command failed' }
```

For noninteractive Nu, explicitly load its config, e.g.
`nu.exe --config "$env:XDG_CONFIG_HOME\nushell\config.nu" -c 'dev rg --version'`
from PowerShell. Bare `nu -c` config-loading semantics are version-dependent.
Use direct argv, never `mise -c` shell strings. Nu's portable spaced/Unicode,
metacharacter, quote and glob argument tests pass against a fake executable; this
is **not** proof of Windows `.exe`/`.cmd` behavior. PS5.1 native argument quoting
(including embedded quotes/empty arguments) remains a gate; prefer Nu for complex
argv until validated. The wrapper is not a shell sandbox for the command you run.

Version updates are manual: review upstream assets/registry/hooks, edit the relevant
pins in source, review the target diff, apply with consent, then rerun `-Install`.
A changed/customized deployed manifest stops the PowerShell runner. Preserve and
reconcile it, do not force replacement. No duplicate WinGet/global tool ownership,
`mise use -g`, `mise trust`, floating `latest`, automatic uninstall or update.
The installer rejects existing Bun/OMP executables and OMP npm/PowerShell shims
on PATH before provisioning; reconcile those installations manually first.
On Darwin, a disposable `mise lock --platform windows-x64` resolved the pinned
Bun and OMP Windows assets and checksums. A separate isolated mise install/exec
smoke check ran `bun --version` and `omp --version` using Darwin binaries.
No lockfile is deployed: mise's built-in backends perform release verification.
Native Windows installation, executable naming and PowerShell execution remain
validation gates; cross-platform resolution is not native execution proof.
Version pins are not a claim of independent artifact provenance.

## 7. LazyVim explicitly deferred by user decision

A portable regression exposed a real chezmoi source-state collision: adding a
normal `dot_config/nvim` directory conflicts with the existing Unix `.config/nvim`
`git-repo` external, even when all child files are ignored. Ignoring the parent
instead suppresses the Unix external; a `targetPath` alias did not resolve this.
See chezmoi's [source attributes](https://www.chezmoi.io/reference/source-state-attributes/)
and [external semantics](https://www.chezmoi.io/reference/special-files/chezmoiexternal-format/).

The user selected **DEFER LAZYVIM**, rather than introduce a separate Windows
source root or unmanaged seed script. Incomplete Lua deployment files, editor
preparation scripts and Neovim allowlist/ignore changes were removed. There is no
Windows editor configuration deployment, plugin installation, distribution
substitution or Unix NvChad migration in this delivery. Existing Windows config,
plugins, lockfiles and runtime data remain untouched. `dev nvim -u NONE` verifies
the installed editor without loading any existing user plugin configuration.

LazyVim remains the selected future Windows distribution at `~/.config/nvim`.
Retained research for a later ownership decision:

- Starter semantics: init calls `config.lazy`; lazy.nvim and plugins live in
  Neovim runtime data; import `lazyvim.plugins` followed by personal plugin specs.
- Current LazyVim requires Neovim >=0.11.2. Treesitter build/parser hooks need a
  native compiler; Mason/LSP/formatter scripts add tool owners/dependencies.
- Blink 1.7.0 offers a documented Lua matcher avoiding Rust builds/downloads.
  LuaRocks, plugin package specs, image tools, parser-dependent mappings and
  optional Bash extras need explicit review, not silent installation.
- Any later seed must preserve customizations/lockfiles, avoid a mutable config
  git external, audit plugin hooks, and separate explicit plugin preparation from
  startup. No plugins/toolchains have been approved merely by this research.

The regression retains the real Unix NvChad declaration byte-for-byte, isolating
only unrelated externals and transport. It verifies the external remains managed
without a colliding source directory. Windows tests verify existing editor files
remain unmanaged. LazyVim absence is the explicit scope decision, not a missing
feature to patch around during review of this mise-only slice.

### Primary-source review checkpoint

Read-only source/API downloads went to a temporary directory; no downloaded code,
package or editor was executed on Darwin. Sources reviewed at these revisions:

- [LazyVim starter 803bc181](https://github.com/LazyVim/starter/tree/803bc181d7c0d6d5eeba9274d9be49b287294d99): init/config semantics;
  Apache-2.0 license reviewed; no adapted files are delivered in this mise-only slice.
- [LazyVim 99970099](https://github.com/LazyVim/LazyVim/tree/999700997f72227187d49d8b92667183dc7fc809): requires Neovim >=0.11.2;
  plugins/treesitter.lua build/install hooks, lsp/init.lua Mason, formatting.lua,
  extras/coding/blink.lua and default Snacks picker inspected.
- [lazy.nvim 85c7ff37](https://github.com/folke/lazy.nvim/tree/85c7ff3711b730b4030d03144f6db6375044ae82): config install/pkg/rocks controls.
- [Blink 1.7.0 fuzzy docs](https://github.com/saghen/blink.cmp/blob/v1.7.0/doc/configuration/fuzzy.md): Lua implementation avoids Rust downloads/builds.
- [mise acbbdee0](https://github.com/jdx/mise/tree/acbbdee0b150f5eeb14eb287198b11625ea35472): Aqua/exec docs,
  src/env.rs `MISE_NO_CONFIG`, settings.toml automatic-install flags. Aqua works
  natively on Windows without an Aqua CLI; registry is bundled with mise releases.
- [Aqua registry 5b543ce1](https://github.com/aquaproj/aqua-registry/tree/5b543ce1bf1f31f977caaafb54184f02b5840582):
  neovim/neovim, BurntSushi/ripgrep, sharkdp/fd Windows ZIP/MSVC mappings, no Bash hooks.
- Publisher release APIs/assets: [Neovim 0.11.6](https://github.com/neovim/neovim/releases/tag/v0.11.6),
  [ripgrep 15.1.0](https://github.com/BurntSushi/ripgrep/releases/tag/15.1.0),
  [fd 10.3.0](https://github.com/sharkdp/fd/releases/tag/v10.3.0).
- [WinGet jdx.mise manifests](https://github.com/microsoft/winget-pkgs/tree/master/manifests/j/jdx/mise):
  package ID exists; 2026.9.5 appeared in the reviewed listing. Installer scope and
  the actual version selected by WinGet remain native acceptance evidence.

Portable checkpoint: 15 tests, 12 passed and 3 native gates skipped. Includes all
changed template branches, isolated full diff/dry-run, Unix fixtures plus the real
NvChad external declaration, exact Windows mise-only manifest, untouched editor
files, ownership/pins, installed Nu parsing/argv/missing-tool/no-startup-execution
with a fake executable, and installed Darwin mise config isolation/missing-pin
checks in offline disposable stores. No host installation or real-home apply.
PS5.1 execution, native mise isolation/no-auto-install, backend extraction/checksum
behavior and native process/argv proof remain mandatory Windows 11 x64 VM gates,
not claims inferred from these tests. LazyVim implementation is explicitly deferred.
