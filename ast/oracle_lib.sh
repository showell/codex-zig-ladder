# Shared machinery for the up-to-AST milestone oracles. Each milestone is a
# subject bundled from real compiler chapters plus a generated harness, run
# two ways -- seed-compiled bare metal as truth, and through the zig plug --
# and required to agree byte for byte.
#
# A UNIT <u> owns: gen_<u>_harness.py, bundle_<u>.ps1, and the artifacts
# <u>-subject.codex, <u>.ir, <u>.raw, <u>.zig, <u>.zigraw.
# A RUNG <m> owns: <m>.truth, <m>.zigout, <m>.diff, and its entry in the bank.
# Most units carry one rung and the two sets of names coincide; fibx and whole
# carry two, and gen_scale_harness.py and gen_clamp_harness.py hold nothing but
# the subject their unit runs second.
T="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"  # ladder-root-bootstrap: reaches the LADDER only; the checkout comes from ladder_root
REPO="$(python3 "$T/ladder_root.py" codex)"

# The ladder, cheapest first. allcycles.sh sweeps it and rebank_all.sh
# re-banks it, and they must not disagree about what the ladder is: a rung
# missing from one is a rung whose truth is stale while its diff still
# reports green.
LADDER_RUNGS="lex parse desugar scope check lower text pingpong lir fib fibx scale whole clamp"

# A rung is a CLAIM; a unit is a COMPILE. The ladder used one word for both
# until 2026-08-18, and it cost real time: `scale` compiled the same 2.4 MB
# bundle as `fibx` and `clamp` the same 2.58 MB bundle as `whole`, differing
# only in a Text literal, so two thirds of a sweep went on compiling two
# binaries twice. Now each unit's harness runs every one of its subjects and
# marks the dumps, and the arms split the stream back into per-rung files.
#
# Everything downstream still reads <rung>.truth, <rung>.zigout, <rung>.diff,
# and bank_truth.py still banks per rung. What changed is how many compiles
# stand behind them.
LADDER_UNITS="lex parse desugar scope check lower text pingpong lir fib fibx whole"

# The subjects a unit runs. The order here is documentation and nothing else:
# split_truth keys each section on the MARK TEXT, so listing them the other way
# round attributes the dumps correctly anyway. This comment used to claim the
# order was load-bearing, which was a safety property the code does not have and
# the worst kind to assert -- a future reader reordering these would have
# trusted it.
unit_rungs() {
    case "$1" in
        fibx)  echo "fibx scale" ;;
        whole) echo "whole clamp" ;;
        *)     echo "$1" ;;
    esac
}

# Two lists, one ladder, and they are checked against each other HERE rather
# than trusted. The comment on LADDER_RUNGS was written after allcycles.sh and
# rebank_all.sh each kept their own copy and disagreed by one rung; splitting
# rungs from units brings that hazard back in a new shape, where a rung listed
# by nobody's unit silently stops being re-banked while its diff still reports
# green against the truth from three Updates ago.
_carried=""
for _u in $LADDER_UNITS; do _carried="$_carried $(unit_rungs $_u)"; done
for _r in $LADDER_RUNGS; do
    case " $_carried " in
        *" $_r "*) ;;
        *) echo "LADDER MISMATCH: $_r is a rung no unit carries" >&2; exit 1 ;;
    esac
done
for _r in $_carried; do
    case " $LADDER_RUNGS " in
        *" $_r "*) ;;
        *) echo "LADDER MISMATCH: a unit carries $_r, which is not a rung" >&2; exit 1 ;;
    esac
done
unset _carried _u _r

# Extra mode flags appended to the command line of BOTH blobs, per milestone.
# Empty wherever the seed's derived deck scale is enough, so a milestone that
# already passes keeps compiling byte for byte as it did.
#
# derive-deck-scale is unit-len * 200 / 2993576 clamped to [64, 100]: the
# check subject lands at 64, and lower -- the same subject plus 2,581 lines
# of Lowering -- lands at 69 and still overflows the seed's CHECK deck
# (CDX9002). An explicit decks= skips the clamp, which is the only headroom
# available; raising QEMU's memory is not an option on this machine.
mode_flags() {
    case "$1" in
        lower) echo " decks=100" ;;
        fib)   echo " decks=100" ;;
        # Both these units now carry two subjects and run the pipeline twice
        # in one process, so the reservation (demand-lift-floor, 104 MB) is
        # taken twice and the deck sees two runs' worth of extents. These
        # numbers were sized for one subject and are the likeliest thing to
        # move first: too small shows up as CDX9002 or a fault, which is the
        # honest direction to be wrong in.
        fibx)  echo " decks=160" ;;
        # 160 scaled by unit length: whole is 2,578,233 bytes against fibx's
        # 2,398,065, so 160 * 2578233/2398065 = 172. Deck scale tracks the
        # unit, and guessing low here costs a ten-minute cycle to find out.
        whole) echo " decks=172" ;;
        # passes=text-plug drops the inline passes. Passes.codex says why in
        # so many words: "A plug that emits SOURCE resolves a call by its
        # name, so a pass that substitutes a body and deletes the call
        # deletes the plug's only handle on it." Emitting codex text from
        # inlined IR would produce source with the calls gone -- still a
        # fixed point, but a worthless round trip.
        text)  echo " decks=100 passes=text-plug" ;;
        pingpong) echo " decks=100 passes=text-plug" ;;
        *)     echo "" ;;
    esac
}

