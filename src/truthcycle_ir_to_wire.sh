#!/bin/bash
# ir_to_wire truth arm: the front-end chain on fib, IR text banked as ir_to_wire.truth.
set -e
. "$(dirname "$0")/oracle_lib.sh"
truth_arm ir_to_wire
