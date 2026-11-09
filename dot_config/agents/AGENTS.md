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

## Worktrees and terminal workspaces

- Use Worktrunk (`wt`, or the `worktrunk` tool when available) to create,
  switch, list, merge, and remove Git worktrees. Do not use raw
  `git worktree` commands unless Worktrunk cannot perform the operation.
- Create a new worktree for isolated or parallel work (e.g. separate branches
  or concurrent agents) instead of stashing or switching branches in place.
- When running inside Herdr (`HERDR_ENV=1`), use Herdr when the user asks you
  to orchestrate or control multiple panes, tabs, workspaces, or other agents,
  or otherwise explicitly requests Herdr. Do not reach for Herdr merely because
  a task could benefit from a background terminal or parallel work.
- When running inside Herdr and you create a worktree, add it to a Herdr
  workspace when appropriate (e.g. while orchestrating multiple worktrees or
  agents, or when the user will want to work in or inspect it). Prefer one
  Herdr workspace per worktree.
- Close only the Herdr panes you created once they are no longer needed, and
  never close the calling pane or panes created by the user or other agents.

## PR reviews

When asked to review a pull request:

- Before posting anything, ask the user whether to post findings to the PR
  now or only show them locally.
- When posting, attach each finding as an inline comment on the relevant
  lines; reserve the review body for findings with no specific location and
  an overall summary.
- Submit the review as **Request changes** when any finding should block
  merging (bugs, correctness, security, or significant design problems);
  otherwise submit it as **Approve**.
- On a re-review, check each of your earlier review threads against the
  current code and resolve every thread whose issue has been addressed.

@RTK.md
