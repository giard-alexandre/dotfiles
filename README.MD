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
source. Subsequent `chezmoi apply` runs perform the same
check before changing files. A missing prerequisite stops with a list to install:
Git for source/Git externals, `/bin/bash` for lifecycle scripts, curl for the
macOS Homebrew bootstrap, and apt or pacman (plus sudo for non-root users) on
the corresponding Linux distribution. This checks executable availability,
not versions, connectivity, credentials or package-manager health. Tools installed
*by* the apply scripts (such as zsh, Starship and mise) are not preconditions.

Run the isolated regression check with
`python3 -m unittest -v tests/test_apply_prerequisites.py`.

# Usage

## Common commands

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

# Optional Configs

# High-Level Tools Overview

- zsh: shell of choice.
- [chezmoi](https://www.chezmoi.io/): used to manage these dotfiles and apply updates.
- [mise](https://mise.jdx.dev/): install and manage multiple devtools versions (think `nvm`, but good and for almost all tools).
- [alacritty](https://github.com/alacritty/alacritty): terminal emulator of choice.
- [krew](https://krew.sigs.k8s.io/): kubectl plugins manager.
- [k9s](https://k9scli.io/): kubectl TUI.
- [bat](https://github.com/sharkdp/bat): cat but modern.
- [eza](https://github.com/eza-community/eza): ls clone, but modern, with colors and with icons.
- [helix](https://helix-editor.com/): nvim but simple and rust-based.

# TODOS

- [ ] Hanlde Windows installs?
  - [ ] Krew
  - [ ] Starship

# Useful Links

Some of these files were directly inspired by [budimanjojo's dotfiles](https://github.com/budimanjojo/dotfiles)
