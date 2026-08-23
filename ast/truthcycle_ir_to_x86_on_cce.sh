#!/bin/bash
# ir_to_x86_on_cce has no truth arm of its own: it is the second subject of
# the ir_to_x86 unit, so the only way to produce its truth is to run that
# unit, which produces both. This is the same one compile the ladder now pays once instead of twice.
set -e
. "$(dirname "$0")/oracle_lib.sh"
echo "ir_to_x86_on_cce rides in the ir_to_x86 unit ($(unit_rungs ir_to_x86)); running that, which records both"
truth_arm ir_to_x86
