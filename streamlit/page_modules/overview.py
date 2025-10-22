import streamlit as st
import pandas as pd
import plotly.express as px

def show_overview_page():
    st.markdown('<div class="section-header"><h2>🏥 응급의료시스템 개요 및 현황</h2></div>', unsafe_allow_html=True)
    
    # 골든타임 섹션
    st.markdown("## ⏰ 골든타임(Golden Hour)의 중요성")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="golden-time-box">
            <h3>⏰ 골든타임이란?</h3>
            <p>중증 외상환자가 발생한 후 <strong>첫 1시간</strong> 내에 적절한 치료를 받아야 생존율이 크게 향상되는 시간</p>
        </div>
        """, unsafe_allow_html=True)
       
    with col2:
        st.markdown("""
        <div class="alert-box">
            <h4>🚨 중요한 사실</h4>
            <p>구급차 도착 지연 시 환자 사망률이 <strong>2배 이상</strong> 증가합니다.</p>
        </div>
        """, unsafe_allow_html=True)

    # 구분선
    st.markdown("---")
    
    # 문제점 섹션
    st.markdown("## 📰 현재 119 응급시스템 문제점")
    
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
    