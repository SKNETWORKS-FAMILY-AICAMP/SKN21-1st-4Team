#!/usr/bin/env python3
"""
DB 연결 테스트 스크립트
"""
import sys
import os

# sql 폴더의 db_config 모듈을 import하기 위해 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'sql'))

try:
    from db_config import get_connection, DB_CONFIG
    print("✅ db_config 모듈 import 성공")
    print(f"📊 DB 설정: {DB_CONFIG}")
    
    # 연결 테스트
    print("🔗 DB 연결 테스트 중...")
    conn = get_connection()
    print("✅ DB 연결 성공!")
    
    # 간단한 쿼리 테스트
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    print(f"✅ 쿼리 테스트 성공: {result}")
    
    cursor.close()
    conn.close()
    print("✅ 연결 정상 종료")
    
except ImportError as e:
    print(f"❌ Import 에러: {e}")
except Exception as e:
    print(f"❌ DB 연결 에러: {e}")
    print(f"   에러 타입: {type(e).__name__}")