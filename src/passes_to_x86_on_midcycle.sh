#!/bin/bash
# passes_to_x86 zig arm: the same emission through the plug, diffed.
set -e
. "$(dirname "$0")/oracle_lib.sh"
$(arm_for passes_to_x86) passes_to_x86
