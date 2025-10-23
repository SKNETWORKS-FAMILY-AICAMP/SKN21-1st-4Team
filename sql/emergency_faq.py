import pymysql
import pandas as pd

def emergency_faq_table():

    try:
        conn = pymysql.connect(
            host='192.168.0.23',
            user='first_guest',
            password='1234',
            db='emergency',
            port=3306
        )
        cursor = conn.cursor()

        create_sql = """
        CREATE TABLE emergency_faq (
            idx INT AUTO_INCREMENT PRIMARY KEY,
            faq_question VARCHAR(255) NOT NULL,
            faq_answer VARCHAR(255) NOT NULL
        );
        """

        cursor.execute("DROP TABLE IF EXISTS emergency_faq")
        cursor.execute(create_sql)
        conn.commit()


    finally:
        if conn:
            cursor.close()
            conn.close()

def faq_all():

    try:
        conn = pymysql.connect(
            host='192.168.0.23',
            user='first_guest',
            password='1234',
            db='emergency',
            port=3306
        )

        sql_all = """
        SELECT idx, faq_question, faq_answer
        FROM emergency_faq
        ORDER BY idx;
        """
        df_all = pd.read_sql(sql_all, conn)

    finally:
        conn.close()