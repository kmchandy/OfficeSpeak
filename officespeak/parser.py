"""
claudette/parser.py — Stage B of NoT.

Pseudocode (in the DSL pseudo-language) -> graph dict.

Pure function `parse(pseudocode: str) -> (graph_dict, warnings)`. No file I/O,
no LLM, no DSL dependency. The optional CLI wrapper handles files.

See: catalog/translation_table.md for the grammar and translation rules.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #


class ParseError(Exception):
    """Raised when pseudocode cannot be parsed."""

    def __init__(self, message: str, line: Optional[int] = None):
        self.line_num = line
        if line is not None:
            super().__init__(f"line {line}: {message}")
        else:
            super().__init__(message)


def parse(pseudocode: str) -> tuple[dict, list[str]]:
    """Parse pseudocode -> (graph_dict, warnings_list).

    Raises ParseError on malformed input.
    """
    parser = _Parser(pseudocode)
    return parser.run()


# --------------------------------------------------------------------------- #
# Line preprocessing                                                          #
# --------------------------------------------------------------------------- #


@dataclass
class _Line:
    num: int       # 1-based original line number
    indent: int    # leading whitespace count
    text: str      # content with leading/trailing whitespace stripped


def _preprocess(text: str) -> list[_Line]:
    """Strip comments and blank lines; return list of _Line."""
    out = []
    for i, raw in enumerate(text.splitlines(), start=1):
        # Strip from first unquoted '#' to end of line
        content = _strip_comment(raw)
        if not content.strip():
            continue
        indent = len(content) - len(content.lstrip())
        out.append(_Line(num=i, indent=indent, text=content.strip()))
    return out


def _strip_comment(line: str) -> str:
    """Remove a '#' comment, but not '#' inside quotes."""
    in_str = False
    quote = None
    for i, c in enumerate(line):
        if in_str:
            if c == quote:
                in_str = False
        elif c in ('"', "'"):
            in_str = True
            quote = c
        elif c == "#":
            return line[:i]
    return line


# --------------------------------------------------------------------------- #
# Grammar regexes                                                             #
# --------------------------------------------------------------------------- #

_RE_INPUTS = re.compile(r"^inputs\s*:\s*$")
_RE_FOR_EACH = re.compile(r"^for\s+each\s+(\w+)\s+from\s+(\w+)\s*:\s*$")
_RE_BINDING = re.compile(r"^(\w+)\s*:\s*(.+)$")
_RE_CALL = re.compile(r"^(\w+)\s*\(\s*(.*?)\s*\)\s*$", re.DOTALL)
_RE_STEP = re.compile(r"^(\w+)\s*:\s*(.+?)\s*(?:→|->)\s*(.+)$")
_RE_IF = re.compile(r"^if\s+(.+?)\s*:\s*$")
_RE_ELIF = re.compile(r"^elif\s+(.+?)\s*:\s*$")
_RE_ELSE = re.compile(r"^else\s*:\s*$")
_RE_SEND_TO = re.compile(r"^send\s+to\s+(\w+)\s*(?:\(\s*(.*?)\s*\))?\s*$")
_RE_EQUALITY = re.compile(r'^(\w+)\s*==\s*"([^"]*)"\s*$')
_RE_COMPARISON = re.compile(r"^(\w+)\s*[<>!=]+.*$")


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _split_top_level_commas(s: str) -> list[str]:
    """Split on commas at parenthesis-depth 0 (respecting quotes)."""
    out, cur, depth, in_str, quote = [], [], 0, False, None
    for c in s:
        if in_str:
            cur.append(c)
            if c == quote:
                in_str = False
                quote = None
        elif c in ('"', "'"):
            in_str = True
            quote = c
            cur.append(c)
        elif c in "([{":
            depth += 1
            cur.append(c)
        elif c in ")]}":
            depth -= 1
            cur.append(c)
        elif c == "," and depth == 0:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
    tail = "".join(cur).strip()
    if tail:
        out.append(tail)
    return out


def _parse_value(s: str):
    """Parse a literal: int, float, quoted string, bool, or bare identifier."""
    s = s.strip()
    if not s:
        return ""
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _parse_kwargs(args_str: str, line: int) -> dict:
    """Parse `k=v, k=v` into a dict."""
    args_str = args_str.strip()
    if not args_str:
        return {}
    out = {}
    for kv in _split_top_level_commas(args_str):
        if "=" not in kv:
            raise ParseError(f"expected 'key=value' in args, got {kv!r}", line=line)
        k, v = kv.split("=", 1)
        k = k.strip()
        if not k.isidentifier():
            raise ParseError(f"invalid argument name {k!r}", line=line)
        out[k] = _parse_value(v)
    return out


def _depluralize(word: str) -> str:
    """Naive English depluralization."""
    if word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith("ses") or word.endswith("xes"):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


_VERB_NOUN = {
    "classify": "classifier",
    "extract": "extractor",
    "tag": "tagger",
    "write": "writer",
    "score": "scorer",
    "rate": "rater",
    "count": "counter",
    "compute": "computer",
    "propose": "proposer",
    "critique": "critic",
    "judge": "judge",
    "detect": "detector",
    "identify": "identifier",
    "check": "checker",
    "validate": "validator",
    "verify": "verifier",
    "summarize": "summarizer",
    "translate": "translator",
    "format": "formatter",
    "render": "renderer",
    "analyze": "analyzer",
    "rank": "ranker",
    "filter": "filter",
}

_VERB_PHRASE_SPECIAL = {
    ("identify", "location"): "geolocator",
}


def _derive_role(verb_phrase: str) -> str:
    """Derive a role name from `<verb> <object>` per translation table §2.3."""
    words = verb_phrase.lower().strip().split()
    if not words:
        return "unknown_role"

    if len(words) == 2 and tuple(words) in _VERB_PHRASE_SPECIAL:
        return _VERB_PHRASE_SPECIAL[tuple(words)]

    if len(words) == 1:
        v = words[0]
        return _VERB_NOUN.get(v, v + "er")

    verb, *obj_words = words
    obj_joined = "_".join(obj_words)
    obj_singular = _depluralize(obj_joined)
    verb_noun = _VERB_NOUN.get(verb, verb + "er")
    return f"{obj_singular}_{verb_noun}"


def _outport_for_condition(cond: str, line: int) -> str:
    """Return the outport name for an if/elif condition."""
    c = cond.strip()
    m = _RE_EQUALITY.match(c)
    if m:
        return m.group(2)
    # Comparison or bare predicate
    if _RE_COMPARISON.match(c) or c.isidentifier():
        return "true"
    raise ParseError(
        f"unsupported condition: {cond!r}; "
        f"supported forms are '<field> == \"<value>\"' "
        f"or '<field> <op> <value>' or a bare predicate",
        line=line,
    )


def _default_else_name(first_cond: str) -> str:
    """Return the outport name for an else branch, based on the first if-condition."""
    c = first_cond.strip()
    if _RE_EQUALITY.match(c):
        return "else"
    return "false"


# --------------------------------------------------------------------------- #
# SCC analysis (Tarjan; iterative to avoid recursion limit)                   #
# --------------------------------------------------------------------------- #


def _scc(nodes: list[str], edge_pairs: list[tuple[str, str]]) -> list[set[str]]:
    """Tarjan's strongly-connected-components algorithm (iterative)."""
    succ = {n: [] for n in nodes}
    nodes_set = set(nodes)
    for src, dst in edge_pairs:
        if src in nodes_set and dst in nodes_set:
            succ[src].append(dst)

    index = {}
    lowlink = {}
    on_stack = set()
    stack = []
    next_index = [0]
    sccs = []

    def strongconnect(start):
        # Iterative DFS using an explicit work stack of (node, succ_iter)
        work = [(start, iter(succ[start]))]
        index[start] = next_index[0]
        lowlink[start] = next_index[0]
        next_index[0] += 1
        stack.append(start)
        on_stack.add(start)

        while work:
            v, it = work[-1]
            nxt = next(it, None)
            if nxt is not None:
                if nxt not in index:
                    index[nxt] = next_index[0]
                    lowlink[nxt] = next_index[0]
                    next_index[0] += 1
                    stack.append(nxt)
                    on_stack.add(nxt)
                    work.append((nxt, iter(succ[nxt])))
                elif nxt in on_stack:
                    lowlink[v] = min(lowlink[v], index[nxt])
            else:
                # done with v
                work.pop()
                if work:
                    parent = work[-1][0]
                    lowlink[parent] = min(lowlink[parent], lowlink[v])
                if lowlink[v] == index[v]:
                    comp = set()
                    while True:
                        w = stack.pop()
                        on_stack.discard(w)
                        comp.add(w)
                        if w == v:
                            break
                    sccs.append(comp)

    for n in nodes:
        if n not in index:
            strongconnect(n)

    return sccs


