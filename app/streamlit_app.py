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

if "memory" not in st.session_state:
    st.session_state.memory = ChatMemory()

if "df" not in st.session_state:
    st.session_state.df = None

with st.sidebar:
    st.header("Data")
    up = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    if up is not None:
        if up.name.endswith(".csv"):
            st.session_state.df = pd.read_csv(up)
        else:
            st.session_state.df = pd.read_excel(up)

    if st.session_state.df is not None:
        st.success(f"Loaded: {st.session_state.df.shape[0]} rows × {st.session_state.df.shape[1]} cols")
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

# Render chat history
for m in st.session_state.memory.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

user_q = st.chat_input("Ask a question about your data…")
if user_q:
    st.session_state.memory.add_user(user_q)
    with st.chat_message("user"):
        st.markdown(user_q)

    # Route
    route = route_question(user_q, model=model)
    tool = route.get("tool", "none")

    with st.chat_message("assistant"):
        st.caption(f"Tool: **{tool}** · Reason: {route.get('reason','')}")
        st.write("Plan:", route.get("plan", []))

        # Tool behaviors
        if tool == "profile":
            prof = profile_df(df)
            st.write(prof)
            answer = "I profiled your dataset above. Tell me what outcome/metric you care about, and I’ll dig in."

        elif tool in {"eda", "plot", "stats"}:
            # Ask LLM to write python code using df
            code_prompt = f"""
Write Python code to answer the user's question using pandas/numpy/matplotlib.
Rules:
- You already have df (pandas DataFrame), pd, np, plt available.
- Do NOT import anything.
- Put your final human-readable output in a variable named `result`.
  - result can be a string, dict, pandas DataFrame, or a list of dicts.
- If you create a plot, call plt.figure() and plot, but do not call plt.show().

User question: {user_q}

Context: df columns = {list(df.columns)}
"""
            py_messages = [
                {"role": "system", "content": SYSTEM_ANALYST},
                {"role": "user", "content": code_prompt},
            ]
            raw_code = generate_python(py_messages, model=model)

            # Basic cleanup if model wraps with markdown fences
            code = raw_code.strip()
            if code.startswith("```"):
                code = code.split("```", 2)[1]
                if code.lstrip().startswith("python"):
                    code = code.split("\n", 1)[1]

            st.subheader("Generated code")
            st.code(code, language="python")

            # Execute safely-ish
            env = {"df": df, "pd": pd, "np": np, "plt": plt}
            try:
                _, result = run_user_code(code, env=env)

                # Render plot if created
                fig = plt.gcf()
                if fig and fig.axes:
                    st.pyplot(fig, clear_figure=True)

                # Render result
                if isinstance(result, pd.DataFrame):
                    st.dataframe(result, use_container_width=True)
                    answer = "Here are the computed results in the table above."
                elif isinstance(result, (dict, list)):
                    st.write(result)
                    answer = "Here are the computed results above."
                elif result is None:
                    answer = "I ran the analysis, but the code didn’t set `result`. Want me to re-run with a cleaner output?"
                else:
                    st.markdown(str(result))
                    answer = str(result)

            except Exception as e:
                answer = f"Execution blocked/failed: {e}"

        else:
            # fallback conversational
            msgs = [{"role": "system", "content": SYSTEM_ANALYST}] + st.session_state.memory.last(10)
            answer = chat_text(msgs, model=model)
            st.markdown(answer)

    st.session_state.memory.add_assistant(answer)

