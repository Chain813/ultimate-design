import streamlit as st

from src.stages.stage08_master_plan.page import render_page

st.set_page_config(page_title="08 总体城市设计", layout="wide", initial_sidebar_state="collapsed")
render_page()
