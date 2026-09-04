#!/bin/bash
# lir_to_x86 zig arm: the same subject through the plug, diffed.
set -e
. "$(dirname "$0")/oracle_lib.sh"
zig_arm lir_to_x86
