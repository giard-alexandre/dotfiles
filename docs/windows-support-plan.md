# Native Windows support plan

Status: foundation plus bounded mise slice implemented; LazyVim explicitly deferred. Native
Windows acceptance/release remains **pending**. This is not a Windows support claim.
Baseline: `feat/windows`, commit `e5f69a905e28c204df4133fe36912175f0e5b060`.

Three research agents investigated repository portability, Nushell/terminals, and
native bootstrap documentation. Two independent adversarial reviewers challenged
the draft; their findings are reconciled below. The first implementation received
independent review: READY / OK with notes for a bounded preview only. Native Windows
execution and release acceptance remain pending.

## Current direction: managed-file parity

Windows should function like the macOS/Linux setup wherever practical. Files
managed by chezmoi on Unix should also be managed on Windows when their native
application/path/behavior is supported. Prefer shared templates with targeted
platform branches, not a parallel opt-in configuration model. The existing
allowlist is a transitional safety gate while ports are validated, not the final
scope. Distinguish genuinely unsupported features from unimplemented portable
ones; the latter remain parity work. Existing explicit decisions such as the
LazyVim deferral and native validation gates still apply.

This direction supersedes older checkpoints' minimal/manual-opt-in ownership
choices. Git's root `.gitconfig` is now automatically managed on Windows;
other portable exclusions must be addressed as subsequent validated ports.

## Windows Git profiles

Personal/work commit identity and SSH key selection now share the repository
directory rule. The managed root `.gitconfig` loads the personal defaults.
A case-insensitive conditional work include selects the work email/key. Explicit
OpenSSH options isolate Git from accumulated user/system SSH identities without
modifying existing SSH config or disabling host-key checks. Keys remain
machine-local and manually created/registered. The guide covers first clone,
config precedence and existing SSH proxy/alias exceptions. This supersedes the
personal-only and opt-in baselines in older checkpoints; native authentication remains pending.

## Bun and OMP expansion

The current Windows inventory adds `core:bun@1.4.2` and
`github:can1357/oh-my-pi@18.2.6` to the original three Aqua tools.
This supersedes the three-tool-only scope in earlier checkpoints below.
Both remain mise-owned and explicitly provisioned; Nu embeds the expanded
reviewed manifest automatically. OMP uses its upstream native release, not npm.
Windows x64 URLs/checksums were resolved with a disposable cross-platform mise
lock; isolated Darwin installs ran both version commands successfully.
Native Windows/PS5.1 execution remains pending. See `WINDOWS.md` section 6 for
current provisioning, ownership and verification details.

## Latest adversarial review fixes

- Replaced the moving `HEAD:dot_config/nushell/config.nu` test baseline with a
  byte-exact fixture from `e5f69a9`. The former lookup fails as soon as the source
  rename is committed; the fixture needs neither old paths in HEAD nor Git history.
- Both PowerShell entry points now require a nonempty native x64 platform result
  from `Win32_Processor.Architecture`, in addition to an AMD64/64-bit process.
  ARM64, unknown/mixed/empty results and CIM errors stop before mutation.
- `tests/windows/test_architecture.ps1` exercises the actual entry points with
  mocked CIM and stops at the next platform operation. All 12 cases passed under
  disposable PowerShell 7.5.4 on Darwin; removing the host guard reproduced the
  ARM64-emulation acceptance bug. Native CIM and PS5.1 remain release gates.
- The portable foundation suite passed 12 tests with 3 native gates skipped.
  These fixes do not change the preview scope or LazyVim deferral.

## Independent review follow-up: two P1 preview boundary fixes

Review `windows-mise-review.md` blocked the preview on two trust/ownership gaps.
Both findings accepted; bounded fixes implemented without changing LazyVim deferral:

1. **P1 Nu manifest/XDG boundary:** `dev` now requires the exact canonical XDG
   spelling embedded from the rendering home and compares the complete parsed
   manifest to the source-reviewed table embedded at render time. Direct specs can
   no longer come from arbitrary runtime TOML. Changed versions, extra/missing/
   replaced keys or additional sections stop before even `mise where`. Updating
   approved pins now requires reviewing/applying Nu config and windows.toml together.
2. **P1 singleton mise ownership:** bootstrap no longer executes a sole PATH mise
   before ownership review. It first requires WinGet jdx.mise registration, displays
   resolved path/hash, explains registration is not proof of the path association,
   and requires typed manual ownership confirmation. A LocalAppData ownership.json
   attestation records package ID/path/SHA-256. Nu and PowerShell validate it before
   invoking mise; absent receipt or path/byte changes fail closed. Upgrades require
   explicit reconfirmation. This is the reviewer's manual-confirmation alternative,
   not automatic signature verification or protection against same-user tampering.

Portable evidence: `test_nu_dev_argv_and_no_startup_execution` now uses an
all-invocations log (including `where`) and confirms **zero mise calls** for missing
ownership receipt, a foreign singleton at a different path, changed bytes at the
same path, changed version/backend, extra/missing tool, extra manifest section and
redirected XDG containing an otherwise valid manifest. Valid attested execution and
existing argument/duplicate/missing-tool/startup checks still pass.
`test_windows_manifest_and_ownership` adds static PS gate-order assertions only;
**PS5.1 execution is not available and is not claimed**. Existing 15-test suite
continues to include isolated rendering/diffs/dry-runs and the real Unix NvChad
external declaration: 12 portable passes, 3 explicit native skips.

