Title: Raytracer: the nearest object is found by its distance, and only its hit is built

Branch: showell/NewRepository `raytracer-nearest-first` (`355e4d42`), two
commits on Update 60 (`9fff850c`): the change (`45bdc217`) and its prose
(`355e4d42`); worktree `cobblestone-rtnearest`. Our `u61-candidate` carries
both on top of PR 149 as `4fbc6e72` and `7b9235e7`.

Read cold before sending. The first read found the code right and the
description wrong in eleven places, all addressed here:
- the first bench used Update 60's camera, which shows almost no sphere;
- the Roc claim was too strong;
- the old walk did not build the hit point; Geometry does, and still does;
- the rule was stated without its `d >= 0.0` guard;
- the winner's intersection runs twice;
- PR 149's scope was understated;
- the verification was thinner than PR 149's;
- the build times, the run record and "How it was found" were imprecise;
- the source prose argued rather than stated.

The evidence (both bench rounds, every run, the scripts) is
`outbound/evidence-raytracer-nearest-first/`.

The send is the text below.

---

*Written by Claude (Anthropic), working with Steve Howell, on his account and at his direction.*

**What changes.** Two commits on Update 60 (`9fff850c`), in the Scene Tracing section of `codex/foreword/game/Raytracer.codex`:

- **`rt-trace`** finds the index of the nearest object with `rt-nearest`, then builds that object's `RtHit` with `rt-intersect-obj`. A ray that meets nothing answers `rt-no-hit`, as before.
- **`rt-nearest`** walks the scene's objects in list order.
  - For each object, `rt-obj-dist` calls `ray3-sphere` or `ray3-plane`, and `rt-hit-dist` reads the hit's `rh3-t`, or -1.0 for a miss.
  - An object becomes the best so far when its distance is non-negative and below the best's, which starts at `rt-no-hit`'s 999999.0.
- **`rt-closest` is removed.** Nothing else in the tree calls it: `raytracer-test` calls `rt-trace`.
- **The section** gains a paragraph stating the rule.

No `.expected` changes.

**Why the same object wins.** `rt-closest` replaced the best when `hit.rt-did-hit` and `hit.rt-dist < best.rt-dist`. Geometry never reports a hit at a negative distance:
- `ray3-plane` answers a miss for t < 0;
- `ray3-sphere-solve` takes the far root when the near one is negative, and misses when both are.

So a hit's distance is non-negative, or +inf or NaN, which fail `<` on both sides, and a miss's -1.0 fails `d >= 0.0`. The comparison is `rt-closest`'s own, strict, so the first of equal distances wins in both walks. Misses, ties, a hit at distance 0, hits at or past 999999.0 (both answer `rt-no-hit`), and an empty scene all come out the same.

**What a ray no longer costs.** For every object a ray hits that is not the nearest, `rt-closest` built an `RtHit`:
- for a sphere, the normal through `rt-normalize` (a subtraction, a `geo-sqrt` and three divisions) and a record holding the material;
- for the floor, the record.

It also carried the best `RtHit` down every step of the walk. Now each object costs its `ray3-sphere` or `ray3-plane` call, which still builds Geometry's `RayHit3` and its point, and one comparison.

The nearest object's intersection runs twice: once in the walk, and once in `rt-intersect-obj`, which stays the one place an `RtHit` is built. The repeat is one Geometry call per ray, and gives the same bits.

**Measured.** A bench outside the tree renders a scene with `rt-render` at 160 × 120 for 30 frames and prints the sum of every pixel; its source is below.
- The scene is `raytracer-test`'s two spheres and light, with a unit floor normal and a camera of field 1000, one sphere moving with the clock.
- Under Update 60's camera that view shows almost no sphere (PR 149). So the bench was bundled from our integration branch, which carries PR 149: its tree before this change (`6e9f9624`) and with it (`4fbc6e72`).
- Seven runs of each side, interleaved.

| `codexzig`, then `zig build-exe` (zig 0.16.0) | build | before | after |
|---|---|---|---|
| `-ODebug` | about 1 s | median 2.036 s, fastest 2.017 | median 1.788 s, fastest 1.747 |
| `-OReleaseFast` | 20 to 21 s | median 0.547 s, fastest 0.542 | median 0.484 s, fastest 0.475 |

Both sides print `checksum 2399541620792`.

On Update 60's own tree the same bench sees almost only floor and misses, and there the medians go from 2.22 to 1.71 s (Debug) and from 0.56 to 0.45 s (ReleaseFast).

The same scene in our Roc port of this chapter (Codex emitted as Roc) prints the same sum. There the change moves the whole render by no more than 2% under either of Roc's backends. Finding each pixel's nearest hit alone is 8% faster under LLVM (medians 0.036 to 0.033 s) and about the same under Roc's development backend.

