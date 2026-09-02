# Shared machinery for the two-venue sweep (design random894, agreed
# Steve + Claude 2026-08-20): ALL rung QEMU on the droplet, all zig
# build/run/diff local, venue by workload class. Sources oracle_lib.sh
# for the unit list, verdicts and guards, and shadows only the two arm
# functions with remote variants -- the local arms stay the authority for
# the all-local fallback (ast/allcycles.sh, untouched). Those live in
# ast/plug_arm_lib.sh since 2026-08-25, which oracle_lib.sh sources, so
# sourcing oracle_lib.sh still brings in everything shadowed here.
#
# Not a runnable script; sweep_prep.sh, sweep_canary.sh and sweep_long.sh
# source it.

T="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$T/ast/oracle_lib.sh"
# rung_stamp lives in oracle_lib.sh now, shared with
# the legacy loops (wiring batch, process review D3/S1).

# The remote arm: same rm-stale-first discipline, same transport-log
# placement, same zig_verdict as the local arms it shadows. Only the
# QEMU venue moved.
remote_ring_arm() {
    local m=$1
    cd "$T"
    # The same refusal the local arms make. This path is a THIRD consumer of
    # ast/<m>.ir and produces none of it, so without the check here the guard
    # has a hole exactly where the two-venue sweep runs -- which is the venue
    # that found the stale-IR problem in the first place.
    unit_flags "$m" || return 1
    python3 "$T/truth_prov.py" check-ir "$m" "$FLAGS" || return 1
    rm -f "ast/${m}.zig"
    # One labeled retry: the straw adds a failure mode the local arms do
    # not have (a dropped link kills the remote session and its guest --
    # the 2026-08-20 wifi blip cost fib its rung), and a transient link
    # failure should cost a retry, not a red rung. Labeled, so a plug
    # that genuinely dies shows up as two identical failures, never as
    # quiet flakiness.
    if ! ./droplet_transpile.sh "ast/${m}.ir" "ast/${m}.zig" ring \
            > "ast/${m}.transport.log" 2>&1; then
        echo "TRANSPORT FAILED for $m, retrying once (ast/${m}.transport.log):"
        tail -6 "ast/${m}.transport.log"
        rm -f "ast/${m}.zig"
        if ! ./droplet_transpile.sh "ast/${m}.ir" "ast/${m}.zig" ring \
                >> "ast/${m}.transport.log" 2>&1; then
            echo "TRANSPORT FAILED for $m twice -- not a blip:"
            tail -6 "ast/${m}.transport.log"
            return 1
        fi
    fi
    zig_verdict "$m"
}

# Every droplet arm rides the ring, unlike the local split in arm_for:
# the TCP plug's boot-time heap reservation needs >= 1600 MB of guest
# RAM (measured 2026-08-20: connects at 1600, exits SILENTLY at 1500 --
# nothing on serial, clean debug-port exit). The 8 GB ladder droplet's
# 3072 MB cap would hold that now, but only the ring kernel travels
# (sweep_prep.sh), so the TCP arm stays local until it does.
# The ring plug boots and serves there comfortably. The Codex network
# stack keeps its oracle coverage in the local venues -- cycle.sh's
# warmups and the all-local allcycles.sh both push IR over TCP -- and
# the two transports were measured byte-identical on the same IR
# (laptop tcp vs droplet ring, 2026-08-20).
remote_arm_for() {
    echo remote_ring_arm
}

# One unit through its remote arm with the silence rule allcycles.sh
# taught us: a rung that produces neither ORACLE nor TRANSPORT FAILED is
# a failure, not a pass.
run_unit_remote() {
    local m=$1
    rung_stamp "$m"
    local log rc
    # Everything to a file, a digest to the terminal. The old shape captured
    # the rung's output into a variable and printed `head -34` of it, which
    # is a display decision made by throwing data away: it ate a panic
    # message once and a CX-DECK line once, both silently, and each time the
    # answer was another grep bolted on beside the cut. The file is cheap and
    # nothing has to guess in advance which lines will matter.
    log="$T/logs/rung-$(date -u +%Y%m%dT%H%M%SZ)-$m.log"
    mkdir -p "$T/logs"
    $(remote_arm_for "$m") "$m" > "$log" 2>&1; rc=$?
    grep -E 'ORACLE|MISMATCH|CX-DECK|panic:|cursors met|exhausted|FAILED|CODEGEN-HALTED' \
        "$log" | head -24
    echo "  ($(wc -l < "$log") lines: $log)"
    local out; out=$(cat "$log")
    [ "$rc" -ne 0 ] && return 1
    case "$out" in
        *ORACLE*|*TRANSPORT\ FAILED*) ;;
        *) echo "NO VERDICT from $m -- treating as failure"; return 1 ;;
    esac
    [ "$m" = ir_to_codex_roundtrip ] && { roundtrip_fixed_point || return 1; }
    return 0
}
