# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a dotfiles management system using [Chezmoi](https://www.chezmoi.io/) to manage Nushell configuration, development tools, and system preferences across macOS, Linux, and Windows. The repository uses a topic-centric architecture where configuration is organized into modular Nushell modules that auto-load from the `~/.config/nushell/autoload/` directory.

## Common Commands

### Chezmoi Operations
```bash
# Preview changes before applying
chezmoi diff

# Apply configuration to system
chezmoi apply

# Apply and refresh external files (mise, plugins, themes)
chezmoi apply -R

# Apply and re-run initialization prompts
chezmoi apply --init

# Pull remote changes and apply
chezmoi update

# Open shell in source directory
chezmoi cd

# Upgrade chezmoi itself
chezmoi upgrade
```

### Development Workflow
```bash
# Test changes locally before committing
chezmoi diff

# After modifying templates or components, apply to verify
chezmoi apply

# Re-fetch external dependencies (nu_scripts, mise)
chezmoi apply -R

# Restart shell to test changes
exec nu
```

### Mise Tool Management
```bash
# Install tools defined in mise config
mise install

# List installed tools and versions
mise ls

# Update all tools to latest versions
mise upgrade

# Install a specific tool version
mise use node@20
```

## Architecture

### Topic-Centric Module System

Modules live in `~/.config/nushell/autoload/` (managed as `dot_config/nushell/autoload/` in chezmoi) and are organized by topic (git, docker, kubernetes, etc.). Each module is a `.nu` file that exports:

- **Aliases** - Using `export alias name = command`
- **Custom commands** - Using `export def command_name []`
- **Environment variables** - Using `$env.VAR_NAME = value`

All modules in the autoload directory are automatically loaded via `use autoload *` in `config.nu`.

Key modules:
- `system.nu` - Core system utilities and cross-platform compatibility
- `git.nu` - Git aliases and functions
- `docker.nu`, `kubernetes.nu` - Container and orchestration tools
- `eza.nu`, `bat.nu` - Modern CLI tool aliases
- `navigation.nu` - Project directory navigation (`c`, `cw`)
- `macos.nu.tmpl`, `apt.nu.tmpl` - Platform-specific commands

### Shell Loading Order

Nushell loads configuration in this order:
1. **`env.nu`** - Environment variables and PATH setup (runs first, before config.nu)
2. **`config.nu`** - Main configuration:
   - Sets up Carapace completer for external commands (kubectl, docker, etc.)
   - Configures shell behavior (history, completions, keybindings)
   - Loads all modules from `autoload/` directory via `use autoload *`
   - Initializes mise (version manager) via `mise activate nu`
   - Initializes zoxide (smart cd) via `zoxide init nushell`
   - Initializes Starship prompt
   - Sources `~/.localrc.nu` for local overrides (if exists)

### Chezmoi File Naming

Chezmoi uses special prefixes to map files:
- `dot_` → `.` (e.g., `dot_zshrc` → `~/.zshrc`)
- `private_` → files with restricted permissions
- `executable_` → files with execute bit set
- `.tmpl` suffix → processed as Go templates

Examples:
- `dot_config/` → `~/.config/`
- `private_dot_ssh/` → `~/.ssh/` (with restricted perms)
- `dot_zshrc.tmpl` → `~/.zshrc` (template processed)

### Template Data Flow

Interactive prompts in `.chezmoi.toml.tmpl` populate data used throughout templates:
- `{{ .fullName }}`, `{{ .personalEmail }}`
- `{{ .personalProjectFolder }}`, `{{ .workProjectFolder }}`
- `{{ .hasWorkProfile }}`, `{{ .workEmail }}`
- OS detection: `{{ .chezmoi.os }}`, `{{ .chezmoi.arch }}`

YAML data files in `.chezmoidata/`:
- `packages.yaml` - Package lists by OS (brew, apt, pacman, winget)
- `fonts.yaml` - Font installation configurations

### Script Execution Order

Chezmoi scripts in `.chezmoiscripts/` run in lexical order:
- `run_once_*` - Run exactly once (tracked by chezmoi)
- `run_onchange_*` - Run when script content changes
- `run_before_*` - Run before applying configuration
- `run_after_*` - Run after applying configuration

Typical order:
1. `run_once_before_000-macos-install-brew.sh.tmpl` - Install Homebrew
2. `run_onchange_before_010-*-install-packages.sh.tmpl` - Install OS packages (includes nushell, carapace, zoxide)
3. Configuration files applied
4. `run_onchange_after_001-fonts_*.sh.tmpl` - Install fonts
5. `run_once_after_100-set-nu-default-shell.sh.tmpl` - Set nushell as default shell
6. `run_onchange_after_103-install-mise-tools.sh.tmpl` - Install mise tools

