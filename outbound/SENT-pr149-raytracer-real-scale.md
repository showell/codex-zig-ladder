Title: Raytracer: shading and the camera in the units of Real geometry
URL: https://github.com/damiant3/Cobblestone/pull/149

Branch: showell/NewRepository `raytracer-real-scale` (`372b2a0c`), two commits
on Update 60 (`9fff850c`); worktree `cobblestone-raytracer`.

How it was found: roc-apps' framebuffer platform drew raytracer-test's scene
(`framebuffer/demos/raytrace-on-screen.codex`). The spheres were flat whatever
the light did, and at the test's field of view the red sphere was one pixel.

The description was read cold before sending by a fresh agent given the
repositories. It found eight claims wrong or imprecise and nine gaps, all
addressed:
- the Integer-era reference is Update 23, Update 26's parent;
- in Update 60 the floor saturates through the specular term, not the diffuse;
- the old 162's shaded point lies past the far wall;
- the foreword tests had since been run.

The send is the text below.

---

*Written by Claude (Anthropic), working with Steve Howell, on his account and at his direction.*

**What changes.** Two commits on Update 60 (`9fff850c`):

- **`rt-shade`:** `diff-contrib` and `spec-contrib` no longer divide by `1000.0`. `mat-diffuse` and `mat-specular` are thousandths and the terms they multiply are at most 1, so the product is already in the thousandths that `rt-ambient` and `rgb-scale` use.
- **`rt-pixel-ray`:** `half-fov` divides `cam-fov` by `2000.0`, not `2.0`.
  - The Integer field of view is read as thousandths of the image's height at a forward distance of 1; 1000 is about 53° vertically.
  - `rt-camera-new` keeps its signature, but its field value changes meaning: a caller outside this tree that passes 1 for a narrow view now passes 1000.
- **The chapter's prose** says which values are thousandths, what the field of view measures, and that normals are unit length.
- **`raytracer-test`:** the floor's normal is `vec3-new 0.0 1.0 0.0`, not `0.0 1000.0 0.0`.
- **`raytracer-test.expected`:** `color=rgb(51,0,0)` becomes `rgb(92,0,0)`, and `pixels=192 bg=111 hit=81` becomes `bg=82 hit=110`.

**Why.** Update 26 (`8001c8ee`; the history has two commits of that title, and this is the one whose parent is Update 23, `ccce2b31`) made Raytracer's geometry Real.

Before it, Quaternion's `vec3-dot` and `vec3-scale` divided by `quat-scale` (1000). `rt-normalize` returned vectors 1000 long, and `rt-pixel-ray` built its direction as `(nx * aspect / 1000, ny, 1000)`. The conversion took that scale out of `vec3-dot` and `vec3-scale`, `rt-normalize`, `aspect`, `rt-shade`'s two `vec3-scale … (0 - 1000)`, the power loop (`rt-pow-int` became `rt-pow-real`) and the forward reach. It left the scale in three places:

1. **`rt-shade`'s `/ 1000.0`.** For a unit normal the diffuse term is at most 0.8 (matte) and the specular at most 0.7 (shiny), against an ambient of 200. A sphere is therefore lit at 200 or 201 thousandths wherever the light stands, which for the test's 255-valued channels is 51. `raytracer-test`'s `rgb(51,0,0)` is that.

2. **`rt-pixel-ray`'s half field of view of 500 against a forward reach of 1.** A ray reaches up to 500 times forward vertically, and about 667 times horizontally at 16 × 12, so the camera sees nearly half the sphere of directions. In the test's render the red sphere is 1 pixel of 192 and the green sphere none (table below).

3. **`raytracer-test`'s floor normal,** a unit vector in the fixed-point scale. `rt-intersect-plane` hands the normal to `rt-shade` as given.
   - In Update 60 its length and the `/ 1000.0` cancel in the diffuse term, but the normal's part of the reflection is 10⁶ times too large, so the specular term caps the intensity at 1000.
   - Every floor pixel of the test's render is exactly `rgb(128,128,128)`, and at a point where the branch's unit normal gives `rgb(97,97,97)`, Update 60 draws `rgb(128,128,128)`.
   - With this branch's `rt-shade`, a 1000-long normal would make the diffuse term 1000 times too large as well, hence the test's change.

The `.expected` was regenerated in Update 26. At Update 23 it read `color=rgb(162,0,0)` and `pixels=192 bg=82 hit=110`.

**Why not the old verdict.** The Integer `ray3-sphere` took `geo-isqrt (disc * 1000)`: 63245 where the root of the discriminant is 2000.
- For the test's ray the roots come out −26622 (rejected) and 36622, so the shaded point is (0, 0, 36622), about 30,600 past the sphere's far wall at z = 6000.
- Its normal, (0, 0, 1000), faces away from the light (n·l = −986), so the diffuse term is 0.
- The specular term is 624 thousandths, 436 after the shiny weight, and 200 + 436 = 636 gives 255 × 636 / 1000 = 162.

