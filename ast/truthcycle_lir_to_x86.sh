#!/bin/bash
# lir_to_x86 truth arm: bare-metal emitted-byte dump banked as lir_to_x86.truth.
set -e
. "$(dirname "$0")/oracle_lib.sh"
truth_arm lir_to_x86
