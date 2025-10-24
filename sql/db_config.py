"""
데이터베이스 연결 설정을 중앙화하여 관리하는 모듈
"""
import pymysql

# 데이터베이스 연결 설정
DB_CONFIG = {
    'host': '192.168.0.25',
    'user': 'first_guest',
    'password': '1234',
    'db': 'emergency',
    'port': 3306
}

def get_connection():
    """
    데이터베이스 연결을 생성하고 반환
    
    Returns:
        pymysql.Connection: 데이터베이스 연결 객체
    """
    return pymysql.connect(**DB_CONFIG)