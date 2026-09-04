#!/usr/bin/env python3
"""Where do the deck bytes go? A per-site allocation census for an emitted
program.

The prelude's CX-DECK line says how MUCH the deck grew; this says WHO grew
it. Every allocation funnels through one vtable (cx_bump_alloc / resize /
free), so the patch keys each byte by two return addresses: the allocator
call site (which prelude helper -- cx_new, cx_ll_empty, a list growth) and
the outermost cx_deck_enter (which deck-record bracket in the program).
Main-heap bytes are keyed by call site alone. The table is dumped to STDOUT
every 32 MB of deck growth and at the exhaust panic, so a run that dies
still reports; the truth stream is stderr and is untouched.

    ./deck_census.py patch  src/codexir.zig src/codexir-census.zig [slack_mb] [reserve_mb]
    zig build-exe src/codexir-census.zig -femit-bin=native/codexir-census
    ./native/codexir-census < subject > census.out 2> subject.ir
    ./deck_census.py report census.out native/codexir-census

The binary built from the patched source is an INSTRUMENT, not pipeline
output: say so in the sandbox MANIFEST. Symbolisation is by function name
through addr2line; zig 0.16's DWARF has forms binutils cannot read for line
numbers, so sites resolve to functions, which for a one-expression-per-def
program is the bracket.

This is how finding 24's "volume" half was answered 2026-08-22: no family
grows superlinearly; the harness's single deck was sized by a placeholder.
findings/README.md 24, JUSTIFICATIONS "deck census".
"""
import collections
import pathlib
import subprocess
import sys

TABLE = r'''
// ---- deck census: bytes by (allocator call site, bracket site) ----
const CxSite = struct { ra: usize = 0, br: usize = 0, bytes: i64 = 0, n: i64 = 0 };
var cx_sites: [8192]CxSite = [_]CxSite{.{}} ** 8192;
var cx_site_count: usize = 0;
var cx_site_dropped: i64 = 0;
var cx_cur_bracket: usize = 0;
var cx_main_bytes: i64 = 0;
var cx_deck_bytes: i64 = 0;
var cx_dump_stride: i64 = 0;
var cx_dump_seq: i64 = 0;
fn cx_site_add(ra: usize, br: usize, bytes: i64) void {
    var h: usize = (ra *% 0x9E3779B97F4A7C15) ^ (br *% 0xC2B2AE3D27D4EB4F);
    h = (h >> 17) & 8191;
    var i: usize = 0;
    while (i < 8192) : (i += 1) {
        const k = (h + i) & 8191;
        const s = &cx_sites[k];
        if (s.n == 0 and s.ra == 0) {
            if (cx_site_count >= 7000) { cx_site_dropped += bytes; return; }
            s.ra = ra; s.br = br; cx_site_count += 1;
        }
        if (s.ra == ra and s.br == br) { s.bytes += bytes; s.n += 1; return; }
    }
    cx_site_dropped += bytes;
}
fn cx_census_dump(why: []const u8) void {
    cx_dump_seq += 1;
    var b: [256]u8 = undefined;
    var s = std.fmt.bufPrint(&b, "CENSUS dump seq={d} why={s} deck_bytes={d} main_bytes={d} used={d} sites={d} dropped={d}\n", .{ cx_dump_seq, why, cx_deck_bytes, cx_main_bytes, cx_deck_hw - cx_deck_base, cx_site_count, cx_site_dropped }) catch return;
    _ = std.os.linux.write(1, s.ptr, s.len);
    for (cx_sites) |e| {
        if (e.n == 0 and e.ra == 0) continue;
        s = std.fmt.bufPrint(&b, "CENSUS site seq={d} ra=0x{x} br=0x{x} bytes={d} n={d}\n", .{ cx_dump_seq, e.ra, e.br, e.bytes, e.n }) catch continue;
        _ = std.os.linux.write(1, s.ptr, s.len);
    }
}
fn cx_census_account(ra: usize, bytes: i64) void {
    if (cx_nest > 0) {
        cx_deck_bytes += bytes;
        cx_site_add(ra, cx_cur_bracket, bytes);
        if (cx_deck_bytes - cx_dump_stride >= 33554432) { cx_dump_stride = cx_deck_bytes; cx_census_dump("stride"); }
    } else { cx_main_bytes += bytes; cx_site_add(ra, 0, bytes); }
}
'''

