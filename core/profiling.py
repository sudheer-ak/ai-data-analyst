import pandas as pd

def profile_df(df: pd.DataFrame) -> dict:
    n_rows, n_cols = df.shape
    dtypes = {c: str(df[c].dtype) for c in df.columns}
    missing = {c: int(df[c].isna().sum()) for c in df.columns}
    missing_pct = {c: float(df[c].isna().mean()) for c in df.columns}

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = [c for c in df.columns if c not in numeric_cols]

    summary_num = {}
    if numeric_cols:
        desc = df[numeric_cols].describe().T
        for c in numeric_cols:
            summary_num[c] = {
                "mean": float(desc.loc[c, "mean"]),
                "std": float(desc.loc[c, "std"]) if "std" in desc.columns else None,
                "min": float(desc.loc[c, "min"]),
                "max": float(desc.loc[c, "max"]),
            }

    return {
        "shape": {"rows": n_rows, "cols": n_cols},
        "numeric_cols": numeric_cols,
        "categorical_cols": cat_cols,
        "dtypes": dtypes,
        "missing": missing,
        "missing_pct": missing_pct,
        "numeric_summary": summary_num,
    }

