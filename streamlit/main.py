import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

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
        .main-header {
            text-align: center;
            background: linear-gradient(90deg, #ff6b6b, #ee5a52);
            color: white;
            padding: 18px;
            border-radius: 12px;
            margin-bottom: 22px;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
        }
    
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

# 임시 데이터 생성 함수
@st.cache_data
def create_sample_data():
    regions = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', 
               '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
    
    years = [2020, 2021, 2022, 2023, 2024]
    
    data = []
    for region in regions:
        for year in years:
            # 인구 대비 적절한 구급차 수와 이송환자 수 생성
            base_ambulances = np.random.randint(50, 300) if region in ['서울', '경기', '부산'] else np.random.randint(15, 100)
            base_patients = base_ambulances * np.random.randint(800, 1500)  # 구급차당 연간 이송환자 수
            
            # 연도별 증가 트렌드 반영
            year_factor = 1 + (year - 2020) * 0.02
            
            data.append({
                '지역': region,
                '연도': year,
                '구급차수': int(base_ambulances * year_factor),
                '이송환자수': int(base_patients * year_factor * np.random.uniform(0.9, 1.1)),
                '인구수': np.random.randint(500000, 10000000) if region in ['서울', '경기'] else np.random.randint(100000, 3000000)
            })
    
    return pd.DataFrame(data)

# 필요 구급차 수 계산 함수
def calculate_required_ambulances(calls_per_year, avg_cycle_time_hours, target_utilization):
    """
    필요 구급차 수 계산
    calls_per_year: 연간 호출 수
    avg_cycle_time_hours: 평균 사이클 타임 (시간)
    target_utilization: 목표 가동률 (0.3 = 30%)
    """
    # 연간 시간 수
    hours_per_year = 365 * 24
    
    # 필요 구급차 수 = (호출량 * 평균 사이클 타임) / (연간 시간 * 목표 가동률)
    required = (calls_per_year * avg_cycle_time_hours) / (hours_per_year * target_utilization)
    
    return int(np.ceil(required))

# 메인 앱
def main():
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>🚑 119 응급의료시스템 분석 대시보드</h1>
        <p>구급차 수요 예측 및 운영 효율성 분석 시스템</p>
    </div>
    """, unsafe_allow_html=True)

    # 사이드바
    st.sidebar.title("📊 분석 메뉴")
    
    # 세션 상태 초기화
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏥 골든타임의 중요성"
    
    # 메뉴 옵션들
    menu_options = [
        "🏥 골든타임의 중요성", 
        "📰 현재 시스템 문제점", 
        "📊 데이터 분석", 
        "🔬 구급차 수요 분석", 
        "📈 지역별 현황"
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
    
    if page == "🏥 골든타임의 중요성":
        show_golden_time_page()
    elif page == "📰 현재 시스템 문제점":
        show_problems_page()
    elif page == "📊 데이터 분석":
        show_data_analysis_page()
    elif page == "🔬 구급차 수요 분석":
        show_demand_analysis_page()
    elif page == "📈 지역별 현황":
        show_regional_status_page()

def show_golden_time_page():
    st.markdown('<div class="section-header"><h2>🏥 골든타임(Golden Hour)의 중요성</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="golden-time-box">
            <h3>⏰ 골든타임이란?</h3>
            <p>중증 외상환자가 발생한 후 <strong>첫 1시간</strong> 내에 적절한 치료를 받아야 생존율이 크게 향상되는 시간</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ### 📊 시간별 생존율 변화
        
        응급상황에서 시간이 지날수록 환자의 생존율은 급격히 감소합니다:
        
        - **10분 이내**: 생존율 90% 이상
        - **30분 이내**: 생존율 70-80%
        - **1시간 이내**: 생존율 50-60%
        - **1시간 초과**: 생존율 30% 이하
        """)
        
        # # 생존율 그래프
        # time_data = pd.DataFrame({
        #     '시간(분)': [5, 10, 20, 30, 45, 60, 90, 120],
        #     '생존율(%)': [95, 90, 85, 75, 65, 55, 35, 20]
        # })
        
        # fig = px.line(time_data, x='시간(분)', y='생존율(%)', 
        #              title='시간 경과에 따른 생존율 변화',
        #              markers=True)
        # fig.update_traces(line_color='red', line_width=3)
        # fig.add_hline(y=60, line_dash="dash", line_color="orange", 
        #              annotation_text="골든타임 (60분)")
        # fig.update_layout(
        #     plot_bgcolor='rgba(0,0,0,0)',
        #     paper_bgcolor='rgba(0,0,0,0)',
        #     font=dict(size=12)
        # )
        # st.plotly_chart(fig, use_container_width=True)
    
