import streamlit as st

from src.stages.stage12_guideline.page import render_page


st.set_page_config(page_title="12 城市设计导则", layout="wide", initial_sidebar_state="collapsed")
render_page()
