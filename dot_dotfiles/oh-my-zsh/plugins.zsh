#!/bin/zsh

# Disable Oh-My-Zsh autoupdates as they are handled by chezmoi
zstyle ':omz:update' mode disabled
zstyle :omz:plugins:iterm2 shell-integration yes

ZSH_AUTOSUGGEST_BUFFER_MAX_SIZE=100

ZSH_HIGHLIGHT_HIGHLIGHTERS=( main brackets root )

# Default OMZ Plugins
plugins=(
	brew
	docker-compose
	docker
	extract
	fzf
	git
	iterm2
	kubectl
	macos
	rust
	z
	dotnet
	fzf
)

# Custom Plugins
plugins+=(
	ports
	git-fetch-merge
	git-sync
	async
	zsh-completions
	fast-syntax-highlighting
	zsh-history-substring-search
	zsh-autosuggestions
)