Native PS5.1 registration/display/consent/refusal/receipt persistence and upgrade
invalidation, actual WinGet installation linkage and native Nu hash/path behavior
remain VM release gates. Independent re-review `b229f1df-51aa-4323-a228-11426055765e`
confirmed both P1 fixes with no remaining findings: **Preview OK with notes**.
The parent reran the 15-test suite: 12 passed, 3 native gates skipped; `git diff
--check` passed. This clears the preview block, not native release acceptance.
No installs, real apply, commits, pushes or staging; prior foundation and explicit
LazyVim deferral preserved.

## Latest resumed checkpoint: mise delivered, LazyVim deferred by user

User explicitly selected **DEFER LAZYVIM** after a regression exposed a chezmoi
source/external collision. This is the current scope contract: finish mise only,
preserve foundation and Unix NvChad, no separate Windows source root or unmanaged
editor seed. Native execution remains a **release gate**, not a reason to abandon
portable implementation. No packages were installed, no real home apply, and no
commits/pushes/staging occurred. Intentional foundation changes were preserved.

Implemented:

- WinGet `jdx.mise` install/reuse switch in the explicit bootstrap, separate from
  core packages. No duplicate WinGet ownership for Neovim/rg/fd.
- Reviewed literal `~/.config/mise/windows.toml`: native Aqua Neovim 0.11.6,
  ripgrep 15.1.0 and fd 10.3.0 only. Windows ZIP/MSVC recipes/assets confirmed
  from primary sources. Shared Unix latest/conf.d/trust configuration untouched.
- Explicit `developer-tools.ps1 -Install`, strict source/deployed manifest match,
  consent/foreign PATH ownership check, exact tool specs, dedicated native
  LocalAppData mise-windows data/cache/state. No global/project config discovery
  (`MISE_NO_CONFIG`), broad trust or activation. Execution disables both automatic-
  install flags AND checks `mise where` for every pin before running a command.
  Nu `dev` reads the same table only on demand; PS `-Run` supports automation.
- Missing-pin checks matter: installed Darwin mise 2026.8.4 with exec automatic
  install disabled still ran an absolute test command with a missing tool spec.
  Checking `where` first rejects missing tools before falling through to unrelated
  PATH commands; portable fake-Nu and real offline-mise checks cover this behavior.
- `docs/WINDOWS.md` sections 6–7 document commands, ownership, version/backend/
  config/store policy, updates/conflicts, sources and the explicit editor deferral.

LazyVim disposition:

- A normal `dot_config/nvim` source directory conflicts with Unix's git-repo
  external even if all child files are ignored. Ignoring the parent also suppresses
  the external; targetPath alias did not solve it. A real-external regression caught
  what the earlier unrelated-external stubs could not prove.
- User declined changing the source ownership/onboarding contract now. Removed
  only this worker's incomplete Lua seed, editor scripts, license copy and nvim
  allowlist/ignore additions. There are no separate roots or unmanaged seed writes.
- Future selected distribution remains Windows LazyVim at canonical XDG nvim;
  no substitute editor distribution or Unix migration. Neovim binary provisioning
  remains useful; `dev nvim -u NONE` is the no-user-config validation route.
- Research is retained in docs/WINDOWS.md: starter semantics/revision; LazyVim
  >=0.11.2; Treesitter compiler/parser hooks; Mason tool ownership; Blink Lua
  matcher avoiding Rust; package/LuaRocks/image/optional extras requiring review.
  Those findings are not a plugin installation or full dependency approval.

Validation checkpoint: `python3 tests/windows/test_foundation.py`: 15 tests,
12 passed / 3 native gates skipped. Exact mise-only Windows manifest, existing
Windows editor files untouched, actual Unix NvChad declaration retained byte-for-
byte with isolated transport/unrelated externals, ownership/pins, installed Darwin
Nu parsing/argv/no-startup/missing-tool behavior against fake mise.exe, installed
Darwin mise ignoring hostile global/project configs and detecting missing pins
with offline disposable stores. All prior script/changed-template renders, XDG
rejection, Unix byte-preservation and isolated diff/full dry-runs still pass.

Primary-source immutable review revisions and asset links are in docs/WINDOWS.md:
mise acbbdee0, Aqua registry 5b543ce1; deferred editor research starter 803bc181,
LazyVim 99970099, lazy.nvim 85c7ff37 and Blink 1.7.0. These are source evidence,
not native installation proof. No downloaded code executed. No Windows artifact
lock/digests generated; record actual WinGet mise version/scope and native Aqua
verification in acceptance rather than fabricating it on Darwin.

Mandatory remaining gates: PS5.1 parsing/execution and native complex argv; exact
mise version/registry, native installs/reuse/refusal/offline/verification, config
isolation/no-auto-install and subprocess proof of no Bash/compiler; repeat apply
and custom/partial-state recovery; previous stock WinGet/Nu/Terminal/Git gates;
immutable onboarding provenance. Independent review should review the **mise-only
slice and foundation compatibility**, not treat deferred LazyVim as a defect to
patch around. Native release and independent review remain pending.

## Earlier foundation checkpoint: implemented slice and superseding XDG contract

The latest user explicitly approved **user-level `XDG_CONFIG_HOME=<absolute
home>/.config` before Nu or Neovim starts**. This supersedes the earlier AppData Nu
wrapper proposal and rejection of XDG overrides. Existing `dot_config` destinations
are canonical. Do not globally relocate `APPDATA`; do not require/set
`XDG_DATA_HOME`. Windows-only LazyVim remains selected at `~/.config/nvim`, with
native runtime data/cache separation; it is not implemented in this slice.

Completed in the working tree (no commits, packages or real host apply):

- Windows allowlist: Nu config/env, opt-in `.config/git/windows.inc`, commit template
  and EditorConfig only; repository infrastructure explicitly ignored everywhere.
- Windows externals render empty **before** release lookups. Each alternative below
  remains pending; none is claimed permanently unportable.
