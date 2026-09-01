# Comment on issue 97: we are not closing the zig side after all

Posted 2026-09-01 as a comment on
https://github.com/damiant3/Cobblestone/issues/97.

Retracts one sentence from the issue body. Steve's call: priorities moved, the
zig half is not queued, and their agents cover their side better than we can
from outside. Nothing about the fix-location argument changes.

---

*Comment written by Claude, on Steve Howell's account and at his direction.*

Retracting one line from the issue above -- **"Closing the zig side of the
recursive helper is ours to do, and we expect to."** We are not going to. Steve
has moved us onto other work and this is not queued behind anything; treating
it as ours would just park it.

Nothing else in the report changes, and the half that was always worth more is
the half we were not going to write anyway: the recursive-sum helper is
synthesised in `Emit/X86_64.codex`, **below the wire**, so arm64 answers `ne`,
riscv is unmeasured, and the zig plug compares pointers. Hoisting it into
lowering beside `deriving Eq` fixes all of them in one place.

One more witness since we filed, in case it is useful to whoever picks this up.
Over 326 corpus programs compiled **and executed** through the zig plug and
diffed against hand-verified expectations, `recursive-eq` is the single
`differ` in the run:

    want  eq ne eq eq ne ...
    got   ne ne ne ne ne ...

The probe is in the issue body (`findings/probe-recursive-eq.codex`); it is
five rows and the two that agree are the diagnosis, not noise.

Leaving it with you.
