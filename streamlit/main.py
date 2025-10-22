import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

# 유틸리티 함수 import
try:
    from utils import create_sample_data, calculate_required_ambulances
except ImportError:
    st.error("utils 모듈을 찾을 수 없습니다.")

# 페이지 모듈 import
try:
    from page_modules.overview import show_overview_page
    from page_modules.analysis import show_analysis_page
    from page_modules.faq import show_faq_page
except ImportError as e:
    st.error(f"페이지 모듈을 찾을 수 없습니다: {e}")

# 페이지 설정
st.set_page_config(
    page_title="119 응급의료시스템 분석",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
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

    /* responsive tweaks */
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
    
    /* 사이드바 메뉴 스타일링 */
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    /* 사이드바 버튼 스타일 개선 */
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
    
    .stButton > button:hover {
        background-color: #f5f5f5;
        color: #333333;
    }
    
    /* 현재 선택된 메뉴 스타일 */
    .current-menu {
        font-weight: bold !important;
        font-size: 16px !important;
        color: #333333 !important;
        padding: 12px 16px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# 메인 앱
def main():
    # 사이드바
    st.sidebar.title("📊 분석 메뉴")
    
    # 세션 상태 초기화
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏥 응급의료시스템 개요"
    
    # 메뉴 옵션들
    menu_options = [
        "🏥 응급의료시스템 개요", 
        "📊 데이터 및 수요 분석", 
        "❓ 자주 묻는 질문"
    ]
    
    # 각 메뉴를 개별 버튼으로 표시
    for option in menu_options:
        if option == st.session_state.current_page:
            # 현재 선택된 메뉴는 볼드체로만 표시
            st.sidebar.markdown(f"""
                <div class="current-menu">
                    {option}
                </div>
            """, unsafe_allow_html=True)
        else:
            # 다른 메뉴들은 클릭 가능한 버튼으로 표시
            if st.sidebar.button(option, key=f"btn_{option}"):
                st.session_state.current_page = option
                st.rerun()
    
    page = st.session_state.current_page
    
    try:
        if page == "🏥 응급의료시스템 개요":
            show_overview_page()
        elif page == "📊 데이터 및 수요 분석":
            show_analysis_page()
        elif page == "❓ 자주 묻는 질문":
            show_faq_page()
    except Exception as e:
        st.error(f"페이지를 로드하는 중 오류가 발생했습니다: {e}")
        st.write("사용 가능한 페이지:")
        st.write("- 🏥 응급의료시스템 개요")
        st.write("- 📊 데이터 및 수요 분석")
        st.write("- ❓ 자주 묻는 질문")
if __name__ == "__main__":
    main()