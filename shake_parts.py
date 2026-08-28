#!/usr/bin/env python3
"""Cut `zig-prelude` into shakeable parts, and prove the cut is lossless.

The prelude is one `Text` built from 123 `& "..."` chunks, and the seam is
already there: each chunk is one zig top-level declaration or one comment
block. This reads them out and groups them into parts, where a part is
(leading comments + one declaration) -- comments belong to the decl they
explain, or shaking leaves a header of explanations for code that is gone.

NOTHING HERE IS TYPED BY HAND. Hand-editing 123 string literals byte-exactly is
where a week would go, and a single dropped `\\n` is indistinguishable from a
wrong closure once both are downstream. So the table is generated, and the
generator is gated. FOUR GATES, and they answer four different questions --
which matters, because the first two were once mistaken for the whole set and
two edge bugs shipped through them:

    DECLARATION   every `^(pub )?(fn|const|var) NAME` in the joined text is a
                  part name. A declaration no part is named after cannot be
                  kept on its own account. Free, and it fails on the cut this
                  file shipped with.

    IDENTITY      the parts, concatenated in order, equal the prelude the plug
                  ACTUALLY EMITS -- compared against a real emitted .zig, not
                  against my own decoder. Plus: each part's fragment list
                  rebuilds its own text byte for byte.

    CORPUS EDGE   --check-corpus. Shake each emitted program with its REAL
                  roots and ask zig's question of the result: is anything
                  referenced here not declared here. THIS IS THE ONLY ONE THAT
                  SEES AN EDGE. The all-roots identity check cannot: with every
                  name a root, reachability completes before any edge matters.

    PROVE-GATE    --prove-gate. Suppress one declaration and require the corpus
                  gate to name it, so its power is checked rather than assumed.

Usage, in the order they are worth running:

    ./shake_parts.py EMITTER --prove-gate   RUN/ast/*.zig
    ./shake_parts.py EMITTER --check-corpus corpus/.codexzig/*.zig
    ./shake_parts.py EMITTER --against      RUN/ast/codexir.zig
    ./shake_parts.py EMITTER --splice OUT [--shake-on]

EMITTER must be the chunk-list source, not generator output -- this consumes
the chunk list and replaces it, so it is not idempotent and refuses rather
than splicing an empty table over a good one. Take it from git if the working
tree has already been restructured:

    git show <rev>:codex/plugs/zig/ZigEmitter.codex

The corpus files come from `corpus_run.py --transpile`, which is minutes and
no QEMU.
"""

import argparse
import pathlib
import re
import sys

CHUNK = re.compile(r'^\s*&?\s*"(.*)"\s*$')

