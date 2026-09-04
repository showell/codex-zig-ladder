#!/bin/bash
# The DDC witness path (codex/plugs/csharp/emit-compiler.ps1), zig edition,
# recon mode: concat the whole compiler, self-host it to IR-CCE through the
# ring (the refill's production case -- the source is ~3x the ring), push
# the IR through the zig plug, and read the marker inventory. The inventory
# IS the remaining-work list for a native zig compiler; a clean zig
# typecheck here is parity with the C# witness's bar.
#
# Not part of any ceremony. This is the parked endgame's instrument
# (PRIORITIES "Parked" / random839: piggyback the C# DDC witness path,
# where C# stops at "compiles" and zig RUNS); run it when the compiler's
# own marker inventory is the question. Kept deliberately -- retire it
# only with that item.
set -e
T="$(cd "$(dirname "$0")" && pwd)"
. "$T/src/oracle_lib.sh"
# Self-hosting the whole compiler through the ring and then through
# the plug: the longest guest in the tree.
REPO="$(python3 "$T/ladder_root.py" codex)"
R=$T/recon
mkdir -p "$R"

echo "--- concat codex/compiler -> Codex.codex"
~/.local/pwsh/pwsh -NoProfile -File "$REPO/build/concat-codex-self.ps1" -OutFile "$R/Codex.codex"
ls -la "$R/Codex.codex"

python3 - "$R" <<'PY'
import sys
r = sys.argv[1]
src = open(f'{r}/Codex.codex', 'rb').read()
open(f'{r}/compiler-ir.blob', 'wb').write(b"IR-CCE passes=text-plug\n" + src + b"\x04")
print(f"blob: {len(src)} bytes of source")
PY

echo "--- self-host to IR-CCE (long; the ring refills behind the reader)"
python3 -u -c "
import sys; sys.path.insert(0, '$T')
import ring_compile
ok = ring_compile.compile_ring('$R/compiler-ir.blob', '$R/compiler.ir', timeout=5400)
sys.exit(0 if ok else 1)
"
ls -la "$R/compiler.ir"

echo "--- through the zig plug (checked transfer)"
python3 -u "$T/plug_run_checked.py" \
    "$REPO/codex/plugs/zig/build-output/zig-plug.cdx" \
    "$R/compiler.ir" "$R/Codex.zig"

echo "--- marker inventory"
grep -o 'zig plug: [^"]*' "$R/Codex.zig" | sort | uniq -c | sort -rn | tee "$R/markers.txt"
echo "--- zig typecheck (first 40 errors)"
(cd "$R" && timeout 900 zig build-exe Codex.zig -fno-emit-bin 2>&1 | head -60) || true