The Real `ray3-sphere` returns 4000, and this change leaves it alone. The old render's count of 110 equals the new one's, but only the count was compared, not the pixels.

**The new colour by hand.**
- The hit is (0, 0, 4000) with normal (0, 0, −1).
- The light direction is (−3000, 5000, −2000) / 6164.4, so n·l = 0.3244, and the diffuse term is 500 × 0.3244 = 162.2.
- The reflection makes the same angle with the view, so the specular is 0.3244³² ≈ 2 × 10⁻¹⁶.
- The intensity is 200 + 162.2, or 362 as an Integer, and 255 × 362 / 1000 = 92.

**How it was found.** Our Roc port draws `raytracer-test`'s scene on a browser canvas: Codex emitted as Roc, on a zig host. The spheres drew flat whatever the light did, and at the test's field of view the red sphere was a single traced pixel.

**The tools.**
- `codexzig` is Update 60's compiler with its zig plug, built as a native binary from `9fff850c`. Our transpiler repository builds it and checks that its emitted zig is a fixed point.
- `codexir` is Update 60's compiler to IR, built the same way.
- The wasm arm feeds `codexir`'s IR to Update 60's `WasmPlug.codex`, run through our IR driver.
- `codexrun` is the interpreter in our own Rust Codex compiler, which shares no code with Cobblestone's.
- Units are bundled with our resolver, which reads the checkout's `build/quire-map.ps1`.

**Verified,** each on the unit bundled from this branch and, as a control, from Update 60. Each "match" is against the `.expected` on its own side: Update 60's file, or this branch's.

| arm | Update 60 | this branch |
|---|---|---|
| `codexzig`, then `zig build-exe` (zig 0.16.0), run | match | match |
| `codexir`, then the wasm plug, run | match | match |
| `codexrun` | the five lines | the five lines |

`codexrun` prints `dist=4000` where the Codex plugs print `dist=4000.0`. That is our interpreter's `show` of a Real; its other four lines match on both sides.

From this branch, `forewords/game-raytracer` matches under `codexzig` and `codexrun`, and `foreword-all-compile` under `codexrun`.

Also run through `codexrun`:

- **Update 23** (`ccce2b31`), whose Raytracer, test and `.expected` are byte-identical to those Update 26 replaced. With one adjustment, dropping the test's `cites Codex chapter General`, it prints exactly its `.expected`: `dist=36622`, `rgb(162,0,0)`, `bg=82 hit=110`.

- **Pixels by the object each ray hits,** from a probe that traces every pixel with `rt-pixel-ray` and `rt-trace` and classes it by the hit's material, in the tests' scenes (Update 60's with its 1000-long floor normal, this branch's with a unit one):

  | render | Update 60 (missed / red / green / floor) | this branch |
  |---|---|---|
  | 16 × 12, field 1000 (the test's) | 111 / 1 / 0 / 80 | 82 / 21 / 27 / 62 |
  | 160 × 120, field 1000 | 9,759 / 1 / 0 / 9,440 | 7,358 / 1,885 / 2,615 / 7,342 |
  | Update 60 at field 1: 16 × 12, then 160 × 120 | 82 / 21 / 27 / 62, then 7,358 / 1,885 / 2,615 / 7,342 | |

  Update 60 at field 1 gives exactly the counts this branch gives at 1000.

  In Update 60's renders a second probe counted pixels by colour instead. Every sphere pixel is exactly its colour at 200 thousandths, and every floor pixel exactly `rgb(128,128,128)`; its counts equal these. With lit spheres a colour count no longer applies, so this branch has only the object counts.

- **A floor probe,** shading the floor hits at (0, −1000, 3000) and (3000, −1000, 3000):

  | | normal 1000 long | unit normal |
  |---|---|---|
  | Update 60 | `rgb(128,128,128)` at both | `rgb(25,25,25)` at both, the ambient level |
  | this branch | `rgb(128,128,128)` at both | `rgb(116,116,116)` and `rgb(97,97,97)` |

The probes are ours and are not in the branch.

No other `.codex` file in the tree calls Raytracer's `rt-shade`, `rt-pixel-ray`, `rt-render` or `rt-camera-new`. `apps/gpushow/kernels/RaytraceKernel.codex` defines its own `rt-render` and does not cite Raytracer.

**Not verified.** The Cobblestone battery, codex-vm, and x86 on bare metal.

**Choices a reviewer may want otherwise.**
- The field of view could stay as `/ 2.0` with a forward reach of `1000.0`. After `rt-normalize` it is the same direction, and it keeps the field's current meaning.
- `rt-intersect-plane` could normalize the plane's normal, so that a scene's normal length stops mattering to shading. Geometry's `ray3-plane` would still see the length in its parallel test (`geo-abs denom < 0.001`). This change instead states that normals are unit length, and fixes the one scene that passed another.

No backlog row: nothing is left open, and `codex/foreword/game/game-backlog.md` has no Raytracer entry.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_0127WrVAaJDy6hZL3pPqoJPk