# One zig top-level declaration, as the prelude writes them. `fn Cx...` covers
# the comptime type constructors (CxFn1, CxList); `var`/`const` cover the heap
# and table globals.
#
# ANCHORED AT COLUMN 0 AND SEARCHED, NOT MATCHED AT THE CHUNK HEAD. The first
# rule here asked whether a chunk BEGAN with a declaration, and three of 123 do
# not: they carry their explanatory comment block and the declaration in one
# chunk, so the chunk read as a pure comment and welded onto the part BELOW it.
# `cx_heap_base`, `cx_utf8_to_cce` and `cx_vtag` were the casualties -- declared
# inside a part that nothing calling them reaches, so the shake kept every
# caller and dropped the declaration. 468 of 589 corpus programs would have
# failed with `use of undeclared identifier`, and no fixture could see it.
# Column 0 is what makes the search safe: zig indents everything inside a body,
# and a comment line begins with `//`.
DECL = re.compile(r'(?m)^(?:pub\s+)?(?:fn|const|var)\s+([A-Za-z_][A-Za-z0-9_]*)')


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

    A chunk is named by the declaration it CONTAINS, wherever in the chunk that
    declaration starts -- three chunks put a comment block and a declaration in
    one string, and reading only the chunk's first line lost all three. No
    chunk holds two top-level declarations, checked here rather than assumed,
    because a chunk that did would need splitting and silently naming it after
    the first is exactly the failure this file exists to prevent.

    Trailing comment chunks with no decl after them become a part named '' --
    kept unconditionally, because there is nothing to reach them by.
    """
    parts, pending = [], []
    for c in chunks:
        found = DECL.findall(c)
        if len(found) > 1:
            raise SystemExit(
                f'shake_parts: one chunk declares {len(found)} top-level names '
                f'{found}; a part is one declaration, so this chunk must be split '
                f'in the prelude source before it can be shaken.')
        if found:
            parts.append((found[0], ''.join(pending) + c))
            pending = []
        else:
            pending.append(c)
    if pending:
        parts.append(('', ''.join(pending)))
    return parts


def check_every_decl_is_a_part(parts, joined):
    """Every top-level declaration in the prelude must BE a part name.

    The shake drops a part by name. A declaration that no part is named after
    cannot be kept on its own account -- it survives only when whichever part
    swallowed it happens to be kept, which is a coincidence, not a dependency.
    This is the gate that catches it, and it is the difference between an
    unreachable name and a broken build.
    """
    names = {n for n, _ in parts if n}
    orphans = [d for d in DECL.findall(joined) if d not in names]
    if orphans:
        raise SystemExit(
            'shake_parts: DECLARATION GATE FAIL -- the prelude declares '
            f'{", ".join(orphans)} but no part is named after them, so the shake '
            'can drop the declaration while keeping its callers. Fix the cut, '
            'not the gate.')
    return len(names)


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


def escape(t):
    """Inverse of unescape(). Tested by round-trip, not by inspection."""
    out = []
    for c in t:
        if c == '\\': out.append('\\\\')
        elif c == '"': out.append('\\"')
        elif c == '\n': out.append('\\n')
        elif c == '\t': out.append('\\t')
        else: out.append(c)
    return ''.join(out)


# Where a prelude name is NOT a reference: line comments, string literals,
# zig's `\\` multiline-string lines, and character literals. ONE definition,
# shared by the generator that decides what becomes a `ShakeUse` and by the
# checker that asks what the shaken output actually references -- if those two
# disagreed about where code is, the gate would be checking a different program
# than the one that ships.
NONCODE = (r'//[^\n]*'                 # line comment
           r'|\\\\[^\n]*'              # zig multiline-string line
           r'|"(?:\\.|[^"\\])*"'       # string literal
           r"|'(?:\\.|[^'\\])*'")      # character literal
NONCODE_RE = re.compile(NONCODE)


def skip_at(text, i):
    """If a non-code token starts at `i`, return its end index; else None."""
    m = NONCODE_RE.match(text, i)
    return m.end() if m else None


def names_in_code(text, names):
    r"""The subset of `names` appearing in CODE position in `text`.

    Independent of the closure: it re-derives usage from finished text rather
    than from the edges the table recorded, which is what lets it catch an edge
    the table is missing. One regex pass, because this runs over megabytes --
    the non-code alternatives come FIRST, so a name inside a comment or a
    string is consumed as part of that token and never offered as a match.

    `\b` does the prefix work: `_` is a word character, so `\bcx_print\b`
    cannot match inside `cx_print_line`.
    """
    pat = re.compile(NONCODE + r'|\b(?:'
                     + '|'.join(re.escape(n) for n in names) + r')\b')
    found = set()
    for m in pat.finditer(text):
        t = m.group(0)
        if NONCODE_RE.fullmatch(t):
            continue
        found.add(t)
    return found


def fragment(text, names, kind):
    """Split one part's text into Lit/Use fragments.

    A name only becomes a Use where it appears in CODE. Inside a `//` comment
    or a string literal it stays Lit, because it is not a reference there --
    which is the precision a scanner cannot have, and the reason this is worth
    generating once rather than deriving every time.

    Longest name first, so `cx_print` cannot claim the head of `cx_print_line`.
    """
    order = sorted(names, key=len, reverse=True)
    frags, buf, i, n = [], [], 0, len(text)
    def flush():
        if buf:
            frags.append(('Lit', ''.join(buf)))
            buf.clear()
    while i < n:
        c = text[i]
        j = skip_at(text, i)
        if j is not None:                              # comment, string, char
            buf.append(text[i:j]); i = max(j, i + 1); continue
        matched = None
        for nm in order:
            if not text.startswith(nm, i):
                continue
            before = text[i-1] if i else ' '
            if before.isalnum() or before == '_':
                continue
            after = text[i+len(nm):]
            # NO CALL-SHAPE REQUIREMENT, and this cost a native build to learn.
            # An earlier rule demanded `name(` for functions, on the reasoning
            # that a function is referenced by calling it. It is not: a function
            # used as a VALUE has no parenthesis after it, and the prelude does
            # exactly that --
            #     const cx_heap_vtable = std.mem.Allocator.VTable{
            #         .alloc = cx_bump_alloc, .resize = cx_bump_resize, ... };
            # -- so the edge was missed, the part dropped, and zig answered
            # `use of undeclared identifier 'cx_bump_alloc'`. That is the one
            # failure direction that matters, and no fixture could have caught
            # it: it needs the real prelude.
            #
            # The word boundary alone is the sound rule. `_` is a word
            # character, so it still refuses to match cx_print inside
            # cx_print_line. It over-matches a name used as a bare word in code
            # that is not a reference, which keeps a part nobody needed -- the
            # safe direction, and the price of soundness here.
            if after[:1].isalnum() or after[:1] == '_':
                continue
            matched = nm; break
        if matched:
            flush(); frags.append(('Use', matched)); i += len(matched); continue
        buf.append(c); i += 1
    flush()
    return frags


def decl_kinds(parts):
    out = {}
    for n, t in parts:
        if not n: continue
        m = re.search(r'^(?:pub\s+)?(fn|const|var)\s+' + re.escape(n), t, re.M)
        out[n] = m.group(1) if m else 'fn'
    return out


def codex_name(zig_name, taken):
    """A Codex definition name for a zig declaration name.

    Codex definitions are lowercase and hyphenated; zig's are mixed case with
    underscores. Lowercasing and swapping `_` for `-` is the whole rule, and
    collisions are refused rather than resolved -- two parts sharing a Codex
    name would silently make one unreachable, which is the failure this whole
    exercise exists to prevent.
    """
    n = 'zig-p-' + zig_name.lower().replace('_', '-')
    if n in taken:
        raise SystemExit(f'shake_parts: Codex name collision on {n!r}')
    taken.add(n)
    return n


PRELUDE_HEAD = """ The prelude, cut into selectable parts. Each is a `List ShakeFrag` from
 `Foreword chapter Shake`: `ShakeLit` is inert text, `ShakeUse` is text that is
 ALSO a dependency on another part -- two projections of one list, so a part's
 text and its edges cannot drift apart.

 NOTHING HERE IMPLEMENTS THE SELECTION. The closure, the ordering and the
 reporting live in `Shake`, which knows nothing about zig and is exercised by
 its own fixtures. This chapter supplies only the data and the roots.

 A part's own declaration site is a ShakeUse of itself; `shake-frag-uses`
 drops the self-edge, which keeps one rule here instead of two.

 GENERATED by the ladder's `shake_parts.py` and gated part by part:
 `shake-frag-text` of each list rebuilds its original chunk byte for byte. Do
 not hand-edit; edit the prelude source and regenerate.

