#!/bin/bash
# Raytracer nearest-first on u61-candidate, where PR 149's camera puts the
# spheres in view: 6e9f9624 (before) against 4fbc6e72 (after).
#   zig: ray-bench.codex through Cobblestone's zig plug, Debug and ReleaseFast
#   roc: RayBench.roc over rocemit's modules, dev and speed
# Seven runs of each side, interleaved; every build prints its time, and every
# run's time and checksum is kept in this log.
set -u
S="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
B=$HOME/build/rust-target/release
ROC=$HOME/build/roc-nightly/roc
ZIG=$HOME/zig-0.16.0/zig
TIMEFORMAT='%R'
one() {  # one <cmd...>: "<seconds> <last output line>"
    local t
    t=$( { time "$@" > "$S/run.out" 2>&1; } 2>&1 )
    echo "$t $(tail -1 "$S/run.out")"
}

for side in before after; do
    Z=$S/b2-zig-$side
    "$B/bundle" one "$Z/ray-bench.codex" "$Z/unit.codex" 2>&1 | grep -v "DEAD QUIRE\|^CASE"
    "$HOME/codexzig/codexzig" < "$Z/unit.codex" 2> "$Z/bench.zig" > /dev/null
    echo "codexzig $side: $(wc -c < "$Z/bench.zig") bytes of zig; rt-nearest in unit: $(grep -c rt-nearest "$Z/unit.codex"), half-fov /2000: $(grep -c '2000.0' "$Z/unit.codex")"
    for mode in Debug ReleaseFast; do
        start=$SECONDS
        (cd "$Z" && "$ZIG" build-exe bench.zig -O$mode -femit-bin=bench-$mode) > "$Z/build-$mode.log" 2>&1
        echo "zig $side built -O$mode in $((SECONDS - start)) s"
    done
    D=$S/b2-roc-$side
    rm -rf "$D/emit" "$D/roc"; mkdir -p "$D/emit" "$D/roc"
    "$B/rocemit" --by-reach "$D/raytrace-on-screen.codex" "$D/emit" > /dev/null
    cp "$D/emit"/*.roc "$D/roc/"; rm -f "$D/roc/RaytraceOnScreen.roc" "$D/roc/Mem.roc"
    cp "$HOME/showell_repos/roc-apps/framebuffer/bench/RayBench.roc" "$D/roc/"
    for opt in dev speed; do
        start=$SECONDS
        (cd "$D/roc" && "$ROC" build --opt=$opt RayBench.roc --output="$D/bench-$opt") > "$D/build-$opt.log" 2>&1
        echo "roc $side built --opt=$opt in $((SECONDS - start)) s"
    done
done

for mode in Debug ReleaseFast; do
    for k in 1 2 3 4 5 6 7; do
        for side in before after; do
            echo "zig $mode $side run $k: $(one "$S/b2-zig-$side/bench-$mode")"
        done
    done
done
for opt in dev speed; do
    for mode in trace render; do
        for k in 1 2 3 4 5 6 7; do
            for side in before after; do
                echo "roc $opt $mode $side run $k: $(one "$S/b2-roc-$side/bench-$opt" 30 $mode)"
            done
        done
    done
done
echo "=== done"
