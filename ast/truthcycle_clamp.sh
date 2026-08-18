#!/bin/bash
# clamp has no truth arm of its own: it is the second subject of the whole unit,
# so the only way to produce clamp.truth is to run that unit, which produces
# both. This is the same one compile the ladder now pays once instead of twice.
set -e
. "$(dirname "$0")/oracle_lib.sh"
echo "clamp rides in the whole unit ($(unit_rungs whole)); running that, which banks both"
truth_arm whole
