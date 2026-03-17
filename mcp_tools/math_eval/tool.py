"""Safely evaluate a mathematical expression."""

import ast
import math
import operator

SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

SAFE_FUNCS = {
    "abs": abs, "round": round, "min": min, "max": max,
    "sqrt": math.sqrt, "ceil": math.ceil, "floor": math.floor,
    "log": math.log, "log10": math.log10, "sin": math.sin,
    "cos": math.cos, "tan": math.tan, "pi": math.pi, "e": math.e,
}


def _eval_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value!r}")
    if isinstance(node, ast.UnaryOp) and type(node.op) in SAFE_OPS:
        return SAFE_OPS[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPS:
        return SAFE_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        func = SAFE_FUNCS.get(node.func.id)
        if func is None:
            raise ValueError(f"Unknown function: {node.func.id}")
        args = [_eval_node(a) for a in node.args]
        return func(*args) if callable(func) else func
    if isinstance(node, ast.Name) and node.id in SAFE_FUNCS:
        val = SAFE_FUNCS[node.id]
        if not callable(val):
            return val
        raise ValueError(f"{node.id} requires arguments")
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def run(expression: str) -> str:
    """Evaluate a math expression safely without exec/eval."""
    tree = ast.parse(expression, mode="eval")
    result = _eval_node(tree.body)
    if isinstance(result, float) and result == int(result):
        return str(int(result))
    return str(result)
