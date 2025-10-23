import pandas as pd
import pymysql

# MySQL 연결 설정
host = "192.168.0.23"
user = "first_guest"
password = "1234"
database = "emergency"

files = [
    "DATA/2019_car.csv",
    "DATA/2020_car.csv",
    "DATA/2021_car.csv",
    "DATA/2022_car.csv",
    "DATA/2023_car.csv"]



with pymysql.connect(host=host, user=user, password=password, database=database) as connection:
    with connection.cursor() as cursor:

        for f in files:
            df = pd.read_csv(f)

            df = df.rename(columns={"분류": "car_local", "계": "car_count", "계.1" : "emp_count"})
            df = df[["car_count", "emp_count", "car_local"]]
            

            df["year"] = int(f[5:9])  # "DATA/2019_car.csv"에서 연도 추출 (5:9)

            sql = 'insert into emergency_car (year, car_count, emp_count, car_local) values (%s, %s, %s, %s)'
            for row in df.iterrows():
                row_data = row[1]
                # print((row_data['year'], row_data['car_count'].replace(',', ''), row_data['emp_count'].replace(',', ''), row_data['car_local']))
                cursor.execute(sql, (row_data['year'], int(row_data['car_count'].replace(',','')), int(row_data['emp_count'].replace(',','')), row_data['car_local']))
            
            print(f"{f} 파일 적재 완료")

        connection.commit()
        print("모든 데이터 커밋 완료")