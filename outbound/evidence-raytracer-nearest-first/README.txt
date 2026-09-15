Evidence for the Raytracer nearest-first PR (branch raytracer-nearest-first).

bench2.sh / bench2.log   the bench on u61-candidate: 6e9f9624 (before) against
                         4fbc6e72 (after), seven runs of each side interleaved,
                         every run's time and checksum.
verify-bench.sh / .log   the first round, on Update 60 against the branch: the
                         wasm arm on raytracer-test, and the benches with three
                         or five runs a side, not interleaved.
ray-bench.codex          the bench program both rounds bundle.

The seven interleaved zig runs of the first round were printed, not logged:
  zig Debug u60: 2.220 2.169 2.448 2.109 2.260 2.445 1.991
  zig Debug branch: 1.767 1.703 1.804 1.727 1.714 1.708 1.687
  zig ReleaseFast u60: 0.558 0.554 0.567 0.573 0.523 0.602 0.551
  zig ReleaseFast branch: 0.449 0.450 0.452 0.492 0.484 0.482 0.434
