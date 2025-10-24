import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# utils.py 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'streamlit'))
from utils import create_sample_data, calculate_required_ambulances, load_emergency_ex_data

def show_analysis_page():
    st.markdown('<div class="section-header"><h2>📊 데이터 분석 및 구급차 수요 분석</h2></div>', unsafe_allow_html=True)
    
    # 탭으로 분리
    tab1, tab2 = st.tabs(["📊 전국 응급의료 데이터 분석", "🔬 구급차 수요 분석 및 계산"])
    
    with tab1:
        # 데이터 분석 섹션
        st.markdown("### 📈 전국 응급의료 현황 데이터")
        
        # 데이터 로드
        df = create_sample_data()
        
        # 데이터가 비어있거나 연도 컬럼이 없는 경우 처리
        if df.empty or '연도' not in df.columns:
            st.warning("📊 표시할 데이터가 없습니다.")
            st.info("**해결 방법:**")
            st.write("1. CSV 파일들을 실행하여 데이터베이스에 데이터를 먼저 로드하세요")
            st.write("2. 데이터베이스 연결 설정을 확인하세요")
            st.write("3. emergency_car, emergency_move 테이블이 존재하는지 확인하세요")
            return
        
        # 사용 가능한 연도 확인
        available_years = sorted(df['연도'].unique(), reverse=True)
        if len(available_years) == 0:
            st.warning("사용 가능한 연도 데이터가 없습니다.")
            return
        
        # 필터링 옵션
        col1, col2 = st.columns([1, 1])
        
        with col1:
            selected_year = st.selectbox(
                "분석 연도 선택:",
                options=available_years,
                index=0,  # 최신 연도가 기본값
                key="year_select"
            )
        
        # 데이터 필터링 (연도만 필터링, 모든 지역 표시)
        filtered_df = df[df['연도'] == selected_year].copy()
        
        # 지역별 구급차수 및 이송환자수 통합 분석
        st.markdown(f"#### 📊 {selected_year}년 지역별 데이터 현황")
        
        if not filtered_df.empty:
            # 간단한 요약 통계만 표시
            st.markdown("#### 📈 선택된 연도 데이터 요약")
            
            col1, col2 = st.columns(2)
            with col1:
                total_ambulances = filtered_df['구급차수'].sum()
                st.metric("총 구급차 수", f"{total_ambulances:,}대")
            with col2:
                total_patients = filtered_df['이송환자수'].sum()
                st.metric("총 이송환자 수", f"{total_patients:,}명")
            
            # 추가 분석: 구급차 1대당 이송환자수
            st.markdown("#### 📈 구급차 효율성 분석")
            
            # 구급차수 기준으로 정렬 및 효율성 계산
            sorted_df = filtered_df.sort_values('구급차수', ascending=True)
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
        
        # 연도별 탭으로 데이터 표시
        st.markdown("#### 📋 연도별 상세 데이터")
        
        # 데이터가 있는지 확인
        if not df.empty and '연도' in df.columns:
            # 연도별 탭 생성 (최신 연도부터)
            years = sorted(df['연도'].unique(), reverse=True)   
            if len(years) > 0:
                year_tabs = st.tabs([f"{year}년" for year in years])
                
                for i, year in enumerate(years):
                    with year_tabs[i]:
                        year_data = df[df['연도'] == year].copy()
                        year_data = year_data.sort_values('구급차수', ascending=False)
                        
                        # 연도 컬럼 제거 (탭에서 이미 연도가 표시되므로)
                        year_data = year_data.drop('연도', axis=1)
                        
                        # 전체 데이터 테이블 (인덱스 숨김)
                        st.dataframe(year_data, use_container_width=True, hide_index=True)
            else:
                st.warning("📊 연도별 데이터가 없습니다.")
        else:
            st.warning("📊 표시할 데이터가 없습니다. 데이터베이스 연결을 확인해주세요.")
        
        # 원그래프 섹션 추가
        st.markdown("#### 📊 환자 정보 분석")
        
        # emergency_ex 데이터 로드
        ex_data = load_emergency_ex_data()
        
        if not ex_data.empty:
            # 연도 선택 (상단에서 선택한 연도와 동일하게)
            selected_ex_year = selected_year
            ex_filtered = ex_data[ex_data['연도'] == selected_ex_year].copy()
            
            if not ex_filtered.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # 성별 비율 원그래프
                    gender_counts = ex_filtered['성별'].value_counts()
                    if not gender_counts.empty:
                        gender_fig = px.pie(
                            values=gender_counts.values,
                            names=gender_counts.index,
                            title=f'{selected_ex_year}년 성별 비율',
                            color_discrete_sequence=['#FF6B9D', '#4ECDC4']
                        )
                        gender_fig.update_traces(textposition='inside', textinfo='percent+label')
                        gender_fig.update_layout(
                            height=400,
                            showlegend=True,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(gender_fig, use_container_width=True)
                    else:
                        st.warning("성별 데이터가 없습니다.")
                
                with col2:
                    # 증상 비율 원그래프 (상위 10개만)
                    cause_counts = ex_filtered['증상'].value_counts().head(10)
                    if not cause_counts.empty:
                        cause_fig = px.pie(
                            values=cause_counts.values,
                            names=cause_counts.index,
                            title=f'{selected_ex_year}년 주요 증상 분류 (상위 10개)',
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        cause_fig.update_traces(textposition='inside', textinfo='percent+label')
                        cause_fig.update_layout(
                            height=400,
                            showlegend=True,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(cause_fig, use_container_width=True)
                    else:
                        st.warning("증상 데이터가 없습니다.")
                
                # 통계 요약
                st.markdown("##### 📈 통계 요약")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_patients = len(ex_filtered)
                    st.metric("총 환자 수", f"{total_patients:,}명")
                
                with col2:
                    if '성별' in ex_filtered.columns:
                        male_ratio = (ex_filtered['성별'] == '남').mean() * 100
                        st.metric("남성 비율", f"{male_ratio:.1f}%")
                
                with col3:
                    if '성별' in ex_filtered.columns:
                        female_ratio = (ex_filtered['성별'] == '여').mean() * 100
                        st.metric("여성 비율", f"{female_ratio:.1f}%")
                
                with col4:
                    if '증상' in ex_filtered.columns:
                        unique_symptoms = ex_filtered['증상'].nunique()
                        st.metric("증상 종류", f"{unique_symptoms}개")
            else:
                st.warning(f"{selected_ex_year}년 환자 정보 데이터가 없습니다.")
        else:
            st.warning("환자 정보 데이터베이스에 연결할 수 없습니다.")
    
    with tab2:
        # 구급차 수요 분석 섹션
        st.markdown("### 🧮 구급차 필요 대수 계산")
        
        # 계산 공식 설명
        st.markdown("#### 📐 계산 공식")
        
        # 여백을 위한 빈 공간 추가
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 메인 공식을 LaTeX로 표시 (더 많은 여백과 크기 조정)
        st.latex(r"""
        \displaystyle
        \text{필요 구급차 수} = \frac{\text{연간 호출량} \times \text{평균 사이클 타임}}{\text{목표 가동률}}
        """)
        
        # 여백을 위한 빈 공간 추가
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
        **변수 설명:**
        - **연간 호출량**: 해당 지역의 연간 응급호출 횟수
        - **평균 사이클 타임**: 출동부터 복귀까지의 시간 (시간 단위)
          - 도시 지역: 0.5 ~ 1.0 시간 (30-60분)
          - 농촌 지역: 2.0 ~ 2.5 시간 (120-150분)
        - **목표 가동률**: 0.3 ~ 0.5 (30-50%) - 과부하 방지를 위한 여유율 확보
        """)
        
        
        
        # 지역별 구급차 수요 분석
        st.markdown("#### 🗺️ 지역별 구급차 수요 분석")
        
        st.markdown("""
        **분석 조건 (테스트용 - 매우 엄격한 기준):**
        - 평균 사이클 타임: 90분 (1.5시간)
        - 목표 가동률: 50%
        - 연간 응급호출 수: 이송환자수 × 2.5 (매우 많은 호출 가정)
        - 주요 지역 구급차 수: 40% 감소 적용 (테스트용)
        """)
        
        # 데이터가 있는지 확인
        if not df.empty and '연도' in df.columns:
            # 연도별 탭 생성
            years_analysis = sorted(df['연도'].unique(), reverse=True)
            if len(years_analysis) > 0:
                analysis_tabs = st.tabs([f"{year}년 분석" for year in years_analysis])
                
                # 고정값 설정
                CYCLE_TIME_HOURS = 1.5  # 90분
                TARGET_UTILIZATION = 0.5  # 50%
                
                for i, year in enumerate(years_analysis):
                    with analysis_tabs[i]:
                        year_data = df[df['연도'] == year].copy()
                
                # 각 지역별 분석 계산
                analysis_results = []
                for _, row in year_data.iterrows():
                    # 테스트를 위해 매우 엄격한 조건 적용
                    # 연간 응급호출 수를 대폭 증가시켜 부족 상황 강제 생성
                    estimated_calls = int(row['이송환자수'] * 2.5)  # 150% 더 많게 설정
                    
                    # 필요 구급차 수 계산
                    required_ambulances = calculate_required_ambulances(
                        estimated_calls, CYCLE_TIME_HOURS, TARGET_UTILIZATION
                    )
                    
                    # 테스트용: 일부 지역의 현재 구급차 수를 강제로 줄임
                    current_ambulances = row['구급차수']
                    if row['지역'] in ['서울', '경기', '부산', '대구', '인천']:
                        current_ambulances = int(current_ambulances * 0.6)  # 40% 감소
                    elif row['지역'] in ['광주', '대전', '울산', '강원']:
                        current_ambulances = int(current_ambulances * 0.7)  # 30% 감소
                    
                    shortage = required_ambulances - current_ambulances
                    
                    # 상태 판정
                    if shortage > 0:
                        status = "부족"
                        status_color = "#ffebee"  # 연한 빨간색 배경
                    else:
                        status = "적절"
                        status_color = "#ffffff"  # 흰색 배경
                    
                    analysis_results.append({
                        '지역': row['지역'],
                        '현재 구급차수': current_ambulances,
                        '추정 호출수': f"{estimated_calls:,}",
                        '필요 구급차수': required_ambulances,
                        '과부족': shortage,
                        '상태': status,
                        '배경색': status_color
                    })
                
                # 결과를 DataFrame으로 변환
                analysis_df = pd.DataFrame(analysis_results)
                
                # 현재 연도 통계 먼저 계산
                total_regions = len(analysis_df)
                shortage_regions = len(analysis_df[analysis_df['상태'] == '부족'])
                adequate_regions = total_regions - shortage_regions
                total_shortage = analysis_df[analysis_df['과부족'] > 0]['과부족'].sum()
                
                # 전년도 대비 증감 계산
                current_year = year
                previous_year = current_year - 1
                
                # 전년도 데이터가 있는 경우에만 계산
                if previous_year in df['연도'].values:
                    prev_year_data = df[df['연도'] == previous_year].copy()
                    
                    # 전년도 분석 결과 계산
                    prev_analysis_results = []
                    for _, row in prev_year_data.iterrows():
                        estimated_calls = int(row['이송환자수'] * 2.5)
                        required_ambulances = calculate_required_ambulances(
                            estimated_calls, CYCLE_TIME_HOURS, TARGET_UTILIZATION
                        )
                        
                        current_ambulances = row['구급차수']
                        if row['지역'] in ['서울', '경기', '부산', '대구', '인천']:
                            current_ambulances = int(current_ambulances * 0.6)
                        elif row['지역'] in ['광주', '대전', '울산', '강원']:
                            current_ambulances = int(current_ambulances * 0.7)
                        
                        shortage = required_ambulances - current_ambulances
                        status = "부족" if shortage > 0 else "적절"
                        
                        prev_analysis_results.append({
                            '지역': row['지역'],
                            '상태': status,
                            '과부족': shortage
                        })
                    
                    prev_analysis_df = pd.DataFrame(prev_analysis_results)
                    
                    # 전년도 통계
                    prev_total_regions = len(prev_analysis_df)
                    prev_shortage_regions = len(prev_analysis_df[prev_analysis_df['상태'] == '부족'])
                    prev_adequate_regions = prev_total_regions - prev_shortage_regions
                    prev_total_shortage = prev_analysis_df[prev_analysis_df['과부족'] > 0]['과부족'].sum()
                    
                    # 증감 계산
                    delta_shortage = shortage_regions - prev_shortage_regions
                    delta_adequate = adequate_regions - prev_adequate_regions
                    delta_total_shortage = total_shortage - prev_total_shortage
                else:
                    # 전년도 데이터가 없는 경우 (2019년)
                    delta_shortage = None
                    delta_adequate = None
                    delta_total_shortage = None
                
                # 요약 통계
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("전체 지역수", f"{total_regions}개")
                with col2:
                    if delta_shortage is not None:
                        st.metric("부족 지역", f"{shortage_regions}개", delta=f"{delta_shortage:+d}개")
                    else:
                        st.metric("부족 지역", f"{shortage_regions}개", delta="기준년도")
                with col3:
                    if delta_adequate is not None:
                        st.metric("적절 지역", f"{adequate_regions}개", delta=f"{delta_adequate:+d}개")
                    else:
                        st.metric("적절 지역", f"{adequate_regions}개", delta="기준년도")
                with col4:
                    if delta_total_shortage is not None:
                        st.metric("총 부족 대수", f"{total_shortage}대", delta=f"{delta_total_shortage:+d}대")
                    else:
                        st.metric("총 부족 대수", f"{total_shortage}대", delta="기준년도")
                
                # 스타일링된 테이블 표시
                st.markdown("##### 📊 지역별 분석 결과")
                
                # 표시용 DataFrame 준비 (배경색 컬럼 제거)
                display_df = analysis_df.drop('배경색', axis=1).copy()
                
                # 컬럼명 변경
                display_df = display_df.rename(columns={
                    '현재 구급차수': '현재 구급차수 (대)',
                    '필요 구급차수': '필요 구급차수 (대)',
                    '과부족': '과부족 (대)'
                })
                
                # 과부족 컬럼에 + 기호 추가
                display_df['과부족 (대)'] = display_df['과부족 (대)'].apply(lambda x: f"+{x}" if x >= 0 else str(x))
                
                # 부족 우선으로 정렬 (부족 지역이 위에 오도록)
                display_df['정렬순서'] = display_df['상태'].map({'부족': 0, '적절': 1})
                display_df = display_df.sort_values(['정렬순서', '과부족 (대)']).drop('정렬순서', axis=1).reset_index(drop=True)
                
                # 통합 테이블 표시 (조건부 스타일링 적용)
                def highlight_shortage(row):
                    if row['상태'] == '부족':
                        return ['background-color: #ffebee'] * len(row)  # 연한 빨간색
                    else:
                        return ['background-color: white'] * len(row)   # 흰색
                
                # 스타일 적용된 데이터프레임 표시 (스크롤 없이 전체 표시)
                styled_df = display_df.style.apply(highlight_shortage, axis=1)
                
                # 높이를 충분히 설정하여 모든 행이 표시되도록 함
                table_height = len(display_df) * 35 + 50  # 행당 35px + 헤더 50px
                
                st.dataframe(
                    styled_df,
                    use_container_width=True,
                    hide_index=True,
                    height=table_height,
                    column_config={
                        "상태": st.column_config.TextColumn(
                            "상태",
                            help="🔴 부족: 빨간색 배경, ✅ 적절: 흰색 배경"
                        ),
                        "과부족 (대)": st.column_config.TextColumn(
                            "과부족 (대)",
                            help="음수는 부족, 양수는 여유"
                        )
                    }
                )
            else:
                st.warning("📊 분석할 연도별 데이터가 없습니다.")
        else:
            st.warning("📊 표시할 데이터가 없습니다. 데이터베이스 연결을 확인해주세요.")
