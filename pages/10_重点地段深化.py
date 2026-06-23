import streamlit as st

from src.stages.stage10_detail_design.page import render_page

st.set_page_config(page_title="10 重点地段深化", layout="wide", initial_sidebar_state="collapsed")
render_page()