"""

PRELUDE_TAIL = """
 Every part name, and the roots for one emitted program.

 A part is a root when its name appears anywhere in the program text. That is
 a crude substring test, and the imprecision it can have runs in the SAFE
 direction: an extra root keeps a part nobody needed, a missing root drops a
 live declaration and breaks the build.

 In practice it has no imprecision at all, and the reason is worth writing
 down rather than measuring again. The two places a name could hide without
 being a reference are comments and string literals. Emitted zig carries
 almost no comments, and a Codex text literal is emitted as CCE hex escapes --
 `"\\x30\\x0d\\x18..."` -- so a program's own strings CANNOT contain a prelude
 name in a form this scan can see. Crude roots and code-position roots agree
 exactly on every program tried, and that is structural, not luck.

 COST, measured on this venue before it was written: `index-of` is Codex-level
 rather than a builtin, so this is naive substring search, 93 names over the
 program. It runs at about 8.6M characters a second on bare metal under QEMU,
 which puts the largest program we emit at roughly 21 seconds. Affordable, and
 checked rather than assumed -- the first draft of that measurement used
 needles beginning `zzz`, which never appears, so every position failed on the
 first character and the answer was the best case rather than the worst.

  zig-prelude-part-names : List Text = zig-prelude-names-loop zig-prelude-parts 0 []

  zig-prelude-names-loop : List ShakePart, Integer, List Text -> List Text
  zig-prelude-names-loop (ps) (i) (acc) =
   if i >= list-length ps then acc
   else zig-prelude-names-loop ps (i + 1) (acc & [(list-at ps i).name])

  zig-prelude-roots : Text -> List Text
  zig-prelude-roots (prog) = zig-roots-loop prog zig-prelude-part-names 0 []

  zig-roots-loop : Text, List Text, Integer, List Text -> List Text
  zig-roots-loop (prog) (ns) (i) (acc) =
   if i >= list-length ns then acc
   else let n = list-at ns i
   in when index-of prog n
    is Just (at) -> zig-roots-loop prog ns (i + 1) (acc & [n])
    is None -> zig-roots-loop prog ns (i + 1) acc

  zig-prelude-for : Text -> Text
  zig-prelude-for (prog) = shake-text zig-prelude-parts (zig-prelude-roots prog)

 The unshaken whole, kept for the identity gate: shaking with every name as a
 root must reproduce what the hand-written chunk list produced.

  zig-prelude : Text = shake-text zig-prelude-parts zig-prelude-part-names
