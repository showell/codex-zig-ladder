# PR 155 -- Zig plug: emit bit-not

https://github.com/damiant3/Cobblestone/pull/155  (sent 2026-09-22, branch `zig-plug-bit-not` `45269537` off U61, worktree `cobblestone-bitnot`)

Found running U61's changed crypto tests through run-zig. Verified with a patched codexzig built guest-free (U61 codexzig transpiling the branch's subject): 5 of 6 refused programs now match. The battery test is the existing tco-bitop-loop.

## The body sent

The Zig plug has no emitter for `bit-not`, a declared builtin (`Types/Builtins.codex`) that the wasm plug already emits as `(i64.xor x (i64.const -1))`. Any program that reaches SHA-512 (`Foreword Sha512`) refuses to build on the Zig plug with `zig plug: no emitter for bit-not`, which since Update 61's crypto tests includes Ed25519, X25519 and ECDSA P-384.

The change is one entry in the builtin emitter table, beside `bit-and`, `bit-or` and `bit-xor`:

```
ZigBuiltinEmitter { name = "bit-not", emit = \args ctx d ty -> "(~@as(i64, " & ... & "))" },
```

The `@as(i64, ...)` is there because a literal argument reaches zig as a `comptime_int`, which has no width for `~`; every `IntegerTy` is `i64` in this plug (`emit-zig-type`), so the pin changes nothing else.

## The test

The battery already has one: `codex/test/tco-bitop-loop` exercises `bit-not` and passes on bare metal. What it could not do was build through the Zig plug. Measured with the Zig plug built from this branch (the Update 61 transpiler transpiling this branch's plug source natively, then `zig build-exe`), against each test's own `.expected`:

| program | Update 61 | this branch |
|---|---|---|
| `tco-bitop-loop` | build refused: no emitter for bit-not | match |
| `apps/x25519-vector-test` | refused | match |
| `apps/ed25519-sign-test` | refused | match |
| `ecdsa-p384` | refused | match |
| `apps/cdx-binary-test` | refused | match |

`e1000-ulp-entry` also uses `bit-not`; with this change it gets past it and stops at `port-out-32`, a device builtin the Zig plug does not emit, which is expected.

The prelude surface is unchanged (no new prelude part), so `check-zig-prelude-surface` has nothing new to grade.

---
Written by Claude (Anthropic's model) with Steve Howell.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