# (old, new) pairs against the prelude text ZigEmitter emits. Each must match
# exactly once; a zero count means the prelude moved and this file is stale.
EDITS = [
    ('const cx_gpa = std.mem.Allocator{ .ptr = undefined, .vtable = &cx_heap_vtable };\n',
     'const cx_gpa = std.mem.Allocator{ .ptr = undefined, .vtable = &cx_heap_vtable };\n' + TABLE),
    ('fn cx_bump_alloc(_: *anyopaque, len: usize, alignment: std.mem.Alignment, _: usize) ?[*]u8 {\n'
     '    const base = alignment.forward(@intCast(cx_hp));\n'
     '    if (base + len > cx_heap_reserve) std.debug.panic(',
     'fn cx_bump_alloc(_: *anyopaque, len: usize, alignment: std.mem.Alignment, cx_ra: usize) ?[*]u8 {\n'
     '    const base = alignment.forward(@intCast(cx_hp));\n'
     '    cx_census_account(cx_ra, @as(i64, @intCast(base + len)) - cx_hp);\n'
     '    if (base + len > cx_heap_reserve) cx_census_dump("exhausted");\n'
     '    if (base + len > cx_heap_reserve) std.debug.panic('),
    ('fn cx_bump_resize(_: *anyopaque, memory: []u8, _: std.mem.Alignment, new_len: usize, _: usize) bool {',
     'fn cx_bump_resize(_: *anyopaque, memory: []u8, _: std.mem.Alignment, new_len: usize, cx_ra: usize) bool {'),
    ('        if (cx_frontier_crosses(off, new_len)) return false;\n        cx_hp = @intCast(off + new_len);\n',
     '        if (cx_frontier_crosses(off, new_len)) return false;\n'
     '        cx_census_account(cx_ra, @as(i64, @intCast(off + new_len)) - cx_hp);\n'
     '        cx_hp = @intCast(off + new_len);\n'),
    ('fn cx_bump_free(_: *anyopaque, memory: []u8, _: std.mem.Alignment, _: usize) void {\n'
     '    const off = @intFromPtr(memory.ptr) - @intFromPtr(cx_heap_base());\n'
     '    if (off + memory.len == @as(usize, @intCast(cx_hp))) cx_hp = @intCast(off);',
     'fn cx_bump_free(_: *anyopaque, memory: []u8, _: std.mem.Alignment, cx_ra: usize) void {\n'
     '    const off = @intFromPtr(memory.ptr) - @intFromPtr(cx_heap_base());\n'
     '    if (off + memory.len == @as(usize, @intCast(cx_hp))) { cx_census_account(cx_ra, @as(i64, @intCast(off)) - cx_hp); cx_hp = @intCast(off); }'),
    ('fn cx_deck_enter() i64 {\n    if (cx_nest == 0) {\n        cx_bivy = cx_hp;\n        cx_hp = cx_dptr;\n    }',
     'fn cx_deck_enter() i64 {\n    if (cx_nest == 0) {\n        cx_cur_bracket = @returnAddress();\n        cx_bivy = cx_hp;\n        cx_hp = cx_dptr;\n    }'),
]


def patch(src_path, out_path, slack_mb=0, reserve_mb=None):
    src = pathlib.Path(src_path).read_text()
    edits = list(EDITS)
    edits.append(('const cx_deck_slack: i64 = 0;',
                  f'const cx_deck_slack: i64 = {slack_mb * 1024 * 1024};'))
    if reserve_mb is not None:
        edits.append(('const cx_heap_reserve: usize = 1536 * 1024 * 1024;',
                      f'const cx_heap_reserve: usize = {reserve_mb} * 1024 * 1024;'))
    for old, new in edits:
        n = src.count(old)
        if n != 1:
            raise SystemExit(f'deck_census: prelude text matched {n} times, not once:\n{old[:90]}')
        src = src.replace(old, new)
    pathlib.Path(out_path).write_text(src)
    print(f'wrote {out_path}  slack={slack_mb} MB  reserve={reserve_mb or 1536} MB')


def symbolise(binary, addrs):
    if not addrs:
        return {}
    out = subprocess.run(['addr2line', '-f', '-e', binary] + sorted(addrs),
                         capture_output=True, text=True).stdout.splitlines()
    names = out[0::2]
    return dict(zip(sorted(addrs), names))


def report(dump_path, binary, top=20):
    lines = pathlib.Path(dump_path).read_text().splitlines()
    dumps = [l for l in lines if l.startswith('CENSUS dump')]
    if not dumps:
        raise SystemExit('deck_census: no CENSUS dump lines -- did the run reach 32 MB of deck?')
    last = dumps[-1]
    seq = last.split('seq=')[1].split()[0]
    print(last)
    rows = []
    for l in lines:
        if not l.startswith(f'CENSUS site seq={seq} '):
            continue
        f = dict(p.split('=') for p in l.split()[2:])
        rows.append((f['ra'], f['br'], int(f['bytes']), int(f['n'])))
    syms = symbolise(binary, {r[0] for r in rows} | {r[1] for r in rows if r[1] != '0x0'})
    syms['0x0'] = '(main heap)'

    def table(title, key):
        agg = collections.defaultdict(lambda: [0, 0])
        for r in rows:
            k = key(r)
            if k is None:
                continue
            agg[k][0] += r[2]
            agg[k][1] += r[3]
        print(f'\n== {title} ==')
        print(f'{"bytes":>12} {"allocs":>9} {"avg":>6}  site')
        for k, (b, n) in sorted(agg.items(), key=lambda x: -x[1][0])[:top]:
            print(f'{b:>12} {n:>9} {b // max(n, 1):>6}  {k}')

    table('deck bytes by allocator call site', lambda r: syms[r[0]] if r[1] != '0x0' else None)
    table('deck bytes by bracket site', lambda r: syms[r[1]] if r[1] != '0x0' else None)
    table('deck bytes by (call site <- bracket)', lambda r: f'{syms[r[0]]}  <-  {syms[r[1]]}' if r[1] != '0x0' else None)
    table('main-heap bytes by allocator call site', lambda r: syms[r[0]] if r[1] == '0x0' else None)


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == 'patch':
        patch(a[1], a[2], int(a[3]) if len(a) > 3 else 0, int(a[4]) if len(a) > 4 else None)
    elif len(a) == 3 and a[0] == 'report':
        report(a[1], a[2])
    else:
        raise SystemExit(__doc__)