def show_problems_page():
    st.markdown('<div class="section-header"><h2>📰 현재 119 응급시스템 문제점</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        ### 🚨 주요 문제점들
        
        #### 1. 구급차 부족 문제
        - 인구 대비 구급차 수 부족
        - 출동 대기시간 증가
        - 병원 이송 지연
        
        #### 2. 지역별 격차
        - 도시와 농촌 간 서비스 격차
        - 섬 지역의 응급의료 접근성 문제
        - 의료취약지역 증가
        
        #### 3. 시스템 과부하
        - 응급실 포화상태
        - 구급차 회전율 저하
        - 의료진 피로도 증가
        """)
    
    with col2:
        st.markdown("""
        ### 📰 관련 뉴스 사례
        
        #### "구급차 늦어 응급환자 사망" 사건들
        
        **사례 1: 2023년 서울 강남구**
        - 심장마비 환자, 구급차 도착까지 25분 소요
        - 병원 도착 전 사망
        
        **사례 2: 2023년 경기 외곽지역**
        - 교통사고 중상환자, 구급차 부족으로 40분 대기
        - 후송 지연으로 인한 합병증 발생
        
        **사례 3: 2024년 제주도**
        - 관광객 응급상황, 구급차 모두 출동 중
        - 1시간 30분 후 이송 가능
        """)
        
        st.markdown("""
        <div class="alert-box">
            <h4>📊 통계로 보는 문제의 심각성</h4>
            <ul>
                <li><strong>평균 출동시간</strong>: 12.3분 (목표 8분 대비 54% 초과)</li>
                <li><strong>구급차 가동률</strong>: 65% (권장 30-50% 대비 과부하)</li>
                <li><strong>응급실 대기시간</strong>: 평균 45분</li>
                <li><strong>지역별 격차</strong>: 최대 3배 차이</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def show_data_analysis_page():
    st.markdown('<div class="section-header"><h2>📊 전국 응급의료 데이터 분석</h2></div>', unsafe_allow_html=True)
    
    # 데이터 로드
    df = create_sample_data()
    
    # 필터링 옵션
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        selected_years = st.multiselect(
            "분석 연도 선택:",
            options=df['연도'].unique(),
            default=df['연도'].unique()
        )
    
    with col2:
        selected_regions = st.multiselect(
            "분석 지역 선택:",
            options=df['지역'].unique(),
            default=df['지역'].unique()[:5]
        )
    
    with col3:
        metric_type = st.selectbox(
            "분석 지표:",
            ["구급차수", "이송환자수", "인구당 구급차수"]
        )
    
    # 데이터 필터링
    filtered_df = df[
        (df['연도'].isin(selected_years)) & 
        (df['지역'].isin(selected_regions))
    ].copy()
    
    if metric_type == "인구당 구급차수":
        filtered_df['인구당 구급차수'] = (filtered_df['구급차수'] / filtered_df['인구수']) * 100000
    
    # 시계열 분석
    st.markdown("### 📈 연도별 추이 분석")
    
    if metric_type == "인구당 구급차수":
        fig = px.line(filtered_df, x='연도', y='인구당 구급차수', color='지역',
                     title='연도별 인구 10만명당 구급차 수 추이',
                     markers=True)
        fig.update_layout(yaxis_title="인구 10만명당 구급차 수")
    else:
        fig = px.line(filtered_df, x='연도', y=metric_type, color='지역',
                     title=f'연도별 {metric_type} 추이',
                     markers=True)
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 지역별 비교
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🗺️ 2024년 지역별 구급차 현황")
        latest_data = filtered_df[filtered_df['연도'] == 2024]
        
        fig_bar = px.bar(latest_data, x='지역', y='구급차수',
                        title='2024년 지역별 구급차 수',
                        color='구급차수',
                        color_continuous_scale='Reds')
        fig_bar.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.markdown("### 🏥 구급차당 이송환자 수")
        latest_data['구급차당_이송환자수'] = latest_data['이송환자수'] / latest_data['구급차수']
        
        fig_scatter = px.scatter(latest_data, x='구급차수', y='이송환자수',
                               size='인구수', color='지역',
                               hover_data=['구급차당_이송환자수'],
                               title='구급차 수 vs 이송환자 수 (2024년)')
        fig_scatter.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # 데이터 테이블
    st.markdown("### 📋 상세 데이터")
    st.dataframe(
        filtered_df.pivot(index='지역', columns='연도', values=metric_type).round(2),
        use_container_width=True
    )

def show_demand_analysis_page():
    st.markdown('<div class="section-header"><h2>🔬 구급차 수요 분석 및 계산</h2></div>', unsafe_allow_html=True)
    
    # 계산 공식 설명
    st.markdown("""
    ### 📐 구급차 필요 대수 계산 공식
    
    **필요 구급차 수 = (호출량 × 평균 사이클 타임) / 목표 가동률**
    
    - **평균 사이클 타임**: 출동부터 복귀까지의 시간
      - 도시 지역: 30-60분
      - 농촌 지역: 120-150분
    - **목표 가동률**: 30-50% (과부하 방지를 위한 여유율 확보)
    """)
    
    # 계산기 섹션
    st.markdown("### 🧮 구급차 수요 계산기")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📊 입력 값 설정")
        
        calls_per_year = st.number_input(
            "연간 응급호출 수:",
            min_value=1000,
            max_value=100000,
            value=15000,
            step=500,
            help="해당 지역의 연간 예상 응급호출 횟수"
        )
        
        region_type = st.selectbox(
            "지역 유형:",
            ["도시 지역", "농촌 지역", "사용자 정의"]
        )
        
        if region_type == "도시 지역":
            cycle_time = st.slider("평균 사이클 타임 (분):", 30, 60, 45)
        elif region_type == "농촌 지역":
            cycle_time = st.slider("평균 사이클 타임 (분):", 120, 150, 135)
        else:
            cycle_time = st.slider("평균 사이클 타임 (분):", 20, 200, 60)
        
        target_utilization = st.slider(
            "목표 가동률 (%):",
            min_value=20,
            max_value=70,
            value=40,
            step=5,
            help="권장: 30-50% (여유율 확보를 위해)"
        )
        
        # 계산 실행
        cycle_time_hours = cycle_time / 60
        utilization_decimal = target_utilization / 100
        
        required_ambulances = calculate_required_ambulances(
            calls_per_year, cycle_time_hours, utilization_decimal
        )
        
        current_ambulances = st.number_input(
            "현재 구급차 수:",
            min_value=1,
            max_value=500,
            value=required_ambulances,
            help="비교 분석을 위한 현재 보유 구급차 수"
        )
    
    with col2:
        st.markdown("#### 📈 분석 결과")
        
        # 결과 표시
        st.markdown(f"""
        <div class="metric-card">
            <h4>🎯 계산 결과</h4>
            <ul>
                <li><strong>필요 구급차 수</strong>: {required_ambulances}대</li>
                <li><strong>현재 구급차 수</strong>: {current_ambulances}대</li>
                <li><strong>과부족</strong>: {current_ambulances - required_ambulances:+d}대</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # 상태 판정
        diff = current_ambulances - required_ambulances
        if diff >= 0:
            status_color = "success-box"
            status_text = "✅ 충분"
            recommendation = "현재 구급차 수가 적정 수준입니다."
        else:
            status_color = "alert-box"
            status_text = "⚠️ 부족"
            recommendation = f"{abs(diff)}대의 추가 구급차가 필요합니다."
        
        st.markdown(f"""
        <div class="{status_color}">
            <h4>{status_text}</h4>
            <p>{recommendation}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 가동률 분석
        if current_ambulances > 0:
            actual_utilization = (calls_per_year * cycle_time_hours) / (current_ambulances * 365 * 24) * 100
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>📊 가동률 분석</h4>
                <ul>
                    <li><strong>목표 가동률</strong>: {target_utilization}%</li>
                    <li><strong>실제 가동률</strong>: {actual_utilization:.1f}%</li>
                    <li><strong>여유율</strong>: {100 - actual_utilization:.1f}%</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # 시나리오 분석
    st.markdown("### 🎯 시나리오 분석")
    
    scenarios = pd.DataFrame({
        '시나리오': ['현재', '목표(30%)', '목표(40%)', '목표(50%)'],
        '가동률': [30, 40, 50, 60],
        '필요대수': [
            calculate_required_ambulances(calls_per_year, cycle_time_hours, 0.3),
            calculate_required_ambulances(calls_per_year, cycle_time_hours, 0.4),
            calculate_required_ambulances(calls_per_year, cycle_time_hours, 0.5),
            calculate_required_ambulances(calls_per_year, cycle_time_hours, 0.6)
        ]
    })
    
    fig_scenario = px.bar(scenarios, x='시나리오', y='필요대수',
                         title='목표 가동률별 필요 구급차 수',
                         color='필요대수',
                         color_continuous_scale='Blues')
    fig_scenario.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_scenario, use_container_width=True)

def show_regional_status_page():
    st.markdown('<div class="section-header"><h2>📈 지역별 현황 및 개선 방안</h2></div>', unsafe_allow_html=True)
    
    # 데이터 로드
    df = create_sample_data()
    latest_df = df[df['연도'] == 2024].copy()
    
    # 지역별 필요 구급차 수 계산
    latest_df['도시여부'] = latest_df['지역'].apply(
        lambda x: '도시' if x in ['서울', '부산', '대구', '인천', '광주', '대전', '울산'] else '농촌'
    )
    latest_df['평균사이클타임'] = latest_df['도시여부'].apply(
        lambda x: 45/60 if x == '도시' else 135/60  # 시간 단위
    )
    latest_df['연간호출수'] = latest_df['이송환자수'] * 1.2  # 이송환자 외 추가 호출 고려
    
    target_util = 0.4  # 40% 목표 가동률
    latest_df['필요구급차수'] = latest_df.apply(
        lambda row: calculate_required_ambulances(
            row['연간호출수'], row['평균사이클타임'], target_util
        ), axis=1
    )
    latest_df['부족대수'] = latest_df['필요구급차수'] - latest_df['구급차수']
    latest_df['상태'] = latest_df['부족대수'].apply(
        lambda x: '충분' if x <= 0 else '부족'
    )
    
    # 전국 현황 요약
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_current = latest_df['구급차수'].sum()
        st.metric("전국 현재 구급차", f"{total_current:,}대")
    
    with col2:
        total_required = latest_df['필요구급차수'].sum()
        st.metric("전국 필요 구급차", f"{total_required:,}대")
    
    with col3:
        total_shortage = latest_df['부족대수'].sum()
        st.metric("전국 부족 대수", f"{total_shortage:,}대", delta=f"{(total_shortage/total_current*100):.1f}%")
    
    with col4:
        insufficient_regions = len(latest_df[latest_df['상태'] == '부족'])
        st.metric("부족 지역", f"{insufficient_regions}개", delta=f"{(insufficient_regions/len(latest_df)*100):.1f}%")
    
    # 지역별 상세 현황
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🗺️ 지역별 구급차 현황")
        
        # 부족/충분 상태별 색상 구분
        color_map = {'부족': 'red', '충분': 'green'}
        latest_df['색상'] = latest_df['상태'].map(color_map)
        
        fig_status = px.bar(latest_df, x='지역', y='구급차수',
                           color='상태',
                           title='지역별 구급차 현황 (2024년)',
                           color_discrete_map={'부족': '#ff6b6b', '충분': '#51cf66'})
        
        # 필요 대수 라인 추가
        fig_status.add_scatter(x=latest_df['지역'], y=latest_df['필요구급차수'],
                              mode='markers', name='필요 대수',
                              marker=dict(color='blue', size=8, symbol='diamond'))
        
        fig_status.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 부족 대수 분석")
        
        shortage_df = latest_df[latest_df['부족대수'] > 0].copy()
        if not shortage_df.empty:
            fig_shortage = px.bar(shortage_df, x='지역', y='부족대수',
                                 title='지역별 구급차 부족 대수',
                                 color='부족대수',
                                 color_continuous_scale='Reds')
            fig_shortage.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig_shortage, use_container_width=True)
        else:
            st.success("모든 지역에서 구급차가 충분합니다! 🎉")
    
    # 개선 우선순위
    st.markdown("### 🎯 개선 우선순위")
    
    priority_df = latest_df[latest_df['부족대수'] > 0].copy()
    if not priority_df.empty:
        priority_df = priority_df.sort_values('부족대수', ascending=False)
        priority_df['우선순위'] = range(1, len(priority_df) + 1)
        
        st.dataframe(
            priority_df[['우선순위', '지역', '현재구급차수', '필요구급차수', '부족대수', '상태']]
            .rename(columns={
                '현재구급차수': '현재 구급차 수',
                '필요구급차수': '필요 구급차 수',
                '부족대수': '부족 대수'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        # 총 투자 비용 계산
        cost_per_ambulance = 150000000  # 구급차 1대당 1억5천만원 가정
        total_cost = priority_df['부족대수'].sum() * cost_per_ambulance
        
        st.markdown(f"""
        <div class="success-box">
            <h4>💰 예상 투자 비용</h4>
            <ul>
                <li><strong>추가 필요 구급차</strong>: {priority_df['부족대수'].sum()}대</li>
                <li><strong>예상 투자비용</strong>: {total_cost:,}원 ({total_cost/100000000:.1f}억원)</li>
                <li><strong>구급차 1대 비용</strong>: {cost_per_ambulance:,}원</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # 권장사항
    st.markdown("### 💡 개선 권장사항")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        #### 🚑 단기 개선방안
        1. **구급차 추가 배치**
           - 부족 지역 우선 배치
           - 인근 지역간 공동 운영
        
        2. **효율성 향상**
           - 응급의료 정보시스템 고도화
           - GPS 기반 최적 배치
           - 실시간 가용 구급차 관리
        
        3. **인력 충원**
           - 응급구조사 추가 양성
           - 야간/주말 근무체계 개선
        """)
    
    with col2:
        st.markdown("""
        #### 🏥 중장기 개선방안
        1. **지역거점병원 확충**
           - 권역응급의료센터 확대
           - 응급실 병상 수 증가
        
        2. **헬기응급의료 확대**
           - 닥터헬기 운영 지역 확대
           - 24시간 운영체계 구축
        
        3. **예방 중심 정책**
           - 응급상황 예방 교육
           - 만성질환 관리 강화
           - 건강검진 확대
        """)

if __name__ == "__main__":
    main()
