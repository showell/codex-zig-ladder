#!/bin/bash
# ir_to_x86_on_cce has no zig arm of its own: one .zig comes out of the
# ir_to_x86 unit and answers for every subject in it, and zig_verdict splits
# it before diffing. Running that arm produces this rung's .zigout and .diff
# along with ir_to_x86_on_fib's.
set -e
. "$(dirname "$0")/oracle_lib.sh"
echo "ir_to_x86_on_cce rides in the ir_to_x86 unit ($(unit_rungs ir_to_x86)); running that arm, which diffs both"
$(arm_for ir_to_x86) ir_to_x86
