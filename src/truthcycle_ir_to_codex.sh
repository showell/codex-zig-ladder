#!/bin/bash
# ir_to_codex truth arm: bare-metal codex-text emission banked as ir_to_codex.truth.
set -e
. "$(dirname "$0")/oracle_lib.sh"
truth_arm ir_to_codex
