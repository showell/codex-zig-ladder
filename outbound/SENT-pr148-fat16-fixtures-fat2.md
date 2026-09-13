Title: fat16 test fixtures: the second FAT matches the first
URL: https://github.com/damiant3/Cobblestone/pull/148

Branch: showell/NewRepository `fat16-fixtures-fat2-reserved` (`fc98330e`),
one commit on Update 60 (`9fff850c`); worktree `cobblestone-fat2`.

How it was found: the Roc machine's native platform wrote a file onto a copy
of `fat16-write.disk`, and `fsck.fat` on the result said the FATs differ. They
differed before the write. Essay: `:9100/notes/roc-machine-emulator.md`, step 4.

The description was read cold before sending (every byte, offset and history
claim confirmed); the send is the revised text below.

---

*Written by Claude, working with Steve Howell, on his account and at his
direction.*

The eleven `codex/test/fat16-*.disk` fixtures, bytes only, no source. In each
the second FAT now equals the first:

- all eleven: FAT2 reserved entries 0 and 1 were zero where FAT1 holds
  `0xFFF8`/`0xFFFF`; four bytes per file at 1,110,528;
- `fat16-cycle-guard.disk`: its `2 -> 3 -> 2` cycle was in FAT1 only though
  the test's prose and `docs/ExaminersAssay.md` say "in both FAT copies"; four
  more bytes at 1,110,532.

Why: `fsck.fat` 4.2 reports `FATs differ` on all eleven untouched ESPs.
`build/build-img.ps1` wrote the reserved entries to FAT1 only before
`faf1c639` (Update 35), which brought in `Set-Fat`; six of the fixtures first
appear in that same commit, `fat16-longname.disk` was added in `58b08c38`.

Verified: `cmp -l` (4 bytes per file, 8 in cycle-guard); fsck.fat before and
after (ten clean, cycle-guard only its designed defect); by source no verdict
reads the entries (`fat16-cluster-ok` rejects clusters below 2,
`fat16-next-cluster` reads FAT1, `fat16-alloc` reads FAT2 only for the
clusters it allocates); `fat16-write-fat-copies` can carry the entries through
on a write below cluster 256, and no fixture has a free cluster there (freeing
a low chain not checked); the Roc port of Fat16 over a model of codex-vm's IDE
disk gives the same outcome for all eleven on patched and original fixtures.
Not run: the Cobblestone battery, codex-vm. Risks stated: a whole-file hash
would move (none found); if the cycle belongs in FAT1 only, drop that hunk and
change the prose.
