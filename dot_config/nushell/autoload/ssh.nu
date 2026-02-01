# SSH utilities

export def pubkey [] {
  cat ~/.ssh/id_rsa.pub | pbcopy
  print "=> Public key copied to clipboard."
}
