$env.config.show_banner = false

$env.config.history = {
  file_format: sqlite
  max_size: 1_000_000
  sync_on_enter: true
  isolation: false
}

$env.config.completions.algorithm = "prefix"
$env.config.completions.positional = false
$env.config.completions.sort = "smart"

$env.config.footer_mode = "auto"

# ---------------
# Plugin behavior
# ---------------
# Per-plugin configuration. See https://www.nushell.sh/contributor-book/plugins.html#plugin-configuration
$env.config.plugins = {}

# TODO: Extract to other file and import
# Aliases
alias ll = ls -l
alias lla = ls -la

# TODO: Theme, completions, aliases, nu_scripts?


# TODO:
# completer (closure with a |spans| parameter): A command to call for *argument* completions
 # to commands (internal or external).
 #
 # The |spans| parameter is a list of strings representing the tokens (spans)
 # on the current commandline. It is always a list of at least two strings - The
 # command being completed plus the first argument of that command ("" if no argument has
 # been partially typed yet), and additional strings for additional arguments beyond
 # the first.
 #
 # This setting is usually set to a closure which will call a third-party completion system, such
 # as Carapace.
 #
 # Note: The following is an over-simplified completer command that will call Carapace if it
 # is installed. Please use the official Carapace completer, which can be generated automatically
 # by Carapace itself. See the Carapace documentation for the proper syntax.
 #$env.config.completions.external.completer = {|spans|
 #  carapace $spans.0 nushell ...$spans | from json
 #}
