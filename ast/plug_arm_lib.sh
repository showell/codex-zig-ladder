# The two arms that run the PLUG and judge it: zig_verdict, zig_arm,
# ring_arm, arm_for. Sourced by oracle_lib.sh, so every caller sees them
# exactly as before; nothing outside this file changed hands.
#
# It is a separate file for one reason, and the reason is the truth
# sidecars. A truth is a BARE-METAL measurement, and `truth_prov.set_hash`
# keys it on the harness content it was measured under -- whole files,
# hashed. `oracle_lib.sh` was in that set and held both arms, so editing
# the plug side of it changed the key of every truth on disk, and the plug
# side is the side an emitter hunt edits. Nothing here can reach a
# bare-metal truth: these functions run AFTER one exists and only ever
# compare against it. So they sit outside the watched set, and the set now
# contains what a truth actually depends on.
#
# The pressure was real before it was measured. `ast/ensure_ir.sh` is its
# own file rather than a function in `oracle_lib.sh` for exactly this
# reason, which is a design bent around a hash.
#
# The rule that still holds: anything that can change what the TRUTH ARM
# produces belongs in oracle_lib.sh, inside the watched set. If a function
# here ever grows a way to affect a truth, it moves back.

# Run the emitted zig, diff against the truth. Shared by both arms: the
# transport is what differs between them, never the verdict -- except
# WHICH plug's provenance vouches for the .zig, which the arm passes in.
zig_verdict() {
    local m=$1
    local prov=${2:-plug_provenance}
    $prov || return 1
    cd $T/ast
    # program output goes to stderr (std.debug.print); truth was serial bytes
    #
    # The run is bounded (bounded_run, resident) for this incident: an
    # emitted binary with no arena balloons past 3 GB and livelocked the
    # whole WSL VM twice in 2026-08 -- the second time on this very line.
    # Under the bound the kernel kills the child and the balloon is a
    # recorded rung failure instead of a dead host.
    # BOTH streams to disk. stderr is the program's output and the thing the
    # verdict is diffed from; stdout is instrumentation (CX-DECK) and used to
    # exist only as a bash variable that the caller then truncated. Nothing
    # is discarded here, so nothing downstream has to guess which lines were
    # worth keeping -- the terminal gets a digest, the files get everything.
    if ! (bounded_run "$ZIG_ARM_MEMORY_MAX" timeout 600 zig run ${m}.zig \
            > ${m}.stdout 2> ${m}.zigraw); then
        echo "--- zig compile/run failed; full output in ast/${m}.zigraw and ast/${m}.stdout"
        grep -E 'panic:|error:|CODEGEN-HALTED|cursors met|exhausted' ${m}.zigraw ${m}.stdout | head -6
        return 1
    fi
    # The unit ran once and answered for every subject it carries, exactly as
    # the bare-metal side did. Split before diffing so each rung still gets its
    # own verdict: a merged diff would name the unit and leave the reader to
    # work out which subject moved.
    python3 split_truth.py ${m}.zigraw zigout $(unit_rungs $m) \
        || { echo "SPLIT FAILED for $m -- see ast/${m}.zigraw"; return 1; }
    local rung rc=0
    for rung in $(unit_rungs $m); do
        # A truth recorded under another seed diffs as confidently as a
        # fresh one. Refuse it at the rung that would use it, not hours
        # later at bank time (C4).
        python3 "$T/truth_prov.py" check "$rung" || { rc=1; continue; }
        if diff <(tr -d '\r' < ${rung}.truth) ${rung}.zigout > ${rung}.diff 2>&1; then
            echo "ORACLE PASS: zig $rung output byte-identical to bare-metal truth"
        else
            echo "ORACLE DIFF for $rung (first 15 lines):"
            head -15 ${rung}.diff
            rc=1
        fi
    done
    return $rc
}

# Push the IR through the plug over TCP (verified transfer -- see
# TRANSPORT_CORRUPTION.md). The default arm: it exercises the
# Codex-written network stack on every run, which is itself an oracle
# surface and is where the odd-frame defect was caught.
zig_arm() {
    local m=$1
    cd $T
    # Refuse IR no run under this seed and this subject produced, before
    # spending a transport on it. A stale .ir transpiles cleanly and diffs
    # against today's bank as a green that means nothing.
    python3 "$T/truth_prov.py" check-ir "$m" "$(mode_flags $m)" || return 1
    rm -f ast/${m}.zig
    # Transport chatter goes to a log, not to the caller: the sweep prints
    # a bounded slice of each rung's output, and a transfer that narrates
    # 25 lines pushed the verdict past the cut -- fibx passed SILENTLY,
    # which reads exactly like a rung that never ran.
    if ! python3 -u plug_run_checked.py \
        $REPO/codex/plugs/zig/build-output/zig-plug.cdx \
        ast/${m}.ir ast/${m}.zig > ast/${m}.transport.log 2>&1; then
        echo "TRANSPORT FAILED for $m (ast/${m}.transport.log):"
        tail -6 ast/${m}.transport.log
        return 1
    fi
    zig_verdict $m
}

# The ring arm, for subjects past the TCP intake ceiling: the receive
# path costs ~130 bytes of guest heap per IR byte and fibx is 13.1 MB,
# where read-serial-cce costs one. Same parser, same emitter, and the
# ring plug is rebuilt from the same ZigEmitter -- only the transport
# and the plug body differ.
ring_arm() {
    local m=$1
    cd $T
    # Refuse IR no run under this seed and this subject produced, before
    # spending a transport on it. A stale .ir transpiles cleanly and diffs
    # against today's bank as a green that means nothing.
    python3 "$T/truth_prov.py" check-ir "$m" "$(mode_flags $m)" || return 1
    rm -f ast/${m}.zig
    if ! python3 -u plug_run_ring.py ast/${m}.ir ast/${m}.zig \
        > ast/${m}.transport.log 2>&1; then
        echo "TRANSPORT FAILED for $m (ast/${m}.transport.log):"
        tail -6 ast/${m}.transport.log
        return 1
    fi
    zig_verdict $m ring_provenance
}

# Which transport a rung needs is a property of the rung, so the sweep
# asks here rather than carrying a list of its own.
arm_for() {
    # CODEX_ALL_RING=1 sends every unit through the ring: the TCP plug
    # cannot boot inside a guest under 1600 MB (measured 2026-08-20 -- it
    # connects at 1600 and exits SILENTLY below that), so a small-RAM
    # venue runs all-ring and consciously surrenders the TCP-transport
    # coverage to laptop runs. The transports are measured
    # byte-identical on the same IR.
    [ -n "${CODEX_ALL_RING:-}" ] && { echo ring_arm; return; }
    case "$1" in
        ir_to_x86|passes_to_x86) echo ring_arm ;;
        *)                       echo zig_arm ;;
    esac
}
