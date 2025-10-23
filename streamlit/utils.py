import pandas as pd
import numpy as np
import streamlit as st

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
            base_ambulances = np.random.randint(10, 20) if region in ['서울', '경기', '부산'] else np.random.randint(15, 30)
            base_patients = base_ambulances * np.random.randint(800, 1500)  # 구급차당 연간 이송환자 수
            
            # 연도별 증가 트렌드 반영
            year_factor = 1 + (year - 2020) * 0.02  # 연간 2% 증가
            
            # 지역별 인구 설정 (단위: 만명)
            population_map = {
                '서울': 960, '경기': 1350, '부산': 340, '대구': 240, '인천': 300,
                '광주': 150, '대전': 150, '울산': 115, '세종': 35,
                '강원': 150, '충북': 160, '충남': 220, '전북': 180, '전남': 185,
                '경북': 265, '경남': 335, '제주': 67
            }
            
            population = population_map.get(region, 100)
            
            data.append({
                '지역': region,
                '연도': year,
                '구급차수': int(base_ambulances * year_factor),
                '이송환자수': int(base_patients * year_factor),
                '인구수': population * 10000,  # 실제 인구수로 변환
                '응답시간': np.random.normal(9, 2),  # 평균 9분, 표준편차 2분
                '가동률': np.random.uniform(0.4, 0.8)  # 40-80% 가동률
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