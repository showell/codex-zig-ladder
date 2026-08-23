#!/bin/bash
# passes_to_x86 truth arm: every chapter but the driver, through the back end; both rungs' truths recorded.
set -e
. "$(dirname "$0")/oracle_lib.sh"
truth_arm passes_to_x86
