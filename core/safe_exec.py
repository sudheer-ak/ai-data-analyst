"""
A minimal "safe-ish" executor:
- blocks imports
- blocks file/network ops by not exposing them
- only exposes df, pd, np, plt
This is not perfect security, but good for MVP.
For production, use a proper sandbox (separate process/container).
"""
from __future__ import annotations

import ast
import textwrap
from typing import Any, Dict, Tuple
import re

def extract_columns_from_code(code: str):
    """
    Find column names used like df["col"] or df['col']
    """
    pattern = r"df\[['\"]([^'\"]+)['\"]\]"
    return set(re.findall(pattern, code))

def _validate_ast(code: str) -> None:
    tree = ast.parse(code)
    banned = (ast.Import, ast.ImportFrom, ast.With, ast.Try, ast.Global, ast.Nonlocal, ast.Lambda)
    for node in ast.walk(tree):
        if isinstance(node, banned):
            raise ValueError("Code contains a blocked construct (imports/with/try/global/etc).")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"open", "exec", "eval", "__import__"}:
                raise ValueError("Blocked function call detected.")
        if isinstance(node, ast.Attribute):
            # Block obvious escapes
            if node.attr in {"system", "popen", "remove", "unlink", "rmdir"}:
                raise ValueError("Blocked attribute usage detected.")

def run_user_code(code: str, env: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    code = textwrap.dedent(code).strip()
    _validate_ast(code)

    # ---- Column validation layer ----
    df = env.get("df")
    if df is not None:
        used_cols = extract_columns_from_code(code)
        invalid_cols = used_cols - set(df.columns)

        if invalid_cols:
            raise ValueError(
                f"Invalid column(s) referenced: {invalid_cols}. "
                f"Available columns are: {list(df.columns)}"
            )

    # ---- Safe execution ----
    local_env: Dict[str, Any] = {}
    safe_globals = {"__builtins__": {}}
    safe_globals.update(env)

    exec(code, safe_globals, local_env)  # noqa: S102 (intentional)
    combined = {**safe_globals, **local_env}

    out = combined.get("result", None)
    return combined, out


