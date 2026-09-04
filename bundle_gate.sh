#!/bin/bash
# Two bundlers, one checkout, same instant: do they agree byte for byte?
#
#   ./bundle_gate.sh
#
# The Rust front end resolves its own cites (rust-codex-compiler `src/bundle.rs`)
# and every other arm's unit comes from `cite_resolve.py`. That is the point of
# having written the second one: a bundling bug applied identically to all four
# arms is one no comparison between them can find, so the bundler is the one
# component the ladder cannot falsify by agreement. This is what falsifies it.
#
# IT GENERATES THE PYTHON UNITS FRESH, and that is not an optimisation to skip.
# Run against a units directory banked days ago, most of the diff is upstream's
# own prose edits between then and now -- 33 units differed that way on the first
# run and not one of them was a bundler disagreeing. A gate that reports the
# checkout moving is not a gate on the bundlers.
#
# WHAT A DIFFERENCE MEANS: a finding, until someone shows it is a bug in the Rust
# arm. It is never a reason to go back to using one bundler for everything.
#
# The known and filed exception is CRLF: 20 chapters upstream are committed with
# carriage returns, Python's text-mode read drops them and Rust keeps the bytes,
# so those units differ by exactly that (issue 124). Five corpus units are in
# that set today.
set -uo pipefail
T="$(cd "$(dirname "$0")" && pwd)"
BUNDLE="${CODEXBUNDLE:-${CARGO_TARGET_DIR:-$HOME/build/rust-target}/release/bundle}"
[ -x "$BUNDLE" ] || { echo "no bundle binary at $BUNDLE; set CODEXBUNDLE" >&2; exit 2; }
: "${CODEX_ROOT:?CODEX_ROOT names the checkout both bundlers must read}"

units="$(mktemp -d)"; trap 'rm -rf "$units"' EXIT
echo "resolving the corpus with cite_resolve.py ..."
"$T/resolve_corpus.py" "$units" > "$units/.log" 2>&1
echo "  $(find "$units" -name '*.codex' | wc -l) units, $(grep -c 'cites' "$units/.log" || true) unresolved cites reported"
rm -f "$units/.log"

echo "comparing against the Rust resolver ..."
"$BUNDLE" diff "$units" "$CODEX_ROOT/codex/test"
