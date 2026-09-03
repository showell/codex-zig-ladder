#!/usr/bin/env python3
"""Generate ZigcHarness.codex: a Codex compiler that runs as a normal process.

The whole rung proves the transpiled compiler emits the right bytes. It
cannot prove the transpiled compiler is usable, because its subject is a Text
literal baked in at bundle time and its output is a decimal dump. This is the
same compiler with a real I/O boundary: source in on stdin, CDX out on
stdout.

IT NO LONGER STANDS IN FOR opening.codex -- it CALLS it. Update 55 split the
entry point out, so Chapter: Opening is bundlable by a subject supplying its
own `opening`, and this harness is two driver calls where it was thirty lines
of copied phase order and deck arithmetic. What follows described the copy:

It used to stand in for opening.codex, which needs an operating system -- its effect
row is [Console, FileSystem, Device.Block], it paints progress on a
framebuffer and it reads and writes a FAT16 volume. This keeps the half that
compiles and drops the half that needs a machine, which is the difference
between a driver and a kernel.

Verification is not a ladder oracle: nothing bare-metal runs this harness.
The check is direct and stronger -- compile a program with the zig binary,
compile the same program with the seed, and the two CDX files must be equal.
"""
import pathlib

from emit_harness import driver_cdx_source, HOSTED_DECK_BYTES

HERE = pathlib.Path(__file__).parent

out = f'''Chapter: ZigcHarness

Section: Driver

 read-file-uni takes a path and the zig plug opens it: cx_read_file_uni is an
 openat of the path it is given, read to EOF. So "/dev/stdin" is doing real
 work here rather than standing in for something -- it is how a hosted process
 names the stream it was handed.

 The C# plug emits _Cce.ReadStream() and drops the argument, reading stdin
 whatever it is passed. The same source therefore runs under both, and it does
 so because this path names the stream C# would have read anyway, not because
 the argument goes unread twice.

  opening : [Console, FileSystem] Nothing = act
    src <- read-file-uni "/dev/stdin"
    {driver_cdx_source("src", deck_bytes=HOSTED_DECK_BYTES)}
    in act
      write-binary (res.header-bytes)
      write-binary-buf (res.content-buf) 0 (res.content-len)
      write-binary (res.tail-bytes)
    end
  end
'''

dest = HERE / 'ZigcHarness.codex'
dest.write_text(out)
print(f'{dest}: {len(out)} bytes')
