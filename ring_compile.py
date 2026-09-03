# Compile via codex-vm's ring-preload contract under QEMU: the input blob
# (mode line + unit + EOT) is placed at guest phys 0x500000 by the generic
# loader pre-boot, and the write-pos cell (zeroed by the boot stub) is
# re-injected post-READY through the gdbstub — the same re-injection
# codex-vm does on the guest's first LSR read. No streamed serial input,
# so the QEMU 6.2 chardev stall has nothing to race against.
# Serial stays for output only (READY, logs, SIZE:<n>, binary).
#
# Blobs larger than the 1 MB ring stream through it: both ring positions
# are unbounded counters masked at access (X86_64Boot.codex, cells 28704/
# 28712), so the host refills from behind the guest's read cursor and the
# ring becomes a window. ring_refill_test.sh is the oracle for that path.
import os
import pathlib
import re
import socket
import sys
import bisect
import time

import codex_vm
from ladder_root import CODEX

REPO = str(CODEX)
# The accel contract and the kernel-irqchip=off workaround live in
# codex_vm.launch now, with the guest, so this file cannot disagree with
# it about CODEX_ACCEL again -- it did, hard-coding tcg while codex_vm
# read the environment.
# CODEX_MEM_MB sizes the guest for smaller hosts (the droplet has 2 GB).
MEM_MB = int(os.environ.get("CODEX_MEM_MB", "3072"))
RING_ADDR = 0x500000
RING_SIZE = 0x100000          # 1 MB, must match seed's serial-ring-buf-size
WPOS_ADDR = 28704             # 0x7020
RPOS_ADDR = 28712             # 0x7028

class Gdb:
    def __init__(self, port):
        self.s = socket.create_connection(("127.0.0.1", port), timeout=10)
        # TCP_NODELAY, or every gdbstub round trip costs a delayed ACK.
        # cmd() acks a reply with a bare "+" and then sends the next
        # packet as a separate small write, which is exactly the pattern
        # Nagle holds until the "+" is acknowledged -- and the peer sits
        # on that ack for 40 ms. Measured on the 2.9 MB compiler source
        # (DONE 2026-08-24): 41 ms per 1 KB M packet, giving 25 KB/s and
        # 99% of a ring fill spent writing, against a guest draining the
        # whole 1 MB ring in under 191 ms. The stall was the transport,
        # not the ring, the poll interval, or the guest.
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.s.settimeout(5)
        # QEMU halts the VM on connect and may emit a spontaneous stop
        # packet; drain and ack anything queued before the first command.
        self.s.settimeout(0.8)
        try:
            while True:
                junk = self.s.recv(4096)
                if not junk:
                    break
                if b"$" in junk:
                    self.s.sendall(b"+")
        except (TimeoutError, OSError):
            pass
        self.s.settimeout(5)

    def _cks(self, payload):
        return sum(payload) % 256

    def cmd(self, payload):
        pkt = b"$" + payload + b"#" + b"%02x" % self._cks(payload)
        self.s.sendall(pkt)
        buf = b""
        while True:
            c = self.s.recv(4096)
            if not c:
                raise RuntimeError("gdb closed")
            buf += c
            if b"#" in buf[1:]:
                start = buf.index(b"$")
                end = buf.index(b"#", start)
                self.s.sendall(b"+")
                return buf[start + 1:end]

    def write_mem(self, addr, data):
        payload = b"M%x,%x:" % (addr, len(data)) + data.hex().encode()
        r = self.cmd(payload)
        if r != b"OK":
            raise RuntimeError(f"gdb write @{addr:#x} failed: {r!r}")

    def read_mem(self, addr, n):
        r = self.cmd(b"m%x,%x" % (addr, n))
        if r.startswith(b"E") or len(r) != n * 2:
            raise RuntimeError(f"gdb read @{addr:#x} unexpected reply: {r!r}")
        return bytes.fromhex(r.decode())

    def cont_nowait(self):
        # 'c' replies only at the next stop, so consume just the '+' ack.
        payload = b"c"
        pkt = b"$" + payload + b"#" + b"%02x" % self._cks(payload)
        self.s.sendall(pkt)
        self.s.recv(1)

    def interrupt(self):
        # Raw 0x03 stops a running target; QEMU answers with a stop packet.
        self.s.sendall(b"\x03")
        buf = b""
        while True:
            c = self.s.recv(4096)
            if not c:
                raise RuntimeError("gdb closed during interrupt")
            buf += c
            if b"#" in buf[1:]:
                self.s.sendall(b"+")
                return

    def read_pc(self):
        """RIP, so a stall can be told apart from a wedge.

        `rpos` not moving means the guest is not CONSUMING. It says nothing
        about whether the guest is running: a compiler legitimately reads
        nothing for as long as it takes to check a chapter. Watching RIP as
        well is what separates "busy" from "stuck", and QEMU's x86-64 gdbstub
        numbers RIP 16 (0x10).
        """
        try:
            r = self.cmd(b"p10")
        except Exception:
            return None
        if r.startswith(b"E") or len(r) < 16:
            return None
        return int.from_bytes(bytes.fromhex(r.decode()[:16]), "little")

    def detach(self):
        try:
            self.cmd(b"D")
        except Exception:
            pass
        self.s.close()

