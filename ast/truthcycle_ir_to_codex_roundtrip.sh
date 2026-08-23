#!/bin/bash
# Stage 2 of the fixed point: compile stage 1's emitted text and emit again.
# ir_to_codex.truth == ir_to_codex_roundtrip.truth is the whole claim, so it
# is checked here rather than asserted: roundtrip_fixed_point is the test
# that comment was.
set -e
. "$(dirname "$0")/oracle_lib.sh"
truth_arm ir_to_codex_roundtrip
roundtrip_fixed_point
