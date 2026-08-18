#!/bin/bash
# scale has no zig arm of its own: one .zig comes out of the fibx unit and answers
# for every subject in it, and zig_verdict splits it before diffing. Running
# that arm produces scale.zigout and scale.diff along with fibx's.
set -e
. "$(dirname "$0")/oracle_lib.sh"
echo "scale rides in the fibx unit ($(unit_rungs fibx)); running that arm, which diffs both"
$(arm_for fibx) fibx