- Darwin trailing echo and unconditional Zsh wrapup leaks fixed. All ten Windows
  lifecycle templates render empty, without Nu/Starship/Unix interpreter execution.
- Init validates the process XDG contract and x64. Normal target rendering checks
  XDG, x64 and current-home destination through `.chezmoiignore`; standalone init
  cannot use shared named templates, so its small check is deliberately inline.
  Project paths are constructed before TOML quoting.
- Self-contained, explicit PS5.1 `scripts/windows/bootstrap.ps1`: default read-only
  preflight; conflict/reparse/legacy-config stops; separately consented user/process
  XDG and WinGet core install/reuse. No init/apply, policy bypass, persistent PATH
  overwrite, automatic upgrades, Git reset or remote-script execution.
- Minimal Nu keeps config in `.config/nushell`; SQLite history explicitly goes to
  native LocalAppData at startup. Unix Nu output is byte-identical to the baseline.
- Windows Git uses a **manual opt-in include**, not replacement `.gitconfig`, so
  credential/work/ignore content stays local. Existing local optional-tool keys
  still require review; do not claim the include neutralizes unknown settings.
- `docs/WINDOWS.md` routes explicit acquisition/preflight/init/diff/dry-run/conflict
  review/consented apply and manual native Nu Terminal profile UI setup. README
  routes Windows before destructive Unix examples. No settings JSONC/fragment edits.
- `tests/windows/test_foundation.py`: seven portable checks pass on Darwin with
  isolated source/home/config/cache/state paths: exact Windows manifest, all script
  renders, full/targeted XDG rejection, architecture/destination rejection, native
  path spelling, existing credential-file preservation, init TOML parsing (personal
  and work branches), Unix Nu baseline comparison, Windows full diff/dry-run and
  Unix offline-fixture diff/dry-runs. Two native gate tests are explicitly skipped.
  Unix fixtures explicitly stub release/external/Starship dependencies only in temp.

Native gates **not run**: PS5.1 parser/execution (no tooling installed on host),
WinGet registration/scopes/install/refusal/reboot/reuse, Nu native syntax/startup and
history, fresh Terminal inheritance/UI, native Git/GCM/work includes, reparse-point
and known-folder checks, real apply/idempotence, redirected folders and ARM64.
No immutable reviewed bootstrap artifact/digest is published yet; onboarding is a
review preview, not a released trust chain. `git diff --check` must be rerun after
any edits. No files are staged.

Latest validation checkpoint: `python3 tests/windows/test_foundation.py` ran nine
cases: seven passed, two native gates skipped; `git diff --check` passed.
Chezmoi on the Darwin host: v2.72.0 (Homebrew). The test runner explicitly supplies
`--source`, `--destination`, `--config`, `--cache`, `--persistent-state` and fixture
`--override-data`; its diff/dry-run calls do not touch the real home. Initial test
failures caught the init named-template limitation and fixture prompt-key mismatch;
both were corrected before the passing run. Native PowerShell tooling remains
unavailable, not silently replaced with another interpreter.

Independent implementation review `fcf90a77-2674-4557-960f-29983788abf6` accepted
the bounded preview. Its two P1 release gates remain: native Windows execution and
immutable reviewed bootstrap provenance. Its P2 documentation finding was corrected:
history-directory creation happens when Nu loads the config, not exclusively during
interactive startup. The guide now calls for separate command/config-load tests.

Next steps, in order: disposable Windows 11 x64 native gates and package
versions/scopes; publish reviewed bootstrap provenance;
then separate mise subset/integrations and Windows-only LazyVim/native external
ports. Do not widen this slice to all tools or automate JSONC. The remaining phased
plan below records prior research and future intent, **not completed features**;
this checkpoint and `docs/WINDOWS.md` govern any conflicting older proposal.

## Fixed requirements and recommended scope

- Native Windows only. No WSL, Cygwin, MSYS or Git Bash runtime dependency.
- **WinGet and mise-en-place are approved dependency managers.** Use WinGet for
  Windows applications and bootstrap tools; prefer mise for versioned runtimes and
  CLI dependencies where project/global version management adds value. Assign one
  owner per tool. No Scoop/Chocolatey fallback.
- **Nushell is the default interactive shell.** PowerShell is an explicit automation
  interpreter, not an interactive-shell fallback advertised as completed setup.
- Preserve macOS/Linux behavior and port useful shared configuration in stages.
- For externals, plan applicable native alternatives at the application's correct
  Windows location; do not silently discard portable content. Ask the user when
  behavior, replacement, installation ownership or destination remains uncertain.
- User-selected editor distribution: **LazyVim** for the Windows Neovim setup.
  User-selected shell scope: **minimal Nushell**, not an Oh My Zsh feature-parity port.
- Recommended initial target: Windows 11 x64, standard user, standard local AppData
  locations, stable Windows Terminal. ARM64 and redirected folders need separate
  validation; neither is presumed impossible to support later.
- Windows Terminal default profile and Windows' default terminal application are
  different settings. Do not replace COMSPEC, file associations, SSH server shell
  or IDE task interpreters to simulate Unix `chsh`.

## Findings that determine the design

1. `.chezmoiexternal.toml.tmpl` queries releases before mapping Windows mise to
   `INVALID_OS`; additional downloads assume Unix archives, executable names and
   `funzip`. Guard incompatible branches before lookups, not just their URLs.
2. `dot_local/share/nushell/vendor/autoload/starship.nu.tmpl` executes Starship
   during rendering. A package script in the same apply cannot reliably satisfy
   this dependency. Windows integration generation must happen after installation.
3. `.chezmoiscripts/run_onchange_before_010-darwin-install-packages.sh.tmpl` has a
   final echo outside its Darwin conditional. Windows consequently receives a
   nonempty shell script. The Zsh wrapup is also unconditional. Audit every script.
