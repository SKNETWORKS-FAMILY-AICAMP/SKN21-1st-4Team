import pandas as pd
import pymysql
import sys
import os

# sql 폴더의 db_config 모듈을 import하기 위해 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'sql'))
from db_config import get_connection

files = [
    "DATA/2019_move.csv",
    "DATA/2020_move.csv",
    "DATA/2021_move.csv",
    "DATA/2022_move.csv",
    "DATA/2023_move.csv"]



with get_connection() as connection:
    with connection.cursor() as cursor:

        for f in files:
            df = pd.read_csv(f)

            
            df = df[["move_local", "move_count"]]
            

            df["year"] = int(f[5:9])

            cur = connection.cursor()

            sql = 'insert into emergency_move (year, move_local, move_count) values (%s, %s, %s)'
            for row in df.iterrows():
                row_data = row[1]
                # print((row_data['year'], row_data['car_count'].replace(',', ''), row_data['emp_count'].replace(',', ''), row_data['car_local']))
                cursor.execute(sql, (row_data['year'], (row_data['move_local']), int(row_data['move_count'])))

        connection.commit()
        
print(f"{f}년도 적재 완료")
