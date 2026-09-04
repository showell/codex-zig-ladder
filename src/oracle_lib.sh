# Shared machinery for the up-to-AST milestone oracles. Each milestone is a
# subject bundled from real compiler chapters plus a generated harness, run
# two ways -- seed-compiled bare metal as truth, and through the zig plug --
# and required to agree byte for byte.
#
# A UNIT <u> owns: gen_<u>_harness.py, bundle_<u>.ps1, and the artifacts
# <u>-subject.codex, <u>.ir, <u>.raw, <u>.zig, <u>.zigraw.
# A RUNG <m> owns: <m>.truth, <m>.zigout, <m>.diff, and its entry in the bank.
# Most units carry one rung and the two sets of names coincide. ir_to_x86 and
# passes_to_x86 carry two, marked by the rung's `_on_<subject>` suffix, and
# gen_<rung>_harness.py for their second rung holds nothing but its subject.
T="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"  # ladder-root-bootstrap: reaches the LADDER only; the checkout comes from ladder_root
# WHERE GENERATED FILES GO, and it is not $T. $T is the ladder's SOURCE; every
# harness, subject, blob, emitted zig and truth a rung produces belongs in the
# sandbox. ladder_root.py refuses when there is no $SANDBOX rather than falling
# back to the checkout -- falling back is how 343 MB got into a 4 MB repo.
O="$(python3 "$T/ladder_root.py" out)" || exit 1
mkdir -p "$O"
REPO="$(python3 "$T/ladder_root.py" codex)"

# The ladder, cheapest first. allcycles.sh sweeps it and rebank_all.sh
# re-banks it, and they must not disagree about what the ladder is: a rung
# missing from one is a rung whose truth is stale while its diff still
# reports green.
LADDER_RUNGS="lex parse desugar scope check lower ir_to_codex ir_to_codex_roundtrip lir_to_x86 ir_to_wire ir_to_x86_on_fib ir_to_x86_on_cce passes_to_x86_on_mid passes_to_x86_on_arith"

# A rung is a CLAIM; a unit is a COMPILE. The ladder used one word for both
# until 2026-08-18, and it cost real time: ir_to_x86's two rungs compiled the
# same 2.4 MB bundle twice, passes_to_x86's the same 2.58 MB, differing
# only in a Text literal, so two thirds of a sweep went on compiling two
# binaries twice. Now each unit's harness runs every one of its subjects and
# marks the dumps, and the arms split the stream back into per-rung files.
#
# Everything downstream still reads <rung>.truth, <rung>.zigout, <rung>.diff,
# and bank_truth.py still banks per rung. What changed is how many compiles
# stand behind them.
LADDER_UNITS="lex parse desugar scope check lower ir_to_codex ir_to_codex_roundtrip lir_to_x86 ir_to_wire ir_to_x86 passes_to_x86"

# The subjects a unit runs. The order here is documentation and nothing else:
# split_truth keys each section on the MARK TEXT, so listing them the other way
# round attributes the dumps correctly anyway. This comment used to claim the
# order was load-bearing, which was a safety property the code does not have and
# the worst kind to assert -- a future reader reordering these would have
# trusted it.
unit_rungs() {
    case "$1" in
        ir_to_x86)     echo "ir_to_x86_on_fib ir_to_x86_on_cce" ;;
        passes_to_x86) echo "passes_to_x86_on_mid passes_to_x86_on_arith" ;;
        *)             echo "$1" ;;
    esac
}

# The harness file a unit's generator writes: the unit name in CamelCase
# plus Harness.codex (lex -> LexHarness.codex, ir_to_x86 ->
# IrToX86Harness.codex). Only the FILE name derives from the unit; the
# chapter name inside it is the generator's and reaches the compiled unit.
harness_for() {
    echo "$(echo "$1" | sed -E 's/(^|_)([a-z0-9])/\U\2/g')Harness.codex"
}

# The compute lock is NOT here any more (2026-08-25). It is taken by
# codex_vm.launch, the one line in this tree that runs qemu, so a script
# cannot start a guest without asking and no script has to remember to.
# This file held the shell half of a rule that also lived in Python, and
# the two spellings had to be kept in step by hand.

