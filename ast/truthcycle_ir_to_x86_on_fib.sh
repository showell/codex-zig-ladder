#!/bin/bash
# ir_to_x86 truth arm: fib through the tree emitter, both rungs' truths recorded.
set -e
. "$(dirname "$0")/oracle_lib.sh"
truth_arm ir_to_x86
