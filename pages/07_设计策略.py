import streamlit as st

from src.stages.stage07_strategy.page import render_page


st.set_page_config(page_title="07 设计策略", layout="wide", initial_sidebar_state="collapsed")
render_page()
