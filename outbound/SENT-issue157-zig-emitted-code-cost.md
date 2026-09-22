# Issue 157 -- the Zig plug's emitted-code cost, as the crypto tests show it

https://github.com/damiant3/Cobblestone/issues/157  (sent 2026-09-22, against U61 `3af67f99`)

Steve's framing: crypto in Codex-emitted Zig is not a use case; the point is what crypto reveals about the emitter in general. A measurement report, no change requested. Key refinement found before sending: upstream's plugs-backlog records that riscv's memoised nullary defs broke real-cert (list-set-at writes in place into sha256-h0's list), so rebuilding per reference is REQUIRED for correctness -- the report says so and does not ask for memoisation. Evidence: outbound/evidence-zig-constant-per-reference/.

## The text sent

We ran Update 61's new crypto tests through the Zig plug (all correct where they build; PRs 155 and 156 cover the two that did not). They are the most allocation-heavy programs in the tree, so they make a good lens on what emitted Zig costs in general. This is a measurement report, not a request to change anything: three observations, one convenient reproducer, and what we did not measure.

## 1. A constant is rebuilt, and its memory kept, at every reference

A zero-parameter definition compiles to a function ("constants compile to nullary functions, so the reference must call"), so naming a constant list allocates a fresh copy every time. Reproducer -- a 64-entry table read a million times:

```
Chapter: ConstTable
  cites Foreword chapter Console

Section: Body

  table : List Integer = [1, 2, 3, ..., 64]

  sum-by-name : Integer, Integer -> Integer
  sum-by-name (i) (acc) =
   if i >= 1000000 then acc
   else sum-by-name (i + 1) (acc + list-at table (bit-and i 63))

  opening : [Console] Nothing
  opening = act
    print-line-uni (show (sum-by-name 0 0))
  end
```

and the same program with the table passed down once (`sum-bound table 0 0`, reading `list-at t ...`). Both print `32500000`. Update 61's Zig plug (built natively from `3af67f99`), zig 0.16.0:

| | build | time | peak RSS | minor faults |
|---|---|---|---|---|
| named at every read | Debug | 0.59 s | 525,312 KB | 131,037 |
| named at every read | ReleaseSafe | 0.36 s | 524,288 KB | 131,018 |
| bound once | Debug | 0.00 s | 1,920 KB | 177 |
| bound once | ReleaseSafe | 0.00 s | 896 KB | 159 |

512 MB is exactly one million copies of 64 eight-byte elements: nothing reclaims them, so a long enough loop that names a constant table runs out of memory. The time is almost all kernel page-faulting that fresh memory (ReleaseFast is no faster, 0.354 s).

We are not suggesting memoisation. `plugs-backlog.md` records why riscv's memoised zero-parameter defs broke `real-cert`: `list-set-at` writes in place, `sha256-compress` writes into the list it gets from `sha256-h0`, so a shared constant is a corrupted constant. Rebuilding per reference is what keeps that correct. Sharing would be safe only for a constant nothing writes (`sha256-k` is read-only; `sha256-h0` is not), which is a question the plug cannot currently answer.

In the crypto it shows as `sha256-k`, SHA-256's 64 round constants, rebuilt once per compression. PBKDF2 survives the memory side only because it wraps every round in `__heap-save` / `__heap-restore`.

## 2. Safe builds poison every allocation

Emitted lists grow through `std.ArrayList` and so through `std.mem.Allocator`, whose `alloc` fills fresh memory with `0xAA` in Debug and ReleaseSafe. On `apps/vault-crypto-test` (PBKDF2 at 100,000 iterations, several derivations), ReleaseSafe, `perf` with call graphs:

| where | share of the run |
|---|---|
| SHA-256 arithmetic (inlined) | 52% |
| `memset` -- the poisoning -- of which: | 30% |
| &nbsp;&nbsp;`hash-words-to-bytes`: 32 bytes built by `acc & [4 bytes]` per word | ~11% |
| &nbsp;&nbsp;`sha256-k` rebuilt per compression (item 1) | ~9% |
| &nbsp;&nbsp;other concatenation, e.g. `ipad & message` | ~6% |

So in safe builds an allocation costs its size twice, once to poison and once to fill. Whether lists could come straight from the plug's bump allocator, which already exists (`cx_bump_alloc`), rather than through the `Allocator` interface, is your call; we have not tried it.

## 3. Trapping arithmetic ties the build mode

`emit-zig-binary` emits plain `+ - *` for a trapping Integer and relies on Zig's runtime safety checks for COMPILER-36's traps. That is correct, and it means ReleaseFast is not a legitimate build of emitted Codex: it would turn a trap into undefined behaviour. ReleaseSafe is the fastest mode that keeps the language's meaning. On the vault test: Debug 61.8 s, ReleaseSafe 3.97 s, ReleaseFast 2.37 s, all with identical output.

A small prose point beside it: the comment above `zig-is-real-type` (`ZigEmitter.codex:603`) still says "Integer arithmetic wraps ... the integer rows carry the wrapping forms", which `zig-bin-op-plain` and the note at `:1359` contradict.

## Not measured

Bare metal, and any other plug. None of this says the crypto is slow where you run it.

Reproducers and numbers: https://github.com/showell/codex-zig-ladder/tree/master/outbound/evidence-zig-constant-per-reference

---
Written by Claude (Anthropic's model) with Steve Howell.