# Generate the harness, bundle the subject, compile it both ways, run the
# bare-metal binary, bank its output as the truth side.
truth_arm() {
    local m=$1
    cd $T/ast
    python3 gen_${m}_harness.py

    # NOT `pwsh ... | tail -1`: under a pipe the status is tail's, and
    # plug-build-lib exits 3 on an unresolvable cite. Update 42 added a
    # BootPaint cite to PhaseAllocator; the bundler refused correctly, this
    # line swallowed it, and four rungs went on to compile the PREVIOUS
    # subject still sitting on disk -- two of them banked truth from it.
    # The subject is removed first so a refusal cannot leave a stale one
    # that looks like a fresh one.
    rm -f ${m}-subject.codex
    local bout
    if ! bout=$(~/.local/pwsh/pwsh -NoProfile -File ./bundle_${m}.ps1 2>&1); then
        printf '%s\n' "$bout" | tail -5
        echo "BUNDLE FAILED for $m"; return 1
    fi
    printf '%s\n' "$bout" | tail -1
    [ -s ${m}-subject.codex ] || { echo "BUNDLE FAILED: no ${m}-subject.codex"; return 1; }

    # Ask the cheap question before the expensive one. A chapter bundled twice
    # is visible in the subject text and costs milliseconds to see; it cost us
    # a compile four minutes into a sweep once and twenty-five minutes into one
    # the next day.
    python3 "$T/check_bundles.py" "$m" || { echo "BUNDLE REFUSED for $m"; return 1; }

    python3 - "$m" "$(mode_flags $m)" <<'PY'
import sys
m, flags = sys.argv[1], sys.argv[2]
src = open(f'{m}-subject.codex', 'rb').read()
open(f'{m}-cdx.blob', 'wb').write(b"CDX map" + flags.encode() + b"\n" + src + b"\x04")
open(f'{m}-ir-cce.blob', 'wb').write(b"IR-CCE" + flags.encode() + b"\n" + src + b"\x04")
print(f"blobs written ({len(src)} bytes of source), mode flags:{flags or ' none'}")
PY

    cd $T
    # A failed compile must stop the run. Banking a truth file from a stale
    # or missing binary is how a broken subject looks like a passing one.
    echo "--- compiling subject to a bare-metal binary"
    rm -f ast/${m}-subject.cdx ast/${m}.ir
    if ! python3 -u ring_compile.py ast/${m}-cdx.blob ast/${m}-subject.cdx 2>&1 | tail -20; then
        echo "COMPILE FAILED (bare metal) -- see the diagnostics above"; return 1
    fi
    [ -s ast/${m}-subject.cdx ] || { echo "COMPILE FAILED: no ${m}-subject.cdx"; return 1; }

    echo "--- compiling subject to IR-CCE for the plug"
    if ! python3 -u ring_compile.py ast/${m}-ir-cce.blob ast/${m}.ir 2>&1 | tail -20; then
        echo "COMPILE FAILED (IR-CCE) -- see the diagnostics above"; return 1
    fi
    [ -s ast/${m}.ir ] || { echo "COMPILE FAILED: no ${m}.ir"; return 1; }

    # Judge what the compiler said, not just whether it produced bytes. A
    # compile can succeed and still be telling us something: CDX3006 meant a
    # bundle carried a chapter twice for months, and nobody read it because
    # warnings scroll. check_diags.py holds a table of every code we have
    # looked at, with a reason, and refuses anything not in it -- so a code we
    # have never seen stops the rung instead of joining the scroll.
    if ! python3 "$T/check_diags.py" ast/${m}-subject.cdx.diags ast/${m}.ir.diags; then
        echo "DIAGNOSTICS REFUSED for $m (see check_diags.py POLICY)"; return 1
    fi

    echo "--- running the subject on bare metal"
    # Removed first, and the run's status checked, for the reason stated at the
    # bundle step: an artifact left behind by an earlier run reads exactly like
    # one this run produced. .raw is the newest intermediate here and it got
    # neither guard, which mattered most under verify_merge.sh -- where the
    # expected answer IS "identical to the bank", so splitting yesterday's .raw
    # would have produced the very result the run was launched to see.
    rm -f ast/${m}.raw
    if ! python3 - "$m" <<'PY'
import sys
import codex_vm
m = sys.argv[1]
# idle_timeout is silence tolerance, not total runtime: these subjects
# compute for a long stretch before their first print.
out = codex_vm.run_cdx(f'ast/{m}-subject.cdx', timeout=5400, idle_timeout=600)
lines = [l for l in out.decode(errors='replace').splitlines()
         if not l.startswith(("WD:", "HEAP:", "STACK:"))]
open(f'ast/{m}.raw', 'w').write("\n".join(lines) + "\n")
print(f"ran ast/{m}-subject.cdx: {len(lines)} lines")
PY
    then
        echo "RUN FAILED for $m -- the guest did not finish"; return 1
    fi
    [ -s ast/${m}.raw ] || { echo "RUN FAILED: no ast/${m}.raw"; return 1; }

    # One run, one truth file per subject in it. A unit carrying one subject
    # prints no marks and passes through, so this is the same operation for
    # every rung on the ladder rather than a special case for the big two.
    (cd $T/ast && python3 split_truth.py ${m}.raw truth $(unit_rungs $m)) \
        || { echo "SPLIT FAILED for $m -- see ast/${m}.raw"; return 1; }
}

