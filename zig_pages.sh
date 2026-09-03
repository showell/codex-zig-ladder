#!/bin/bash
# Print the pages of Chapter: Zig Emitter as a PowerShell array literal body:
#
#     'ZigEmitter','ZigEmitterExpressions','ZigEmitterApply','ZigPrelude'
#
# The bundlers splice it into -Chapters. THE LIST LIVES IN ONE FILE because it
# lived in three and they drifted: when the emitter went from one file to four,
# only the author's build.ps1 learned about it and the ladder bundled page 1
# alone -- 17 x CDX3002 naming definitions that were sitting in files nobody
# asked for.
set -e
T="$(cd "$(dirname "$0")" && pwd)"
list="$T/zig_plug_pages.txt"
[ -s "$list" ] || { echo "missing $list" >&2; exit 1; }
out=$(grep -v '^[[:space:]]*#' "$list" | grep -v '^[[:space:]]*$' \
      | sed "s/^[[:space:]]*//;s/[[:space:]]*$//;s/.*/'&'/" | paste -sd, -)
[ -n "$out" ] || { echo "$list names no pages" >&2; exit 1; }
printf '%s' "$out"
