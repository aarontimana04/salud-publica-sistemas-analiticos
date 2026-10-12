from pathlib import Path
import streamlit as st

if st.query_params.get("source") == "excel":
    source = Path(__file__).with_name("excel_app.py")
    exec(compile(source.read_text(), str(source), "exec"))
else:
    from demo_dashboard import main
    main()