4. Without an inherited override Windows Nu defaults to `%APPDATA%\nushell`.
   Approved user/process XDG_CONFIG_HOME makes `~/.config/nushell` canonical before
   startup. Alacritty still needs independently verified native discovery later.
5. Current Git config assumes cache credentials, vim, delta, diffmerge and helper
   commands. Baseline Git must work without these optional dependencies.
6. Existing agent instruction symlinks and private-file attributes do not prove
   Windows symlink permission or ACL behavior.

## Phased implementation

### 1. Establish the native rendering safety boundary

Edit:

- `.chezmoiignore`: Windows target filtering; exclude Windows AppData targets on
  other OSes; explicitly exclude repository-only `scripts/`, `tests/`, `.github/`
  and their descendants when added. Preserve existing documentation exclusions.
- `.chezmoiexternal.toml.tmpl`: split entries by platform before incompatible
  release lookups. Use the per-external replacement/destination plan below; retain
  portable configuration/theme content at native locations. WinGet/mise own native
  binary installation where supported, without duplicate external-owned binaries.
- `.chezmoi.toml.tmpl`: validate native architecture and paths; construct paths
  before TOML serialization. Keep personal answers local and Unix behavior intact.
- Darwin package script: move its trailing echo inside the Darwin conditional.
- `.chezmoiscripts/run_after_999-wrapup.zsh.tmpl`: gate to Unix.
- `dot_gitconfig.tmpl`: introduce the Windows contract described below.

Add proposed files:

- Implemented guard is integrated into `scripts/windows/bootstrap.ps1`; default
  invocation is read-only and required before documented apply routes.
- Implemented `dot_config/nushell/config.nu.tmpl` preserves the original Unix
  output and supplies a minimal Windows branch. No AppData Nu wrapper is needed.

The initial Windows target set is an allowlist. Incompatible and deferred families
are excluded, not deployed with an implicit promise they work. Preserve
`~/.dotfiles/git/template.txt`; do not blanket-ignore its parent without an exception.

**Gate:** every Windows `.sh`/`.zsh` lifecycle renders empty/whitespace; no Unix
interpreter or release lookup is needed for Windows rendering. All changed branches
render correctly, and macOS/Linux behavior is preserved. The Darwin echo no longer
appearing on Linux is one intentional, documented output difference.

### 2. Bootstrap with WinGet and make Nu the default

Implemented `scripts/windows/bootstrap.ps1`, `docs/WINDOWS.md` and README Windows
routing. This slice uses manual Terminal profile UI instructions; an owned fragment
and JSON example are deferred pending native validation, not required for baseline.

Dependency order:

1. Built-in Windows PowerShell 5.1 acquires and verifies the reviewed bootstrap.
2. Read-only OS/user/layout/policy/command checks.
3. Working WinGet/App Installer, or explicit native recovery instructions and stop.
4. Install/reuse native core packages through WinGet:
   `Git.Git`, `twpayne.chezmoi`, `Nushell.Nushell`; reuse suitable stable Terminal
   or install `Microsoft.WindowsTerminal`.
5. Resolve executable paths and refresh current-process discovery safely.
6. `chezmoi init` with explicit source/repository/branch and local answers, **no apply**.
7. Guard, diff, full dry-run, conflict review, then consented apply.
8. Validate plain interactive Nu and Git.
9. Add a native Nu profile and select it as default in the Terminal UI. An owned
   fragment remains a possible later improvement, not implemented.
10. Verify fresh Terminal launch, normal default tabs and plus-button tabs.

Keep initial automation PS5.1-compatible. PowerShell 7 is not needed to install
itself or to obtain the minimal Nu session. No Windows package mutation lifecycle
hook is needed initially; bootstrap owns package reconciliation explicitly.

For the developer-tools stage, install/reuse `jdx.mise` through WinGet, verify its
native executable and version, then provision the selected mise dependency set.
The minimal Nu/Git/chezmoi/Terminal path stays independent of mise activation so a
failed tool install cannot prevent opening a recovery shell. This is sequencing,
not a requirement for further approval to use mise.

**Gate:** follow the published instructions on stock Windows without Git, chezmoi,
Nu or PS7. Repeat successfully after partial failure. Second apply has no extra
writes or duplicate profiles. Only then claim the baseline is supported.

### 3. Port the daily-use environment

After the baseline gate, adapt rather than discard useful portable capabilities:

- mise: reuse the repository's tool inventory where native Windows backends work.
  Define an explicit Windows subset and tested versions/backends; install that set
  after `jdx.mise` is available. Prioritize Node, Python and Go as runtime candidates,
  and bat/fzf/ripgrep/fd/eza as CLI candidates, subject to individual verification.
  Adapt `dot_config/mise/conf.d/{tools,settings,plugins,trusted-paths}.toml` and
  `dot_config/mise/create_config.toml` as applicable (the trusted-paths source is
  `.toml.tmpl`). Verify native config discovery before choosing Windows wrappers;
  keep non-Windows tool sets intact and avoid duplicate WinGet ownership.
- Starship: retain shared `dot_config/starship.toml`, set `STARSHIP_CONFIG`
  explicitly, generate one native Nu autoload file after installation. Missing
  Starship leaves a usable plain Nu prompt. Add a font/plain-text fallback.
- Nu aliases/completions: keep the current minimal Nu configuration and builtin
  behavior. Do not add OMZ-equivalent utility wrappers or third-party completion
  packs without asking. Never source Zsh `.localrc` in Nu; a separate native local
  override may be added only through a parse-safe mechanism.
- fzf/bat: enable native executables and verify current `fzf --nushell` integration.
  Start without previews, then test native preview interpreter and filename quoting.
