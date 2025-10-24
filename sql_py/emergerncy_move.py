import pymysql
import pandas as pd
import sys
import os

# 홈디렉토리의 db_config 모듈을 import하기 위해 경로 추가
sys.path.append(os.path.expanduser('~'))
from db_config import get_connection

def emergency_move_table():
    
    try:
        conn = get_connection()

        cursor = conn.cursor()

        create_sql = """
        CREATE TABLE emergency_move (
            idx INT AUTO_INCREMENT PRIMARY KEY,
            year YEAR NOT NULL,
            move_count INT,
            move_local VARCHAR(50) NOT NULL
        );
        """

        cursor.execute("DROP TABLE IF EXISTS emergency_move")
        cursor.execute(create_sql)
        conn.commit()

    finally:
        if conn:
            cursor.close()
            conn.close()

def move_all():

    try:
        conn = get_connection()

        sql_all = """
        SELECT year, move_local, move_count
        FROM emergency_move
        ORDER BY year, move_local;
        """
        df_all = pd.read_sql(sql_all, conn)


    finally:
        conn.close()

def move_local(region):
    try:
        conn = get_connection()

        sql_region = f"""
        SELECT year, move_local, move_count
        FROM emergency_move
        WHERE move_local = '{region}'
        ORDER BY year;
        """
        df_region = pd.read_sql(sql_region, conn)

    finally:
        conn.close()
