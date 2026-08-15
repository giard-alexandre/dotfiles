# Repository Guidelines

## Project Structure & Module Organization

This repository is a chezmoi source tree for cross-platform dotfiles. Files named `dot_*` map to dotfiles in the home directory; `.tmpl` files use chezmoi's Go-template syntax. Reusable shell fragments live in `.components/`, lifecycle scripts in `.chezmoiscripts/`, shared template fragments in `.chezmoitemplates/`, and host/package data in `.chezmoidata*`. Application-specific configuration is under `dot_config/`; supporting documentation and images belong in `docs/`.

## Development and Validation Commands

There is no build step or automated test suite. Validate changes from the repository root:

- `chezmoi diff` previews differences between rendered target state and the home directory.
- `chezmoi apply --dry-run --verbose` renders the full source and reports planned actions without changing files.
- `chezmoi execute-template < path/to/file.tmpl` checks an individual template's rendered output.
- `chezmoi apply` updates the home directory and may run install scripts; use it only after reviewing the dry run.

## Coding Style & Naming Conventions

Follow `dot_editorconfig`: four-space indentation, LF line endings, UTF-8, trimmed trailing whitespace, and a final newline. Preserve the shell dialect declared by each shebang and quote variable expansions. Keep templates readable, using `{{- ... -}}` whitespace trimming deliberately. Follow chezmoi naming semantics such as `private_`, `executable_`, `create_`, and `run_once_`; script names should retain their numeric execution order, for example `run_onchange_before_010-...`.

## Testing Guidelines

Render every changed template and run the full dry-run command. For OS-specific behavior, keep conditions explicit (`.chezmoi.os`) and inspect each affected branch. Confirm executable/private attributes through chezmoi naming, not manual filesystem changes. No coverage threshold is defined.

## Commit & Pull Request Guidelines

Use concise conventional subjects observed in history: `feat: add ...`, `fix: correct ...`, `chore: update ...`, or `refactor: remove ...`; optional scopes such as `feat(alacritty): ...` are welcome. Name branches by type and topic, such as `fix/mise-and-zsh`. Pull requests should explain affected platforms and files, list validation commands, link relevant issues, and include screenshots only for visible terminal or prompt changes. Keep unrelated configuration changes separate.

## Security & Local Configuration

Never commit tokens, SSH keys, email addresses, or machine-only settings. Put local shell overrides in `~/.localrc`, and model shared differences through prompts, data files, and templates.
