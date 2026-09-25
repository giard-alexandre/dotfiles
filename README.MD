![preview](https://raw.githubusercontent.com/heuristicAL/dotfiles/main/docs/screenshot_terminal.png)

# Get Started

**Native Windows:** start with [the Windows foundation guide](docs/WINDOWS.md).
It is a bounded preview pending native validation: PowerShell 5.1, WinGet, minimal
Nushell and user-level `XDG_CONFIG_HOME`. Do **not** run the Unix cleanup or shell
bootstrap commands below on Windows.

## macOS / Linux only
>
> Migrating from the old dotfiles? run the following command to clean things up before you install: `rm -rf ~/.znap ~/.asdf ~/.dotfiles`
> Make sure to backup your `~/.ssh/config` file as we're now managing that as part of this repo.

## Github Access Token

In order to avoid any issues with rate limiting on the GH API, I recommend adding a [personal access token](https://docs.github.com/en/enterprise-server@3.4/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) to your shell env. You can do this by setting one of these env variables:

- `CHEZMOI_GITHUB_ACCESS_TOKEN`
- `GITHUB_ACCESS_TOKEN`
- `GITHUB_TOKEN`

> Note: I recommend using GITHUB_TOKEN as this is most compatible with other tools.

## Install chezmoi on your machine using the shell script
>
> We're installing it to the `~/.local/bin` directory to accomodate as many Unix-style OSs as possible.

I recommend forking the repo into your own `dotfiles` repo and then using the below command to install chezmoi, clone the repo and apply it in one step.
> Note: this one-liner assumes it is cloning a repo called `dotfiles` from the user `$GITHUB_USERNAME`, make sure that's what you call your fork.
> Otherwise, please check the `chezmoi` docs for how to specify a different repo name.

```shell
sh -c "$(curl -fsLS get.chezmoi.io)" -- -b $HOME/.local/bin init --apply $GITHUB_USERNAME
```

After the source is available, the config template checks for required programs
before the first questionnaire; a remote `init` needs Git earlier, to clone the
source. Subsequent `chezmoi apply` runs perform the same check before changing
files. A missing prerequisite stops with a list to install: Git for source/Git
externals; `/bin/bash` for Unix lifecycle scripts; curl for macOS Homebrew; apt
or pacman (plus sudo for non-root users) on the corresponding Linux distribution;
and `winget.exe` for Windows package provisioning. This checks executable
availability, not versions, connectivity, credentials or package-manager health.
The Windows PowerShell preflight also checks core tools, OS and account safety;
template checks do not replace it. Tools installed *by* Unix apply scripts
(such as zsh, Starship and mise) are not preconditions.

Run the isolated regression checks with
`python3 -B -m unittest -v tests/test_apply_prerequisites.py` and
`python3 -B tests/windows/test_foundation.py`.

# Windows compared with macOS/Linux

**The goal is the same chezmoi-managed experience on every supported platform.**
If a file or application works natively on Windows, its configuration should also
be managed there, preferably through shared templates with small platform branches.
Windows is not intended to remain a separate, minimal, opt-in setup.

**Current status:** Windows is an incremental preview targeting Windows 11 x64.
The code and portable checks exist, but native installation, PowerShell 5.1,
interactive sessions and account authentication still need Windows acceptance.
ARM64 and redirected/nonstandard home layouts are not yet validated.
The Windows allowlist in [`.chezmoiignore`](.chezmoiignore) is a temporary safety
boundary: excluded files may be **not yet ported**, rather than unsupported.

## What is different today, and why

| Area | macOS/Linux configuration | Windows configuration | Reason / status |
| --- | --- | --- | --- |
| Bootstrap and packages | OS-specific Homebrew/apt/pacman hooks and Unix shell scripts; mise downloaded through a chezmoi external. | Explicit PowerShell bootstrap; WinGet owns Git, chezmoi, Nu, Windows Terminal and mise. | **Platform adaptation:** native package managers, installer scope and exit codes differ. Unix lifecycle scripts are not safe Windows installers. |
| Applying files vs. installing tools | Chezmoi lifecycle hooks can install packages/tools, including `mise install`. | Normal reviewed apply manages files; package/tool installation is a separate explicit step with consent. | **Current safety policy:** Windows installer/recovery paths are not yet native-validated. File management is automatic; package installation is not a hidden apply side effect. |
| Interactive shell | Zsh, Oh My Zsh, shell fragments/functions and Starship; Nu configuration also exists. | Minimal native Nushell with history, `ll`/`lla` and the explicit `dev` runner; PowerShell is used for bootstrap/automation. | **Shell choice and pending integration:** Zsh code cannot be sourced into Nu. Native equivalents need individual ports; Starship is not inherently unsupported. No WSL session is required. |
| Configuration paths | Unix home/XDG conventions and application-specific paths. | User/process `XDG_CONFIG_HOME` is established as `~/.config` before starting applications; Nu history and the isolated mise store use LocalAppData. | **Platform adaptation:** native applications may otherwise discover AppData configurations instead. Existing configurations must be reconciled before changing discovery. `APPDATA` is not globally relocated. |
| Git file ownership | Chezmoi manages `~/.gitconfig` and the optional work profile. | Chezmoi also manages `~/.gitconfig`; it automatically loads the Windows defaults and conditional work profile. | **Already aligned:** no manual include or activation is required. Both use the supplied personal/work profile data. Review existing `.gitconfig` before replacement; apply does not merge arbitrary local settings. |
| Git tools and credentials | Vim, delta, DiffMerge and shell helper aliases; `osxkeychain` on macOS, `cache` on Linux. | Notepad, no pager or forced merge GUI, fewer aliases, and no credential-helper override. | **Dependency adaptation plus parity gaps:** do not configure missing programs or replace system Git Credential Manager with Unix's helper. The portable Git settings still omitted are listed below. |
| SSH account selection | Managed `~/.ssh/config` selects work keys by host patterns; Git commit identity is selected by repository directory. macOS also uses `UseKeychain`. | Git selects both identity and key by repository directory; ordinary `~/.ssh/config` remains unmanaged for now. | **Deliberate Git behavior difference:** personal and work accounts can share the same hostname. Windows uses one explicit identity without inheriting extra SSH identities; `UseKeychain` is macOS-specific. |
| Mise inventory and execution | Broad shared `conf.d` inventory, mostly `latest`, with Zsh activation and project configuration discovery. Intel Mac fd is pinned separately. | Five pinned tools in `windows.toml`: Neovim, ripgrep, fd, Bun and OMP. Run them through `dev <command>` or the PowerShell runner; no shell activation. | **Current isolation policy, not a mise limitation:** explicit native backends, versions and ownership are reviewed before expansion. The runner ignores global/project mise config and disables automatic installs; normal activation/project workflows remain a parity gap. |
| Bun and OMP | Mise's Bun backend plus the npm OMP package, installed using Bun. | Mise's core Bun backend plus OMP's native GitHub release backend. | **Supported native alternative:** both remain mise-owned; the standalone OMP executable avoids an npm installation layer on Windows. See [Bun and OMP](#bun-and-omp). |
| Neovim configuration | The external currently deploys **NvChad**. | Neovim's executable is provisioned, but editor configuration remains unmanaged. | **Explicitly deferred:** the planned Windows LazyVim config collided with Unix external/source ownership. This needs a layout solution, not a claim that Windows cannot run Neovim/LazyVim. |
| Terminal and desktop integration | Managed terminal/theme configurations and platform-specific desktop helpers. | Windows Terminal with a manually configured Nu profile; optional Alacritty, themes and prompt integrations remain pending. | **Mixed:** macOS desktop helpers cannot simply run on Windows; native terminal configuration is portable work still to do. Terminal JSONC is not rewritten until preservation/recovery is validated. |
| Other managed files | Broader application configuration, global Git ignores, shared agent instructions/symlinks, CLI/runtime and shell helpers. | Most are still outside the Windows allowlist. | **Unfinished parity work:** verify native paths, dependencies, permissions and symlink/copy behavior before enabling them. They are not all inherently incompatible with Windows. |

### Git is managed by default, but its settings are not yet equivalent

Both platforms configure the supplied name/personal email, a work email when
enabled, `init.defaultBranch=main`, `core.autocrlf=input`, the commit template and
some builtin aliases. Windows normalizes the work path and uses case-insensitive
`gitdir/i` matching; macOS/Linux currently use `gitdir`.

The Windows baseline **does not yet carry over** several portable Unix defaults:
`pull.rebase`, fetch pruning, push auto-setup/follow-tags, rebase autosquash/autostash,
rerere, diff algorithm/conflict style, sorting, and several builtin aliases.
It also does not yet manage/reference the shared `~/.gitignore`.
These are **parity gaps from the initial minimal baseline**, not Windows
restrictions or a decision to permanently use different Git behavior.
Delta, DiffMerge and shell-backed aliases additionally require their dependencies
or a reviewed native equivalent before being enabled.

Windows does not overwrite system-level Git Credential Manager configuration.
However, replacing an existing user `.gitconfig` does **not** preserve helper
declarations or custom includes stored in that file: back it up and reconcile
needed settings before apply. Credential stores and private keys are not managed.

### Personal/work SSH behavior and its tradeoff

On Windows, repositories under `work_project_folder` use `work_email` and
`~/.ssh/ssh_work`; all other repositories use the personal email and
`~/.ssh/ssh_personal`. This works with the same host, such as `github.com`, for both
accounts. The first work clone can require an explicit work include before Git
has repository metadata to match; the guide provides the command.

Git's Windows `core.sshCommand` uses `-F none`, `IdentitiesOnly=yes`, one
`IdentityFile`, and public-key-only authentication. Host-key checking stays enabled.
**Tradeoff:** Git does not inherit user/system SSH aliases, proxy settings or other
SSH options; those need explicit reviewed exceptions. Ordinary non-Git SSH is not
changed. The existing Unix SSH template is left unchanged: it matches work hosts,
can accumulate work and personal identity entries, and currently disables
host-key checking for work hosts. Those behaviors are not copied to Windows.

Generate/register machine-local keys explicitly; never commit private keys.
Windows agent/passphrase handling is not automated. HTTPS remotes still use the
credential helper, not SSH keys. See the
[Git profiles and key setup guide](docs/WINDOWS.md#4-git-personalwork-identity-and-ssh-keys).

## Current Windows managed files

- `~/.gitconfig`, `~/.config/git/windows.inc`, and `windows-work.inc` when enabled.
- `~/.config/nushell/config.nu` and `env.nu`.
- `~/.config/mise/windows.toml`.
- `~/.dotfiles/git/template.txt` and `~/.editorconfig`.

The rest of the portability plan is in [the Windows support plan](docs/windows-support-plan.md).
Use [the Windows guide](docs/WINDOWS.md) for the exact preflight, preview, apply,
installation and rollback sequence—not the Unix installation one-liner.
Portable rendering/Git/Nu checks are useful evidence, but they are not native
Windows installation or SSH-authentication proof.

# Usage

## Common commands

These are general chezmoi commands. For the current Windows preview, follow the
guide's preflight and conflict-review steps before apply; do not use `update` or
`init --apply` as an unattended onboarding shortcut.

```sh
# Update the destination directory to match the target state
chezmoi apply

# Update the destination directory and refresh external files manually
chezmoi apply -R

# Update the destination directory and refresh the init files `promptStringOnce`, etc.
chezmoi apply --init

# Print the diff between the target state and the destination state
chezmoi diff

# Pull and apply any changes
chezmoi update

# Upgrade chezmoi to the latest released version
chezmoi upgrade

# Launch a shell in the source directory
chezmoi cd
```

## Bun and OMP

On macOS/Linux, mise installs Bun and [OMP](https://github.com/can1357/oh-my-pi)
from the managed `conf.d/tools.toml` inventory. The global mise setting
`npm.package_manager = "bun"` selects Bun for all mise-managed `npm:` tools.
It does not alias `npm` or change application projects' package managers.

The chezmoi provisioning hook runs `mise install` when the managed configuration
changes. Existing mise shell activation exposes `bun` and `omp`; no separate
Bun-global installation or PATH entry is needed.

```sh
mise exec -- omp --version
# Explicitly upgrade the selected tools:
mise upgrade bun 'npm:@oh-my-pi/pi-coding-agent'
```

Windows also provisions Bun and OMP through mise, using pinned versions in the
isolated `windows.toml` profile. OMP uses the native GitHub release backend there,
not the Unix npm backend. After the explicit Windows provisioning step, use
`dev bun --version` and `dev omp` in Nu. See
[Windows developer-tool provisioning](docs/WINDOWS.md#6-explicit-developer-tool-provisioning-after-reviewed-apply).

# Optional Configs

# High-Level Tools Overview

- zsh: macOS/Linux interactive shell; Nushell is the Windows interactive shell.
- [chezmoi](https://www.chezmoi.io/): used to manage these dotfiles and apply updates.
- [mise](https://mise.jdx.dev/): install and manage multiple devtools versions (think `nvm`, but good and for almost all tools).
- [alacritty](https://github.com/alacritty/alacritty): terminal emulator of choice.
- [krew](https://krew.sigs.k8s.io/): kubectl plugins manager.
- [k9s](https://k9scli.io/): kubectl TUI.
- [bat](https://github.com/sharkdp/bat): cat but modern.
- [eza](https://github.com/eza-community/eza): ls clone, but modern, with colors and with icons.
- [helix](https://helix-editor.com/): nvim but simple and rust-based.

# TODOS

- [ ] Complete native Windows acceptance for bootstrap, repeat apply, tools, Git/SSH and Terminal.
- [ ] Close Windows managed-file and portable Git-setting parity gaps.
- [ ] Port remaining native mise tools and shell/terminal integrations (including Krew and Starship).
- [ ] Revisit the explicitly deferred Windows LazyVim configuration.

# Useful Links

Some of these files were directly inspired by [budimanjojo's dotfiles](https://github.com/budimanjojo/dotfiles)
