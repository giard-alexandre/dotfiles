# Homebrew wrapper function

export def --wrapped brew [...args] {
  if ($args | length) > 0 and ($args | first) == "cleanup" {
    ^brew-cleanup
  } else if ($args | length) > 0 and ($args | first) == "bump" {
    ^brew-bump
  } else {
    ^brew ...$args
  }
}
