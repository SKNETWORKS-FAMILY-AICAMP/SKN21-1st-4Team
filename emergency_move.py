import pandas as pd
import pymysql


host="127.0.0.1",
user="root",
password="0000",
database="emergency"


# host="192.168.0.23"
# user="first_guest"
# password="1234"
# database="emergency"

files = [
    "data/2019_move.csv",
    "data/2020_move.csv",
    "data/2021_move.csv",
    "data/2022_move.csv",
    "data/2023_move.csv"]



with pymysql.connect(host=host, user=user, password=password, database=database) as connection:
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