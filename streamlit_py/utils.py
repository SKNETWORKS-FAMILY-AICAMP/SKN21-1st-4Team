import pandas as pd
import numpy as np
import streamlit as st
import pymysql
import sys
import os

# 프로젝트 루트의 db_config 모듈을 import하기 위해 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db_config import get_connection

def get_mysql_connection():
    """MySQL 데이터베이스 연결"""
    try:
        connection = get_connection()
        return connection
    except Exception as e:
        st.error(f"MySQL 연결 오류: {e}")
        return None

def load_emergency_car_data():
    """emergency_car 테이블에서 구급차 및 이송환자 데이터 로드"""
    try:
        connection = get_mysql_connection()
        if connection is None:
            st.warning("데이터베이스 연결에 실패했습니다.")
            return pd.DataFrame()
        
        query = """
        SELECT year, car_local as 지역, car_count as 구급차수
        FROM emergency_car 
        ORDER BY year, car_local
        """
        df = pd.read_sql(query, connection)
        connection.close()
        
        if df.empty:
            st.warning("emergency_car 테이블에 데이터가 없습니다.")
            return pd.DataFrame()
        
        # 연도를 정수형으로 변환
        df['연도'] = df['year'].astype(int)
        df = df.drop('year', axis=1)
        
        # '전체' 지역 제외
        df = df[df['지역'] != '전체']
        
        return df
        
    except Exception as e:
        st.error(f"구급차 데이터 로드 중 오류가 발생했습니다: {e}")
        st.error(f"오류 세부사항: {str(e)}")
        return pd.DataFrame()

def load_emergency_move_data():
    """emergency_move 테이블에서 후송 횟수 데이터 로드"""
    try:
        connection = get_mysql_connection()
        if connection is None:
            return pd.DataFrame()
        
        query = """
        SELECT year, move_local as 지역, move_count as 이송환자수
        FROM emergency_move 
        ORDER BY year, move_local
        """
        df = pd.read_sql(query, connection)
        connection.close()
        
        # 연도를 정수형으로 변환
        df['연도'] = df['year'].astype(int)
        df = df.drop('year', axis=1)
        
        # '전체' 지역 제외
        df = df[df['지역'] != '전체']
        
        return df
        
    except Exception as e:
        st.error(f"후송 데이터 로드 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

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
def create_sample_data():
    """통합 데이터 생성 - 구급차 데이터와 후송 데이터를 병합"""
    try:
        car_data = load_emergency_car_data()
        move_data = load_emergency_move_data()
        
        # 두 데이터 모두 비어있으면 기본 구조 반환
        if car_data.empty and move_data.empty:
            return pd.DataFrame(columns=['연도', '지역', '구급차수', '이송환자수'])
        
        # 구급차 데이터가 비어있으면 후송 데이터만 반환
        if car_data.empty and not move_data.empty:
            move_data['구급차수'] = 0
            return move_data[['연도', '지역', '구급차수', '이송환자수']]
        
        # 후송 데이터가 비어있으면 구급차 데이터만 반환  
        if move_data.empty and not car_data.empty:
            car_data['이송환자수'] = 0
            return car_data[['연도', '지역', '구급차수', '이송환자수']]
        
        # 두 데이터 모두 있으면 병합
        if not car_data.empty and not move_data.empty:
            merged_data = pd.merge(
                car_data, 
                move_data, 
                on=['연도', '지역'], 
                how='outer'
            )
            
            # NaN 값을 0으로 채우기
            merged_data = merged_data.fillna(0)
            
            # '전체' 지역 제외 (혹시 병합 과정에서 생성되었을 경우)
            merged_data = merged_data[merged_data['지역'] != '전체']
            
            # 숫자형 컬럼의 데이터 타입 정리
            numeric_cols = ['구급차수', '이송환자수']
            for col in numeric_cols:
                if col in merged_data.columns:
                    merged_data[col] = pd.to_numeric(merged_data[col], errors='coerce').fillna(0).astype(int)
            
            return merged_data
        
        # 기본 빈 DataFrame 반환
        return pd.DataFrame(columns=['연도', '지역', '구급차수', '이송환자수'])
        
    except Exception as e:
        st.error(f"데이터 생성 중 오류: {e}")
        return pd.DataFrame(columns=['연도', '지역', '구급차수', '이송환자수'])

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