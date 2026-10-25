---
name: stage-commit-push
description: Review unstaged and untracked files, collect a per-file disposition, commit the selected index, push origin main, and optionally run the project build.
---

# Stage, commit, push, and optionally build

Run this workflow only when the user explicitly asks to use it or asks you to
complete this commit-and-push workflow. Do not trigger publishing just because
the skill is available.

## Resolve unstaged files

Inspect the repository with `git status --short --untracked-files=all`. Include
tracked files with unstaged changes and untracked, non-ignored files. Expand
untracked directories to their individual files so the user can decide for
each file. Do not treat already staged changes as unstaged; they are already
part of the index and will be included in the commit.

For every unstaged or untracked file, ask the user to choose one action:

1. **Delete it** — remove only that path; use `git rm -- <path>` for a tracked
   file so its deletion is staged. If Git refuses because the file has local
   changes, the user's explicit delete choice permits `git rm -f -- <path>`.
2. **Keep it for later** — leave it in the working tree and leave its unstaged
   changes out of this commit. If it also has staged changes, those staged
   changes remain in the index.
3. **Keep it and ignore it** — retain the working file and add a narrow,
   path-specific `.gitignore` entry. For a tracked file, explain that Git
   ignores do not stop tracking: use `git rm --cached -- <path>` to remove it
   from the index while leaving the working copy in place, and stage that
   removal. If Git refuses because the index has changes, use
   `git rm --cached -f -- <path>`; this still leaves the working file intact.
4. **Stage and track it** — run `git add -- <path>` to include the file in the
   index (and begin tracking it if it was untracked).

Use the structured choice interface when available. In Plan mode, use its
choice prompt for the file decisions. If that interface is unavailable, ask in
chat with the same four labeled choices. You may group several file decisions
in one prompt, but identify every path and wait for all choices before making
changes. Do not infer a choice from a filename or file contents.

Apply only the selected actions. Preserve existing `.gitignore` rules and add
the narrowest suitable entry for each ignore choice. Do not use a blanket
`git add -A`, since that could stage files the user chose to keep for later.
After resolving choices, stage any `.gitignore` edits and any other explicitly
selected files that are not yet staged. Recheck `git status` and inspect
`git diff --cached` so the final index is clear. Tell the user that the commit
will include all pre-existing staged changes, plus changes selected for
staging and any staged deletions or ignore-rule updates.

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
