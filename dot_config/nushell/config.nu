# Nushell Configuration
# This file runs after env.nu and configures the shell behavior

# Carapace completer for external commands
let carapace_completer = {|spans|
  carapace $spans.0 nushell ...$spans | from json
}

# Main configuration
$env.config = ($env.config | merge {
  show_banner: false
  edit_mode: "emacs"
  footer_mode: 25
  float_precision: 2
  buffer_editor: $env.EDITOR

  shell_integration: {
    osc2: true
    osc7: true
    osc8: true
    osc9_9: false
    osc133: true
    osc633: true
    reset_application_mode: true
  }

  history: {
    max_size: 100_000
    sync_on_enter: true
    file_format: "sqlite"
  }

  completions: {
    case_sensitive: false
    quick: true
    partial: true
    algorithm: "fuzzy"
    external: {
      enable: true
      max_results: 100
      completer: $carapace_completer
    }
  }

  cursor_shape: {
    emacs: line
  }
})

# Load autoload modules
use autoload *

# Initialize mise (version manager)
# Note: Files are generated here but sourced below (source requires files at parse time)
if (which mise | is-not-empty) {
  ^mise activate nu | save -f ~/.config/nushell/mise.nu
}

# Initialize zoxide (smart directory jumping)
if (which zoxide | is-not-empty) {
  ^zoxide init nushell | save -f ~/.config/nushell/zoxide.nu
}

# Initialize Starship prompt
if (which starship | is-not-empty) {
  mkdir ~/.cache/starship
  ^starship init nu | save -f ~/.cache/starship/init.nu
}

# Source generated configurations
source ~/.config/nushell/mise.nu
source ~/.config/nushell/zoxide.nu
use ~/.cache/starship/init.nu

# Local overrides (not version controlled)
# To use: create ~/.localrc.nu with your custom configuration
# Note: Due to Nushell's parse-time source, restart shell after creating the file
