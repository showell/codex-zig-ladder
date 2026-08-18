#!/bin/bash
# clamp has no zig arm of its own: one .zig comes out of the whole unit and answers
# for every subject in it, and zig_verdict splits it before diffing. Running
# that arm produces clamp.zigout and clamp.diff along with whole's.
set -e
. "$(dirname "$0")/oracle_lib.sh"
echo "clamp rides in the whole unit ($(unit_rungs whole)); running that arm, which diffs both"
$(arm_for whole) whole
