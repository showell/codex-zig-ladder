#!/usr/bin/env python3
"""Cut `zig-prelude` into shakeable parts, and prove the cut is lossless.

The prelude is one `Text` built from ~123 `& "..."` chunks, and the seam is
already there: each chunk is EXACTLY one zig top-level declaration or one
comment block. This reads them out and groups them into parts, where a part is
(leading comments + one declaration) -- comments belong to the decl they
explain, or shaking leaves a header of explanations for code that is gone.

NOTHING HERE IS TYPED BY HAND. Hand-editing 123 string literals byte-exactly is
where a week would go, and a single dropped `\\n` is indistinguishable from a
wrong closure once both are downstream. So the table is generated, and the
generator is gated:

    the parts, concatenated in order, must equal the prelude the plug ACTUALLY
    EMITS -- not a self-check against my own decoder, but a comparison against
    a real emitted .zig from a sandbox.

That gate is the reason to trust anything built on top. Run it before trusting
a shaken output, and again after any prelude edit.
"""

import argparse
import pathlib
import re
import sys

CHUNK = re.compile(r'^\s*&?\s*"(.*)"\s*$')

# One zig top-level declaration, as the prelude writes them. `fn Cx...` covers
# the comptime type constructors (CxFn1, CxList); `var`/`const` cover the heap
# and table globals.
DECL = re.compile(r'^(?:pub\s+)?(?:fn|const|var)\s+([A-Za-z_][A-Za-z0-9_]*)')


def unescape(s):
    """Codex string escapes, and only the ones the prelude uses."""
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            nxt = s[i + 1]
            out.append({'n': '\n', 't': '\t', '"': '"', '\\': '\\'}.get(nxt, '\\' + nxt))
            i += 2
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def read_chunks(emitter):
    """The chunk texts of `zig-prelude`, in order."""
    lines = emitter.read_text(errors='replace').split('\n')
    start = next(i for i, l in enumerate(lines) if l.strip().startswith('zig-prelude : Text'))
    chunks = []
    for l in lines[start + 1:]:
        m = CHUNK.match(l)
        if not m:
            if l.strip() == '':
                break
            # A line inside the definition that is not a quoted chunk means the
            # shape assumed here is wrong; say so rather than silently stopping
            # early with a short table.
            raise SystemExit(f'shake_parts: unrecognised line in zig-prelude: {l[:70]!r}')
        chunks.append(unescape(m.group(1)))
    return chunks


def group(chunks):
    """Parts: (name, text). A comment chunk rides with the decl BELOW it.

    Trailing comment chunks with no decl after them become a part named '' --
    kept unconditionally, because there is nothing to reach them by.
    """
    parts, pending = [], []
    for c in chunks:
        m = DECL.match(c.lstrip())
        if m:
            parts.append((m.group(1), ''.join(pending) + c))
            pending = []
        else:
            pending.append(c)
    if pending:
        parts.append(('', ''.join(pending)))
    return parts


def needs_of(parts):
    """Edges, derived rather than declared.

    `\bNAME\b` is the rule, and the word boundary is doing real work: `_` is a
    word character, so `\bcx_print\b` does NOT match `cx_print_line`. That is
    the prefix trap the essay flagged, handled by the regex rather than by a
    hand-written `name & "("`.

    It over-matches on names inside comments and string literals, and that is
    the SAFE direction: an extra edge keeps a part nobody needed, a missing
    edge drops a live declaration and breaks the build for whichever programs
    happen to reach it. Every ambiguity here resolves toward keeping.
    """
    names = [n for n, _ in parts if n]
    pat = {n: re.compile(r'\b' + re.escape(n) + r'\b') for n in names}
    out = {}
    for n, text in parts:
        if not n:
            continue
        out[n] = sorted(m for m in names if m != n and pat[m].search(text))
    return out


def closure(needs, roots):
    """The same walk probe-shake.codex proves, in the language that can run it
    over 37 KB without booting a machine. If these two ever disagree, the
    probe is the oracle -- it is the one under the double-compiling check."""
    acc, work, i = [], list(roots), 0
    while i < len(work):
        n = work[i]
        i += 1
        if n in acc:
            continue
        acc.append(n)
        work.extend(needs.get(n, []))
    return acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('emitter', help='path to ZigEmitter.codex')
    ap.add_argument('--against', help='an emitted .zig to gate the cut against')
    ap.add_argument('--shake', help='an emitted .zig to shake, reporting what survives')
    a = ap.parse_args()

    chunks = read_chunks(pathlib.Path(a.emitter))
    parts = group(chunks)
    joined = ''.join(t for _, t in parts)

    named = [n for n, _ in parts if n]
    print(f'chunks {len(chunks)}   parts {len(parts)}   named {len(named)}   '
          f'anonymous {len(parts) - len(named)}   bytes {len(joined):,}')

    if a.shake:
        needs = needs_of(parts)
        body = pathlib.Path(a.shake).read_text(errors='replace')
        cut = body.find(joined)
        if cut < 0:
            print(f'  {pathlib.Path(a.shake).name}: prelude not found verbatim, skipping')
            return 1
        program = body[:cut] + body[cut + len(joined):]
        names = [n for n, _ in parts if n]
        roots = [n for n in names if re.search(r'\b' + re.escape(n) + r'\b', program)]
        keep = set(closure(needs, roots))
        kept_bytes = sum(len(t) for n, t in parts if n in keep or not n)
        print(f'  {pathlib.Path(a.shake).name}:')
        print(f'    roots {len(roots)}  ->  kept {len(keep)}/{len(names)} parts   '
              f'{kept_bytes:,}/{len(joined):,} bytes  '
              f'({100 * kept_bytes // max(len(joined),1)}% of prelude)')
        print(f'    indirect-only (reached via needs, never named by the program): '
              f'{len(keep) - len(set(roots) & keep)}')
        return 0

    if a.against:
        emitted = pathlib.Path(a.against).read_text(errors='replace')
        if joined in emitted:
            print(f'IDENTITY GATE: PASS -- the {len(joined):,} bytes appear verbatim '
                  f'in {pathlib.Path(a.against).name}')
        else:
            print('IDENTITY GATE: FAIL -- the concatenation does not appear in the '
                  'emitted file; the cut is lossy or the decoder is wrong')
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
