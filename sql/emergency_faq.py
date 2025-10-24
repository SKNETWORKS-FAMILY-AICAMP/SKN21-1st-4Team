import pymysql
import pandas as pd
from db_config import get_connection

def emergency_faq_table():

    try:
        conn = get_connection()
        cursor = conn.cursor()

        create_sql = """
        CREATE TABLE emergency_faq (
            idx INT AUTO_INCREMENT PRIMARY KEY,
            faq_question TEXT NOT NULL,
            faq_answer TEXT NOT NULL
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
        conn = get_connection()

        sql_all = """
        SELECT idx, faq_question, faq_answer
        FROM emergency_faq
        ORDER BY idx;
        """
        df_all = pd.read_sql(sql_all, conn)

    finally:
        conn.close()