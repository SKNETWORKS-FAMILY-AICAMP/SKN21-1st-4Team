import pandas as pd
import numpy as np
import streamlit as st
import pymysql

def get_mysql_connection():
    """MySQL 데이터베이스 연결"""
    try:
        connection = pymysql.connect(
            host="192.168.0.23",
            database="emergency", 
            user="first_guest",
            password="1234",
            port=3306
        )
        return connection
    except Exception as e:
        st.error(f"MySQL 연결 오류: {e}")
        return None

@st.cache_data(ttl=3600)  # 1시간 캐시
def load_emergency_car_data():
    """emergency_car 테이블에서 구급차 및 이송환자 데이터 로드"""
    try:
        connection = get_mysql_connection()
        if connection is None:
            return pd.DataFrame()
        
        query = """
        SELECT year, car_local as 지역, car_count as 구급차수, emp_count as 이송환자수
        FROM emergency_car 
        ORDER BY year, car_local
        """
        df = pd.read_sql(query, connection)
        connection.close()
        
        # 연도를 정수형으로 변환
        df['연도'] = df['year'].astype(int)
        df = df.drop('year', axis=1)
        
        return df
        
    except Exception as e:
        st.error(f"구급차 데이터 로드 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)  # 1시간 캐시
def load_emergency_move_data():
    """emergency_move 테이블에서 후송 횟수 데이터 로드"""
    try:
        connection = get_mysql_connection()
        if connection is None:
            return pd.DataFrame()
        
        query = """
        SELECT year, move_local as 지역, move_count as 후송횟수
        FROM emergency_move 
        ORDER BY year, move_local
        """
        df = pd.read_sql(query, connection)
        connection.close()
        
        # 연도를 정수형으로 변환
        df['연도'] = df['year'].astype(int)
        df = df.drop('year', axis=1)
        
        return df
        
    except Exception as e:
        st.error(f"후송 데이터 로드 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)  # 1시간 캐시  
def load_emergency_ex_data():
    """emergency_ex 테이블에서 환자 정보 데이터 로드"""
    try:
        connection = get_mysql_connection()
        if connection is None:
            return pd.DataFrame()
        
        query = """
        SELECT year, local as 지역, cause as 증상, gender as 성별, job as 직업
        FROM emergency_ex 
        ORDER BY year, local
        """
        df = pd.read_sql(query, connection)
        connection.close()
        
        # 연도를 정수형으로 변환
        df['연도'] = df['year'].astype(int)
        df = df.drop('year', axis=1)
        
        return df
        
    except Exception as e:
        st.error(f"환자 정보 데이터 로드 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

def get_regional_data(region):
    """특정 지역의 종합 데이터 반환"""
    car_data = load_emergency_car_data()
    move_data = load_emergency_move_data()
    ex_data = load_emergency_ex_data()
    
    # 지역별 필터링
    region_car = car_data[car_data['지역'] == region] if not car_data.empty else pd.DataFrame()
    region_move = move_data[move_data['지역'] == region] if not move_data.empty else pd.DataFrame()
    region_ex = ex_data[ex_data['지역'] == region] if not ex_data.empty else pd.DataFrame()
    
    return {
        'car_data': region_car,
        'move_data': region_move,
        'ex_data': region_ex
    }

# 통합 데이터 생성 함수 (기존 create_sample_data 대체)
@st.cache_data
def create_sample_data():
    """하위 호환성을 위한 통합 데이터 생성 함수"""
    return load_emergency_car_data()

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