@echo off
call venv\Scripts\activate
python -m streamlit run frontend\app.py --server.address 0.0.0.0 --server.port 8501