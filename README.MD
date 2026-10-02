![preview](https://raw.githubusercontent.com/heuristicAL/dotfiles/main/docs/screenshot_terminal.png)

# Get Started
> Migrating from the old dotfiles? run the following command to clean things up before you install: `rm -rf ~/.znap ~/.asdf ~/.dotfiles`
> Make sure to backup your `~/.ssh/config` file as we're now managing that as part of this repo.

## Github Access Token
In order to avoid any issues with rate limiting on the GH API, I recommend adding a [personal access token](https://docs.github.com/en/enterprise-server@3.4/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) to your shell env. You can do this by setting one of these env variables:
- `CHEZMOI_GITHUB_ACCESS_TOKEN`
- `GITHUB_ACCESS_TOKEN`
- `GITHUB_TOKEN`

> Note: I recommend using GITHUB_TOKEN as this is most compatible with other tools.


## Install chezmoi on your machine using the shell script.
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
macOS Homebrew bootstrap, and apt, pacman, or dnf (plus sudo for non-root users)
when a Linux package-install hook applies. This checks executable availability,
not versions, connectivity, credentials or package-manager health. Tools installed
*by* the apply scripts (such as zsh, Starship and mise) are not preconditions.

Linux provisioning selects a package manager from `/etc/os-release`'s `ID`, then
`ID_LIKE`: Debian/Ubuntu and derivatives (such as Mint, Pop!_OS, and Kali) use apt;
Arch and derivatives (such as Manjaro and EndeavourOS) use pacman; Fedora and
modern RHEL-family systems (including Rocky and AlmaLinux) use dnf. DNF installs
the base tools and the provider of `chsh` needed by shell setup; either curl or
curl-minimal satisfies its curl requirement. Other distributions are allowed,
but must have the required tools provisioned separately; no package hook runs
for them. DNF-family systems without dnf need it installed before applying.
The apt hook refreshes package indexes before installation; the Arch hook uses
`pacman -Syu` to avoid partial upgrades. Both stop on package-manager errors.

Run the isolated regression check with
`python3 -m unittest -v tests/test_apply_prerequisites.py`.

# Usage
## Platform-specific helpers

The Homebrew wrapper, Oh My Zsh `brew` plugin, and `brew-bump`/`brew-cleanup`
helpers are enabled only on macOS. Applying on other platforms removes any
previously installed copies of those two helper scripts; it does not remove
Homebrew itself.

The `airport`/`afk` aliases, macOS defaults script, and Oh My Zsh `macos`/`iterm2`
plugins are also enabled only on macOS. Chezmoi templates select platform-specific
content before installation; these files do not probe `uname` at shell startup.

The obsolete `fix-internet`, `flush-dns`, `restart-audio`, and `dotinstall` helpers
are removed from the target home directory on the next apply. .NET SDKs are
managed through mise's `dotnet` inventory; use `mise install` to install them.

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

## Tool installation and prompts

Starship and Delta remain Homebrew packages on macOS and are installed through
mise on Linux. Homebrew supplies current Intel Mac Delta builds, so macOS does
not need an old upstream-binary pin. Helix and .NET SDKs are managed by mise on
both macOS and Linux. Platform-specific installers preserve these tools rather
than dropping them because another platform needs a different installation path.

After the platform's tools are installed, a separate hook runs on every apply
to generate `~/.local/share/nushell/vendor/autoload/starship.nu`, restoring it
if deleted even when the mise installation hook is cached. It invokes Homebrew's
Starship directly on macOS and mise's Starship on Linux. Starship is not executed
while chezmoi renders templates, so it need not exist before the first apply.
The mise hook also creates `~/.claude` before initializing RTK's global integration.

## Herdr platform-specific bindings

Chezmoi's `106-install-herdr-plugins` hooks invoke `herdr plugin install --yes`
after Herdr is available. On macOS/Linux, the hook runs through mise after tool
installation. On Windows, a native `.cmd` hook uses Herdr from PATH.
The installation inventory lives in `.chezmoidata/herdr.yaml`: Unix installs
gitview, Git Status, resurrect, plugin manager, and Worktrunk; Windows installs
Git Status, resurrect, and the Windows Worktrunk fork.

Herdr owns its generated `plugins.json`, plugin checkouts, and plugin config/state
directories. Chezmoi no longer manages that registry or overwrites unrelated
local registrations. The `run_onchange` hooks run on the first apply and whenever
the rendered inventory changes; reinstall a plugin with Herdr to refresh it.

macOS/Linux use `devashish2203/herdr-worktrunk` (`worktrunk`); Windows uses
[giard-alexandre/herdr-worktrunk-windows](https://github.com/giard-alexandre/herdr-worktrunk-windows)
(`worktrunk.windows`). Both use their repository's default branch, without a
`--ref` argument. The Worktrunk shortcuts (`prefix+shift+g` and `prefix+shift+d`)
resolve to the selected plugin's `open-with-remotes` and `remove` actions.

Native plugin builds require Rust/Cargo and a C linker. The Unix tool/package
hooks supply Rust, jq, build prerequisites, and the checksum tools used by gitview;
macOS needs the Xcode Command Line Tools used by Homebrew. On Windows, have
Herdr, Git, Rust/Cargo with its Windows linker/toolchain, and Node available on
PATH before applying. Windows Worktrunk additionally requires Herdr 0.8.0+,
Worktrunk 0.60.0+ (`git-wt`), fzf, and Windows PowerShell 5.1+.
Reload Herdr after applying the configuration.

## Global Git ignores

The home-directory `~/.gitignore` excludes `.pi` coding-agent configuration/state,
`.scratch` exploratory files, and `.ralph` autonomous-agent loop artifacts at
any depth. The managed Git config uses it through `core.excludesfile`.

# Optional Configs

# High-Level Tools Overview

- zsh: shell of choice.
- [chezmoi](https://www.chezmoi.io/): used to manage these dotfiles and apply updates.
- [mise](https://mise.jdx.dev/): install and manage multiple devtools versions (think `nvm`, but good and for almost all tools).
- [alacritty](https://github.com/alacritty/alacritty): terminal emulator of choice.
- [Ghostty](https://ghostty.org/): terminal configured with the One Double Dark theme in `~/.config/ghostty/theme.config`.
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
