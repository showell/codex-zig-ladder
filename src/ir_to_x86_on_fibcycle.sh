#!/bin/bash
# ir_to_x86 zig arm: the same emission through the plug, diffed. One .zig
# answers for both rungs the unit carries. Which transport it needs is
# arm_for's to say, not this script's -- it said zig_arm here for a while
# after the sweep had already moved the unit to the ring, so the two
# disagreed about what the rung even ran.
set -e
. "$(dirname "$0")/oracle_lib.sh"
$(arm_for ir_to_x86) ir_to_x86