### External Dependencies

Managed via `.chezmoiexternal.toml.tmpl`:
- **Git repos**: NvChad, nu_scripts, Alacritty themes
- **GitHub releases**: mise, sad, dra, age (automatically downloads latest)

To refresh: `chezmoi apply -R`

**Completions**: Handled by [Carapace](https://carapace.sh/) (installed via package manager), which provides completions for kubectl, docker, git, gh, and hundreds of other commands.

## Adding New Modules

To add a new topic module (e.g., "erlang"):

1. Create file: `dot_config/nushell/autoload/erlang.nu`
2. Add Nushell code:
   ```nu
   # Erlang aliases and functions
   export alias erl = iex -S mix
   export def erlang_version [] {
     erl -eval 'erlang:display(erlang:system_info(otp_release)), halt().' -noshell
   }
   ```
3. Run `chezmoi apply` to install
4. Restart shell: `exec nu`

The module will automatically load via `use autoload *` in config.nu. For PATH modifications, add them to `env.nu.tmpl` instead.

## Personalization

### Local Overrides
- **Shell**: Add custom/secret config to `~/.localrc.nu` (not version-controlled, sourced by config.nu)
- **Git**: Edit `~/.gitconfig` directly (includes chezmoi-managed config)
- **SSH**: Edit `~/.ssh/config` (managed as `private_dot_ssh/private_config`)
- **Prompt**: Modify `dot_config/starship.toml`

### Configuration Prompts
Re-run initialization prompts: `chezmoi apply --init`

This will ask for:
- Full name, personal/work emails
- Project folder paths (mapped to `c` and `cw` shortcuts)
- Work profile settings

## Platform-Specific Behavior

The codebase supports macOS, Linux, and Windows through:
- Conditional templates: `{{ if eq .chezmoi.os "darwin" }}`
- Platform-specific scripts: `*-darwin-*.sh`, `*-linux-*.sh`
- OS-specific package lists in `.chezmoidata/packages.yaml`

## Key Technologies

- **Shell**: [Nushell](https://www.nushell.sh/) (modern, structured data shell)
- **Completions**: [Carapace](https://carapace.sh/) (universal completion system)
- **Navigation**: [zoxide](https://github.com/ajeetdsouza/zoxide) (smart cd command)
- **Prompt**: [Starship](https://starship.rs/) (cross-platform, fast)
- **Multiplexer**: [Zellij](https://zellij.dev/) (modern tmux alternative)
- **Version Manager**: [mise](https://mise.jdx.dev/) (replaces asdf, nvm, rbenv, etc.)
- **Terminal**: Alacritty, Ghostty
- **Editor**: Neovim (NvChad), Helix
- **macOS Window Management**: Yabai (tiling WM), skhd (hotkeys)

## Important Notes

### GitHub API Rate Limiting
Set a personal access token to avoid rate limits when fetching external dependencies:
```bash
export GITHUB_TOKEN="your_token_here"  # Recommended
# Or: GITHUB_ACCESS_TOKEN, CHEZMOI_GITHUB_ACCESS_TOKEN
```

### Nushell Quick Start

After applying dotfiles with `chezmoi apply`:

```nu
# Navigation
c               # cd to personal projects folder
c myproject     # cd to specific project (tab completion works!)
cdr             # cd to git repository root

# Common aliases
ls              # eza with icons
ll              # eza long format
cat file.txt    # bat with syntax highlighting

# Git shortcuts
gs              # git status
ga file         # git add
gc              # git commit
gp              # git push

# Kubernetes
k get pods      # kubectl get pods (with tab completion!)
kx              # switch context
kn              # switch namespace

# Reload config
reload          # restart nushell with new config
```

### Migration from Zsh
Previous zsh/Oh-My-Zsh configuration has been replaced with Nushell:
- All aliases converted to Nushell modules in `~/.config/nushell/autoload/`
- Completions now provided by Carapace (better than zsh completion plugins)
- zoxide replaces autojump/z for smart directory navigation
- Local overrides: use `~/.localrc.nu` instead of `~/.localrc`

### Work Profile
When `hasWorkProfile` is true, additional configuration is activated:
- Work email for Git commits on work hosts
- Separate work projects folder (`$PROJECTS_WORK`, shortcut: `cw`)
- SSH key selection based on host patterns