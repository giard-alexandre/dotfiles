# Git aliases and functions

# Git aliases
export alias gl = git pull --prune
export alias glg = git log --graph --decorate --oneline --abbrev-commit
export alias glga = git log --graph --decorate --oneline --abbrev-commit --all
export alias gp = git push origin HEAD
export alias gpa = git push origin --all
export alias gd = git diff
export alias gc = git commit -s
export alias gca = git commit -s -a
export alias gco = git checkout
export alias gb = git branch -v
export alias ga = git add
export alias gaa = git add -A
export alias gcm = git commit -s -m
export alias gcam = git commit -s -a -m
export alias gs = git status -sb

# Push and create/view PR
export def gpr [] {
  ^git push origin HEAD
  ^git pr
}

# Show commits since last tag
export def glnext [] {
  let last_tag = (^git describe --tags --abbrev=0 HEAD^ | str trim)
  ^git log --oneline $"($last_tag)..HEAD"
}

# Gitignore generator
export def gi [...langs: string] {
  let query = ($langs | str join ",")
  http get $"https://www.gitignore.io/api/($query)"
}