# The pingpong rung's real claim, which the arm diff does not make.
#
# pingpong's subject IS text.truth: stage 2 compiles the text stage 1 emitted
# and emits again, so a compiler that round-trips its own output must produce
# the same bytes back. Both arms agreeing says nothing about that -- they would
# agree just as contentedly on a second pass that dropped half the chapter,
# because both would drop the same half.
#
# This was written in truthcycle_pingpong.sh as "the whole claim" and checked
# by nothing. The files matched, by luck rather than by test, for as long as
# the rung has existed. A missing file fails here rather than passing quietly:
# an unrun rung and a green one must not look alike.
pingpong_fixed_point() {
    cd $T/ast
    local f
    for f in text.truth pingpong.truth; do
        [ -s "$f" ] || {
            echo "FIXED POINT UNCHECKED: no $f (run truthcycle_text.sh and truthcycle_pingpong.sh)"
            return 1
        }
    done
    if diff <(tr -d '\r' < text.truth) <(tr -d '\r' < pingpong.truth) \
            > pingpong.fixpoint.diff 2>&1; then
        echo "FIXED POINT: pingpong.truth byte-identical to text.truth"
    else
        echo "FIXED POINT BROKEN (first 15 lines):"
        head -15 pingpong.fixpoint.diff
        return 1
    fi
}

# The plug binary is only evidence about the ZigEmitter it was built from, and
# CODEX_ROOT names a working tree that can move underneath a running sweep. This
# refuses rather than reporting on a plug whose source has since changed.
plug_provenance() {
    local fp="$REPO/codex/plugs/zig/build-output/zig-plug.fingerprint"
    [ -f "$fp" ] || { echo "NO PLUG FINGERPRINT -- run cycle.sh"; return 1; }
    local now
    now=$(cat "$REPO/codex/plugs/zig/ZigEmitter.codex" "$REPO/codex/plugs/zig/ZigPlug.codex" \
          | sha256sum | cut -d' ' -f1)
    local was
    was=$(cat "$fp")
    if [ "$now" != "$was" ]; then
        echo "PLUG SOURCE MOVED since the plug was built:"
        echo "  built from ${was:0:16}, tree now holds ${now:0:16}"
        echo "  the checkout at $REPO changed under this run; rebuild with cycle.sh"
        return 1
    fi
}

# Run the emitted zig, diff against the truth. Shared by both arms: the
# transport is what differs between them, never the verdict.
zig_verdict() {
    local m=$1
    plug_provenance || return 1
    cd $T/ast
    # program output goes to stderr (std.debug.print); truth was serial bytes
    #
    # The address-space cap is the same 2.5 GB corpus_run.py puts on its zig
    # runs, and for the same incident: an emitted binary with no arena
    # balloons past 3 GB and livelocks the whole WSL VM (twice now -- the
    # second time was this very line, fibx under the Update 47 emitter, which
    # lacks PR 71's arena). Under the cap the allocation fails in the child,
    # @panic("oom") fires, and the balloon is a recorded rung failure instead
    # of a dead VM. ulimit is per-subshell, so nothing else inherits it.
    if ! (ulimit -v $((2560 * 1024)) && timeout 600 zig run ${m}.zig 2> ${m}.zigraw); then
        echo "--- zig compile/run errors:"
        head -40 ${m}.zigraw
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
# path costs ~130 bytes of guest heap per IR byte and fibx is 12.9 MB,
# where read-serial-cce costs one. Same parser, same emitter, and the
# ring plug is rebuilt from the same ZigEmitter -- only the transport
# and the plug body differ.
ring_arm() {
    local m=$1
    cd $T
    rm -f ast/${m}.zig
    if ! python3 -u plug_run_ring.py ast/${m}.ir ast/${m}.zig \
        > ast/${m}.transport.log 2>&1; then
        echo "TRANSPORT FAILED for $m (ast/${m}.transport.log):"
        tail -6 ast/${m}.transport.log
        return 1
    fi
    zig_verdict $m
}

# Which transport a rung needs is a property of the rung, so the sweep
# asks here rather than carrying a list of its own.
arm_for() {
    case "$1" in
        fibx|whole) echo ring_arm ;;
        *)          echo zig_arm ;;
    esac
}
