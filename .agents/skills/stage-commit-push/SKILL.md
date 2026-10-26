---
name: stage-commit-push
description: Stage tracked changes automatically, collect choices for untracked files, commit, push origin main, and optionally run the project build.
---

# Stage, commit, push, and optionally build

Run this workflow only when the user explicitly asks to use it or asks you to
complete this commit-and-push workflow. Do not trigger publishing just because
the skill is available.

## Stage tracked changes and resolve untracked files

Inspect the repository with `git status --short --untracked-files=all`.
Automatically stage all tracked modifications and deletions with `git add -u`,
except any paths the user explicitly asked to exclude. If there are exclusions,
stage only the other tracked paths with `git add -- <path>`. Do not ask which
tracked files to stage. Preserve pre-existing staged changes in the index.

Expand untracked, non-ignored directories to individual files. Ask for a choice
only for each untracked file:

1. **Delete it** — remove only that untracked path.
2. **Keep it for later** — leave it untracked in the working tree and out of
   this commit.
3. **Keep it and ignore it** — retain the working file and add a narrow,
   path-specific `.gitignore` entry.
4. **Stage and track it** — run `git add -- <path>` to include the file in the
   index (and begin tracking it if it was untracked).

Use the structured choice interface when available. In Plan mode, use its
choice prompt for the file decisions. If that interface is unavailable, ask in
chat with the same four labeled choices. You may group several file decisions
in one prompt, but identify every untracked path and wait for all choices before
acting on untracked files. Do not infer a choice from a filename or file contents.

For untracked files, apply only the selected actions. Preserve existing
`.gitignore` rules and add the narrowest suitable entry for each ignore choice.
Do not use a blanket
`git add -A`, since that could stage files the user chose to keep for later.
After resolving choices, stage any `.gitignore` edits and any other explicitly
selected files that are not yet staged. Recheck `git status` and inspect
`git diff --cached` so the final index is clear. Tell the user that the commit
will include all pre-existing staged changes, tracked modifications and
deletions (except explicit exclusions), selected untracked files and any
ignore-rule updates.

## Commit

If the index has changes, write a specific commit message based on the staged
diff. Follow the 50/72 convention: keep the subject at or below 50 characters,
leave a blank line, and wrap body text at 72 columns. Make the body usefully
verbose by describing the main changes and their purpose; do not invent details
that are not supported by the diff. Commit the index with that message.

If there is nothing to commit, report that clearly and do not create an empty
commit. Continue to the requested push step.

## Push

After the commit step, run exactly `git push origin main`, from the repository
root and outside the sandbox using the available escalation mechanism. Use the
tool's required approval prompt for unsandboxed execution. Do not force-push or
rewrite history. If the push fails, report the error and stop; do not start the
build step.

## Optional build

Only after a successful push, ask whether the user wants to run
`uv run build.py`. Prefer the structured choice interface when available and
otherwise ask in chat. If accepted, run exactly `uv run build.py` from the
repository root and outside the sandbox using the escalation mechanism and its
required approval prompt. If declined, finish without running it.