- Git delta/editor/merge integration: feature-gated, installed and tested first.
- Alacritty: adapt `%APPDATA%\alacritty` targets, imports/themes, URL opener and
  direct `nu.exe` child. Keep its theme external at the matching native location.
  Preserve other-platform configurations.
- Neovim/LazyVim: replace the Windows branch of the misleadingly labelled
  NvChad external with a reviewed LazyVim starter at `~/.config/nvim` through XDG.
  Provision native Neovim and required dependencies through mise/WinGet, verify
  `stdpath('config')`, then run `:LazyHealth`. Preserve existing config/data with
  explicit conflict handling; do not migrate other OSes without approval.
- Agent instructions: deploy ordinary copies from shared canonical content on
  Windows, after proving chezmoi's same-target source collision/selection behavior.
  Keep existing Unix symlinks. Read the applicable agent-content instructions.
- SSH/Helix/k9s/other native applications: verify native lookup locations, packages,
  config schema and permissions before enabling their corresponding targets.

Potential new scopes: `.chezmoitemplates/nushell/`, native Nu `scripts/` wrappers,
`scripts/windows/Configure-NativeIntegrations.ps1`, shared/native Alacritty wrappers.
Use exact WinGet IDs or explicit verified mise backend/tool identifiers, according
to the ownership table below; do not assume a Linux tool name guarantees a native
Windows package or backend.

**Gate per feature:** native lookup, startup, missing-tool behavior, repeated apply,
upgrade regeneration where relevant, and macOS/Linux regression tests.

### 4. Extend and automate validated support

- Investigate native runtime/toolchain equivalents individually; do not run the
  entire shared mise `latest` list on Windows. No asdf Bash backends.
- Expand the approved mise dependency set as native backends are verified. Prefer
  project-local versions for project runtimes and a deliberate global default for
  general CLI tools; prevent project activation from destabilizing bootstrap tools.
- Add `tests/windows/` and native Windows CI around the proven contracts; keep
  simple assertions where sufficient, rather than requiring a new test framework.
- Automate Terminal settings only if justified, with JSONC-preserving edits,
  conflict detection, exact-byte backups and rollback. Manual UI stays supported.
- Add redirected-folder and ARM64 support only after dedicated native tests.

## Portability matrix

“Later” means excluded from the first Windows deployment, not declared unportable.

| Existing family | Windows treatment |
| --- | --- |
| chezmoi data/config/ignores | Adapt native paths, architecture and package ownership |
| Zsh, OMZ, `.components`, Zsh functions | Exclude Windows targets; user chose minimal Nu, no automatic plugin/workflow recreation |
| Homebrew/apt/pacman/chsh/macOS lifecycle | Exclude execution; fix leaked script output |
| macOS helpers, borders, Ghostty | Exclude; no verified native Windows Ghostty GUI baseline |
| Current Nu settings, structured `ll`/`lla`, history | Implemented minimal Windows branch in canonical `.config/nushell`; history in native LocalAppData |
| Unix Nu autoload/completion paths | Exclude Windows targets; generate native integrations later |
| Starship config | Portable later, with explicit lookup and optional glyph support |
| Alacritty config/imports/keybindings | Adapt native paths, Nu startup and opener later |
| Git config/work identity/ignore/commit template | Root `.gitconfig`, personal/work identity/key includes and commit template managed; global ignore/integration parity pending; credential stores and private keys stay local |
| SSH config and placeholders | Later: native OpenSSH, ACL and policy validation; no key copying |
| Shared agent instructions | Portable content; ordinary-file discovery copies later |
| Existing agent symlinks | Exclude initially; no Developer Mode prerequisite |
| Helix, k9s skins/config, kube placeholder | Later: native package/path/schema/permission checks |
| mise manager/config/trusted paths | Approved developer-tools stage: WinGet installs mise; mise manages verified native runtimes/CLIs with explicit versions and trust |
| `.psqlrc`, `.gemrc`, default Go packages | Later: runtime availability, paths and pager dependencies |
| General `.dotfiles/bin` shell helpers | Rewrite individually if useful; exclude originals on Windows |
| `.editorconfig` | Retain; test native line-ending behavior |
| age/sad/dra | Plan same native tools through verified mise/WinGet ownership; ask before unsupported alternatives or custom extraction |
| Neovim distribution external | Pending Windows-only LazyVim at XDG `.config/nvim`; preserve Unix selection |
| Alacritty theme external | Retain upstream theme repository at native RoamingAppData theme path |
| docs/scripts/tests/workflows | Repository-only, never home configuration targets |

The runtime inventory includes neovim, bat, dprint, eza, fd, fzf, fx, gojq, jqp,
ripgrep, node, go, go-jsonnet, jsonnet-bundler, python, kubectl, k9s, kubie, krew,
helm and tanka. Each needs a native package/backend decision; never infer support
for the whole list from mise supporting Windows. Prefer reuse through mise when
its native backend is suitable; otherwise use WinGet if available, or defer that
tool. Bat/fzf must not have two owners.

## External replacement and destination plan

This is the disposition for every current `.chezmoiexternal.toml.tmpl` family.
Disabling a broken Unix entry is only the safety step, not the complete port.
Use verified application lookup paths and manager-owned executable locations;
there is no universal Windows replacement for `~/.local/bin`.

