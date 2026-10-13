export PATH=/usr/local/bin:$PATH

# compinit drops fpath dirs that compaudit thinks are insecure, which is any
# dir not owned by root or by you. Upstream compaudit also trusts the owner of
# the zsh binary, but it finds that owner through /proc/$$/exe, and macOS has
# no /proc. So a Homebrew zsh whose prefix belongs to another user (for
# example Workbrew's `workbrew` user) loses its own function dirs. Then
# compdump, is-at-least, etc. go missing.
# Fix: define compaudit from the stock source, also trusting whoever owns zsh's
# function library, as long as that file is not group- or world-writable.
# This must run before anything calls compinit (mise activate, oh-my-zsh).
() {
  emulate -L zsh
  local -a found=( ${^fpath}/compaudit(N.) )
  (( $#found )) || return 0
  local file=$found[1]
  [[ -n $file(#qN.f:go-w:) ]] || return 0
  zmodload -F zsh/stat b:zstat 2>/dev/null || return 0
  local -i owner
  owner=$(zstat +uid -- $file 2>/dev/null) || return 0
  (( owner != 0 && owner != EUID )) || return 0
  local stock='local _i_owners="u0u${EUID}"' src="$(<$file)"
  [[ $src == *"$stock"* ]] || return 0
  functions[compaudit]=${src/$stock/local _i_owners=\"u0u\${EUID}u${owner}\"}
}
