import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from dotenv import load_dotenv

from core.memory import ChatMemory
from core.router import route_question
from core.prompts import SYSTEM_ANALYST
from core.llm import chat_text, generate_python
from core.safe_exec import run_user_code
from core.profiling import profile_df

load_dotenv()

st.set_page_config(page_title="Advanced AI Data Analyst", layout="wide")
st.title("Advanced AI Data Analyst (MVP)")

model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
if not os.environ.get("OPENAI_API_KEY"):
    st.warning("Set OPENAI_API_KEY in your environment or .env")

# -------------------------------
# Session state
# -------------------------------
if "memory" not in st.session_state:
    st.session_state.memory = ChatMemory()

if "df" not in st.session_state:
    st.session_state.df = None

if "last_column" not in st.session_state:
    st.session_state.last_column = None


def find_candidate_columns(user_text: str, columns: list[str]) -> list[str]:
    text = user_text.lower()
    return [c for c in columns if c.lower() in text]


# -------------------------------
# Sidebar: Data upload
# -------------------------------
with st.sidebar:
    st.header("Data")
    up = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    if up is not None:
        if up.name.endswith(".csv"):
            st.session_state.df = pd.read_csv(up)
        else:
            st.session_state.df = pd.read_excel(up)

    if st.session_state.df is not None:
        st.success(
            f"Loaded: {st.session_state.df.shape[0]} rows × {st.session_state.df.shape[1]} cols"
        )
        st.caption("Preview")
        st.dataframe(st.session_state.df.head(20), use_container_width=True)

        if st.button("Auto Profile"):
            prof = profile_df(st.session_state.df)
            st.subheader("Dataset Profile")
            st.write(prof)

st.divider()

df = st.session_state.df
if df is None:
    st.info("Upload a dataset to begin.")
    st.stop()

# -------------------------------
# Render chat history
# -------------------------------
for m in st.session_state.memory.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# -------------------------------
# Chat input
# -------------------------------
user_q = st.chat_input("Ask a question about your data…")
if user_q:
    st.session_state.memory.add_user(user_q)
    with st.chat_message("user"):
        st.markdown(user_q)


    route = route_question(
        user_q,
        model=model,
        has_df=True
    )
    tool = route.get("tool", "eda")

    with st.chat_message("assistant"):
        st.caption(f"Tool: **{tool}** · Reason: {route.get('reason','')}")

        # ---------------------------
        # PROFILE
        # ---------------------------
        if tool == "profile":
            prof = profile_df(df)
            st.write(prof)
            answer = "I profiled your dataset above. Tell me what outcome or metric you want to analyze."

        # ---------------------------
        # EDA / PLOT / STATS
        # ---------------------------
        elif tool in {"eda", "plot", "stats"}:

            columns = list(df.columns)
            candidates = find_candidate_columns(user_q, columns)

            if len(candidates) == 1:
                inferred_column = candidates[0]
                st.session_state.last_column = inferred_column
            elif len(candidates) > 1:
                msg = (
                    f"I found multiple matching columns: {candidates}. "
                    f"Which one should I use?"
                )
                st.markdown(msg)
                st.session_state.memory.add_assistant(msg)
                st.stop()
            else:
                inferred_column = st.session_state.last_column

            column_hint = (
                f"The user is referring to column '{inferred_column}'."
                if inferred_column else ""
            )


            code_prompt = f"""
Write Python code to answer the user's question using pandas/numpy/matplotlib.

STRICT SCHEMA RULES:
- You MUST use column names EXACTLY as they appear in df.columns.
- DO NOT invent, rename, infer, or assume column names.
- Do NOT attempt fuzzy matching or semantic guessing of column names.
- If the requested column does not exist, STOP and set:
  result = "Column not found. Available columns are: {list(df.columns)}"

EXECUTION RULES:
- df, pd, np, plt are already available.
- Do NOT import anything.
- If creating a plot, call plt.figure() and create the plot, but do NOT call plt.show().
- Put the final output in a variable named `result`.

Context:
- Available columns: {list(df.columns)}
- {column_hint}

User question: {user_q}
"""

            py_messages = [
                {"role": "system", "content": SYSTEM_ANALYST},
                {"role": "user", "content": code_prompt},
            ]
            raw_code = generate_python(py_messages, model=model)

            # Cleanup markdown fences
            code = raw_code.strip()
            if code.startswith("```"):
                code = code.split("```", 2)[1]
                if code.lstrip().startswith("python"):
                    code = code.split("\n", 1)[1]

            st.subheader("Generated code")
            st.code(code, language="python")


            env = {"df": df, "pd": pd, "np": np, "plt": plt}
            try:
                _, result = run_user_code(code, env=env)

                fig = plt.gcf()
                if fig and fig.axes:
                    st.pyplot(fig, clear_figure=True)

                if isinstance(result, pd.DataFrame):
                    st.dataframe(result, use_container_width=True)
                    answer = "Here are the computed results."
                elif isinstance(result, (dict, list)):
                    st.write(result)
                    answer = "Here are the computed results."
                elif result is None:
                    answer = "Analysis ran successfully, but no explicit result was returned."
                else:
                    st.markdown(str(result))
                    answer = str(result)

            except Exception as e:
                answer = f"Execution blocked: {e}"

        # ---------------------------
        # Fallback (non-data)
        # ---------------------------
        else:
            msgs = [{"role": "system", "content": SYSTEM_ANALYST}] + st.session_state.memory.last(10)
            answer = chat_text(msgs, model=model)
            st.markdown(answer)

    st.session_state.memory.add_assistant(answer)


