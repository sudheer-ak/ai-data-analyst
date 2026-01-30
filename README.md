# Advanced AI Data Analyst

An AI-powered data analysis application that allows users to upload datasets and
perform exploratory analysis, visualizations, and statistical insights using
natural language.

## Features
- Upload CSV or Excel datasets
- Automatic dataset profiling
- Natural language analysis
- Safe Python execution
- Visualization with matplotlib
- Column-aware validation (no guessing)
- Streamlit-based UI

## Tech Stack
- Python
- Streamlit
- Pandas, NumPy, Matplotlib
- OpenAI API
- Modular architecture

## How to Run
```bash
cd ai-data-analyst
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m streamlit run app/streamlit_app.py

