#!/bin/bash
# passes_to_x86_on_arith has no zig arm of its own: one .zig comes out of
# the passes_to_x86 unit and answers for every subject in it, and zig_verdict
# splits it before diffing. Running that arm produces this rung's .zigout and
# .diff along with passes_to_x86_on_mid's.
set -e
. "$(dirname "$0")/oracle_lib.sh"
echo "passes_to_x86_on_arith rides in the passes_to_x86 unit ($(unit_rungs passes_to_x86)); running that arm, which diffs both"
$(arm_for passes_to_x86) passes_to_x86
