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

# Optional Configs

# High-Level Tools Overview

- zsh: shell of choice.
- [zellij](https://zellij.dev/): tmux but modern, faster and with a more promising future.
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
