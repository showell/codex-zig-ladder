#!/bin/bash
# ir_to_wire zig arm: the same chain through the plug, diffed.
set -e
. "$(dirname "$0")/oracle_lib.sh"
zig_arm ir_to_wire
