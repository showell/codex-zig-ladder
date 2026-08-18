#!/bin/bash
# scale has no truth arm of its own: it is the second subject of the fibx unit,
# so the only way to produce scale.truth is to run that unit, which produces
# both. This is the same one compile the ladder now pays once instead of twice.
set -e
. "$(dirname "$0")/oracle_lib.sh"
echo "scale rides in the fibx unit ($(unit_rungs fibx)); running that, which banks both"
truth_arm fibx
