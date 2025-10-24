import os
import sys
import subprocess
import time

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# sql문 사용을 위한 import
import sql_py.emergency_car as sql_car
import sql_py.emergency_ex as sql_ex
import sql_py.emergency_faq as sql_faq
import sql_py.emergerncy_move as sql_move 

# csv data upload를 위한 import
import csv_py.emergency_car as csv_car
import csv_py.emergency_move as csv_move
import csv_py.emergency_ex as csv_ex

def setup_database():
    """데이터베이스 테이블 생성 및 데이터 로드"""
    print("🔧 데이터베이스 테이블 생성 중...")
    
    try:
        # 테이블 생성
        sql_car.emergency_car_table()
        print("✅ emergency_car 테이블 생성 완료")
        
        sql_ex.emergency_ex_table()
        print("✅ emergency_ex 테이블 생성 완료")
        
        sql_faq.emergency_faq_table()
        print("✅ emergency_faq 테이블 생성 완료")
        
        sql_move.emergency_move_table()
        print("✅ emergency_move 테이블 생성 완료")
        
        print("\n📊 CSV 데이터 로드 중...")
        
        # CSV 데이터 로드
        csv_car.load_car()
        print("✅ emergency_car 데이터 로드 완료")
        
        csv_move.load_move()
        print("✅ emergency_move 데이터 로드 완료")
        
        csv_ex.main()
        print("✅ emergency_ex 데이터 로드 완료")
        
        print("\n🎉 모든 데이터베이스 설정이 완료되었습니다!")
        
    except Exception as e:
        print(f"❌ 데이터베이스 설정 중 오류 발생: {e}")
        return False
    
    return True

def run_streamlit():
    """Streamlit 애플리케이션 실행"""
    print("🚀 Streamlit 애플리케이션을 시작합니다...")
    
    # 기존 Streamlit 프로세스 종료
    print("🔄 기존 Streamlit 프로세스를 정리합니다...")
    try:
        subprocess.run(['pkill', '-f', 'streamlit'], capture_output=True, timeout=5)
    except:
        pass
    
    # 잠시 대기
    time.sleep(2)
    
    # main.py의 절대 경로
    main_py_path = os.path.join(project_root, 'streamlit_py', 'main.py')
    
    try:
        print(f"📍 Streamlit을 포트 8501에서 시작합니다...")
        print(f"🌐 브라우저에서 http://localhost:8501 접속하세요")
        
        # Streamlit 실행 (백그라운드가 아닌 직접 실행)
        result = subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', main_py_path,
            '--server.port', '8501'
        ], cwd=project_root)
        
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print("\n🛑 사용자가 애플리케이션을 종료했습니다.")
        return True
    except Exception as e:
        print(f"❌ Streamlit 실행 중 오류 발생: {e}")
        return False

def run():
    """메인 실행 함수 - 데이터베이스 설정만 실행"""
    print("=" * 50)
    print("🏥 응급의료 데이터 분석 시스템 - 데이터베이스 설정")
    print("=" * 50)
    
    # 데이터베이스 설정만 실행
    if setup_database():
        print("✅ 데이터베이스 설정이 완료되었습니다.")
        return True
    else:
        print("❌ 데이터베이스 설정 실패")
        return False

def main():
    """전체 실행 함수 - 데이터베이스 설정 + Streamlit 실행"""
    print("=" * 50)
    print("🏥 응급의료 데이터 분석 시스템 시작")
    print("=" * 50)
    
    # 데이터베이스 설정
    if setup_database():
        # Streamlit 실행
        success = run_streamlit()
        if success:
            print("✅ 애플리케이션이 정상적으로 실행되었습니다.")
        else:
            print("❌ Streamlit 실행 중 문제가 발생했습니다.")
    else:
        print("❌ 데이터베이스 설정 실패로 인해 애플리케이션을 시작할 수 없습니다.")

if __name__ == "__main__":
    main()