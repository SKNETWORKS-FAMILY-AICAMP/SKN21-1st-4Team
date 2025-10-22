import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import create_sample_data, calculate_required_ambulances

def show_analysis_page():
    st.markdown('<div class="section-header"><h2>📊 데이터 분석 및 구급차 수요 분석</h2></div>', unsafe_allow_html=True)
    
    # 탭으로 분리
    tab1, tab2 = st.tabs(["📊 전국 응급의료 데이터 분석", "🔬 구급차 수요 분석 및 계산"])
    
    with tab1:
        # 데이터 분석 섹션
        st.markdown("### 📈 전국 응급의료 현황 데이터")
        
        # 데이터 로드
        df = create_sample_data()
        
        # 필터링 옵션
        col1, col2 = st.columns([1, 1])
        
        with col1:
            selected_year = st.selectbox(
                "분석 연도 선택:",
                options=sorted(df['연도'].unique(), reverse=True),
                index=0,  # 최신 연도가 기본값
                key="year_select"
            )
        
        # 데이터 필터링 (연도만 필터링, 모든 지역 표시)
        filtered_df = df[df['연도'] == selected_year].copy()
        
        # 지역별 구급차수 및 이송환자수 통합 분석
        st.markdown(f"#### 📊 {selected_year}년 지역별 구급차수 및 이송환자수 현황")
        
        if not filtered_df.empty:
            # plotly graph_objects를 사용한 이중 Y축 차트
            
            # 구급차수 기준으로 정렬
            sorted_df = filtered_df.sort_values('구급차수', ascending=True)
            
            # 이중 Y축 서브플롯 생성
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # 구급차수 막대 그래프 (왼쪽 Y축)
            fig.add_trace(
                go.Bar(
                    x=sorted_df['지역'],
                    y=sorted_df['구급차수'],
                    name='구급차수',
                    marker_color='#1f77b4',
                    opacity=0.8,
                    offsetgroup=1
                ),
                secondary_y=False,
            )
            
            # 이송환자수 막대 그래프 (오른쪽 Y축)
            fig.add_trace(
                go.Bar(
                    x=sorted_df['지역'],
                    y=sorted_df['이송환자수'],
                    name='이송환자수',
                    marker_color='#ff7f0e',
                    opacity=0.7,
                    yaxis='y2',
                    offsetgroup=2
                ),
                secondary_y=True,
            )
            
            # X축 설정
            fig.update_xaxes(title_text="지역", tickangle=-45)
            
            # Y축 설정
            fig.update_yaxes(title_text="구급차수 (대)", secondary_y=False, title_font_color='#1f77b4')
            fig.update_yaxes(title_text="이송환자수 (명)", secondary_y=True, title_font_color='#ff7f0e')
            
            # 레이아웃 설정
            fig.update_layout(
                title=f'{selected_year}년 지역별 구급차수 및 이송환자수 (이중 Y축)',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=500,
                barmode='group',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 추가 분석: 구급차 1대당 이송환자수
            st.markdown("#### 📈 구급차 효율성 분석")
            sorted_df['구급차당_이송환자수'] = sorted_df['이송환자수'] / sorted_df['구급차수']
            sorted_df = sorted_df.sort_values('구급차당_이송환자수', ascending=False)
            
            efficiency_fig = px.bar(
                sorted_df, 
                x='지역', 
                y='구급차당_이송환자수',
                title='구급차 1대당 이송환자수 (효율성 지표)',
                color='구급차당_이송환자수',
                color_continuous_scale='Viridis'
            )
            efficiency_fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
                xaxis_tickangle=-45,
                yaxis_title="구급차 1대당 이송환자수 (명/대)"
            )
            st.plotly_chart(efficiency_fig, use_container_width=True)
        
        # 데이터 테이블 (모든 연도 데이터 표시)
        st.markdown("#### 📋 전체 연도별 상세 데이터 (2020-2024)")
        
        # 모든 데이터를 연도별로 정렬하여 표시
        all_data = df[['연도', '지역', '구급차수', '이송환자수']].copy()
        all_data = all_data.sort_values(['연도', '구급차수'], ascending=[False, False])
        
        st.dataframe(all_data, use_container_width=True, hide_index=True)
    
    with tab2:
        # 구급차 수요 분석 섹션
        st.markdown("### 🧮 구급차 필요 대수 계산")
        
        # 계산 공식 설명
        st.markdown("""
        #### 📐 계산 공식
        
        **필요 구급차 수 = (호출량 × 평균 사이클 타임) / 목표 가동률**
        
        - **평균 사이클 타임**: 출동부터 복귀까지의 시간
          - 도시 지역: 30-60분
          - 농촌 지역: 120-150분
        - **목표 가동률**: 30-50% (과부하 방지를 위한 여유율 확보)
        """)
        
        # 계산기 섹션
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### 📊 입력 값 설정")
            
            calls_per_year = st.number_input(
                "연간 응급호출 수:",
                min_value=1000,
                max_value=100000,
                value=15000,
                step=500,
                help="해당 지역의 연간 예상 응급호출 횟수",
                key="calls_input"
            )
            
            region_type = st.selectbox(
                "지역 유형:",
                ["도시 지역", "농촌 지역", "사용자 정의"],
                key="region_type_select"
            )
            
            if region_type == "도시 지역":
                cycle_time = st.slider("평균 사이클 타임 (분):", 30, 60, 45, key="cycle_urban")
            elif region_type == "농촌 지역":
                cycle_time = st.slider("평균 사이클 타임 (분):", 120, 150, 135, key="cycle_rural")
            else:
                cycle_time = st.slider("평균 사이클 타임 (분):", 20, 200, 60, key="cycle_custom")
            
            target_utilization = st.slider(
                "목표 가동률 (%):",
                min_value=20,
                max_value=70,
                value=40,
                step=5,
                help="권장: 30-50% (여유율 확보를 위해)",
                key="utilization_slider"
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
                help="비교 분석을 위한 현재 보유 구급차 수",
                key="current_ambulances_input"
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
        st.markdown("#### 🎯 시나리오 분석")
        
        scenarios = pd.DataFrame({
            '시나리오': ['목표(30%)', '목표(40%)', '목표(50%)', '목표(60%)'],
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
                             color_discrete_sequence=['#1f77b4'])
        fig_scenario.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_scenario, use_container_width=True)