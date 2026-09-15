Evidence for the Raytracer nearest-first PR (branch raytracer-nearest-first).

bench2.sh / bench2.log   the bench on u61-candidate: 6e9f9624 (before) against
                         4fbc6e72 (after), seven runs of each side interleaved,
                         every run's time and checksum, and every build time.
verify-bench.sh / .log   the first round, on Update 60 against the branch
                         (45bdc217): the wasm arm on raytracer-test (the only
                         unit in its units directory), and the benches with
                         three or five runs a side, not interleaved.
ray-bench.codex          the bench program both rounds bundled. Its opening
                         prose line was reworded after the runs so it does not
                         name our demo; the code is the code that ran.

Printed, not logged: the seven interleaved zig runs on Update 60's tree, from
a command with no script, whose checksums were not kept (the three-run round
in verify-bench.log printed checksum 1082315010240 on both sides):
  zig Debug u60: 2.220 2.169 2.448 2.109 2.260 2.445 1.991
  zig Debug branch: 1.767 1.703 1.804 1.727 1.714 1.708 1.687
  zig ReleaseFast u60: 0.558 0.554 0.567 0.573 0.523 0.602 0.551
  zig ReleaseFast branch: 0.449 0.450 0.452 0.492 0.484 0.482 0.434

Also printed, not logged: forewords/game-raytracer and raytracer-test matched
under run-zig and codexrun, and apps/foreword-all-compile under codexrun, on
both Update 60 and the branch head (355e4d42).
