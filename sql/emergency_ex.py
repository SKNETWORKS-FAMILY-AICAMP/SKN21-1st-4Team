import pymysql
import pandas as pd
import sys
import os

# 홈디렉토리의 db_config 모듈을 import하기 위해 경로 추가
sys.path.append(os.path.expanduser('~'))
from db_config import get_connection

def emergency_ex_table():
    
    try:
        conn = get_connection()

        cursor = conn.cursor()

        create_sql = """
        CREATE TABLE emergency_ex (
            idx INT AUTO_INCREMENT PRIMARY KEY,
            year YEAR NOT NULL,
            cause VARCHAR(50),
            gender VARCHAR(10),
            local VARCHAR(50),
            job VARCHAR(50)
        );
        """

        cursor.execute("DROP TABLE IF EXISTS emergency_ex")
        cursor.execute(create_sql)
        conn.commit()

    finally:
        if conn:
            cursor.close()
            conn.close()

def ex_all():
      
    try:
        conn = get_connection()

        sql_all = """
        SELECT year, local, cause, gender, job
        FROM emergency_ex
        ORDER BY year, local;
        """
        df_all = pd.read_sql(sql_all, conn)

    finally:
        conn.close()

def ex_local(region):

    try:
        conn = get_connection()

        sql_region = f"""
        SELECT year, local, cause, gender, job
        FROM emergency_ex
        WHERE local = '{region}'
        ORDER BY year;
        """
        df_region = pd.read_sql(sql_region, conn)

    finally:
        conn.close()
        
