#!/bin/bash
# Does the diagnostics reporter work, and did it leave the artifact alone?
#
#   ./verify.sh <path-to-codexzig>
#
# Three checks, and the second and third are why this is a script rather than a
# command. A reporter that prints something for every program passes the first
# and is worthless; a reporter that leaks into stderr passes the first two and
# breaks every consumer of the emitted zig.
set -u
CZ="${1:?usage: verify.sh <codexzig binary>}"
D="$(cd "$(dirname "$0")" && pwd)"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
rc=0

run () {   # run <name> -> $T/<name>.zig (stderr) and $T/<name>.out (stdout)
    "$CZ" < "$D/$1.codex" 2> "$T/$1.zig" > "$T/$1.out"
}

echo "== 1. a program with a WARNING reports it, and still compiles"
run warns
n=$(grep -c 'CDX3005' "$T/warns.out" || true)
if [ "$n" = 1 ]; then echo "   PASS: one CDX3005 on stdout"; sed 's/^/     /' "$T/warns.out"
else echo "   FAIL: expected 1 CDX3005 on stdout, got $n"; cat "$T/warns.out"; rc=1; fi
grep -q 'pub fn main' "$T/warns.zig" \
    && echo "   PASS: it still emitted a program (warning is not an error)" \
    || { echo "   FAIL: no program emitted"; rc=1; }

echo "== 2. a CLEAN program reports NOTHING"
run clean
if [ -s "$T/clean.out" ]; then
    echo "   FAIL: stdout should be empty, holds:"; sed 's/^/     /' "$T/clean.out"; rc=1
else echo "   PASS: stdout empty -- the reporter relays, it does not manufacture"; fi

echo "== 3. the emitted zig is UNTOUCHED by any of this"
grep -q 'CDX3005\|codexzig:' "$T/warns.zig" \
    && { echo "   FAIL: a diagnostic leaked into the emitted zig"; rc=1; } \
    || echo "   PASS: no diagnostic text in the artifact"
echo "   warns.zig $(wc -c < "$T/warns.zig") bytes, clean.zig $(wc -c < "$T/clean.zig") bytes"

exit $rc
