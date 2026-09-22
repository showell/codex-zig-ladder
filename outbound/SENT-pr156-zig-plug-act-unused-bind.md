# PR 156 -- Zig plug: an unused bind in an act is silenced

https://github.com/damiant3/Cobblestone/pull/156  (sent 2026-09-22, branch `zig-plug-act-unused-bind` `8af2b7a4` off U61, worktree `cobblestone-actbind`)

Found through key-manager-test; both act emitters (emit-zig-act-stmts and emit-zig-act-tail). New test codex/test/act-unused-bind, verified before/after on the Zig plug and on codexrun; not run on bare metal.

## The body sent

Inside an `act`, `x <- e` whose `x` no later statement reads is emitted by the Zig plug as `const x = e;`, and zig refuses an unused local constant. The `IrLet` arms already handle the same case (our PR 138: bind, then `_ = x;`); the two act-statement emitters, `emit-zig-act-stmts` and its tail-position twin `emit-zig-act-tail`, never got the rule. This adds it to both, using `zig-occurs-stmts` over the statements that follow:

```
else if zig-occurs-stmts stmts (i + 1) name then "const x = e; "
else "const x = e; _ = x; "
```

## The test

`codex/test/act-unused-bind` (new) is the smallest program that shows it:

```
  noisy : Integer -> [Console] Integer
  noisy (n) = act
    print-line-uni ("noisy " & show n)
    n
  end

  opening : [Console] Nothing
  opening = act
    w <- noisy 1
    print-line-uni "after"
  end
```

Expected output `noisy 1` / `after`. The effect still runs; only the unused name is discarded.

| | Update 61 Zig plug | this branch's Zig plug | our Rust interpreter |
|---|---|---|---|
| `act-unused-bind` | build refused: `unused local constant` | match | match |

Found through `apps/key-manager-test`, whose FAT16 chain (`fat16-write-chain`, `w <- fat16-write-cluster ...`) has this shape; that test also needs `block-read-sector`, a device builtin, so it cannot run on the Zig plug either way. We have not run the new test on bare metal; the program is ordinary and its expected output is what our interpreter and the fixed Zig plug both print.

---
Written by Claude (Anthropic's model) with Steve Howell.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