| Current external | Native Windows plan and destination |
| --- | --- |
| `.local/bin/mise` | WinGet `jdx.mise`, with its installed native path verified. Do not also download mise through the Windows external branch. |
| `.config/nvim` cloning `NvChad/NvChad` under an AstroNvim heading | User chose **LazyVim**. Adapt `LazyVim/starter` into `~/.config/nvim` through inherited XDG_CONFIG_HOME; runtime/plugin data belongs to Neovim's native data path, normally `%LOCALAPPDATA%\\nvim-data`, not the versioned config. |
| `.config/alacritty/themes` | Retain `alacritty/alacritty-theme`, under `%APPDATA%\\alacritty\\themes` when Alacritty is enabled. Reference the actual repository member, e.g. an absolute native path ending in `themes\\themes\\<theme>.toml`; verify path resolution rather than assume import-relative behavior. |
| `.oh-my-zsh` and fast-syntax-highlighting/history-substring-search/completions/autosuggestions | No Zsh files on Windows. Minimal Nu uses its native highlighting, history, hints and completions; these are not drop-in plugin equivalents. |
| OMZ ports/git-fetch-merge/git-sync/mkc/async plugins | Omit under the user's minimal-Nu decision. Do not add process-killing, Git push/merge/cleanup or other replacement workflows without asking. |
| `.docker/completions/_docker` and `_docker-compose` | Omit the Zsh scripts. No additional Docker completion layer in minimal Nu. If requested later, ask which CLI variants and native completion provider to support; installing completions does not authorize a Docker engine/runtime. |
| `.local/bin/sad` | Keep sad where feasible: a verified mise/WinGet native package and its owned path. Upstream Windows MSVC ZIPs exist for x64/ARM64; package/backend and archive layout still need verification. Do not use `funzip` or an extensionless Windows target. |
| `.local/bin/dra` | Keep dra through verified native mise/WinGet ownership. Observed upstream Windows x64 MSVC ZIP exists; no ARM64 asset was found in the inspected release. Do not silently emulate it or replace it with another tool. |
| `.local/bin/age` | Keep age through verified native mise/WinGet ownership. Upstream Windows amd64/ARM64 ZIPs exist. Do not use the Unix `.tar.gz` selection. Do not generate/import keys; ask before separately provisioning age-keygen if it is not part of the selected package. |

Neovim configuration is not a forever-refreshing copy of a distribution's mutable
starter. Seed from a reviewed LazyVim starter revision, then own the adapted config
in chezmoi (Windows-selected `dot_config/nvim/` content or shared templates).
Do not let `refreshPeriod` overwrite custom Lua or plugin lockfiles. If retaining
an external for seeding, define an explicit non-destructive, one-time seed contract
first. LazyVim plugins, caches and state are distinct from the managed starter.
Audit chosen LazyVim plugins/extras and native compiler/parser/tool requirements;
automatic plugin installation must not introduce a Bash toolchain. Keep the plain
Nu recovery baseline independent of editor first-run installation.

For binary entries, first verify a suitable native package/backend and exact
identifier, executable name, architecture and PATH. A managed package may supply
additional executables; record those, but do not run configuration/key generation
as a side effect. If neither manager provides a suitable route, **ask the user**
whether to use a verified direct-release external, select another tool, or omit it.
Do not invent a package ID or silently choose custom ZIP extraction. If approved,
verify checksum/provenance, exact archive members and a user-owned native bin
location with explicit PATH management; that external becomes the sole owner.

Any future literal `AppData/Local` and `AppData/Roaming` adapter paths need native
known-folder validation and conflict preservation. They are not used for Nu or
Neovim configuration: inherited XDG_CONFIG_HOME points both at canonical `.config`.
Redirected folders and conflicting XDG values need manual reconciliation, not a
second accidental tree.
Preserve existing Neovim/config/theme modifications; no forced clone/reset/delete
or cleanup of `nvim-data`. Ask about conflicts or cross-platform editor migration.

**Gate:** inspect each external's Windows branch, ensure incompatible lookups never
run, and verify the replacement's actual executable/config/theme discovery. Test
repeat apply, existing modified content, missing dependencies, fresh native editor
startup/health and absence of Unix helper processes. Keep remaining package/backend
questions explicit until answered; native asset availability is not install proof.

## Cross-cutting contracts

### Fail before incorrect config writes

Superseding implementation: no static AppData Nu/Neovim target tree. A pure template
check in `.chezmoiignore` rejects missing/conflicting process XDG_CONFIG_HOME,
unsupported architecture and non-home destination; full/targeted dry-run and diff
failure propagation is covered by portable fixtures. Init checks XDG inline before
prompting. No PowerShell process or dependency is invoked during rendering.

Native preflight checks persistent User/Machine/Process XDG values, known folders,
existing legacy configurations and managed-path reparse points. Run it before
**every documented apply route**. The render guard does not itself inspect registry
or reparse points; do not claim raw apply without preflight covers those cases.
There are no automatically managed AppData configuration adapters in this slice.

An after hook is too late. A before hook alone does not cover dry-run, which does
not execute scripts. `abortEmpty` is not an error. Distinguish “no managed target
writes” from any chezmoi-internal cache/lock/state initialization; do not promise
zero tool-internal writes without measuring them.

### Bootstrap acquisition and package behavior

Publish an immutable reviewed script URL and expected SHA-256/provenance through
a trusted release or maintainer channel before enabling onboarding. Provide a
native PS5.1 download-to-file, `Get-FileHash`, compare, inspect, explicitly execute
procedure; no piped code. The script must be self-contained before Git installation.
Do not fabricate a digest or use a mutable branch as an immutable trust anchor.

Detect missing WinGet versus pending App Installer registration, stale PATH/aliases,
network/source failure and enterprise policy. Microsoft-supported native repair
of WinGet itself is permitted with consent. Mise is an approved dependency manager,
not a workaround for repairing a broken WinGet bootstrap. Do not substitute Scoop
or Chocolatey.
Do not bypass policy or silently elevate the whole deployment.

