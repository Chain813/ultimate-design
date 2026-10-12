import streamlit as st

from src.stages.stage09_systems.page import render_page

st.set_page_config(page_title="09 专项系统设计", layout="wide", initial_sidebar_state="collapsed")
render_page()
