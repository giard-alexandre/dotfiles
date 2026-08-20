# Global Agent Guidelines

## Repository instructions

- Before working in a repository, identify its root and read every applicable
  `AGENTS.md` from the repository root down to the current working directory.
- When working in a nested directory, check for a closer `AGENTS.md` and follow
  it for files within that directory's scope.
- If the current agent does not discover `AGENTS.md` automatically, explicitly
  search for and read these files before planning or making changes.
- More specific repository instructions take precedence over these global
  defaults when they do not conflict with higher-priority instructions.

## Documentation

- When a request depends on a library, framework, SDK, API, CLI tool, or cloud
  service, consult current authoritative documentation before answering or
  changing code. Prefer version-appropriate primary sources.
- When Context7 is available, prefer it for library documentation. Otherwise,
  use the documentation or search facilities available to the agent.
- Documentation lookup is not required for refactoring, standalone scripts,
  business-logic debugging, code review, or general programming concepts unless
  the task depends on version-specific behavior.

## Collaboration

- For every non-trivial task containing a concrete, bounded subtask, delegate
  that subtask when agent collaboration is available.
- Give delegated work a clear scope, deliverable, relevant paths or evidence
  requirements, and explicit boundaries.
- Parallelize only independent work. Avoid overlapping writes and assign clear
  ownership when edits could conflict.
- Inspect and reconcile delegated results rather than forwarding them blindly.
  The coordinating agent owns final synthesis, validation, and the response.
