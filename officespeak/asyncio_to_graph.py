"""
officespeak/asyncio_to_graph.py — Stage B of OfficeSpeak.

OfficeSpeak-style asyncio Python -> graph dict.

Pure function: `parse(python_source: str) -> (graph_dict, warnings)`.
No LLM calls; walks the Python AST guided by the translation table.

See: paper/translation_table_asyncio_to_office.md
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #


class TranslationError(Exception):
    """Raised when an asyncio pattern is not recognized."""

    def __init__(self, message: str, node: Optional[ast.AST] = None):
        line = getattr(node, "lineno", None)
        if line is not None:
            super().__init__(f"line {line}: {message}")
        else:
            super().__init__(message)


def parse(python_source: str) -> tuple[dict, list[str]]:
    """Translate OfficeSpeak-style asyncio Python into a graph dict.

    Returns (graph, warnings). Raises TranslationError on unrecognizable
    patterns.

    See: paper/translation_table_asyncio_to_office.md for the full
    pattern table.
    """
    return _Translator(python_source).run()


# --------------------------------------------------------------------------- #
# Sink-name conventions                                                       #
# --------------------------------------------------------------------------- #

# In OfficeSpeak-style code, `send_to(msg, "name", **kwargs)` uses short names
# that map to DSL's registered sinks. Extend as needed.
_SINK_NAME_MAP = {
    "terminal": "intelligence_display",
    "console":  "console_printer",
    "jsonl":    "jsonl_recorder",
    "slack":    "slack_sink",
    "gmail":    "gmail_sink",
    "webhook":  "webhook_sink",
    "discard":  "discard",
}


# --------------------------------------------------------------------------- #
# Translator internals                                                        #
# --------------------------------------------------------------------------- #


@dataclass
class _Translator:
    source: str
    tree: Optional[ast.Module] = None
    warnings: list = field(default_factory=list)

    sources: list = field(default_factory=list)
    vertices: list = field(default_factory=list)
    sinks: list = field(default_factory=list)
    edges: list = field(default_factory=list)

    # name -> vertex id  (top-level function/class -> vertex)
    agent_id_by_name: dict = field(default_factory=dict)

    # (sink_name, params_tuple) -> sink id
    sink_id_by_key: dict = field(default_factory=dict)

    # local instance name in main -> vertex id (for `tally = SeverityTally()`)
    class_instance_names: dict = field(default_factory=dict)

    # ── Dataflow symbol table (built while walking process_one) ──────── #
    # Each variable name maps to the list of (node_id, outport) endpoints
    # that produce its value. A value produced by an agent has one
    # endpoint; the source stream (process_one's parameter) is produced
    # by *all* sources, so it maps to one endpoint per source. Edges are
    # created directly from these data dependencies — there is no
    # pattern catalogue. The graph is whatever process_one's control flow
    # specifies.
    producers: dict = field(default_factory=dict)

    # (node_id, outport) endpoints of every source — what process_one's
    # parameter resolves to.
    source_endpoints: list = field(default_factory=list)

    # producer-endpoint tuple -> router vertex id, so several `if`
    # branches that route the same value share one router.
    router_by_producer: dict = field(default_factory=dict)

    # Endpoints produced by process_one's `return` — the pipeline's
    # output, wired to any leaf agents driven from main (e.g. a tally).
    pipeline_output: list = field(default_factory=list)

    # ---------------------------------------------------------------- #
    # Top-level driver                                                 #
    # ---------------------------------------------------------------- #

    def run(self) -> tuple[dict, list[str]]:
        self.tree = ast.parse(self.source)
        self._extract_sources()
        self._extract_agents()
        self._extract_class_instances()
        self._extract_graph_from_process_one()
        self._extract_extra_edges_from_main()
        return self._build_graph(), self.warnings

    # ---------------------------------------------------------------- #
    # §1.1 SOURCES dict                                                #
    # ---------------------------------------------------------------- #

    def _extract_sources(self):
        for node in self.tree.body:
            if not (isinstance(node, ast.Assign)
                    and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == "SOURCES"):
                continue
            if not isinstance(node.value, ast.Dict):
                raise TranslationError(
                    "SOURCES must be a dict literal", node=node
                )
            for key_node, val_node in zip(node.value.keys, node.value.values):
                key = self._string_constant(key_node)
                sid = f"s{len(self.sources)}"
                if isinstance(val_node, ast.Constant) and isinstance(val_node.value, str):
                    # URL string → generic RSS; use the dict key as the source name
                    # so multiple RSS sources have distinct names in office.md.
                    self.sources.append({
                        "id": sid,
                        "name": key,
                        "params": {"url": val_node.value},
                    })
                elif isinstance(val_node, ast.Call):
                    fn_name = self._call_function_name(val_node)
                    params = self._call_kwargs(val_node)
                    self.sources.append({
                        "id": sid,
                        "name": fn_name,
                        "params": params,
                    })
                else:
                    raise TranslationError(
                        f"unrecognised SOURCES entry",
                        node=val_node,
                    )
            return
        raise TranslationError("SOURCES dict not found at module scope")

    # ---------------------------------------------------------------- #
    # §1.2 / §1.3 agent definitions                                    #
    # ---------------------------------------------------------------- #

    def _extract_agents(self):
        for node in self.tree.body:
            if isinstance(node, ast.AsyncFunctionDef):
                self._try_add_llm_agent(node)
            elif isinstance(node, ast.ClassDef):
                self._try_add_python_stateful_agent(node)

    def _try_add_llm_agent(self, func: ast.AsyncFunctionDef):
        """Top-level `async def name(message)` with docstring → LLM vertex."""
        if func.name in ("main", "process_one"):
            return
        args = func.args.args
        if len(args) != 1 or args[0].arg != "message":
            return
        docstring = ast.get_docstring(func) or ""
        vid = f"v{len(self.vertices)}"
        self.vertices.append({
            "id": vid,
            "role": func.name,
            "kind": "llm",
            "role_prompt": docstring,
            "source_code": ast.unparse(func),
        })
        self.agent_id_by_name[func.name] = vid

    def _try_add_python_stateful_agent(self, cls: ast.ClassDef):
        """Class with `__init__` and `process(self, message)` → stateful Python vertex."""
        methods = {
            m.name: m for m in cls.body
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        if "__init__" not in methods or "process" not in methods:
            return
        proc = methods["process"]
        args = proc.args.args
        if len(args) != 2 or args[0].arg != "self" or args[1].arg != "message":
            return
        docstring = ast.get_docstring(cls) or ""
        vid = f"v{len(self.vertices)}"
        self.vertices.append({
            "id": vid,
            "role": cls.name.lower(),
            "kind": "python_stateful",
            "role_prompt": docstring,
            "source_code": ast.unparse(cls),
            "class_name": cls.name,
        })
        self.agent_id_by_name[cls.name] = vid

    # ---------------------------------------------------------------- #
    # Class instantiations (e.g. `tally = SeverityTally()`)             #
    # ---------------------------------------------------------------- #

    def _extract_class_instances(self):
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Assign):
                continue
            if not (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)):
                continue
            if not isinstance(node.value, ast.Call):
                continue
            fn_name = self._call_function_name(node.value)
            if fn_name in self.agent_id_by_name:
                vid = self.agent_id_by_name[fn_name]
                self.class_instance_names[node.targets[0].id] = vid
                # Capture constructor kwargs (e.g.
                # ``ThresholdDetector(db_threshold=-30)``) onto the
                # vertex params so the graph carries them and the DSL
                # forwards them to the role factory at compile time.
                kwargs = self._call_kwargs(node.value)
                if kwargs:
                    vertex = self._get_vertex_by_id(vid)
                    if vertex is not None:
                        vertex["params"] = {
                            **vertex.get("params", {}), **kwargs
                        }

    # ---------------------------------------------------------------- #
    # §2 process_one body                                              #
    # ---------------------------------------------------------------- #

    def _extract_graph_from_process_one(self):
        """Translate process_one's control flow into a dataflow graph.

        No pattern catalogue: we walk the statements once, maintaining a
        symbol table that maps each variable to the (node, outport)
        endpoints that produce its value. Every construct translates
        directly:

        * process_one's parameter is produced by the source stream;
        * ``y = agent(x)`` / ``y = agent.process(x)`` draws an edge from
          x's producer(s) into the agent and binds y to the agent's out;
        * ``asyncio.gather(f(x), g(x))`` is just two calls that both read
          x — no special "broadcast" handling is needed;
        * a ``{**a, **b}`` dict-merge of two or more agent-produced values
          is the one place two messages must fan into one, so it becomes
          a synchronizer;
        * ``if cond: send_to(v, sink)`` routes v through a router;
        * ``send_to(v, sink)`` draws an edge from v's producer to a sink;
        * ``return v`` records v's producer as the pipeline output.
        """
        process_one = self._find_top_level_async_def("process_one")
        if process_one is None:
            raise TranslationError("process_one function not found")

        # The source stream feeds process_one's single parameter.
        self.source_endpoints = [(s["id"], "out") for s in self.sources]
        if process_one.args.args:
            param = process_one.args.args[0].arg
            self.producers[param] = list(self.source_endpoints)

        for stmt in process_one.body:
            if self._is_docstring(stmt):
                continue
            elif isinstance(stmt, ast.Assign):
                self._df_assign(stmt)
            elif self._is_send_to_stmt(stmt):
                self._df_send_to(stmt)
            elif isinstance(stmt, ast.If):
                self._df_if(stmt)
            elif isinstance(stmt, ast.Return):
                self._df_return(stmt)
            else:
                self.warnings.append(
                    f"process_one line {stmt.lineno}: unrecognised statement, skipped"
                )

    # ---------------------------------------------------------------- #
    # main() — leaf edges (e.g. `for item in enriched: tally.process(item)`)
    # ---------------------------------------------------------------- #

    def _extract_extra_edges_from_main(self):
        main = self._find_top_level_async_def("main")
        if main is None:
            return
        for node in ast.walk(main):
            if not isinstance(node, ast.Call):
                continue
            if not (isinstance(node.func, ast.Attribute)
                    and node.func.attr == "process"
                    and isinstance(node.func.value, ast.Name)):
                continue
            inst = node.func.value.id
            if inst in self.class_instance_names:
                vertex_id = self.class_instance_names[inst]
                self._add_leaf_edge_from_pipeline_end(vertex_id)

    def _add_leaf_edge_from_pipeline_end(self, target_id: str):
        """Wire process_one's returned value (the pipeline output) to a leaf."""
        endpoints = self.pipeline_output
        if not endpoints:
            # Fallback for a process_one with no explicit return: use the
            # synchronizer's out if there is one.
            for v in self.vertices:
                if v.get("role") == "synchronizer":
                    endpoints = [(v["id"], "out")]
                    break
        for (node_id, port) in endpoints:
            self.edges.append({
                "from": [node_id, port],
                "to": [target_id, "in_"],
            })

    # ---------------------------------------------------------------- #
    # Dataflow statement handlers                                      #
    # ---------------------------------------------------------------- #

    def _df_assign(self, stmt: ast.Assign):
        """Bind the assignment's target(s) to their producing endpoints."""
        value = self._unwrap_await(stmt.value)
        target = stmt.targets[0]

        if self._is_gather_call(value):
            self._df_gather(value, target)
        elif isinstance(value, ast.Dict):
            self._df_dict_merge(value, target)
        elif isinstance(value, ast.Call) and self._agent_vertex_for_call(value):
            result = self._df_invoke(value)
            self._bind(target, [result])
        elif isinstance(value, ast.Name) and value.id in self.producers:
            # Plain alias: y = x
            self._bind(target, [list(self.producers[value.id])])
        else:
            self.warnings.append(
                f"process_one line {stmt.lineno}: unrecognised assignment, skipped"
            )

    def _df_gather(self, gather_call: ast.Call, target: ast.AST):
        """`a, b = await asyncio.gather(f(x), g(x))` — concurrent calls.

        gather introduces no node of its own: it is just several agent
        invocations that happen to run concurrently. Each call becomes an
        edge from its argument's producer into the agent; the tuple
        target binds each result positionally.
        """
        results = []
        for arg in gather_call.args:
            arg = self._unwrap_await(arg)
            if isinstance(arg, ast.Call) and self._agent_vertex_for_call(arg):
                results.append(self._df_invoke(arg))
            else:
                self.warnings.append(
                    "asyncio.gather arg is not an agent call; skipped"
                )
                results.append([])
        self._bind(target, results)

    def _df_dict_merge(self, dict_node: ast.Dict, target: ast.AST):
        """`enriched = {**a, **b, ...}` — fan-in of agent-produced values.

        Merging two independent messages into one is the single place a
        message-passing graph needs a fan-in node, so a dict-merge of two
        or more agent-produced values becomes a ``synchronizer`` whose
        inports are named after the merged variables. Merging a single
        agent-produced value (plus source fields) is just an annotation
        pass-through — no synchronizer needed.
        """
        splat_names = [
            v.id
            for k, v in zip(dict_node.keys, dict_node.values)
            if k is None and isinstance(v, ast.Name)
        ]
        branch_vars = [
            name for name in splat_names
            if self.producers.get(name)
            and all(self._is_vertex_node(n) for (n, _) in self.producers[name])
        ]
        names = self._target_names(target)
        if not names:
            return

        if len(branch_vars) >= 2:
            sync_vid = self._new_vertex_id()
            self.vertices.append({
                "id": sync_vid,
                "role": "synchronizer",
                "kind": "structural",
                "params": {"inports": list(branch_vars)},
                "role_prompt": (
                    "Wait for one message on each named inport; emit one "
                    "merged output. Merge is by field-union: fields from "
                    "each incoming message contribute to the output."
                ),
            })
            for name in branch_vars:
                for (n, p) in self.producers[name]:
                    self.edges.append(
                        {"from": [n, p], "to": [sync_vid, name]}
                    )
            self.producers[names[0]] = [(sync_vid, "out")]
        elif len(branch_vars) == 1:
            self.producers[names[0]] = list(self.producers[branch_vars[0]])
        else:
            self.producers[names[0]] = list(self.source_endpoints)

    def _df_send_to(self, stmt: ast.Expr):
        """`send_to(v, "sink", ...)` — edge from v's producer to a sink."""
        call = self._unwrap_await(stmt.value)
        sink_id = self._sink_from_send_to_call(call)
        if not sink_id or not call.args:
            return
        for (n, p) in self._producers_of_expr(call.args[0]):
            self.edges.append({"from": [n, p], "to": [sink_id, "in_"]})

    def _df_if(self, stmt: ast.If):
        """`if <field == "value">: send_to(v, sink)` — route v to a sink.

        The routed value flows through a ``router`` vertex, which emits
        on the condition's outport only when the field matches. Several
        `if` branches that route the same value share one router.
        """
        field_name, value = self._field_and_value_from_condition(stmt.test)
        outport = (
            value if value is not None
            else self._outport_from_condition(stmt.test)
        )
        for sub in stmt.body:
            if not self._is_send_to_stmt(sub):
                continue
            call = self._unwrap_await(sub.value)
            sink_id = self._sink_from_send_to_call(call)
            if not sink_id or not call.args:
                continue
            producers = self._producers_of_expr(call.args[0])
            if not producers:
                continue
            router_id = self._ensure_router_for(producers)
            router = self._get_vertex_by_id(router_id)
            routes = router["params"]["routes"]
            if not any(r["outport"] == outport for r in routes):
                routes.append(
                    {"outport": outport, "field": field_name, "equals": value}
                )
            outs = router.setdefault("outports", [])
            if outport not in outs:
                outs.append(outport)
            self.edges.append(
                {"from": [router_id, outport], "to": [sink_id, "in_"]}
            )

        if stmt.orelse:
            self.warnings.append(
                f"if at line {stmt.lineno}: else / elif branch not yet handled"
            )

    def _df_return(self, stmt: ast.Return):
        """`return v` — record v's producer as the pipeline output."""
        if stmt.value is not None:
            self.pipeline_output = self._producers_of_expr(stmt.value)

    # ---------------------------------------------------------------- #
    # Dataflow helpers                                                 #
    # ---------------------------------------------------------------- #

    def _df_invoke(self, call: ast.Call) -> list:
        """Wire the call's argument into the agent; return the agent's out.

        ``agent(x)`` and ``instance.process(x)`` are handled the same
        way: x's producer(s) feed the agent's ``in_`` port and the agent
        produces on its ``out`` port.
        """
        vid = self._agent_vertex_for_call(call)
        if call.args:
            for (n, p) in self._producers_of_expr(call.args[0]):
                self.edges.append({"from": [n, p], "to": [vid, "in_"]})
        return [(vid, "out")]

    def _agent_vertex_for_call(self, call: ast.AST) -> Optional[str]:
        """Return the vertex id an agent call resolves to, or None."""
        if not isinstance(call, ast.Call):
            return None
        func = call.func
        if isinstance(func, ast.Name) and func.id in self.agent_id_by_name:
            return self.agent_id_by_name[func.id]
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            inst = func.value.id
            if inst in self.class_instance_names:
                return self.class_instance_names[inst]
            if inst in self.agent_id_by_name:
                return self.agent_id_by_name[inst]
        return None

    def _producers_of_expr(self, expr: ast.AST) -> list:
        """Resolve an expression to the endpoints that produce its value."""
        if isinstance(expr, ast.Name) and expr.id in self.producers:
            return list(self.producers[expr.id])
        if isinstance(expr, ast.Call) and self._agent_vertex_for_call(expr):
            return self._df_invoke(expr)
        return []

    def _bind(self, target: ast.AST, producer_lists: list):
        """Bind assignment target name(s) to producer endpoint list(s)."""
        names = self._target_names(target)
        if len(names) == len(producer_lists):
            for name, producers in zip(names, producer_lists):
                self.producers[name] = list(producers)
        elif len(names) == 1:
            # Single target holding a tuple of results: flatten.
            flat = [ep for producers in producer_lists for ep in producers]
            self.producers[names[0]] = flat

    def _target_names(self, target: ast.AST) -> list:
        if isinstance(target, ast.Tuple):
            return [e.id for e in target.elts if isinstance(e, ast.Name)]
        if isinstance(target, ast.Name):
            return [target.id]
        return []

    def _ensure_router_for(self, producers: list) -> str:
        """Return a router fed by ``producers``, creating it on first use."""
        key = tuple(producers)
        if key in self.router_by_producer:
            return self.router_by_producer[key]
        rid = self._new_vertex_id()
        self.vertices.append({
            "id": rid,
            "role": "router",
            "kind": "structural",
            "params": {"routes": []},
            "role_prompt": (
                "Route each incoming message to the outport(s) whose "
                "condition it matches. A message may match several "
                "outports; one that matches no condition is dropped."
            ),
            "outports": [],
        })
        for (n, p) in producers:
            self.edges.append({"from": [n, p], "to": [rid, "in_"]})
        self.router_by_producer[key] = rid
        return rid

    def _new_vertex_id(self) -> str:
        return f"v{len(self.vertices)}"

    def _is_vertex_node(self, node_id: str) -> bool:
        """True when node_id names a vertex (agent/synchronizer/router)."""
        return isinstance(node_id, str) and node_id.startswith("v")

    def _unwrap_await(self, node: ast.AST) -> ast.AST:
        return node.value if isinstance(node, ast.Await) else node

    def _is_gather_call(self, value: ast.AST) -> bool:
        return (isinstance(value, ast.Call)
                and isinstance(value.func, ast.Attribute)
                and isinstance(value.func.value, ast.Name)
                and value.func.value.id == "asyncio"
                and value.func.attr == "gather")

    # ---------------------------------------------------------------- #
    # Helper predicates                                                #
    # ---------------------------------------------------------------- #

    def _is_docstring(self, stmt: ast.stmt) -> bool:
        return (isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str))

    def _is_send_to_stmt(self, stmt: ast.stmt) -> bool:
        if not isinstance(stmt, ast.Expr):
            return False
        val = stmt.value
        if isinstance(val, ast.Await):
            val = val.value
        return (isinstance(val, ast.Call)
                and isinstance(val.func, ast.Name)
                and val.func.id == "send_to")

    # ---------------------------------------------------------------- #
    # Small utilities                                                  #
    # ---------------------------------------------------------------- #

    def _find_top_level_async_def(self, name: str) -> Optional[ast.AsyncFunctionDef]:
        for node in self.tree.body:
            if isinstance(node, ast.AsyncFunctionDef) and node.name == name:
                return node
        return None

    def _string_constant(self, node: ast.AST) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        raise TranslationError(
            f"expected string constant, got {type(node).__name__}", node=node
        )

    def _call_function_name(self, call: ast.Call) -> str:
        if isinstance(call.func, ast.Name):
            return call.func.id
        if isinstance(call.func, ast.Attribute):
            return call.func.attr
        return "<unknown>"

    def _call_kwargs(self, call: ast.Call) -> dict:
        return {
            k.arg: self._eval_constant(k.value)
            for k in call.keywords if k.arg
        }

    def _eval_constant(self, node: ast.AST):
        if isinstance(node, ast.Constant):
            return node.value
        # Handle `Name('OUTPUT_PATH')` — reference to a module-level constant
        if isinstance(node, ast.Name):
            for stmt in self.tree.body:
                if (isinstance(stmt, ast.Assign)
                        and len(stmt.targets) == 1
                        and isinstance(stmt.targets[0], ast.Name)
                        and stmt.targets[0].id == node.id
                        and isinstance(stmt.value, ast.Constant)):
                    return stmt.value.value
            return node.id
        try:
            return ast.literal_eval(node)
        except Exception:
            return ast.unparse(node)

    def _outport_from_condition(self, test: ast.AST) -> str:
        """Return the outport name for an `if <test>:` branch."""
        # `X == "value"` → outport "value"
        if isinstance(test, ast.Compare) and len(test.ops) == 1:
            op = test.ops[0]
            if isinstance(op, ast.Eq):
                right = test.comparators[0]
                if isinstance(right, ast.Constant) and isinstance(right.value, str):
                    return right.value
        # `x.get("field") == "value"` handled the same way
        if isinstance(test, ast.Compare) and len(test.ops) == 1:
            if isinstance(test.ops[0], ast.Eq):
                right = test.comparators[0]
                if isinstance(right, ast.Constant) and isinstance(right.value, str):
                    return right.value
        # Everything else → "true"
        return "true"

    def _field_and_value_from_condition(
        self, test: ast.AST
    ) -> tuple[Optional[str], Optional[str]]:
        """Extract ``(field, value)`` from ``<field-read> == "value"``.

        Recognises the message-field readers a student typically writes
        in a post-merge conditional:

        * ``message["severity"] == "critical"``      (subscript)
        * ``message.get("severity") == "critical"``  (dict .get)
        * ``message.severity == "critical"``         (attribute)

        Returns ``(None, None)`` when the condition isn't one of these
        ``== "string"`` shapes; the caller then falls back to a plain
        outport name with no field test.
        """
        if not (isinstance(test, ast.Compare)
                and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Eq)):
            return None, None
        right = test.comparators[0]
        if not (isinstance(right, ast.Constant)
                and isinstance(right.value, str)):
            return None, None
        return self._field_name_from_expr(test.left), right.value

    def _field_name_from_expr(self, expr: ast.AST) -> Optional[str]:
        """Return the message-field name read by ``expr``, or ``None``."""
        # message["field"]
        if isinstance(expr, ast.Subscript):
            key = expr.slice
            # Python <3.9 wraps the key in ast.Index; unwrap defensively.
            if isinstance(key, ast.Index):  # pragma: no cover
                key = key.value
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                return key.value
        # message.get("field") / message.get("field", default)
        if (isinstance(expr, ast.Call)
                and isinstance(expr.func, ast.Attribute)
                and expr.func.attr == "get"
                and expr.args):
            a0 = expr.args[0]
            if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                return a0.value
        # message.field
        if isinstance(expr, ast.Attribute):
            return expr.attr
        return None

    def _sink_from_send_to_call(self, call: ast.Call) -> Optional[str]:
        """Extract sink id from `send_to(msg, "name", **kwargs)`."""
        if len(call.args) < 2:
            self.warnings.append("send_to with fewer than 2 args")
            return None
        short_name = self._string_constant(call.args[1])
        params = {
            k.arg: self._eval_constant(k.value)
            for k in call.keywords if k.arg
        }
        dsl_name = _SINK_NAME_MAP.get(short_name, short_name)
        key = (dsl_name, tuple(sorted(params.items())))
        if key in self.sink_id_by_key:
            return self.sink_id_by_key[key]
        sid = f"k{len(self.sinks)}"
        self.sinks.append({
            "id": sid,
            "name": dsl_name,
            "params": params,
        })
        self.sink_id_by_key[key] = sid
        return sid

    def _get_vertex_by_id(self, vid: Optional[str]) -> Optional[dict]:
        if vid is None:
            return None
        for v in self.vertices:
            if v["id"] == vid:
                return v
        return None

    def _build_graph(self) -> dict:
        return {
            "sources": self.sources,
            "vertices": self.vertices,
            "sinks": self.sinks,
            "edges": self.edges,
        }


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #


def _main(argv: Optional[list] = None) -> int:
    import argparse
    p = argparse.ArgumentParser(
        description="Translate OfficeSpeak asyncio Python to a graph YAML.",
    )
    p.add_argument("input", help="Path to a .py file (Run 2 style)")
    p.add_argument("--output", "-o", help="Path to graph YAML (default: stdout)")
    p.add_argument(
        "--include-source", action="store_true",
        help="Include source_code fields in the emitted YAML (verbose)",
    )
    args = p.parse_args(argv)

    text = Path(args.input).read_text()
    try:
        graph, warnings = parse(text)
    except TranslationError as e:
        print(f"TranslationError: {e}", file=sys.stderr)
        return 1

    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)

    if not args.include_source:
        graph = {
            **graph,
            "vertices": [
                {k: v for k, v in vv.items() if k != "source_code"}
                for vv in graph["vertices"]
            ],
        }

    try:
        import yaml
        out = yaml.safe_dump(graph, sort_keys=False, allow_unicode=True)
    except ImportError:
        import json
        out = json.dumps(graph, indent=2, default=str)

    if args.output:
        Path(args.output).write_text(out)
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
