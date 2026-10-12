import streamlit as st

from src.stages.stage13_outputs.page import render_page

st.set_page_config(page_title="13 成果表达", layout="wide", initial_sidebar_state="collapsed")
render_page()