Inspect exact ID/source/version/architecture/installer type/scope. Prefer supported
user scope, not `--scope user` indiscriminately. Reuse sufficient installations;
normal reconciliation must not upgrade unrelated software. Test `--no-upgrade`
and native exit-code handling, reboot/refusal and transitive dependencies. Check
`$LASTEXITCODE` explicitly in PS5.1. Do not overwrite persistent PATH with `setx`;
new children inherit stale parents, so verify a genuinely fresh Terminal process.

### WinGet/mise ownership and activation

| Dependency class | Recommended owner |
| --- | --- |
| Git, chezmoi, Nushell, Windows Terminal, mise itself | WinGet: stable bootstrap executables independent of project activation |
| Windows GUI apps, optional Alacritty/PowerShell and system-integrated packages | WinGet |
| Versioned Node/Python/Go and other project runtimes | mise with a verified native backend and explicit project versions |
| Portable developer CLIs already in the shared mise inventory | Prefer mise when native support/version management is useful; otherwise WinGet |
| Starship, delta and other session-critical integrations | Choose one owner explicitly; WinGet is a simple default, mise is allowed with a stable global version and startup tests |

This is a selection policy, not proof that every listed candidate works on Windows.
Record owner, exact identifier/backend, version policy, architecture, executable,
config location and validation command. Where supported, record lock/checksum data.
Do not install the same tool through both managers or rely on accidental PATH
precedence. Detect pre-existing duplicates and ask before migration; no automatic
uninstall or removal of unrelated versions.

Native core or other upstream-supported backends are candidates, not blanket
approval: verify Windows artifacts, extraction, install hooks, runtime prerequisites
and subprocesses for each. Reject any route requiring Bash/MSYS/WSL. Do not execute
the whole shared `latest` list, enable unreviewed plugins, or broaden trusted paths
to all of HOME. Review project configuration before trusting it.

After WinGet installs mise, discover the Windows config/data locations and deploy
only the reviewed subset. Run explicit native `mise install` against that selected
configuration; verify versions and repeat-run behavior. Package installation occurs
during an explicit provisioning step, never in template rendering or shell startup.
Normal apply must not silently float versions or trigger unrelated upgrades.

Integrate with Nu using `mise activate nu`'s generated module, not Zsh `eval`.
Upstream documents generation in `env.nu` before `config.nu` parses its `use`.
For this plan, prefer generating/validating the module in the explicit integration
step, then enabling its importer only once the file exists. Refresh it on managed
mise upgrades and handle out-of-band upgrades with an explicit repair command.
Do not add a runtime `if` around a potentially missing `use` and assume it is safe.
Missing mise or a removed integration must have a tested plain-Nu recovery path.

Interactive activation must update native PATH predictably on project changes and
nested shells. Noninteractive automation must not depend on an interactive hook:
use explicit `mise exec -- <command>` with reviewed configuration, or deliberately
configured native shims where appropriate. Test `.exe`/`.cmd` wrappers, arguments,
PATH serialization, project/global precedence and executable resolution from a
fresh Terminal and from standalone PowerShell. Keep bootstrap Nu/Git paths stable.

### Windows Git baseline

- Windows `.gitconfig` is managed automatically and loads `.config/git/windows.inc`
  with conditional work identity/key selection. There is no manual opt-in step.
  No `[credential]` stanza is supplied; never override installed system GCM with cache.
- Preserve existing credential configuration, including user-level settings during
  target conflict resolution. Merely omitting a stanza from a replacement global
  file does not preserve arbitrary pre-existing global-file content.
- Baseline editor: `notepad.exe`; local alternatives remain possible.
- Disable paging with Windows `core.pager = ""` initially. Omit delta settings,
  `interactive.diffFilter`, diffmerge tool stanzas and forced tool selection.
- Omit unsupported helper aliases `fm`, `pr`, `fpr`; keep Git builtin aliases.
- Preserve identity, work include, ignore and existing commit template. Test path
  quoting, LF policy and fsmonitor; omit unverified optional settings on Windows.
- Do not promise an installed merge GUI or Unix-free `git mergetool` internals.
  Baseline commit/diff/merge workflows must not require uninstalled Unix helpers.

### Terminal preservation and Nu startup

Current slice: manual new-profile/default selection in Terminal UI; no automation.
If implementing a fragment later, deploy only an owned UTF-8 fragment under the native Terminal Fragments known-folder
location, with a stable GUID and verified/quoted absolute Nu executable. Back up
existing owned fragment/settings before changing them; do not overwrite conflicts.
Select default profile via UI initially. Fragments alone cannot set root
`defaultProfile`. Inspect startup actions/restored layouts rather than deleting
customizations. Rollback restores only owned changes and respects later user edits.

Do not blindly replace or round-trip Terminal JSONC through PowerShell JSON tools.
Other profiles, comments and unknown settings must survive any future automation.

Observe actual `$nu.config-path`, data/history/autoload directories. Test interactive
startup, not just `nu -c` or `nu -n`. Nu `source`/`use` is parse-sensitive: a runtime
conditional does not make a missing module safe. No startup-time installs/network.
PATH stays native and list-based; test `.exe`, `.cmd`, quoting, Unicode and UNC paths.

## Adversarial review disposition

| Finding | Plan correction |
| --- | --- |
| Darwin script emits shell code on Windows | Explicit fix and audit of every lifecycle output |
| AppData rejection happens after writes | Pre-write rendering guard; full/targeted/dry-run gate |
| Bootstrap script unavailable before Git | Self-contained, verified pre-Git acquisition contract |
| New infrastructure could deploy into home | Explicit scripts/tests/.github target exclusions |
| Git optional dependencies remain reachable | Exact omitted/set Windows Git keys and preservation tests |
| Generic README exposes Unix destructive setup | OS routing before command blocks; separate Windows review/apply |
| First slice has too many mutation mechanisms | Plain Nu baseline; optional generators, JSONC automation and tooling later |

