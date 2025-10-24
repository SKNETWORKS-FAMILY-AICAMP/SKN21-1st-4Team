import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import run

# === 0) 모듈 경로 보정 ===
import os, sys
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, ".."))
_CRAWLING_PATH = os.path.join(_PROJECT_ROOT, "crawling_py")
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
if _CRAWLING_PATH not in sys.path:
    sys.path.insert(0, _CRAWLING_PATH)

# === 1) Page config는 스트림릿 명령어 중 가장 먼저 호출 ===
st.set_page_config(
    page_title="119 응급의료시스템 분석",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 오류 메시지는 먼저 모아두었다가 UI 로딩 후 표시
_pending_errors: list[str] = []

# === 2) 유틸리티 함수 import (실패해도 앱이 죽지 않도록) ===
try:
    from utils import create_sample_data, calculate_required_ambulances
except Exception as e:
    _pending_errors.append(f"utils 모듈을 찾을 수 없습니다: {e}")
    create_sample_data = None
    calculate_required_ambulances = None

# === 3) 페이지 모듈 안전 로딩 ===
def _pick_func(mod, names):
    for n in names:
        fn = getattr(mod, n, None)
        if callable(fn):
            return fn
    return None

show_overview_page = None
show_analysis_page = None
show_faq_page = None

try:
    import crawling_py.page_modules.overview as _ov
    show_overview_page = _pick_func(_ov, ["show_overview_page", "show_page", "main"])
    if show_overview_page is None:
        _pending_errors.append("overview 모듈에서 호출 가능한 함수(show_overview_page/show_page/main)를 찾지 못했습니다.")
except Exception as e:
    _pending_errors.append(f"페이지 모듈 로드 오류(overview): {e}")

try:
    import crawling_py.page_modules.analysis as _an
    show_analysis_page = _pick_func(_an, ["show_analysis_page", "show_page", "main"])
    if show_analysis_page is None:
        _pending_errors.append("analysis 모듈에서 호출 가능한 함수(show_analysis_page/show_page/main)를 찾지 못했습니다.")
except Exception as e:
    _pending_errors.append(f"페이지 모듈 로드 오류(analysis): {e}")

try:
    import crawling_py.page_modules.faq as _fq
    show_faq_page = _pick_func(_fq, ["show_faq_page", "show_page", "main"])
    if show_faq_page is None:
        _pending_errors.append("faq 모듈에서 호출 가능한 함수(show_faq_page/show_page/main)를 찾지 못했습니다.")
except Exception as e:
    _pending_errors.append(f"페이지 모듈 로드 오류(faq): {e}")

# === 4) CSS ===
st.markdown("""
<style>
    .section-header {
        background: linear-gradient(90deg, #4ecdc4, #44a08d);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0 15px 0;
        text-align: center;
        font-weight: bold;
    }
    .golden-time-box {
        background: linear-gradient(135deg, #ffd89b, #19547b);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #ff6b6b;
        margin: 10px 0;
    }
    @media (max-width: 600px) {
        .main-header { padding: 14px; }
        .golden-time-box { padding: 14px; }
    }
    .alert-box {
        background: #fff3cd;
        border: 1px solid #ffc107;
        color: #856404;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }
    .success-box {
        background: #d1edff;
        border: 1px solid #0084ff;
        color: #0056b3;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }
    .sidebar .sidebar-content { background-color: #f8f9fa; }
    .stButton > button {
        width: 100%;
        background-color: transparent;
        color: #666666;
        border: none;
        border-radius: 0;
        padding: 12px 16px;
        margin: 5px 0;
        font-size: 14px;
        transition: all 0.2s ease;
        text-align: left;
    }
    .stButton > button:hover { background-color: #f5f5f5; color: #333333; }
    .current-menu {
        font-weight: bold !important;
        font-size: 16px !important;
        color: #333333 !important;
        padding: 12px 16px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# === 5) 메인 앱 ===
def main():
    
    run.run()

    # (로딩 중 쌓인 에러 메시지 출력)
    for msg in _pending_errors:
        st.warning(msg)

    st.sidebar.title("📊 PT 순서")

    # 세션 상태 초기화
    if "current_page" not in st.session_state:
        st.session_state.current_page = "🏥 응급의료시스템 개요"

    menu_options = ["🏥 응급의료시스템 개요", "📊 데이터 및 수요 분석", "❓ 자주 묻는 질문"]

    for option in menu_options:
        if option == st.session_state.current_page:
            st.sidebar.markdown(f'<div class="current-menu">{option}</div>', unsafe_allow_html=True)
        else:
            if st.sidebar.button(option, key=f"btn_{option}"):
                st.session_state.current_page = option
                st.rerun()

    page = st.session_state.current_page

    try:
        if page == "🏥 응급의료시스템 개요":
            if callable(show_overview_page):
                show_overview_page()
            else:
                st.error("페이지를 로드하는 중 오류가 발생했습니다: name 'show_overview_page' is not defined")

        elif page == "📊 데이터 및 수요 분석":
            if callable(show_analysis_page):
                show_analysis_page()
            else:
                st.error("페이지를 로드하는 중 오류가 발생했습니다: name 'show_analysis_page' is not defined")

        elif page == "❓ 자주 묻는 질문":
            if callable(show_faq_page):
                show_faq_page()
            else:
                st.error("페이지를 로드하는 중 오류가 발생했습니다: name 'show_faq_page' is not defined")

    except Exception as e:
        st.error(f"페이지를 표시하는 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()