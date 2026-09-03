# The WGSL plug emits shaders Firefox rejects, in three distinct ways

*Draft, not yet sent. Written by Claude, on Steve Howell's account and at his
direction.*

**STATE, 2026-09-03 evening. The body below was written when only cause 1 was
fixed and is superseded on that point.** All three causes now have an emitter
change on branch `wgsl-firefox` (`08c6a501`), and the plug was BUILT and RUN:

- **cause 1 (terminator) -- fixed and confirmed in real plug output.**
- **cause 3 (hex float literal) -- fixed and confirmed in real plug output.**
- **cause 2 (storage pointer) -- INCOMPLETE, and the plug run is what found it.**
  Dropping the parameter works; naming the global does not. Helpers are emitted
  by `wgsl-topo-pass` at MODULE level, where `ctx.kprefix` is `""`, so keeping
  the prefix kept nothing: the signature loses the parameter while the body
  still writes `(*tex)[ti]`. `wgsl-reachable` already walks kernel to callee to
  build the emit set, so the same walk can record an OWNER PREFIX per helper.
  Not yet written.

Do not send until cause 2 is finished and the kernels are regenerated. The
numbers in the body are from a mechanical transformation of the .wgsl files, not
from the plug; the plug has since run and disagreed.

---

## The shape

Chrome uses **Tint**; Firefox uses **naga**. Tint is the more permissive of the
two, so a generated shader that is accepted everywhere it is tested and refused
in Firefox is the expected direction of failure -- and that is what
`gpushow/web/reflect.html` does.

**Measured with `naga` v30.0.1 over every `.wgsl` in the tree at Update 55
(`675a0775`): 19 pass, 25 fail.** That is 57 per cent of the corpus, and it is
three separate causes rather than one.

| # | cause | files | fix size |
|---|---|---|---|
| 1 | a tail-call `loop` leaves the function with no terminator | 25 (31 functions) | ~4 lines |
| 2 | `ptr<storage, ...>` as a user function parameter | 7 | real work |
| 3 | `bitcast` in a constant expression | 4 | unknown |

Fixing 1 alone takes the tree from 19 passing to 33.

## 1. The tail-call loop has no terminator

`wgsl-emit-loop-helper` (`WgslEmitter.codex`) closes with `"  }\n}\n\n"` -- the
loop, then the function, with nothing between. For a tail-recursive Codex
definition every path inside the loop either returns or continues, so control
cannot reach the end and no `break` is emitted:

```wgsl
fn rf_nearest(...) -> i32 {
  var ox = ox__a; ...
  loop {
    if ((i >= rf_nobj)) { return best_id; }
    else { ... if ((take == 1)) { ...; continue; } else { ...; continue; } }
  }
}
```

Tint's reachability analysis sees that the end is unreachable. naga does not: it
supplies an implicit `return;`, which then disagrees with the declared type.

```
error: Function [11] 'rf_nearest' is invalid
  = The `return` expression None does not match the declared return type Some([0])
```

**The fix is an unreachable return of the zero value after the loop.** The type
language here is two types wide -- `wgsl-ty-text (ty) = if wgsl-is-real ty then
"f32" else "i32"` -- so it is one helper and one line at the emission site:

```
  wgsl-zero-text : CodexType -> Text
  wgsl-zero-text (ty) = if wgsl-is-real ty then "0.0" else "0"
```

```
    & "  }\n  return " & wgsl-zero-text (d.type-val) & ";\n}\n\n"
```

## 2. A storage pointer cannot be a function parameter

```
fn earth_shade_pixel(framebuf : ptr<storage, array<i32>, read_write>, ...) -> i32
```
```
error: Function [2] 'earth_shade_pixel' is invalid
  = Argument 'framebuf' at index 0 is a pointer of space Storage ..., which can't be passed
```

WGSL restricts pointer parameters to the `function`, `private` and `workgroup`
address spaces; `storage` and `uniform` need the `unrestricted_pointer_parameters`
language extension. Tint implements it, naga does not.

This is the one that breaks `GlobeKernels.wgsl`, and it is not a small fix: the
emitter would have to pass indices rather than pointers, or inline those
helpers. Seven files.

## 3. `bitcast` is not a const-expression in naga

```
error: Not implemented as constant expression: bitcast built-in function
```

The plug spells float literals as `bitcast<f32>(1039516303u)`, which is exact
and readable, and in a `const` position naga refuses it. Four files. We have not
investigated whether the const position is avoidable.

## What we did and did not validate

**Did.**
- `naga` v30.0.1 reproduces the reported browser error byte for byte, offline,
  in milliseconds. Every count above is naga's, over the whole tree.
- Fix 1 was applied mechanically to all 25 failing files and re-validated:
  14 of them pass afterwards, 11 fail on causes 2 and 3.
- The patched tree was served and **eye-tested in Firefox**, the browser that
  reported the bug. `reflect.html` renders. That is the end-to-end confirmation,
  not just a validator agreeing with a validator.

**Did not.**
- We did NOT apply the fix to `WgslEmitter.codex` and regenerate the kernels
  through the plug. The 25 patched files were edited directly, so what is proven
  is that the OUTPUT shape is right, not that the proposed emitter edit produces
  exactly it.
- We have not run the wgsl plug's own gate (`plugs/wgsl/run.ps1`), and we do not
  test non-zig plugs as a rule.
- Causes 2 and 3 are diagnosed and sized but not fixed, and we have not checked
  whether Tint accepts them by extension or by leniency.
- No claim about which naga version Firefox ships; v30.0.1 is what we measured.

## Why it is worth a gate, not just a fix

`naga` is a Rust binary that validates a `.wgsl` in milliseconds with no browser
and no GPU. Running it over the kernels in CI would have caught all three of
these at the commit that introduced them, and it is the only Firefox-shaped
oracle available offline. We are happy to send that as a separate change.