# Per-rung wall-clock, printed at the marker so the split point and every
# future scheduling decision come from measured time, not intuition (S1).
rung_stamp() {
    echo "=== $1 ($(unit_rungs $1)) === $(date +%H:%M:%S)"
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
        lower)      echo " decks=100" ;;
        ir_to_wire) echo " decks=100" ;;
        # Both these units now carry two subjects and run the pipeline twice
        # in one process, so the reservation (demand-lift-floor, 104 MB) is
        # taken twice and the deck sees two runs' worth of extents. These
        # numbers were sized for one subject and are the likeliest thing to
        # move first: too small shows up as CDX9002 or a fault, which is the
        # honest direction to be wrong in.
        ir_to_x86)     echo " decks=160" ;;
        # 160 scaled by unit length (u47: passes_to_x86 2,601,343 bytes
        # against ir_to_x86's 2,469,864; the ratio moves per Update). Deck
        # scale tracks the unit, and guessing low here costs a ten-minute
        # cycle to find out.
        passes_to_x86) echo " decks=172" ;;
        # passes=text-plug drops the inline passes. Passes.codex says why in
        # so many words: "A plug that emits SOURCE resolves a call by its
        # name, so a pass that substitutes a body and deletes the call
        # deletes the plug's only handle on it." Emitting codex text from
        # inlined IR would produce source with the calls gone -- still a
        # fixed point, but a worthless round trip.
        ir_to_codex)           echo " decks=100 passes=text-plug" ;;
        ir_to_codex_roundtrip) echo " decks=100 passes=text-plug" ;;
        # THE UNITS THAT NEED NOTHING SAY SO, and an unknown one REFUSES.
        # This was `*) echo "" ;;` -- a unit with no case got no flags, which
        # is indistinguishable from a unit that needs none. The units/rungs
        # cross-check above does not cover this table, so adding a
        # thirteenth unit that needs a deck scale and forgetting the entry
        # bought silence, and the bill arrived later as CDX9002 or a fault in
        # whichever rung it was. The comments above say the derived scale
        # OVERFLOWS for several of these, so a forgotten entry is not a
        # theoretical hazard.
        lex|parse|desugar|scope|check|lir_to_x86) echo "" ;;
        *) echo "mode_flags: no entry for unit '$1' -- add one, with an" >&2
           echo "  empty case if it genuinely needs no deck scale. A missing" >&2
           echo "  entry and a deliberate none must not look alike." >&2
           return 1 ;;
    esac
}

# HOW TO ASK FOR A UNIT'S FLAGS, and the reason it is not `$(mode_flags $m)`.
#
# Command substitution runs a subshell, so a refusal inside mode_flags cannot
# stop the caller -- `$(mode_flags typo)` yields an empty string and the run
# carries on with no deck scale, which is the exact silence the refusal was
# added to end. An ASSIGNMENT does propagate the status, so every caller binds
# first and checks, and nothing interpolates mode_flags directly any more.
unit_flags() {              # <unit> -> sets FLAGS, or fails
    FLAGS=$(mode_flags "$1") || return 1
    return 0
}

