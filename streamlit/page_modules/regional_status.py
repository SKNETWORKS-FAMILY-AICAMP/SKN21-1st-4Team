import streamlit as st
import pandas as pd
import plotly.express as px
from utils import create_sample_data, calculate_required_ambulances

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