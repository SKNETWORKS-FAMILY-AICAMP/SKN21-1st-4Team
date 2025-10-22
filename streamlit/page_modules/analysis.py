import streamlit as st
import pandas as pd
import plotly.express as px
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
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            selected_years = st.multiselect(
                "분석 연도 선택:",
                options=df['연도'].unique(),
                default=df['연도'].unique(),
                key="years_select"
            )
        
        with col2:
            selected_regions = st.multiselect(
                "분석 지역 선택:",
                options=df['지역'].unique(),
                default=df['지역'].unique()[:5],
                key="regions_select"
            )
        
        with col3:
            metric_type = st.selectbox(
                "분석 지표:",
                ["구급차수", "이송환자수", "인구당 구급차수"],
                key="metric_select"
            )
        
        # 데이터 필터링
        filtered_df = df[
            (df['연도'].isin(selected_years)) & 
            (df['지역'].isin(selected_regions))
        ].copy()
        
        if metric_type == "인구당 구급차수":
            filtered_df['인구당 구급차수'] = (filtered_df['구급차수'] / filtered_df['인구수']) * 100000
        
        # 시계열 분석
        st.markdown("#### 📈 연도별 추이 분석")
        
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
            st.markdown("#### 🗺️ 2024년 지역별 구급차 현황")
            latest_data = filtered_df[filtered_df['연도'] == 2024]
            
            if not latest_data.empty:
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
            st.markdown("#### 🏥 구급차당 이송환자 수")
            if not latest_data.empty:
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
        st.markdown("#### 📋 상세 데이터")
        if not filtered_df.empty:
            pivot_data = filtered_df.pivot(index='지역', columns='연도', values=metric_type)
            st.dataframe(pivot_data.round(2), use_container_width=True)
    
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
                             color='필요대수',
                             color_continuous_scale='Blues')
        fig_scenario.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_scenario, use_container_width=True)