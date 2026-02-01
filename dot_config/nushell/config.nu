# Nushell Configuration
# This file runs after env.nu and configures the shell behavior

# Carapace completer for external commands
let carapace_completer = {|spans|
  carapace $spans.0 nushell ...$spans | from json
}

# Main configuration
$env.config.show_banner = false
$env.config.edit_mode = "emacs"

$env.config.history = {
  max_size: 100_000
  sync_on_enter: true
  file_format: "sqlite"
}

$env.config.completions = {
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

$env.config.cursor_shape = {
  emacs: line
}

$env.config.color_config = $dark_theme
$env.config.use_grid_icons = true
$env.config.footer_mode = 25
$env.config.float_precision = 2
$env.config.shell_integration = true
$env.config.buffer_editor = $env.EDITOR

# Load autoload modules
use autoload *

# Initialize mise (version manager)
if (which mise | is-not-empty) {
  let mise_path = ($env.XDG_CONFIG_HOME | path join "nushell" "mise.nu")
  ^mise activate nu | save -f $mise_path
  source $mise_path
}

# Initialize zoxide (smart directory jumping)
if (which zoxide | is-not-empty) {
  let zoxide_path = ($env.XDG_CONFIG_HOME | path join "nushell" "zoxide.nu")
  ^zoxide init nushell | save -f $zoxide_path
  source $zoxide_path
}

# Initialize Starship prompt
if (which starship | is-not-empty) {
  mkdir (~/.cache/starship | path expand)
  let starship_path = (~/.cache/starship/init.nu | path expand)
  ^starship init nu | save -f $starship_path
  use $starship_path
}

# Local overrides (not version controlled)
let localrc = (~/.localrc.nu | path expand)
if ($localrc | path exists) {
  source $localrc
}
