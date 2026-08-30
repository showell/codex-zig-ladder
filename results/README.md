# Comparison results

One directory per before-and-after, written by `compare_arms.py`. **The result
is the deliverable, not the sandbox.**

Before 2026-08-30 a finished comparison left a log inside a run directory that
`BOX.md` says to delete, and its numbers reached a PR body by being retyped --
twice on that day, once wrongly. Nothing recorded which two trees a verdict was
about, which programs were swept, or what the natives were built from, in one
place a reader could check.

Each directory holds:

- `result.md` -- the readable answer. Every moved verdict and every differing
  file **by name**. Nothing truncated: a report that samples is how a sweep that
  touched nothing got read as a sweep that found nothing.
- `result.json` -- the same, machine-readable, with the full provenance block.
- `base-natives.log`, `head-natives.log`, `base-corpus.log`, `head-corpus.log`
  -- what each arm actually did.

The directory name is `<head>-vs-<base>-<scope>-<hash>`, where the hash is over
(base sha, head sha, scope). **Identity is content, not a timestamp**, so the
same comparison is recognisably the same run and re-running refuses instead of
quietly making a second copy under a new name.

Sandboxes are retired when a run succeeds and kept when it fails, which is the
only time anyone wants them.
