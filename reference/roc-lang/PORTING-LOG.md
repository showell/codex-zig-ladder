# Porting log -- roc-lang eval_closure_recursion_tests.zig

Every case in `eval_closure_recursion_tests.zig`, **in file order**, with what
we have done about it. Generated from the vendored file, which is pinned at
commit `ade9294d`; if the file is ever re-taken this log is regenerated with it.

## The rule

**Work down this list in order.** A case is either PORTED, or SKIPPED with a
reason recorded here, and the reason has to be about the LANGUAGE and not about
the effort. Porting out of order is allowed when a case bears directly on work
in flight -- the four ports taken on 2026-08-27 for the branch-join and
empty-list fixes were exactly that -- but the jump is written down here when it
happens, so the next reader can tell a deliberate detour from a gap.

A glob, not a manifest, still decides what RUNS (`roc_ports_run.py` globs
`roc-*.codex`). This file is the record of intent; it is not read by any script
and must never become a second source of truth about which ports exist.

## Status: 10 of 117 ported

| # | case | expected | status |
|---|---|---|---|
| 1 | inline fold sum lambda | `10.0` | **roc-fold-sum** |
| 2 | inline fold product lambda | `24.0` | **roc-fold-product** |
| 3 | inline fold empty list lambda | `42.0` | **roc-fold-empty** |
| 4 | inline fold counts elements lambda | `4.0` | **roc-fold-count** |
| 5 | recursive function with var keeps outer binding | `6.0` | **roc-recursive-var** |
| 6 | simple early return from function via bool | `True` | -- |
| 7 | early return in for loop predicate function | `True` | **roc-early-return-predicate** |
| 8 | tuple pattern var reassignment in while loop | `3.0` | -- |
| 9 | list alias variable aliasing | `6.0` | -- |
| 10 | list alias return original after aliasing | `6.0` | -- |
| 11 | list alias triple aliasing | `3.0` | -- |
| 12 | list alias mutable reassignment | `7.0` | -- |
| 13 | list alias multiple independent lists | `3.0` | -- |
| 14 | list alias empty list aliasing | `42.0` | -- |
| 15 | list alias shadow after alias | `3.0` | -- |
| 16 | list alias both references used | `2.0` | -- |
| 17 | list through identity function | `3.0` | -- |
| 18 | list returned from function | `3.0` | -- |
| 19 | closure captures list and returns it | `3.0` | **roc-closure-captures-list** |
| 20 | function called multiple times with same list | `1.0` | -- |
| 21 | string list through function | `\"a\"` | -- |
| 22 | function extracts from list | `10.0` | -- |
| 23 | closure captures string list | `\"captured\"` | -- |
| 24 | nested function calls with lists | `10.0` | -- |
| 25 | function returns tuple with same list twice | `3.0` | -- |
| 26 | same list passed twice to function | `2.0` | -- |
| 27 | list in tuple single list | `3.0` | -- |
| 28 | multiple lists in tuple | `3.0` | -- |
| 29 | same list twice in tuple | `3.0` | -- |
| 30 | tuple with string list | `\"a\"` | -- |
| 31 | record with list field | `6.0` | -- |
| 32 | record with multiple list fields | `3.0` | -- |
| 33 | same list in multiple record fields | `30.0` | -- |
| 34 | nested record with list | `11.0` | -- |
| 35 | record with string list | `\"hello\"` | -- |
| 36 | record with mixed count and list | `42.0` | -- |
| 37 | tag with list payload | `3.0` | -- |
| 38 | tag with multiple list payloads | `3.0` | -- |
| 39 | tag with string list payload | `\"tag\"` | -- |
| 40 | result with list payload | `6.0` | -- |
| 41 | tuple of records with lists | `3.0` | -- |
| 42 | record of tuples with lists | `11.0` | -- |
| 43 | tag with record containing list | `15.0` | -- |
| 44 | empty list in record | `42.0` | -- |
| 45 | destructure list from record | `3.0` | -- |
| 46 | wildcard discards list field | `3.0` | -- |
| 47 | list rest pattern on integers | `3.0` | -- |
| 48 | string list rest pattern | `\"b\"` | -- |
| 49 | nested list patterns through record | `60.0` | -- |
| 50 | tag with extracted list payload | `15.0` | -- |
| 51 | empty list pattern through record | `42.0` | -- |
| 52 | simple nested list | `3.0` | -- |
| 53 | multiple inner lists | `3.0` | -- |
| 54 | same inner list multiple times | `3.0` | -- |
| 55 | two level inline nested list | `3.0` | -- |
| 56 | three level nested list | `1.0` | -- |
| 57 | nested empty inner list | `42.0` | -- |
| 58 | list of string lists | `\"x\"` | -- |
| 59 | inline string nested lists | `\"a\"` | -- |
| 60 | nested list then aliased | `3.0` | -- |
| 61 | access second inner list | `7.0` | -- |
| 62 | deeply nested inline list | `1.0` | -- |
| 63 | mixed nested and flat lists | `4.0` | -- |
| 64 | minimal empty list pattern match | `42.0` | -- |
| 65 | minimal single element list pattern match | `1.0` | -- |
| 66 | minimal multi element list pattern match | `6.0` | -- |
| 67 | basic various small list sizes | `5.0` | -- |
| 68 | basic two element list pattern match | `30.0` | -- |
| 69 | basic five element list pattern match | `15.0` | -- |
| 70 | basic larger list with rest pattern | `3.0` | -- |
| 71 | basic sequential independent lists | `1.0` | -- |
| 72 | basic return middle list | `5.0` | -- |
| 73 | basic return last list | `15.0` | -- |
| 74 | basic mix of empty and non empty lists | `3.0` | -- |
| 75 | basic return empty from mixed lists | `42.0` | -- |
| 76 | basic nested blocks with lists | `6.0` | -- |
| 77 | basic list created and used in inner block | `60.0` | -- |
| 78 | basic multiple lists chained through aliases | `6.0` | -- |
| 79 | conditional chooses list from then branch | `3.0` | -- |
| 80 | conditional chooses list from else branch | `7.0` | -- |
| 81 | conditional reuses same list in both branches | `3.0` | -- |
| 82 | conditional drops unused branch list | `3.0` | -- |
| 83 | nested conditional list result | `2.0` | -- |
| 84 | conditional string list result | `\"a\"` | -- |
| 85 | conditional inline list literals | `30.0` | -- |
| 86 | conditional empty list branch | `42.0` | -- |
| 87 | string list single captured string | `\"hi\"` | -- |
| 88 | string list multiple captured strings | `\"a\"` | -- |
| 89 | string list return second string | `\"b\"` | -- |
| 90 | string list same string multiple times | `\"hi\"` | -- |
| 91 | string list empty string | `\"\"` | -- |
| 92 | string list small and large strings | `\"hi\"` | -- |
| 93 | string list return large string | `\"This is a very long string that will be heap allocated for sure\"` | -- |
| 94 | string list literal head | `\"a\"` | -- |
| 95 | string list literal second element | `\"b\"` | -- |
| 96 | empty list then string list | `\"x\"` | -- |
| 97 | aliased string list | `\"a\"` | -- |
| 98 | aliased string list returns original | `\"a\"` | -- |
| 99 | mutable string list reassigned | `\"new1\"` | -- |
| 100 | three string lists chooses middle | `\"b1\"` | -- |
| 101 | extract string from nested match | `\"y\"` | -- |
| 102 | list of records with strings | `\"a\"` | -- |
| 103 | list of records with integers | `10.0` | -- |
| 104 | same record multiple times in list | `42.0` | -- |
| 105 | list of records with nested data | `10.0` | -- |
| 106 | list of tuples with integers | `3.0` | -- |
| 107 | list of tuples with strings | `\"a\"` | -- |
| 108 | tag containing list of integers | `10.0` | -- |
| 109 | tag containing list of strings | `\"hello\"` | -- |
| 110 | list of records of lists of strings | `\"a\"` | -- |
| 111 | inline complex structure list | `1.0` | -- |
| 112 | deeply nested mixed structures list | `42.0` | -- |
| 113 | list of Ok Err tags through payload match | `1.0` | -- |
| 114 | iterator-like map uses transformed tag payload | `24` | **roc-iter-map** |
| 115 | returned closure calls captured function argument | `9` | -- |
| 116 | iterator-like keep_if skips rejected tag payloads | `2` | **roc-iter-keep-if** |
| 117 | iterator-like drop_if stops at first kept tag payload | `2` | **roc-iter-drop-if** |
