# PR 159 -- Zig plug: fail raises where it is called, not wherever the name appears

https://github.com/damiant3/Cobblestone/pull/159  (sent 2026-10-19, branch `zig-plug-fail-local` `b70464a6` off U70, on showell/NewRepository)

Found processing U70 (U70.log): the compiler no longer builds through the Zig plug.

## The body sent


Branch `zig-plug-fail-local` (commit `b70464a6`), one commit on Update 70 (`fd7a9a38`).
Touches only `codex/plugs/zig/ZigEmitter.codex`, Section: Failure.

## What breaks

At Update 70 the compiler can no longer be built through the Zig plug. Two
symptoms, one cause:

- `opening() catch cx_fail_exit()`: use of undeclared identifier `cx_fail_exit`.
  The entry wrapper calls it, but the prelude shake never keeps it, because
  nothing references `cx_raise`.
- `expected type 'T', found 'anyerror!T'` in the `BuiltinSpec` emit table.
  Lifted lambdas return error unions through closure wrappers that do not
  catch them.

## Why

`zig-fails` counts every `IrName "fail"` as a raise. The x86-64 emitter binds
that name itself: `emit-try (st) (max) (body) (fb) (fail)` in
`Emit/X86_64.codex`, where it is a `List IRActStmt`. So `emit-try`, and every
definition that reaches it up to `opening`, lands in the failing set of a
program that contains no `fail` at all. In the compiler's own zig that is 388
`anyerror!` signatures and no `cx_raise` anywhere.

## The fix

`fail` counts as a raise only as the callee of an `IrApply`. That is the only
place the emitter lowers it: the builtin emitter fires on an application. A
bare name `fail` is a value, which is what the compiler's parameter is. A
failing user definition is still matched by name, as before.

The wasm plug already avoids this. `wat-defs-call-name` skips a definition
whose parameters bind the name.

## Checked

- The compiler (codexir, built through the Zig plug under QEMU) builds and
  runs, and cobblestone-qemu's five checks are green.
- The Zig transpiler's fixed point holds byte for byte (3,387,089 bytes of
  zig), and its arith sample matches.
- On 128 frozen programs, the zig, wasm and Rust arms all agree.

Not covered, and left as it was: a failing global that a local of the same name
shadows is still matched by name.