# --------------------------------------------------------------------------- #
# Parser                                                                      #
# --------------------------------------------------------------------------- #


@dataclass
class _Parser:
    pseudocode: str
    lines: list[_Line] = field(default_factory=list)
    cursor: int = 0

    # Symbol tables
    inputs_table: dict = field(default_factory=dict)   # var -> list[source_id]
    step_to_vertex: dict = field(default_factory=dict) # step_id -> vertex_id

    # Output collections
    sources: list = field(default_factory=list)
    vertices: list = field(default_factory=list)
    sinks: list = field(default_factory=list)
    edges: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    # Sink dedup
    sink_cache: dict = field(default_factory=dict)

    def run(self) -> tuple[dict, list[str]]:
        self.lines = _preprocess(self.pseudocode)
        if not self.lines:
            raise ParseError("empty pseudocode")

        self._parse_inputs()
        self._parse_for_each()
        self._compute_cyclic()
        self._validate()
        self._warn_termination()

        graph = {
            "sources": self.sources,
            "vertices": [self._clean_vertex(v) for v in self.vertices],
            "sinks": self.sinks,
            "edges": self.edges,
        }
        return graph, self.warnings

    # ---- inputs block ----

    def _parse_inputs(self):
        first = self._peek()
        if first is None or not _RE_INPUTS.match(first.text):
            raise ParseError(
                "expected 'inputs:' as first non-comment line",
                line=first.num if first else None,
            )
        self._advance()
        header_indent = first.indent

        while not self._at_end():
            line = self._peek()
            if line.indent <= header_indent:
                break
            self._parse_input_binding(line)
            self._advance()

    def _parse_input_binding(self, line: _Line):
        m = _RE_BINDING.match(line.text)
        if not m:
            raise ParseError(
                f"expected '<var>: <expr>' in inputs block, got {line.text!r}",
                line=line.num,
            )
        var_name, expr = m.group(1), m.group(2).strip()
        if var_name in self.inputs_table:
            raise ParseError(f"duplicate input variable {var_name!r}", line=line.num)

        call = _RE_CALL.match(expr)
        if call:
            func_name, args_str = call.group(1), call.group(2)
        elif expr.isidentifier():
            # Bare-identifier source (no parens), e.g. `starter`. DSL allows
            # this for sources that take no arguments.
            func_name, args_str = expr, ""
        else:
            raise ParseError(
                f"expected '<func>(...)' or bare identifier on RHS of "
                f"'{var_name}:', got {expr!r}",
                line=line.num,
            )

        if func_name == "merge":
            args = _split_top_level_commas(args_str)
            if not args:
                raise ParseError("merge() requires at least 1 argument", line=line.num)
            merged: list[str] = []
            for arg in args:
                arg = arg.strip()
                if not arg.isidentifier():
                    raise ParseError(
                        f"merge() argument must be a variable name, got {arg!r}",
                        line=line.num,
                    )
                if arg not in self.inputs_table:
                    raise ParseError(
                        f"merge() references undefined variable {arg!r}",
                        line=line.num,
                    )
                for sid in self.inputs_table[arg]:
                    if sid not in merged:
                        merged.append(sid)
            self.inputs_table[var_name] = merged
        else:
            params = _parse_kwargs(args_str, line=line.num)
            sid = f"s{len(self.sources)}"
            self.sources.append({"id": sid, "name": func_name, "params": params})
            self.inputs_table[var_name] = [sid]

    # ---- for-each block ----

    def _parse_for_each(self):
        if self._at_end():
            raise ParseError("expected 'for each <item> from <var>:' after inputs block")
        header = self._peek()
        m = _RE_FOR_EACH.match(header.text)
        if not m:
            raise ParseError(
                f"expected 'for each <item> from <var>:', got {header.text!r}",
                line=header.num,
            )
        _item, var_name = m.group(1), m.group(2)
        if var_name not in self.inputs_table:
            raise ParseError(f"unknown input variable {var_name!r}", line=header.num)
        first_vertex_sources = self.inputs_table[var_name]
        header_indent = header.indent
        self._advance()

        body = []
        while not self._at_end():
            line = self._peek()
            if line.indent <= header_indent:
                break
            body.append(line)
            self._advance()
        if not body:
            raise ParseError("for-each body is empty", line=header.num)

        body_base = body[0].indent

        # ---- Pass 1: collect steps, each with its own routing block ----
        # A step line is followed by its routing: zero or more `send to`
        # lines and at most one if/elif/else block, up to the next step
        # line. A step with an explicit routing block does not chain
        # implicitly; a step with no routing block chains to the following
        # step (the legacy pipeline form).
        steps = []   # {vid, branches, else_name, unconditional, line}
        i = 0
        while i < len(body):
            line = body[i]
            if line.indent != body_base:
                raise ParseError(
                    f"unexpected indent (expected {body_base}, got {line.indent})",
                    line=line.num,
                )
            sm = _RE_STEP.match(line.text)
            if not sm:
                raise ParseError(
                    f"expected a step line '<id>: <verb> <object> -> "
                    f"[reads X,] enriches Y' (each step precedes its own "
                    f"'send to' routing), got {line.text!r}",
                    line=line.num,
                )
            vid = self._add_step(sm, line)
            rec = {"vid": vid, "branches": [], "else_name": "else",
                   "unconditional": [], "line": line.num}
            i += 1
            while i < len(body):
                l2 = body[i]
                if l2.indent != body_base:
                    raise ParseError(
                        f"unexpected indent (expected {body_base}, "
                        f"got {l2.indent})", line=l2.num,
                    )
                if _RE_STEP.match(l2.text):
                    break
                if _RE_IF.match(l2.text):
                    if rec["branches"]:
                        raise ParseError(
                            "a step may have only one if/elif/else block",
                            line=l2.num,
                        )
                    branches, else_name, i = self._parse_branches(
                        body, i, body_base
                    )
                    rec["branches"] = branches
                    rec["else_name"] = else_name
                    continue
                stm = _RE_SEND_TO.match(l2.text)
                if not stm:
                    raise ParseError(
                        f"expected 'send to <target>' or a step line, "
                        f"got {l2.text!r}", line=l2.num,
                    )
                params = _parse_kwargs(stm.group(2) or "", line=l2.num)
                rec["unconditional"].append((stm.group(1), params, l2.num))
                i += 1
            steps.append(rec)

        if not steps:
            raise ParseError(
                "for-each body must contain at least one step line",
                line=header.num,
            )

        # ---- Pass 2: emit edges (forward references now resolvable) ----
        first_vid = steps[0]["vid"]
        for src_id in first_vertex_sources:
            self.edges.append({"from": [src_id, "out"], "to": [first_vid, "in_"]})

        for idx, rec in enumerate(steps):
            vid = rec["vid"]
            if rec["branches"]:
                router_v = self._vertex(vid)
                outport_order = [name for name, _ in rec["branches"]]
                router_v["_outports_explicit"] = outport_order[:]
                router_v["_else_outport_name"] = rec["else_name"]
                branches = list(rec["branches"])
                existing = outport_order[:]
                if rec["else_name"] not in existing:
                    existing.append(rec["else_name"])
                    branches.append((rec["else_name"], []))
                router_v["outports"] = existing
                for outport, sends in branches:
                    for target, params, ln in sends:
                        dst, port = self._resolve_target(target, params, ln)
                        self.edges.append(
                            {"from": [vid, outport], "to": [dst, port]}
                        )
                for target, params, ln in rec["unconditional"]:
                    dst, port = self._resolve_target(target, params, ln)
                    for outport, _ in branches:
                        self.edges.append(
                            {"from": [vid, outport], "to": [dst, port]}
                        )
            elif rec["unconditional"]:
                for target, params, ln in rec["unconditional"]:
                    dst, port = self._resolve_target(target, params, ln)
                    self.edges.append({"from": [vid, "out"], "to": [dst, port]})
            elif idx + 1 < len(steps):
                # No explicit routing: chain implicitly to the next step.
                nxt = steps[idx + 1]["vid"]
                self.edges.append({"from": [vid, "out"], "to": [nxt, "in_"]})
            else:
                raise ParseError(
                    "last step has no 'send to' — nothing consumes its "
                    "output", line=rec["line"],
                )

    def _add_step(self, sm: re.Match, line: _Line) -> str:
        """Create a step vertex (no edges) and return its id."""
        step_id = sm.group(1)
        verb_phrase = sm.group(2).strip()
        annotation = sm.group(3).strip()

        if step_id in self.step_to_vertex:
            raise ParseError(f"duplicate step id {step_id!r}", line=line.num)
        if "enriches" not in annotation:
            raise ParseError(
                f"step missing 'enriches <field>': {annotation!r}", line=line.num
            )
        parts = annotation.rsplit("enriches", 1)
        reads_part = parts[0].strip().rstrip(",").strip()
        enriches_field = parts[1].strip()
        if not enriches_field:
            raise ParseError(
                "'enriches' must be followed by a field name", line=line.num
            )

        reads: list[str] = []
        if reads_part:
            if not reads_part.startswith("reads"):
                raise ParseError(
                    f"unexpected text before 'enriches': {reads_part!r}", line=line.num
                )
            reads_list = reads_part[len("reads"):].strip()
            if reads_list:
                reads = [f.strip() for f in reads_list.split(",") if f.strip()]

        role = _derive_role(verb_phrase)
        vid = f"v{len(self.vertices)}"
        self.step_to_vertex[step_id] = vid
        reads_clause = ", ".join(reads) if reads else "the message"
        purpose = f"Read {reads_clause}; set `{enriches_field}`."

        self.vertices.append({
            "id": vid,
            "role": role,
            "step_id": step_id,
            "verb_phrase": verb_phrase,
            "reads": reads,
            "enriches": enriches_field,
            "purpose": purpose,
            "params": {},
        })
        return vid

    def _vertex(self, vid: str) -> dict:
        for v in self.vertices:
            if v["id"] == vid:
                return v
        raise ParseError(f"internal: no vertex {vid!r}")

    def _parse_branches(
        self, body: list[_Line], i: int, body_base: int
    ) -> tuple[list, str, int]:
        """Parse an if/elif/else block. Returns (branches, else_outport_name, new_i)."""
        branches = []
        else_outport_name = None
        first_cond = None

        first = body[i]
        ifm = _RE_IF.match(first.text)
        assert ifm, "called with non-if line"
        first_cond = ifm.group(1)
        outport = _outport_for_condition(first_cond, first.num)
        else_outport_name = _default_else_name(first_cond)
        i += 1
        sends, i = self._collect_branch_body(body, i, body_base, outport, first.num)
        branches.append((outport, sends))

        while i < len(body) and body[i].indent == body_base:
            line = body[i]
            em = _RE_ELIF.match(line.text)
            ow = _RE_ELSE.match(line.text)
            if em:
                outport = _outport_for_condition(em.group(1), line.num)
                i += 1
                sends, i = self._collect_branch_body(
                    body, i, body_base, outport, line.num
                )
                branches.append((outport, sends))
            elif ow:
                outport = else_outport_name
                i += 1
                sends, i = self._collect_branch_body(
                    body, i, body_base, outport, line.num
                )
                branches.append((outport, sends))
                # Once we hit `else`, the chain is done
                break
            else:
                break
        return branches, else_outport_name, i

    def _collect_branch_body(
        self,
        body: list[_Line],
        i: int,
        body_base: int,
        outport: str,
        header_line_num: int,
    ) -> tuple[list, int]:
        """Collect send-to lines indented more than body_base. Return (sends, new_i)."""
        sends = []
        branch_indent = None
        while i < len(body):
            line = body[i]
            if line.indent <= body_base:
                break
            if branch_indent is None:
                branch_indent = line.indent
            if line.indent < branch_indent:
                break
            stm = _RE_SEND_TO.match(line.text)
            if not stm:
                if _RE_IF.match(line.text) or _RE_ELIF.match(line.text) or _RE_ELSE.match(
                    line.text
                ):
                    raise ParseError(
                        "nested if inside an if-body is not allowed", line=line.num
                    )
                raise ParseError(
                    f"if-body must contain only 'send to' lines; got {line.text!r} "
                    f"(grammar restriction: see translation table §2.4)",
                    line=line.num,
                )
            target = stm.group(1)
            args_str = stm.group(2) or ""
            params = _parse_kwargs(args_str, line=line.num)
            sends.append((target, params, line.num))
            i += 1
        if not sends:
            raise ParseError(
                f"branch body for outport {outport!r} cannot be empty",
                line=header_line_num,
            )
        return sends, i

    # ---- target resolution ----

    def _resolve_target(
        self, target: str, params: dict, line_num: int
    ) -> tuple[str, str]:
        if target in self.step_to_vertex:
            if params:
                raise ParseError(
                    f"back-edge target {target!r} cannot take arguments", line=line_num
                )
            return self.step_to_vertex[target], "in_"
        return self._get_or_create_sink(target, params), "in_"

    def _get_or_create_sink(self, name: str, params: dict) -> str:
        key = (name, tuple(sorted(params.items())))
        if key in self.sink_cache:
            return self.sink_cache[key]
        sid = f"k{len(self.sinks)}"
        self.sinks.append({"id": sid, "name": name, "params": params})
        self.sink_cache[key] = sid
        return sid

    # ---- post-pass: SCC, validation, warnings ----

    def _compute_cyclic(self):
        all_ids = (
            [s["id"] for s in self.sources]
            + [v["id"] for v in self.vertices]
            + [s["id"] for s in self.sinks]
        )
        edge_pairs = [(e["from"][0], e["to"][0]) for e in self.edges]
        sccs = _scc(all_ids, edge_pairs)
        cyclic = set()
        for comp in sccs:
            if len(comp) > 1:
                cyclic.update(comp)
            else:
                (n,) = comp
                if any(src == n and dst == n for src, dst in edge_pairs):
                    cyclic.add(n)
        for v in self.vertices:
            v["cyclic"] = v["id"] in cyclic

    def _validate(self):
        # Every vertex has at least one incoming edge
        incoming_count = {v["id"]: 0 for v in self.vertices}
        for e in self.edges:
            dst = e["to"][0]
            if dst in incoming_count:
                incoming_count[dst] += 1
        for v in self.vertices:
            if incoming_count[v["id"]] == 0:
                self.warnings.append(
                    f"vertex {v['id']} ({v['role']}) has no incoming edges"
                )

    def _warn_termination(self):
        cyclic = [v for v in self.vertices if v["cyclic"]]
        if not cyclic:
            return
        counter_names = {
            "iter", "iteration", "iterations",
            "count", "counter", "round", "rounds",
            "attempt", "attempts", "tries",
        }
        has_counter = any(v["enriches"] in counter_names for v in self.vertices)
        if not has_counter:
            ids = ", ".join(v["id"] for v in cyclic)
            self.warnings.append(
                f"cyclic vertices ({ids}) but no iteration counter field "
                f"detected; relying on convergence-only termination"
            )

    # ---- vertex cleanup ----

    def _clean_vertex(self, v: dict) -> dict:
        """Strip internal-only fields; return the public vertex dict."""
        out = {
            "id": v["id"],
            "role": v["role"],
            "purpose": v["purpose"],
            "reads": v["reads"],
            "enriches": v["enriches"],
            "cyclic": v.get("cyclic", False),
        }
        if "outports" in v and v["outports"]:
            out["outports"] = v["outports"]
        return out

    # ---- cursor helpers ----

    def _peek(self) -> Optional[_Line]:
        return self.lines[self.cursor] if self.cursor < len(self.lines) else None

    def _advance(self) -> _Line:
        line = self.lines[self.cursor]
        self.cursor += 1
        return line

    def _at_end(self) -> bool:
        return self.cursor >= len(self.lines)


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #


def _main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Parse NoT pseudocode into a graph YAML."
    )
    p.add_argument("input", help="Path to a .pseudo file")
    p.add_argument(
        "--output", "-o",
        help="Path to write graph YAML (default: stdout)",
    )
    p.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress warnings"
    )
    args = p.parse_args(argv)

    text = Path(args.input).read_text()
    try:
        graph, warnings = parse(text)
    except ParseError as e:
        print(f"ParseError: {e}", file=sys.stderr)
        return 1

    if warnings and not args.quiet:
        for w in warnings:
            print(f"warning: {w}", file=sys.stderr)

    try:
        import yaml
        out = yaml.safe_dump(graph, sort_keys=False, allow_unicode=True)
    except ImportError:
        out = json.dumps(graph, indent=2)

    if args.output:
        Path(args.output).write_text(out)
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