"""


def splice(emitter, parts, names, kind, shake_on):
    lines = emitter.read_text(errors='replace').split('\n')
    if not any('chapter Shake' in l for l in lines[:8]):
        c = next(i for i, l in enumerate(lines) if l.strip().startswith('cites '))
        lines.insert(c + 1, '  cites Foreword chapter Shake')
    if not any('chapter TextSearch' in l for l in lines[:8]):
        c = next(i for i, l in enumerate(lines) if l.strip().startswith('cites '))
        lines.insert(c + 1, '  cites Foreword chapter TextSearch')
    start = next(i for i, l in enumerate(lines) if l.strip().startswith('zig-prelude : Text'))
    end = start + 1
    while end < len(lines) and CHUNK.match(lines[end]):
        end += 1

    taken, defs, rows = set(), [], []
    for nm, text in parts:
        fr = fragment(text, names, kind)
        assert ''.join(v for _, v in fr) == text, nm
        cn = codex_name(nm, taken)
        body = ', '.join(f'Shake{k} "{escape(v)}"' for k, v in fr)
        defs.append(f'  {cn} : List ShakeFrag\n  {cn} = [{body}]')
        rows.append(f'    ShakePart {{ name = "{nm}", frags = {cn} }}')

    # Continuations indent to 4, matching zig-prelude-decls' own multi-line
    # list literal. Codex is indentation-sensitive and a row at column 0 ends
    # the definition rather than continuing it.
    inner = (',\n' + ' ' * 4).join(r.strip() for r in rows)
    table = '  zig-prelude-parts : List ShakePart =\n   [' + inner + ']'
    block = PRELUDE_HEAD + '\n\n'.join(defs) + '\n\n' + table + '\n' + PRELUDE_TAIL
    # The prose blocks are plain triple-quoted strings, so an escape written
    # for the READER -- `\\x30` as an example of CCE output -- becomes that byte
    # and rides into upstream source as a control character. It did, once.
    bad = sorted({c for c in PRELUDE_HEAD + PRELUDE_TAIL
                  if ord(c) < 32 and c != '\n'})
    if bad:
        raise SystemExit('shake_parts: control characters in the generated prose: '
                         + ', '.join(hex(ord(c)) for c in bad))
    out = lines[:start] + block.split('\n') + lines[end:]
    # The emit site, and whether the shake is ON there. This is a FLAG rather
    # than a hand edit because the restructure and the behaviour change are two
    # different claims: with the shake off, `zig-prelude` runs the real
    # selection with every part name as a root and must move no byte, which is
    # what makes the restructure reviewable on its own. Toggling that by hand
    # in a 258 KB generated file is how the wrong one gets committed.
    site = ('   in types-text & defs-text & zig-main opening-entry-point (m.defs)'
            ' & zig-postlude-banner & zig-prelude')
    shaken = ('   in let zig-prog = types-text & defs-text & zig-main opening-entry-point (m.defs)\n'
              '   in zig-prog & zig-postlude-banner & zig-prelude-for zig-prog')
    hits = [i for i, l in enumerate(out) if l == site]
    if len(hits) != 1:
        raise SystemExit(f'shake_parts: expected 1 emit site, found {len(hits)}')
    if shake_on:
        out[hits[0]:hits[0] + 1] = shaken.split('\n')
    return '\n'.join(out)


def frag_needs(parts, names, kind):
    """Edges as the SHIPPED emitter computes them: from the fragment lists.

    `needs_of` derives edges by scanning a part's whole text, which is not what
    runs -- the emitter walks `ShakeUse` fragments. Simulating the shake with a
    different edge rule than the one that ships would check the wrong thing.
    """
    out = {}
    for nm, text in parts:
        if not nm:
            continue
        seen = []
        for k, v in fragment(text, names, kind):
            if k == 'Use' and v != nm and v not in seen:
                seen.append(v)
        out[nm] = seen
    return out


def check_corpus(parts, joined, files, suppress=None):
    """Shake each emitted program and prove nothing it still references is gone.

    THIS IS THE GATE THE ALL-ROOTS IDENTITY CHECK CANNOT BE. With every part
    name a root, reachability completes before any edge matters, so that check
    proves the cut and the concatenation and nothing else -- both edge bugs
    found so far walked straight through it. Here the roots are the real ones,
    so a missing edge actually drops a part.

    IT ASKS ABOUT DECLARATIONS, NOT PART NAMES, and the difference is the whole
    value of it. A first version compared referenced PART NAMES against the
    kept part names, and was blind to the orphan bug by construction:
    `cx_heap_base` had no part, so it was never in the vocabulary being looked
    for. Re-run against the old 93-part cut, it reported 14 clean. The question
    that matters is zig's own -- is anything referenced here not declared
    here -- so `declared` is read back out of the finished text and the
    vocabulary is every declaration the FULL prelude has.

    The roots are crude substring matches because that is what
    `zig-prelude-roots` does; simulating a smarter rule would check something
    that does not ship.

    ITS ONE BLIND SPOT, NAMED: it catches "referenced but not declared" and
    cannot catch "required but neither referenced nor declared" -- anything
    zig resolves BY NAME rather than through a reference. `main` is the
    obvious one, and it is safe for a checkable reason rather than a lucky
    one: `zig-main` emits `fn main` and `fn cx_entry` into the PROGRAM region,
    so neither is a prelude part and the shake cannot reach them. Checked the
    whole list against zig's name-resolved declarations -- main, _start,
    panic, std_options, os, root, log -- and no part is one. If a part ever
    is, this gate will not see it go missing.
    """
    names = [n for n, _ in parts if n]
    vocab = DECL.findall(joined)          # every declaration, part or not
    kind = decl_kinds(parts)
    needs = frag_needs(parts, names, kind)
    text_of = dict(parts)

    ok, bad, skipped, tot_kept, tot_all = 0, 0, 0, 0, 0
    worst = {}
    for f in files:
        body = f.read_text(errors='replace')
        cut = body.find(joined)
        if cut < 0:
            print(f'  {f.name}: prelude not found verbatim -- SKIPPED')
            skipped += 1
            continue
        program = body[:cut] + body[cut + len(joined):]
        roots = [n for n in names if n in program]
        keep = set(closure(needs, roots))
        kept_text = ''.join(text_of[n] for n in names
                            if n in keep and n != suppress)
        shaken = program + kept_text
        declared = set(DECL.findall(kept_text))
        missing = sorted(names_in_code(shaken, vocab) - declared)
        tot_kept += len(keep)
        tot_all += len(names)
        if missing:
            bad += 1
            for m in missing:
                worst[m] = worst.get(m, 0) + 1
            if bad <= 5:
                print(f'  {f.name}: UNDECLARED after shaking -- {", ".join(missing)}')
        else:
            ok += 1
    if bad > 5:
        print(f'  ... and {bad - 5} more')
    if worst:
        top = sorted(worst.items(), key=lambda kv: -kv[1])
        print('  most often undeclared: '
              + ', '.join(f'{n} ({c})' for n, c in top[:6]))
    pct = 100 * tot_kept // max(tot_all, 1)
    print(f'  CORPUS EDGE GATE: {ok} clean, {bad} broken, {skipped} skipped   '
          f'(mean {pct}% of {len(names)} parts kept)')
    return 1 if bad or (ok == 0 and skipped) else 0


def prove_gate(parts, joined, files):
    """Prove the corpus gate can FAIL, by breaking the prelude on purpose.

    A gate nobody has seen fail is a claim, not an instrument, and this one has
    already been wrong once in exactly that way: its first version compared
    part names and reported 14 clean on a cut that would not have compiled.

    THE VICTIM IS CHOSEN TO EXERCISE THE CLOSURE. The obvious pick -- most
    incoming edges -- is `std`, which every program names directly, so
    suppressing it proves only that the scanner works; reachability never
    enters into it. The interesting part is one no program mentions, that
    survives ONLY because something else reached it, which is exactly the class
    the orphan bug hit. So the victim is the most-depended-on part that is
    never a root in any of these programs.
    """
    names = [n for n, _ in parts if n]
    needs = frag_needs(parts, names, decl_kinds(parts))
    incoming = {n: 0 for n in names}
    for dsts in needs.values():
        for d in dsts:
            if d in incoming:
                incoming[d] += 1

    rooted = set()
    for f in files:
        body = f.read_text(errors='replace')
        cut = body.find(joined)
        if cut < 0:
            continue
        program = body[:cut] + body[cut + len(joined):]
        rooted |= {n for n in names if n in program}
    indirect = [n for n in names if n not in rooted and incoming[n] > 0]
    if not indirect:
        print('  PROVE-GATE FAIL: every part is a root somewhere, so no victim '
              'here would exercise the closure')
        return 1
    victim = max(indirect, key=lambda n: (incoming[n], n))
    print(f'  victim: {victim} -- {incoming[victim]} incoming edges, named by no '
          f'program, so it survives only through the closure')

    print('  intact:')
    if check_corpus(parts, joined, files) != 0:
        print('  PROVE-GATE FAIL: the gate is red before anything was broken')
        return 1
    print(f'  with {victim} suppressed:')
    rc = check_corpus(parts, joined, files, suppress=victim)
    if rc == 0:
        print(f'  PROVE-GATE FAIL: {victim} was removed and the gate stayed green')
        return 1
    print('  PROVE-GATE PASS: the gate is green when intact and red when broken')
    return 0


def verify_table(emitter, parts, names, kind, restructured):
    """The table in the shipped emitter is EXACTLY what this generator produces.

    Everything `--check-corpus` concludes is about the edges in `frag_needs`,
    which this file derives. The emitter runs the edges in its own generated
    table. Those are the same by construction only while nobody has touched
    the table by hand, and "nobody would" is not a gate.

    No second parser: splice the original chunk list again and compare. A
    parser for the generated form could disagree with the generator that wrote
    it, which is the drift this is meant to detect.
    """
    have = restructured.read_text(errors='replace')
    for shake_on in (False, True):
        want = splice(emitter, parts, names, kind, shake_on)
        if want == have:
            print(f'  TABLE GATE: PASS -- byte-identical to a fresh splice, shake '
                  f'{"ON" if shake_on else "OFF"}')
            return 0
    # Say WHERE, or this is a bare no.
    want = splice(emitter, parts, names, kind, False)
    hl, wl = have.split('\n'), want.split('\n')
    for i in range(min(len(hl), len(wl))):
        if hl[i] != wl[i]:
            print(f'  TABLE GATE: FAIL -- first difference at line {i+1}')
            print(f'    shipped   {hl[i][:90]!r}')
            print(f'    generated {wl[i][:90]!r}')
            break
    else:
        print(f'  TABLE GATE: FAIL -- lengths differ, {len(hl)} vs {len(wl)} lines')
    return 1


def check_emitted(parts, joined, files):
    """Ask zig's question of REAL output, shaken or not. No simulation at all.

    `--check-corpus` predicts: it takes an UNSHAKEN emit, removes the prelude,
    computes roots and edges here, and reports what the shake would do. That is
    the only thing available before the shake is turned on, and once it IS on
    the full prelude no longer appears verbatim in any emitted file, so that
    mode skips everything.

    This mode reads the finished file instead: every prelude name that appears
    in code position must be declared in that same file. It re-derives nothing
    from the table beyond the vocabulary of names to look for, so it cannot
    agree with the closure by sharing its mistake.

    A program that declares a prelude name ITSELF counts as declaring it, and
    that is correct for this question -- zig only asks whether the identifier
    resolves. Whether a program is ALLOWED to declare one is a different
    defect, and `zig-prelude-decls` is where that lives.
    """
    vocab = DECL.findall(joined)
    ok, bad = 0, 0
    worst = {}
    for f in files:
        body = f.read_text(errors='replace')
        declared = set(DECL.findall(body))
        missing = sorted(names_in_code(body, vocab) - declared)
        if missing:
            bad += 1
            for m in missing:
                worst[m] = worst.get(m, 0) + 1
            if bad <= 8:
                print(f'  {f.name}: UNDECLARED -- {", ".join(missing)}')
        else:
            ok += 1
    if bad > 8:
        print(f'  ... and {bad - 8} more')
    if worst:
        top = sorted(worst.items(), key=lambda kv: -kv[1])
        print('  most often undeclared: '
              + ', '.join(f'{n} ({c})' for n, c in top[:6]))
    print(f'  EMITTED GATE: {ok} clean, {bad} broken, over {ok + bad} files')
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('emitter', help='path to ZigEmitter.codex')
    ap.add_argument('--against', help='an emitted .zig to gate the cut against')
    ap.add_argument('--shake', help='an emitted .zig to shake, reporting what survives')
    ap.add_argument('--verify-table', dest='verify_table',
                    help='a restructured ZigEmitter.codex: prove its table is\n'
                         'exactly what this generator produces')
    ap.add_argument('--prove-gate', dest='prove_gate', nargs='+',
                    help='emitted .zig files: prove --check-corpus can fail')
    ap.add_argument('--check-emitted', dest='check_emitted', nargs='+',
                    help='emitted .zig files, ALREADY SHAKEN or not: every\n'
                         'prelude name in code position must be declared there')
    ap.add_argument('--check-corpus', dest='check_corpus', nargs='+',
                    help='emitted .zig files: shake each and prove nothing '
                         'it still references was dropped')
    ap.add_argument('--gen-frags', dest='gen_frags', help='write generated Frag lists here')
    ap.add_argument('--splice', help='write a restructured ZigEmitter.codex here')
    ap.add_argument('--shake-on', dest='shake_on', action='store_true',
                    help='with --splice: select per program. Off, the emit site is\n'
                         'unchanged and the restructure must move no byte.')
    a = ap.parse_args()

    chunks = read_chunks(pathlib.Path(a.emitter))
    # This generator is NOT idempotent: it consumes the hand-written chunk list
    # and replaces it, so a second run over its own output finds nothing to cut
    # and would splice an empty table over a good one. It did exactly that once,
    # writing a 258 KB file and reporting `chunks 0` as though that were a
    # result. Refuse instead -- an empty cut is never a legitimate answer.
    if not chunks:
        raise SystemExit(
            'shake_parts: no `& "..."` chunks under `zig-prelude : Text`. This '
            'emitter has already been restructured; run against the original '
            'chunk-list source (e.g. `git show <rev>:codex/plugs/zig/'
            'ZigEmitter.codex`), not against generator output.')
    parts = group(chunks)
    joined = ''.join(t for _, t in parts)
    check_every_decl_is_a_part(parts, joined)

    named = [n for n, _ in parts if n]
    print(f'chunks {len(chunks)}   parts {len(parts)}   named {len(named)}   '
          f'anonymous {len(parts) - len(named)}   bytes {len(joined):,}')
    print(f'  DECLARATION GATE: PASS -- all {len(DECL.findall(joined))} top-level '
          f'declarations are part names')

    if a.splice:
        names = [n for n, _ in parts if n]
        out = splice(pathlib.Path(a.emitter), parts, names, decl_kinds(parts),
                     a.shake_on)
        pathlib.Path(a.splice).write_text(out)
        print(f'  spliced -> {a.splice}  ({len(out):,} bytes, '
              f'{out.count(chr(10)) + 1} lines, shake '
              f'{"ON -- selects per program" if a.shake_on else "OFF -- must move no byte"})')
        return 0

    if a.gen_frags:
        names = [n for n, _ in parts if n]
        kind = decl_kinds(parts)
        lines, uses_total, bad = [], 0, 0
        for nm, text in parts:
            fr = fragment(text, names, kind)
            rebuilt = ''.join(v for _, v in fr)
            if rebuilt != text:
                print(f'  IDENTITY FAIL in part {nm!r}'); bad += 1; continue
            uses_total += sum(1 for k, _ in fr if k == 'Use')
            body = ', '.join(f'{k} "{escape(v)}"' for k, v in fr)
            lines.append(f'  p-{nm} : List Frag\n  p-{nm} = [{body}]')
        print(f'  fragments generated for {len(lines)}/{len(parts)} parts, '
              f'{uses_total} Use edges, {bad} identity failures')
        if bad:
            return 1
        print(f'  FRAGMENT IDENTITY GATE: PASS -- every part rebuilds byte-exactly')
        pathlib.Path(a.gen_frags).write_text('\n\n'.join(lines) + '\n')
        print(f'  wrote {a.gen_frags}')
        return 0

    if a.verify_table:
        names = [n for n, _ in parts if n]
        return verify_table(pathlib.Path(a.emitter), parts, names,
                            decl_kinds(parts), pathlib.Path(a.verify_table))

    if a.prove_gate:
        return prove_gate(parts, joined, [pathlib.Path(x) for x in a.prove_gate])

    if a.check_emitted:
        return check_emitted(parts, joined,
                             [pathlib.Path(x) for x in a.check_emitted])

    if a.check_corpus:
        return check_corpus(parts, joined,
                            [pathlib.Path(x) for x in a.check_corpus])

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
