# FZF with bat preview

export def --wrapped main [...args] {
  ^fzf --preview 'bat --color=always --style=numbers --line-range=:500 {}' ...$args
}
