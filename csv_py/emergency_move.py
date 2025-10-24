import pandas as pd
import pymysql
import sys
import os

# 프로젝트 루트의 db_config 모듈을 import하기 위해 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db_config import get_connection

# ---------- 지역명 변환 함수 ----------
def convert_region_name(region_name):
    """지역명을 풀네임에서 2글자로 변환"""
    if pd.isna(region_name) or region_name == '' or region_name == 'nan':
        return region_name
    
    region_name = str(region_name).strip()
    
    # 지역명 변환 딕셔너리
    region_mapping = {
        # 서울특별시 -> 서울
        '서울특별시': '서울',
        
        # 광역시들
        '부산광역시': '부산',
        '대구광역시': '대구', 
        '인천광역시': '인천',
        '광주광역시': '광주',
        '대전광역시': '대전',
        '울산광역시': '울산',
        
        # 세종특별자치시 -> 세종
        '세종특별자치시': '세종',
        
        # 도들
        '경기도': '경기',
        '강원도': '강원',
        '충청북도': '충북',
        '충청남도': '충남',
        '전라북도': '전북',
        '전라남도': '전남',
        '경상북도': '경북',
        '경상남도': '경남',
        '제주특별자치도': '제주',
        '제주도': '제주'
    }
    
    # 정확히 일치하는 경우
    if region_name in region_mapping:
        return region_mapping[region_name]
    
    # 부분 매칭 (포함되는 경우)
    for full_name, short_name in region_mapping.items():
        if full_name in region_name:
            return short_name
    
    # 매칭되지 않는 경우 첫 2글자 반환 (예: '충청북도청주시' -> '충청')
    if len(region_name) >= 2:
        return region_name[:2]
    
    return region_name
loc = os.path.dirname(os.path.dirname(__file__))+"/"
files = [
    "DATA/2019_move.csv",
    "DATA/2020_move.csv",
    "DATA/2021_move.csv",
    "DATA/2022_move.csv",
    "DATA/2023_move.csv"]


def load_move():
    with get_connection() as connection:
        with connection.cursor() as cursor:

            for f in files:
                df = pd.read_csv(loc+f)
                
                # 컬럼명의 공백 제거
                df.columns = df.columns.str.strip()
                print(f"{f} 컬럼명: {df.columns.tolist()}")

                df = df[["move_local", "move_count"]]
                
                # 지역명을 2글자로 변환
                df['move_local'] = df['move_local'].apply(convert_region_name)
                print(f"{f}에서 지역명을 2글자로 변환했습니다.")
                
                # 지역이 '전체'인 경우 제외
                before_count = len(df)
                df = df[df['move_local'] != '전체']
                after_count = len(df)
                removed_count = before_count - after_count
                if removed_count > 0:
                    print(f"{f}에서 지역이 '전체'인 {removed_count}개 행을 제외했습니다.")

                df["year"] = int(f[5:9])

                cur = connection.cursor()

                sql = 'insert into emergency_move (year, move_local, move_count) values (%s, %s, %s)'
                for row in df.iterrows():
                    row_data = row[1]
                    # print((row_data['year'], row_data['car_count'].replace(',', ''), row_data['emp_count'].replace(',', ''), row_data['car_local']))
                    cursor.execute(sql, (row_data['year'], (row_data['move_local']), int(row_data['move_count'])))

            connection.commit()
            

