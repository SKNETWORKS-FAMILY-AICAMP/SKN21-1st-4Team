import pymysql
import pandas as pd

def emergency_car_table():
    try: 
        conn = pymysql.connect(
            host='192.168.0.23',
            user='first_guest',
            password='1234',
            db='emergency',
            port=3306
        )

        cursor = conn.cursor()

        createsql = """
        CREATE TABLE emergency_car (
            idx INT AUTO_INCREMENT PRIMARY KEY,
            year YEAR NOT NULL,
            car_count INT,
            emp_count INT,
            car_local VARCHAR(50) NOT NULL
        );
        """
        cursor.execute("DROP TABLE IF EXISTS emergency_car")
        cursor.execute(createsql)

        conn.commit()

    finally:
 
        if conn:
            cursor.close() 
            conn.close()

def car_all():

    try:
        conn = pymysql.connect(
            host='192.168.0.23',
            user='first_guest',
            password='1234',
            db='emergency',
            port=3306
        )

    
    # 전체 데이터 조회
        sql_all = """
        SELECT year, car_local, car_count, emp_count 
        FROM emergency_car 
        ORDER BY year, car_local;
        """
        df_all = pd.read_sql(sql_all, conn)

    finally:
        conn.close()

def car_local(region):

    conn = pymysql.connect(
            host='192.168.0.23',
            user='first_guest',
            password='1234',
            db='emergency',
            port=3306
        )

    try:
        # 지역별 데이터 조회
        sql_region = f"""
        SELECT year, car_local, car_count, emp_count
        FROM emergency_car
        WHERE car_local = '{region}'
        ORDER BY year;
        """
        df_region = pd.read_sql(sql_region, conn)

    finally:
        conn.close()
