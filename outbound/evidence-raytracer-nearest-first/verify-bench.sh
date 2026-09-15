#!/bin/bash
# Raytracer nearest-first: Update 60 against the branch.
#   1. the wasm arm on raytracer-test (IR frozen first)
#   2. RayBench.roc over rocemit's modules for each side, dev and LLVM
#   3. ray-bench.codex through Cobblestone's zig plug, Debug and ReleaseFast
# Every build prints its time; every run prints its checksum.
set -u
S="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
B=$HOME/build/rust-target/release
A=$HOME/showell_repos/cobblestone-curated-tests/arms
ROC=$HOME/build/roc-nightly/roc
ZIG=$HOME/zig-0.16.0/zig
TIMEFORMAT='%R'
runs() {  # runs <n> <cmd...>: the command n times, its last output and every time
    local n=$1; shift
    local ts="" out=""
    for _ in $(seq "$n"); do
        t=$( { time "$@" > "$S/run.out" 2>&1; } 2>&1 )
        ts="$ts $t"
    done
    echo "$(tail -1 "$S/run.out") | seconds:$ts"
}

for tag in u60 branch; do
    U=$S/units-$tag
    echo "=== wasm arm, $tag"
    "$A/freeze-upstream-ir" "$U" 2>&1 | tail -2
    "$A/run-wasm" "$U" 2>&1 | grep -v "^codexir\|^codexzig\|^zig\|^wasm\|^$" | tail -2
done

for tag in u60 branch; do
    D=$S/rocbench-$tag
    rm -rf "$D"; mkdir -p "$D/emit" "$D/roc"
    "$B/rocemit" --by-reach "$S/rocbranch-$tag/raytrace-on-screen.codex" "$D/emit" > /dev/null
    cp "$D/emit"/*.roc "$D/roc/"; rm -f "$D/roc/RaytraceOnScreen.roc" "$D/roc/Mem.roc"
    cp "$HOME/showell_repos/roc-apps/framebuffer/bench/RayBench.roc" "$D/roc/"
    for opt in dev speed; do
        start=$SECONDS
        (cd "$D/roc" && "$ROC" build --opt=$opt RayBench.roc --output="$D/bench-$opt") > "$D/build-$opt.log" 2>&1
        echo "roc $tag built --opt=$opt in $((SECONDS - start)) s (exit $?)"
    done
done
for opt in dev speed; do
    for mode in trace render; do
        for tag in u60 branch; do
            echo "roc $opt $mode $tag: $(runs 5 "$S/rocbench-$tag/bench-$opt" 30 $mode)"
        done
    done
done

for tag in u60 branch; do
    Z=$S/zigbench-$tag
    "$B/bundle" one "$Z/ray-bench.codex" "$Z/unit.codex" 2>&1 | grep -v "DEAD QUIRE\|^CASE"
    "$HOME/codexzig/codexzig" < "$Z/unit.codex" 2> "$Z/bench.zig" > "$Z/codexzig.out"
    echo "codexzig $tag exit $? ($(wc -c < "$Z/bench.zig") bytes of zig)"
    for mode in Debug ReleaseFast; do
        start=$SECONDS
        (cd "$Z" && "$ZIG" build-exe bench.zig -O$mode -femit-bin=bench-$mode) > "$Z/build-$mode.log" 2>&1
        echo "zig $tag built -O$mode in $((SECONDS - start)) s (exit $?)"
    done
done
for mode in Debug ReleaseFast; do
    for tag in u60 branch; do
        echo "zig $mode $tag: $(runs 3 "$S/zigbench-$tag/bench-$mode")"
    done
done
echo "=== done"
