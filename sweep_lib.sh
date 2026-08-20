# Shared machinery for the two-venue sweep (design random894, agreed
# Steve + Claude 2026-08-20): ALL rung QEMU on the droplet, all zig
# build/run/diff local, venue by workload class. Sources oracle_lib.sh
# for the unit list, verdicts and guards, and shadows only the two arm
# functions with remote variants -- the local arms in oracle_lib.sh stay
# the authority for the all-local fallback (ast/allcycles.sh, untouched).
#
# Not a runnable script; sweep_prep.sh, sweep_canary.sh and sweep_long.sh
# source it.

T="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$T/ast/oracle_lib.sh"
# take_compute_lock and rung_stamp live in oracle_lib.sh now, shared with
# the legacy loops (wiring batch, process review D3/S1).

# The remote arm: same rm-stale-first discipline, same transport-log
# placement, same zig_verdict as the local arms it shadows. Only the
# QEMU venue moved.
remote_ring_arm() {
    local m=$1
    cd "$T"
    rm -f "ast/${m}.zig"
    if ! ./droplet_transpile.sh "ast/${m}.ir" "ast/${m}.zig" ring \
            > "ast/${m}.transport.log" 2>&1; then
        echo "TRANSPORT FAILED for $m (ast/${m}.transport.log):"
        tail -6 "ast/${m}.transport.log"
        return 1
    fi
    zig_verdict "$m"
}

# Every droplet arm rides the ring, unlike the local split in arm_for:
# the TCP plug's boot-time heap reservation needs >= 1600 MB of guest
# RAM (measured 2026-08-20: connects at 1600, exits SILENTLY at 1500 --
# nothing on serial, clean debug-port exit) and the droplet holds 2 GB
# total with the live site on it, so the appliance caps guests at 1300.
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
    local out rc
    out=$($(remote_arm_for "$m") "$m" 2>&1); rc=$?
    printf '%s\n' "$out" | head -34
    [ "$rc" -ne 0 ] && return 1
    case "$out" in
        *ORACLE*|*TRANSPORT\ FAILED*) ;;
        *) echo "NO VERDICT from $m -- treating as failure"; return 1 ;;
    esac
    [ "$m" = pingpong ] && { pingpong_fixed_point || return 1; }
    return 0
}