def _load_symbols(seed_path):
    """The seed's symbol map, for naming the address a stall sits on.

    `seed/Codex.map` is written beside every kernel: `0xADDR SIZE name`. The
    guest here IS the seed, so a stalled RIP resolves to the seed's own
    function -- which turns "the guest stopped" into "the guest is in
    <name>", the difference between a mystery and a lead.
    """
    m = re.sub(r"\.cdx$", ".map", str(seed_path))
    try:
        rows = []
        for line in open(m, "r", errors="replace"):
            if line.startswith("#"):
                continue
            parts = line.split(None, 2)
            if len(parts) == 3 and parts[0].startswith("0x"):
                rows.append((int(parts[0], 16), int(parts[1]), parts[2].strip()))
        rows.sort()
        return rows
    except Exception:
        return []


def _symbolize(pc, rows):
    if pc is None or not rows:
        return "?"
    i = bisect.bisect_right(rows, (pc, 1 << 62, "")) - 1
    if i < 0:
        return f"{pc:#x}"
    addr, size, name = rows[i]
    if pc < addr + size:
        return f"{name}+{pc - addr:#x}"
    return f"{pc:#x} (past {name})"


def compile_ring(blob_path, out_path, mem_mb=MEM_MB, timeout=1800, seed=None,
                 sentinel=None):
    """Feed a blob through the ring and capture what the guest prints.

    `sentinel` is for a guest that STREAMS rather than frames. The compiler and
    the zig plug both know their output's length before they emit a byte, so
    they announce `SIZE:<n>` and the capture below reads exactly that many
    bytes. A streaming emitter cannot: the wasm plug prints its module as it
    walks the IR precisely because holding the whole text would cost a
    quadratic number of allocations against a bump allocator that never
    reclaims. Given a sentinel, the capture instead ends at that byte string and
    writes everything before it -- so the two guests differ in their framing
    and in nothing else, and the ring, the preload and the refill loop stay one
    implementation rather than two.
    """
    blob = open(blob_path, "rb").read()
    # Both ring positions are unbounded counters masked at access on both
    # the ISR write side and the __bare_metal_read_serial read side, so
    # 1 MB is a WINDOW, not a ceiling: a blob larger than the ring stages
    # its first megabyte through the loader and the rest is refilled from
    # behind the guest's read cursor (see the refill loop below). The
    # single-shot path for blobs that fit is unchanged.
    staged = min(len(blob), RING_SIZE)
    stage_path = blob_path
    if len(blob) > RING_SIZE:
        stage_path = blob_path + ".stage1"
        with open(stage_path, "wb") as f:
            f.write(blob[:RING_SIZE])
    # The ring's two additions to the standard command line: the staged
    # first megabyte preloaded at RING_ADDR, and a gdbstub to drive the
    # ring cursors with the VM stopped. Everything else -- accel, the two
    # chardevs, the 0xFE8 RAM cell, isa-debug-exit -- is codex_vm.launch's,
    # which is the point: this file kept its own copy of all of it and the
    # copy drifted twice.
    gp = codex_vm.free_port()
    proc, data, ctrl = codex_vm.launch(
        seed or f"{REPO}/seed/Codex.cdx", mem_mb, extra_args=[
            "-device", f"loader,file={stage_path},addr={hex(RING_ADDR)},force-raw=on",
            "-gdb", f"tcp:127.0.0.1:{gp}",
        ])
    try:
        t0 = time.time()
        # codex_vm.wait_ready, not a local loop: the local copy lacked the
        # EOF check, so once QEMU died the ctrl socket returned b"" instantly
        # and forever -- a 100% spin with a frozen log until killed by hand
        # (PRIORITIES 7; the timeout only ever covered a live-but-silent
        # guest).
        codex_vm.wait_ready(ctrl, timeout=120)
        print(f"READY at {time.time()-t0:.1f}s; injecting wpos={staged} via gdbstub", flush=True)

        gdb = Gdb(gp)
        gdb.cmd(b"?")                       # attach/halt handshake
        ring_head = gdb.read_mem(RING_ADDR, 8)
        if ring_head != blob[:8]:
            raise RuntimeError(f"ring preload mismatch: {ring_head!r} vs {blob[:8]!r}")
        gdb.write_mem(WPOS_ADDR, staged.to_bytes(8, "little"))
        gdb.write_mem(RPOS_ADDR, (0).to_bytes(8, "little"))
        back = gdb.read_mem(WPOS_ADDR, 8)
        print(f"wpos cell now {int.from_bytes(back, 'little')}; ring head verified", flush=True)

        if staged < len(blob):
            # Refill from behind the read cursor. The VM is stopped for
            # every cell access: the gdbstub writes memory byte-wise, so a
            # wpos update racing the guest's own load could tear and send
            # the reader past real data.
            #
            # The loop runs until the guest has CONSUMED everything, not
            # merely until everything is delivered. A reader that finds
            # the ring dry mid-stream parks in hlt, and nothing on this
            # path ever wakes it -- streamed serial wakes it through UART
            # interrupts, and the preload path has no serial input by
            # design. Each round's stop/resume doubles as that missing
            # wake, so detaching before rpos catches wpos would leave the
            # guest asleep beside a full ring.
            wpos = staged
            stalled = 0
            last_rpos = -1
            t_fill = time.time()
            # Room free at wake is what the guest drained while the host
            # slept; the write duration is what the gdbstub costs to put
            # it back. That pair is what convicted Nagle on the gdb
            # socket (see Gdb.__init__), and it stays because a transport
            # this fast is one regression away from being slow again
            # without anything else noticing.
            #
            # With NODELAY the 2.9 MB compiler fills in 0.7 s and the
            # guest still drains the whole ring between polls, so the
            # 150 ms sleep is now the larger half of a negligible cost.
            # Shortening it buys tenths of a second on a compile measured
            # in minutes; it is not worth the extra guest stops.
            t_write_total = 0.0
            rounds = 0
            dry_rounds = 0
            # WHAT A STALL IS, AND WHAT IT IS NOT.
            #
            # `rpos` standing still means the guest is not CONSUMING. It does
            # not mean the guest has stopped: the compiler reads nothing at all
            # while it checks a chapter, and the biggest subjects go tens of
            # seconds between reads. The old rule -- 400 rounds of no rpos, so
            # about 60 seconds -- could not tell those apart, so it was both too
            # tight for a slow guest and far too slack for a wedged one.
            #
            # RIP separates them. A guest that is executing moves its program
            # counter; a guest that is wedged does not, or cycles a handful of
            # addresses. So:
            #
            #   PC pinned or cycling a tiny set  -> WEDGED, fail fast and name
            #                                       the seed function it is in
            #   PC ranging widely, rpos frozen   -> BUSY, keep waiting up to a
            #                                       hard wall-clock cap
            #
            # Both knobs are env-settable so the thresholds can be measured
            # rather than argued about.
            stall_rounds = int(os.environ.get("RING_STALL_ROUNDS", "400"))
            hard_secs = float(os.environ.get("RING_STALL_HARD_SECS", "900"))
            # RING_TEST_NO_REFILL exists so the detector above can be PROVEN to
            # work. A healthy run stalls zero rounds -- the guest drains 1.2 MB
            # in 0.3s -- so the stall branch never executes and every part of it
            # is untested code that has only ever reported success. Withholding
            # the refill parks the guest exactly where the real failure parked
            # it: everything staged consumed, rpos frozen at the ring size,
            # waiting for input that never comes. If the detector cannot see
            # THAT, it cannot see anything.
            no_refill = os.environ.get("RING_TEST_NO_REFILL") == "1"
            if no_refill:
                print("  [test] RING_TEST_NO_REFILL: refills withheld on purpose;"
                      " the guest is meant to stall", flush=True)
            symbols = _load_symbols(seed or f"{REPO}/seed/Codex.cdx")
            stall_pcs = {}
            max_stalled = 0
            t_stall0 = None
            gdb.cont_nowait()
            while True:
                t_wake = time.time()
                time.sleep(0.15)
                gdb.interrupt()
                rpos = int.from_bytes(gdb.read_mem(RPOS_ADDR, 8), "little")
                wait = time.time() - t_wake
                if rpos >= len(blob):
                    break
                room = RING_SIZE - (wpos - rpos)
                if room > 0 and wpos < len(blob) and not no_refill:
                    t_write = time.time()
                    chunk = blob[wpos:wpos + room]
                    off = 0
                    # 1 KB per M packet: hex doubles the payload and QEMU's
                    # gdbstub buffer is 4096 bytes, packet framing included.
                    while off < len(chunk):
                        piece = chunk[off:off + 1024]
                        pos = (wpos + off) & (RING_SIZE - 1)
                        head = min(len(piece), RING_SIZE - pos)
                        gdb.write_mem(RING_ADDR + pos, piece[:head])
                        if head < len(piece):
                            gdb.write_mem(RING_ADDR, piece[head:])
                        off += len(piece)
                    wpos += len(chunk)
                    gdb.write_mem(WPOS_ADDR, wpos.to_bytes(8, "little"))
                    dt_write = time.time() - t_write
                    t_write_total += dt_write
                    rounds += 1
                    print(f"  refill: wpos {wpos}/{len(blob)} rpos {rpos}"
                          f" room {room} wait {wait*1000:.0f}ms"
                          f" write {len(chunk)}B in {dt_write*1000:.0f}ms",
                          flush=True)
                elif wpos < len(blob):
                    # Woke with data still to send to a ring the guest had
                    # not drained a byte of. Rounds past the last byte are
                    # drain-wait, not straw width, so they do not count.
                    dry_rounds += 1
                if rpos != last_rpos:
                    stalled = 0
                    stall_pcs = {}
                    t_stall0 = None
                else:
                    stalled += 1
                    if t_stall0 is None:
                        t_stall0 = time.time()
                    pc = gdb.read_pc()
                    if pc is not None:
                        stall_pcs[pc] = stall_pcs.get(pc, 0) + 1
                    max_stalled = max(max_stalled, stalled)
                last_rpos = rpos
                if stalled > stall_rounds:
                    held = time.time() - t_stall0
                    top = sorted(stall_pcs.items(), key=lambda kv: -kv[1])[:6]
                    where = ", ".join(
                        f"{_symbolize(a, symbols)} x{n}" for a, n in top) or "no PC samples"
                    busy = len(stall_pcs) > 4
                    # A guest that is plainly EXECUTING is not a wedge, and
                    # killing it here is how a slow rung became a red one. Wait
                    # for the hard cap instead, and say so once.
                    if busy and held < hard_secs:
                        if stalled == stall_rounds + 1:
                            print(f"  [stall] rpos {rpos} frozen {held:.0f}s but the guest is"
                                  f" EXECUTING ({len(stall_pcs)} distinct PCs): {where}",
                                  flush=True)
                            print(f"  [stall] waiting up to {hard_secs:.0f}s"
                                  f" (RING_STALL_HARD_SECS)", flush=True)
                        gdb.cont_nowait()
                        continue
                    kind = ("BUSY past the hard cap" if busy
                            else f"WEDGED on {len(stall_pcs)} distinct PC(s)")
                    raise RuntimeError(
                        f"guest stopped consuming at rpos {rpos} of {len(blob)}"
                        f" -- {kind} after {held:.0f}s / {stalled} rounds; in {where}")
                gdb.cont_nowait()
            fill_secs = time.time() - t_fill
            print(f"ring refill consumed: {len(blob)} bytes in {fill_secs:.1f}s"
                  f" ({rounds} refills, {t_write_total:.1f}s of that in"
                  f" gdbstub writes ="
                  f" {100 * t_write_total / max(fill_secs, 1e-9):.0f}%,"
                  f" {dry_rounds} rounds with no room freed,"
                  f" longest stall {max_stalled} rounds of {stall_rounds})",
                  flush=True)
        print("detaching", flush=True)
        gdb.detach()

        # From here: output-only serial, same SIZE-aware read as compile_blob.
        data.settimeout(5)
        out = b""
        deadline = time.time() + timeout
        needed = None
        t1 = time.time()
        while time.time() < deadline:
            try:
                chunk = data.recv(65536)
            except socket.timeout:
                if needed is not None and len(out) >= needed:
                    break
                continue
            except OSError:
                break
            if not chunk:
                break
            out += chunk
            if needed is None and sentinel is not None:
                idx0 = out.find(sentinel)
                if idx0 >= 0:
                    needed = idx0 + len(sentinel)
            if needed is None:
                idx0 = out.find(b"SIZE:")
                if idx0 >= 0 and b"\n" in out[idx0:]:
                    nl0 = out.index(b"\n", idx0)
                    needed = nl0 + 1 + int(out[idx0 + 5:nl0].split()[0])
                elif b"CODEGEN-HALTED" in out or b"CODEGEN-ERRORS" in out:
                    needed = len(out)
            if needed is not None and len(out) >= needed:
                data.settimeout(2)
        print(f"stream: {len(out)} bytes in {time.time()-t1:.0f}s", flush=True)
        if sentinel is not None:
            # A streaming guest has no header to separate: everything before the
            # sentinel IS the payload, diagnostics included, and the caller owns
            # sorting them out. Refusing loudly here beats writing a file whose
            # first line is a compiler complaint.
            idx = out.find(sentinel)
            if idx < 0:
                print(f"NO SENTINEL {sentinel!r} - the guest did not finish",
                      flush=True)
                print(out[-800:].decode(errors="replace"), flush=True)
                return False
            open(out_path, "wb").write(out[:idx])
            print(f"wrote {out_path} ({idx} bytes before {sentinel.decode()})",
                  flush=True)
            return True
        idx = out.find(b"SIZE:")
        header = out[:idx if idx >= 0 else len(out)].decode(errors="replace")
        # Every diagnostic goes to a file; the console gets a census and a
        # sample. The console cap was a fair call -- a sweep that narrates
        # thousands of lines is unreadable -- but capping at twelve and
        # DISCARDING the rest cost us something real: 108-plus duplicate-
        # definition warnings from one self-inflicted bundling bug filled
        # those twelve slots for months, and while they did, CDX6020
        # (`__record-set` mutates in place, which is finding 10's territory)
        # and CDX2053 never reached the log at all. They were not new when
        # they appeared; they were merely no longer displaced.
        #
        # A harness whose premise is that a disagreement is evidence does not
        # get to throw evidence away because there is a lot of it.
        diags = [l for l in header.splitlines()
                 if l.strip() and not l.startswith("WD:")]
        # A clean compile REMOVES the sidecar rather than leaving last run's:
        # a stale .diags feeds check_diags yesterday's population, keeping a
        # vanished class "present" and defeating the POPULATION MOVED
        # detection the census claims to make.
        dpath = pathlib.Path(str(out_path) + ".diags")
        dpath.unlink(missing_ok=True)
        if diags:
            dpath.write_text("\n".join(diags) + "\n")
            census = {}
            for l in diags:
                m = re.search(r"CDX\d{4}", l)
                census[m.group(0) if m else "other"] = census.get(
                    m.group(0) if m else "other", 0) + 1
            summary = "  ".join(f"{k}x{v}" for k, v in sorted(census.items()))
            print(f"  | {len(diags)} diagnostics -> {dpath.name}   {summary}",
                  flush=True)
            for line in diags[:12]:
                print("  |", line, flush=True)
            if len(diags) > 12:
                print(f"  | ... {len(diags) - 12} more in {dpath.name}",
                      flush=True)
        if idx < 0:
            print("NO SIZE MARKER — compile failed or errored", flush=True)
            return False
        nl = out.index(b"\n", idx)
        size = int(out[idx + 5:nl].split()[0])
        binary = out[nl + 1:nl + 1 + size]
        print(f"  SIZE: {size}, got {len(binary)}", flush=True)
        if len(binary) != size:
            print("SHORT BINARY", flush=True)
            return False
        open(out_path, "wb").write(binary)
        print(f"wrote {out_path}", flush=True)
        trailer = out[nl + 1 + size:]
        if trailer.strip():
            open(out_path + ".map", "wb").write(trailer)
            print(f"wrote {out_path}.map ({len(trailer)} bytes)", flush=True)
        return True
    finally:
        proc.kill()
        proc.wait()

if __name__ == "__main__":
    ok = compile_ring(sys.argv[1], sys.argv[2])
    sys.exit(0 if ok else 1)