All substantive review findings were accepted. Parent synthesis additionally makes
preservation of pre-existing user-level Git credentials an explicit conflict check.
This historical disposition table itself is not execution evidence; implemented
fixes and still-skipped native gates are recorded in the resume checkpoint above.
The subsequent user-approved mise policy broadens dependency ownership; it does
not relax the reviews' native-only, safe-startup or per-tool validation gates.

## Acceptance and release evidence

Use a disposable native Windows 11 x64 VM/standard-user profile. Hosted Windows CI
is useful but not a substitute for a clean user's WinGet/Store/UAC/Terminal behavior.

- Stock PS5.1 entry, verified bootstrap/tamper rejection, exact package postconditions.
- Missing/pending WinGet, offline/policy failure, UAC refusal, stale PATH and reruns.
- Spaced/Unicode username succeeds; unsupported redirection/conflicting XDG fails before managed
  writes on plain full/targeted apply and dry-run. Inspect reparse points and state.
- Render every changed template and every lifecycle Windows branch; inspect manifest
  for infrastructure, Unix configs, shell scripts and symlinks that must be absent.
- Native `chezmoi diff`, `chezmoi apply --dry-run --verbose`, consented apply and second
  identical apply/dry-run. No unexpected writes, duplicate profile or upgrade.
- Real interactive Nu startup, history across tabs, aliases, Ctrl-C, paste, resizing,
  arguments, PATH, config discovery and default Terminal launch.
- Native Git credentials before/after, commit/editor/diff/merge, work include/template.
- Existing dirty source and target conflicts preserved; explicit rollback tested.
- Isolated macOS/Linux rendering/dry-runs; no Windows targets and no unrelated drift.
- Mise: explicit backend/version installs, project/global switching, trusted and
  untrusted config, repeat provisioning, offline/failed downloads, no duplicate
  WinGet tool ownership, native `mise exec`, Nu activation and missing-module recovery.
  Observe subprocesses to exclude hidden Bash/MSYS dependencies; verify upgrades
  refresh generated integration without prompt-time installs or PATH accumulation.
- Optional tools, ACLs, agent copies, redirected folders and ARM64 get separate gates.

Record redacted versions, commands, manifests/diffs, errors, process evidence and UI
checks. No keys, identity answers or history in committed test artifacts.

## Decisions still needed before implementation/release

Recommended defaults above are not additional user requirements. Confirm target
Windows version/architecture and access to a native test VM; choose tested package
versions/scopes and stable profile GUID. Decide prompt/font/editor/optional terminal
priorities, and select per-tool WinGet/mise ownership, native backends and version
policies. LazyVim and minimal Nushell are selected. Ask before ambiguous external
substitutions, direct-release fallbacks, extra shell workflows, or a cross-platform
Neovim migration. Permission to use mise for dependencies is settled; individual tool
compatibility still needs evidence. Publication needs actual reviewed bootstrap
provenance. The guard's ordering must be proven, not assumed.

## Primary sources and review provenance

Authoritative sources consulted by research/reconciliation; mutable docs and manifest
versions must be rechecked and recorded during implementation:

- [chezmoi Windows](https://www.chezmoi.io/user-guide/machines/windows/)
- [Ignore templates](https://www.chezmoi.io/reference/special-files/chezmoiignore/)
- [Script lifecycle/dry-run](https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/)
- [Template output errors](https://www.chezmoi.io/reference/templates/functions/output/)
- [WinGet](https://learn.microsoft.com/en-us/windows/package-manager/winget/)
- [WinGet install controls](https://learn.microsoft.com/en-us/windows/package-manager/winget/install)
- [WinGet manifests](https://github.com/microsoft/winget-pkgs)
- [Nushell configuration](https://www.nushell.sh/book/configuration.html)
- [Nushell environment](https://www.nushell.sh/book/environment.html)
- [Starship shell integration](https://starship.rs/guide/)
- [Terminal startup](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/startup)
- [Terminal fragments](https://learn.microsoft.com/en-us/windows/terminal/json-fragment-extensions)
- [Alacritty configuration](https://alacritty.org/config-alacritty.html)
- [Alacritty themes](https://github.com/alacritty/alacritty-theme)
- [LazyVim Windows installation](https://www.lazyvim.org/installation)
- [LazyVim starter](https://github.com/LazyVim/starter)
- [Neovim native paths](https://neovim.io/doc/user/starting.html#standard-path)
- [sad native releases](https://github.com/ms-jpq/sad/releases)
- [dra native releases](https://github.com/devmatteini/dra/releases)
- [age native releases](https://github.com/FiloSottile/age/releases)
- [mise installation and Nushell activation](https://mise.jdx.dev/installing-mise.html)
- [mise execution](https://mise.jdx.dev/cli/exec.html)
- [mise asdf constraints](https://mise.jdx.dev/dev-tools/backends/asdf.html)

Research/draft workflow: `81dd2350-7292-4d4a-ac25-2f90dfadfb8b`.
Resumed reviews/reconciliation: `a8b0bca2-1d3f-4162-9867-db8288678805`.
Runtime reviewer: `18999cde-5a44-44bd-b613-83394d828a7b`.
Safety reviewer: `43143495-8884-4aed-ba5b-9f3cc9417f24`.
Reconciliation: `13368993-0568-4133-8fdd-7209b5edeaea`.

Historical research originally added only this planning document. The resumed
implementation now adds the bounded foundation and portable checks described at
the top. No package installation, real home apply or native Windows test has been
performed on the Darwin implementation host.
