import streamlit as st

from src.stages.stage11_implementation.page import render_page

st.set_page_config(page_title="11 实施路径", layout="wide", initial_sidebar_state="collapsed")
render_page()