<details>
<summary>The bench, <code>ray-bench.codex</code></summary>

```
Chapter: Ray Bench
  cites Foreword chapter Console
  cites Game chapter Raytracer
  cites Game chapter Color
  cites Game chapter Rasterizer
  cites Math chapter Quaternion
  cites Math chapter Cordic

 raytrace-on-screen's scene and camera, traced at 160 x 120 for 30 frames
 with the clock stepping 100 ms a frame, and the sum of every pixel printed.

 We say:

Section: Scene

  scene-at : Integer -> RtScene
  scene-at (t) =
    let bob = real-from-int (600 * cordic-sin t / 1000)
    in let s1 = ObjSphere (RtSphere { rt-center = vec3-new 0.0 bob 5000.0, rt-radius = 1000.0, rt-mat = mat-shiny rgb-red })
    in let s2 = ObjSphere (RtSphere { rt-center = vec3-new 2000.0 0.0 6000.0, rt-radius = 1500.0, rt-mat = mat-matte rgb-green })
    in let floor = ObjPlane (RtPlane { rt-point = vec3-new 0.0 (0.0 - 1000.0) 0.0, rt-normal = vec3-new 0.0 1.0 0.0, rt-mat = mat-matte (rgb 128 128 128) })
    in let light = vec3-new (0.0 - 3000.0) 5000.0 2000.0
    in let sc = scene-new light rgb-white 200 (rgb 32 32 64)
    in scene-add (scene-add (scene-add sc s1) s2) floor

  camera : RtCamera = rt-camera-new (vec3-new 0.0 0.0 0.0) 1000

Section: Run

  pixel-sum : List Integer, Integer, Integer, Integer -> Integer
  pixel-sum (px) (i) (n) (acc) =
    if i >= n then acc
    else pixel-sum px (i + 1) n (acc + list-at px i)

  frames : Integer, Integer, Integer -> Integer
  frames (n) (t) (acc) =
    if n <= 0 then acc
    else let fb = rt-render (scene-at t) camera 160 120
    in frames (n - 1) (t + 100) (acc + pixel-sum (fb.fb-pixels) 0 (list-length (fb.fb-pixels)) 0)

Section: Entry

  opening : [Console] Nothing = act
    print-line-uni ("checksum " & show (frames 30 100 0))
  end
```

</details>

**Verified.** Each unit was bundled from Update 60 and from this branch, and each match is against Update 60's `.expected`, which this branch leaves as it is.

| unit | arm | Update 60 | this branch |
|---|---|---|---|
| `raytracer-test` | `codexzig`, then `zig build-exe`, run | match | match |
| `raytracer-test` | `codexir`, then the wasm plug, run | match | match |
| `raytracer-test` | `codexrun` | all 5 lines | all 5 lines |
| `forewords/game-raytracer` | `codexzig`, then `zig build-exe`, run | match | match |
| `forewords/game-raytracer` | `codexrun` | match | match |
| `apps/foreword-all-compile` | `codexrun` | match | match |

The wasm arm ran on the first commit; the second changes prose only.

Our integration branch carries this change and PR 149 together. There, the Roc port's picture of the scene is pixel for pixel what it was, and `raytracer-test` passes.

**Not verified.** The Cobblestone battery, codex-vm, and x86 on bare metal.

**Beside PR 149.** PR 149 changes `rt-shade`, `rt-pixel-ray` and the chapter's opening prose, and `raytracer-test.codex` with its `.expected`. `git merge-tree` of the two branches on Update 60 is clean.

**A name used twice.** `apps/gpushow/kernels/RaytraceKernel.codex` also defines `rt-nearest`. Nothing cites that chapter, and it cites only the Gpu chapters, so no unit reaches both.

**The tools.**
- `codexzig` is Update 60's compiler with its zig plug, built as a native binary from `9fff850c`.
- `codexir` is Update 60's compiler to IR, built the same way. The wasm arm feeds its IR to Update 60's `WasmPlug.codex`.
- `codexrun` is the interpreter in our own Rust Codex compiler, which shares no code with Cobblestone's.
- Units are bundled with our resolver, which reads the checkout's `build/quire-map.ps1`.

**How it was found.** Our Roc port draws this scene in a browser. A profile of its wasm in Node (`node --cpu-prof` over a `--debug` build) put 17% of a frame in `rt-closest`, and 22% in `rt-intersect-obj`, which includes the sphere and plane tests this change keeps. The port's LIR showed each step of the walk taking the best hit apart into its fields and building it again.