# Generate the harness, bundle the subject, compile it both ways, run the
# bare-metal binary, bank its output as the truth side.
truth_arm() {
    local m=$1
    cd "$O"
    # The seed as this arm begins. CODEX_ROOT names a working tree that
    # can move underneath an hours-class run, and a truth split under a
    # different seed than compiled it is exactly the mixed state the
    # provenance sidecar exists to rule out -- so record now, require
    # after the split (C5).
    local seed_at_start
    seed_at_start=$(PYTHONPATH="$T" python3 -c \
        'import seed_identity; print(seed_identity.seed_sha256())') \
        || { echo "SEED UNREADABLE for $m"; return 1; }
    # Guarded, and the old harness removed first: any `truth_arm "$u" ||
    # ...` caller disables errexit inside the function body, so an
    # unguarded generator crash would bundle YESTERDAY'S harness and
    # reproduce the previous answer -- a wrong-PASS. The guards make the
    # arm self-sufficient instead of trusting the caller's set -e.
    local h; h=$(harness_for $m)
    rm -f $h
    python3 gen_${m}_harness.py || { echo "HARNESS GEN FAILED for $m"; return 1; }
    [ -s $h ] || { echo "HARNESS GEN FAILED: no $h"; return 1; }

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

    unit_flags "$m" || { echo "NO DECK ENTRY for $m"; return 1; }
    python3 - "$m" "$FLAGS" <<'PY' || { echo "BLOB WRITE FAILED for $m"; return 1; }
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
    rm -f src/${m}-subject.cdx src/${m}.ir
    # PIPESTATUS, not `if ! cmd | tail`: with no `pipefail` set anywhere in the
    # ladder, the status of a pipeline is the LAST command's, so `if !` there
    # tested `tail` and a failing compile read as a success. The bundle step
    # twenty lines up already avoids the pipe for exactly this reason and these
    # two did not. Only the `[ -s ... ]` line below caught it, which reports
    # the wrong check with the wrong message -- and misses entirely a compile
    # that exits non-zero after writing a non-empty file.
    python3 -u ring_compile.py src/${m}-cdx.blob src/${m}-subject.cdx 2>&1 | tail -20
    if [ "${PIPESTATUS[0]}" -ne 0 ]; then
        echo "COMPILE FAILED (bare metal) -- see the diagnostics above"; return 1
    fi
    [ -s src/${m}-subject.cdx ] || { echo "COMPILE FAILED: no ${m}-subject.cdx"; return 1; }

    echo "--- compiling subject to IR-CCE for the plug"
    python3 -u ring_compile.py src/${m}-ir-cce.blob src/${m}.ir 2>&1 | tail -20
    if [ "${PIPESTATUS[0]}" -ne 0 ]; then
        echo "COMPILE FAILED (IR-CCE) -- see the diagnostics above"; return 1
    fi
    [ -s src/${m}.ir ] || { echo "COMPILE FAILED: no ${m}.ir"; return 1; }

    # Stamp the IR the moment it is known good. The zig arm READS this file
    # and never writes it, so in a shared checkout it outlives the run that
    # made it; the sidecar is what lets the arm tell yesterday's from today's.
    unit_flags "$m" || { echo "NO DECK ENTRY for $m"; return 1; }
    python3 "$T/truth_prov.py" stamp-ir "$m" "$FLAGS" \
        || { echo "IR PROVENANCE STAMP FAILED for $m"; return 1; }

    # Judge what the compiler said, not just whether it produced bytes. A
    # compile can succeed and still be telling us something: CDX3006 meant a
    # bundle carried a chapter twice for months, and nobody read it because
    # warnings scroll. check_diags.py holds a table of every code we have
    # looked at, with a reason, and refuses anything not in it -- so a code we
    # have never seen stops the rung instead of joining the scroll.
    if ! python3 "$T/check_diags.py" src/${m}-subject.cdx.diags src/${m}.ir.diags; then
        echo "DIAGNOSTICS REFUSED for $m (see check_diags.py POLICY)"; return 1
    fi

    echo "--- running the subject on bare metal"
    # Removed first, and the run's status checked, for the reason stated at the
    # bundle step: an artifact left behind by an earlier run reads exactly like
    # one this run produced. .raw is the newest intermediate here and it got
    # neither guard, which matters most in verify-against-bank runs -- where
    # the expected answer IS "identical to the bank", so splitting yesterday's
    # .raw would have produced the very result the run was launched to see.
    # The truths and their provenance sidecars go too: a run or split that
    # fails must leave NO truth, or the next verdict diffs against
    # yesterday's and can print ORACLE PASS from it.
    for _r in $(unit_rungs $m); do rm -f src/${_r}.truth src/${_r}.truth.prov; done
    rm -f src/${m}.raw
    if ! python3 - "$m" <<'PY'
import sys
import codex_vm
m = sys.argv[1]
# idle_timeout is silence tolerance, not total runtime: these subjects
# compute for a long stretch before their first print.
out = codex_vm.run_cdx(f'src/{m}-subject.cdx', timeout=5400, idle_timeout=600)
lines = [l for l in out.decode(errors='replace').splitlines()
         if not l.startswith(("WD:", "HEAP:", "STACK:"))]
open(f'src/{m}.raw', 'w').write("\n".join(lines) + "\n")
print(f"ran src/{m}-subject.cdx: {len(lines)} lines")
PY
    then
        echo "RUN FAILED for $m -- the guest did not finish"; return 1
    fi
    [ -s src/${m}.raw ] || { echo "RUN FAILED: no src/${m}.raw"; return 1; }

    # A FAULTED GUEST STILL PRODUCED OUTPUT, and run_cdx returns it rather
    # than raising -- it raises only when the guest never finished at all. So
    # the checks above pass on a #PF dump: it is output, it is non-empty, and
    # split_truth cuts it into per-rung files that look like truths. Asked
    # HERE, before the split, so a fault leaves src/<m>.raw for reading and no
    # truth at all -- which is the rule the removals above already follow.
    # truth_prov.stamp_unit asks again at the certifier, because this arm is
    # not the only caller.
    if ! python3 "$T/truth_prov.py" fault "src/${m}.raw"; then
        echo "RUN FAULTED for $m -- the guest raised an exception; the dump is"
        echo "  in src/${m}.raw and no truth was written"
        return 1
    fi

    # One run, one truth file per subject in it. A unit carrying one subject
    # prints no marks and passes through, so this is the same operation for
    # every rung on the ladder rather than a special case for the big two.
    (cd "$O" && python3 "$T/src/split_truth.py" ${m}.raw truth $(unit_rungs $m)) \
        || { echo "SPLIT FAILED for $m -- see src/${m}.raw"; return 1; }

    # The seed must still be the one that started the arm, or the truths
    # just split were measured by one compiler and will be stamped as
    # another's. Discard them: a run that fails must leave NO truth (C5).
    if ! PYTHONPATH="$T" python3 -c \
        "import seed_identity; seed_identity.require_match('$seed_at_start')"; then
        echo "SEED MOVED under $m during the truth arm; truths discarded"
        for _r in $(unit_rungs $m); do rm -f src/${_r}.truth src/${_r}.truth.prov; done
        return 1
    fi

    # Record what measured this truth -- the seed and the harness content --
    # so banking can refuse a mismatch instead of inferring from timestamps.
    # THE TRUTHS GO WITH THE FAILURE, the same as under a moved seed above.
    # "A run that fails must leave NO truth (C5)" was applied to one of this
    # arm's two late failure paths and not the other, so a stamp refusal left
    # the split truths on disk uncertified -- which is how `lower.truth` came
    # to exist this morning as 65 lines with a register dump in it, under the
    # exact name the zig arm and bank_truth.py read. The certifier is the last
    # thing that can say a measurement is not one; if it says so, the file it
    # refused has no business surviving.
    if ! python3 "$T/truth_prov.py" stamp "$m"; then
        echo "PROVENANCE STAMP FAILED for $m; truths discarded"
        for _r in $(unit_rungs $m); do rm -f src/${_r}.truth src/${_r}.truth.prov; done
        return 1
    fi
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
roundtrip_fixed_point() {
    cd "$O"
    local f
    for f in ir_to_codex.truth ir_to_codex_roundtrip.truth; do
        [ -s "$f" ] || {
            echo "FIXED POINT UNCHECKED: no $f (run truthcycle_ir_to_codex.sh and truthcycle_ir_to_codex_roundtrip.sh)"
            return 1
        }
    done
    if diff <(tr -d '\r' < ir_to_codex.truth) <(tr -d '\r' < ir_to_codex_roundtrip.truth) \
            > ir_to_codex_roundtrip.fixpoint.diff 2>&1; then
        echo "FIXED POINT: ir_to_codex_roundtrip.truth byte-identical to ir_to_codex.truth"
    else
        echo "FIXED POINT BROKEN (first 15 lines):"
        head -15 ir_to_codex_roundtrip.fixpoint.diff
        return 1
    fi
}

# The plug binary is only evidence about the ZigEmitter it was built from, and
# CODEX_ROOT names a working tree that can move underneath a running sweep. This
# refuses rather than reporting on a plug whose source has since changed.
# The plug's fingerprint, written by cycle.sh and sweep_prep.sh and read
# by plug_provenance -- one spelling, because it was three and they had
# to agree by hand.
#
# TWO shas, because they answer different questions. The chapters are what
# an operator edits; the BUNDLE is what was actually compiled, and the two
# chapters are only a third of it -- `plug-build-lib.ps1:220-221` bundles
# PlugTypes.codex and IRTextParser.codex too, so 6,100 of the plug's 9,537
# lines sat outside this guard until 2026-08-25 and a common chapter could
# move under a running sweep with nothing said. That is the same incident
# the guard was built for, one chapter set over.
plug_fingerprint() {                       # -> "<chapters-sha> <bundle-sha>"
    local d="$REPO/codex/plugs/zig" c b
    c=$(cat "$d/ZigEmitter.codex" "$d/ZigPlug.codex" | sha256sum | cut -d' ' -f1)
    b=$(sha256sum "$d/build-output/plug-source.codex" 2>/dev/null | cut -d' ' -f1)
    [ -n "$b" ] || { echo "NO PLUG BUNDLE at $d/build-output/plug-source.codex" >&2; return 1; }
    echo "$c $b"
}

plug_provenance() {
    local fp="$REPO/codex/plugs/zig/build-output/zig-plug.fingerprint"
    [ -f "$fp" ] || { echo "NO PLUG FINGERPRINT -- run cycle.sh"; return 1; }
    local was now
    was=$(cat "$fp")
    now=$(plug_fingerprint) || return 1
    [ "$now" = "$was" ] && return 0
    # A stamp from before the bundle sha is one field, and cannot be
    # compared against two. Say that by name rather than reporting it as
    # a moved checkout.
    if [ "$(echo "$was" | wc -w)" != 2 ]; then
        echo "PLUG FINGERPRINT PREDATES THE BUNDLE STAMP -- rebuild with cycle.sh"
        return 1
    fi
    local was_c=${was%% *} was_b=${was##* } now_c=${now%% *} now_b=${now##* }
    echo "PLUG SOURCE MOVED since the plug was built:"
    [ "$now_c" != "$was_c" ] && \
        echo "  chapters: built from ${was_c:0:16}, tree now holds ${now_c:0:16}"
    [ "$now_b" != "$was_b" ] && \
        echo "  bundle:   built from ${was_b:0:16}, tree now holds ${now_b:0:16}"
    echo "  the checkout at $REPO changed under this run; rebuild with cycle.sh"
    return 1
}

# The ring arm's plug is src/ringplug.cdx, not the TCP plug, so its
# provenance is the ring fingerprint ringplug_build.sh stamped -- the same
# check plug_run_ring.py makes before transpiling, repeated here because
# the checkout can move between the transpile and the verdict. Checking
# the TCP fingerprint on a ring arm asked about a plug that never ran, and
# refused every ring rung in a fresh sandbox (2026-08-22).
ring_provenance() {
    (cd "$T" && python3 -c 'import pathlib, plug_run_ring; plug_run_ring.refuse_stale_ringplug(pathlib.Path("."))') \
        || { echo "RING PLUG PROVENANCE REFUSED -- run src/ringplug_build.sh"; return 1; }
}

# A RESIDENT bound on everything the zig arm runs. The 4 GiB arena the
# heap-unification emitter reserves is lazily faulted, so RLIMIT_AS (the
# old `ulimit -v`) counted the reservation and refused the program before
# it had touched a page; cgroup MemoryMax counts resident pages, which is
# what a runaway actually costs the box (random927, decided by Steve
# 2026-08-23). `systemd-run --user --scope` needs no root and the kernel's
# kill is exit 137, which every verdict already reads as a red. There is
# no fallback branch: the laptop is not a venue (require_compute_venue).
#
# 1.5 GiB here was the number BEFORE finding 24 raised it: fibx measured
# 381 MB of deck plus ~1.2 GB of main, which 1.5 could not hold, and
# `cx_heap_reserve` has been 4 GiB since. The stale figure is not harmless
# prose -- it was read on 2026-09-02 to size whether the hosted harnesses
# could afford the driver's deck floors, and it made a 2.9 GB need look
# like an overrun. The generated zig carries the live constant and its
# reasoning; this line is orientation and defers to it.
ZIG_ARM_MEMORY_MAX=${ZIG_ARM_MEMORY_MAX:-6G}
bounded_run() {   # <MemoryMax> <command...>
    local max=$1; shift
    command -v systemd-run >/dev/null || {
        echo "bounded_run: no systemd-run on this host -- the resident bound is not optional; refusing" >&2
        return 1
    }
    systemd-run --user --scope -p "MemoryMax=$max" --quiet "$@"
}

# The plug's two arms live next door, outside the truth sidecars' watched
# set, because nothing they do can reach a bare-metal truth. Sourced here
# so every caller of zig_arm/ring_arm/arm_for sees them unchanged.
# plug_arm_lib.sh's own header carries the argument.
. "$T/src/plug_arm_lib.sh"
