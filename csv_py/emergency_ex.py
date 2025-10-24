import os
import glob
import pandas as pd
from sqlalchemy import create_engine, text
import sys

# 프로젝트 루트의 db_config 모듈을 import하기 위해 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db_config import DB_CONFIG

# ---------- 사용자 설정 ----------
MYSQL_USER = DB_CONFIG['user']
MYSQL_PASSWORD = DB_CONFIG['password']
MYSQL_HOST = DB_CONFIG['host']
MYSQL_PORT = DB_CONFIG['port']
MYSQL_DATABASE = DB_CONFIG['db']
TABLE_NAME = "emergency_ex"

# 파일 패턴 (예: "DATA/2019_ex.xlsx", "DATA/2020_ex.xlsx", ...)
FILE_GLOB = "DATA/*_ex.xlsx"  # DATA 폴더의 ex 파일들

# 실제 원본(엑셀/CSV) 컬럼명 -> MySQL 테이블 컬럼명 매핑
#   PTN_SYM_SE_NM - 증상  -> cause
#   PTN_CTPV_NM   - 지역  -> local
#   GNDR_NM       - 성별  -> gender
#   PTN_CR_NM     - 직장  -> job
#   PTN_CNTC_YR   - 연도  -> year
COLUMN_MAP = {
    "PTN_CNTC_YR": "year",
    "PTN_SYM_SE_NM": "cause",   # (사용자 요청 그대로 'cause' 오타 포함)
    "GNDR_NM": "gender",
    "PTN_CTPV_NM": "local",
    "PTN_CR_NM": "job",
}

# 2022년 파일용 컬럼 인덱스 매핑 (D=증상, R=연도, BM=지역, BP=직업)
COLUMN_MAP_2022 = {
    17: "year",    # R - 연도
    3: "cause",    # D - 증상  
    62: "gender",  # 성별
    65: "local",   # BM - 지역 (동해시 헤더, 실제로는 시/군)
    67: "job",     # BP - 직업
}

# 읽을 때 사용할 원본 컬럼 순서(없으면 자동 드롭되지 않을 수 있음)
SOURCE_COLS = list(COLUMN_MAP.keys())
TARGET_COLS = list(COLUMN_MAP.values())   # 변환 후 MySQL 테이블에 들어가는 컬럼

# ---------- 지역명 변환 함수 ----------
def convert_region_name(region_name):
    """지역명을 풀네임에서 2글자로 변환"""
    if pd.isna(region_name) or region_name == '' or region_name == 'nan':
        return region_name
    
    region_name = str(region_name).strip()
    
    # 지역명 변환 딕셔너리
    region_mapping = {
        # 서울특별시 -> 서울
        '서울특별시': '서울',
        
        # 광역시들
        '부산광역시': '부산',
        '대구광역시': '대구', 
        '인천광역시': '인천',
        '광주광역시': '광주',
        '대전광역시': '대전',
        '울산광역시': '울산',
        
        # 세종특별자치시 -> 세종
        '세종특별자치시': '세종',
        
        # 도들
        '경기도': '경기',
        '강원도': '강원',
        '충청북도': '충북',
        '충청남도': '충남',
        '전라북도': '전북',
        '전라남도': '전남',
        '경상북도': '경북',
        '경상남도': '경남',
        '제주특별자치도': '제주',
        '제주도': '제주'
    }
    
    # 정확히 일치하는 경우
    if region_name in region_mapping:
        return region_mapping[region_name]
    
    # 부분 매칭 (포함되는 경우)
    for full_name, short_name in region_mapping.items():
        if full_name in region_name:
            return short_name
    
    # 매칭되지 않는 경우 첫 2글자 반환 (예: '충청북도청주시' -> '충청')
    if len(region_name) >= 2:
        return region_name[:2]
    
    return region_name

# ---------- 함수들 ----------
def get_engine():
    url = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    )
    return create_engine(url, pool_pre_ping=True)

def ensure_table(engine):
    """
    emergency_ex 테이블이 없으면 생성합니다.
    스키마는 아래와 같이 가정합니다:
      - year: INT
      - cause, gender, local, job: VARCHAR(255)
    """
    ddl = f"""
    CREATE TABLE IF NOT EXISTS `{TABLE_NAME}` (
      `year`  INT,
      `cause` VARCHAR(255),
      `gender` VARCHAR(255),
      `local` VARCHAR(255),
      `job` VARCHAR(255)
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))
        
def load_file(path: str) -> pd.DataFrame:
    """
    엑셀 파일을 읽어 필요한 컬럼만 추출/정리하여 반환합니다.
    CSV를 사용할 경우에는 pd.read_excel -> pd.read_csv로 바꾸세요.
    """
    filename = os.path.basename(path)
    
    # 엑셀: 첫 번째 시트 기준
    df = pd.read_excel(path, dtype=str)
    
    # 2022년 파일은 구조가 다르므로 별도 처리
    if "2022" in filename:
        print(f"📋 {filename}은 2022년 파일로 특별 처리합니다.")
        
        # 2022년 파일은 컬럼 인덱스로 접근
        result_data = []
        for i in range(len(df)):
            row_data = {}
            for col_idx, target_col in COLUMN_MAP_2022.items():
                if col_idx < len(df.columns):
                    row_data[target_col] = str(df.iloc[i, col_idx]).strip() if pd.notna(df.iloc[i, col_idx]) else ""
                else:
                    row_data[target_col] = ""
            result_data.append(row_data)
        
        result_df = pd.DataFrame(result_data)
        
    else:
        # 기존 파일들 처리 (2019-2021, 2023 등)
        # 필요한 원본 컬럼 체크
        missing = [c for c in SOURCE_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"{filename}에 필요한 컬럼이 없습니다: {missing}")

        # 필요한 원본 컬럼만 사용
        df = df[SOURCE_COLS].copy()

        # 컬럼명 매핑 -> 타겟 컬럼명으로 변경
        result_df = df.rename(columns=COLUMN_MAP)

    # 문자열 공백 제거
    for col in result_df.columns:
        if result_df[col].dtype == object:
            result_df[col] = result_df[col].astype(str).str.strip()

    # 빈 문자열을 NaN으로 치환 ("" -> <NA>)
    result_df = result_df.replace({"": pd.NA})

    # 지역명 변환 (풀네임 -> 2글자)
    if 'local' in result_df.columns:
        result_df['local'] = result_df['local'].apply(convert_region_name)
        print(f"'{filename}'에서 지역명을 2글자로 변환했습니다.")

    # year 숫자 변환 (실패 시 NaN으로)
    result_df["year"] = pd.to_numeric(result_df["year"], errors="coerce").astype("Int64")

    # 최종 컬럼 존재 확인
    missing_target = [c for c in TARGET_COLS if c not in result_df.columns]
    if missing_target:
        raise ValueError(
            f"매핑 후 누락된 타겟 컬럼: {missing_target}. COLUMN_MAP/TARGET_COLS 설정 확인 필요."
        )

    # 타겟 컬럼만 남기고 순서 고정
    result_df = result_df[TARGET_COLS]

    # ✅ 타겟 컬럼 중 하나라도 비어 있으면 행 제거
    result_df = result_df.dropna(subset=TARGET_COLS, how="any")

    # ✅ 지역이 '전체'인 경우 제외
    if 'local' in result_df.columns:
        before_count = len(result_df)
        result_df = result_df[result_df['local'] != '전체']
        after_count = len(result_df)
        removed_count = before_count - after_count
        if removed_count > 0:
            print(f"'{filename}'에서 지역이 '전체'인 {removed_count}개 행을 제외했습니다.")

    # (선택) NaN -> None (to_sql에서 NULL로 인식되게 하고 싶다면 유지)
    result_df = result_df.where(pd.notnull(result_df), None)

    return result_df

def main():
    engine = get_engine() # db 연결 엔진 생성
    ensure_table(engine) # 테이블 존재 확인/생성

    files = sorted(glob.glob(FILE_GLOB))
    if not files:
        print(f"패턴 '{FILE_GLOB}'에 맞는 파일이 없습니다. 같은 폴더에 있는지 확인해주세요.")
        return

    print(f"발견된 파일: {files}")

    total_rows = 0
    for fp in files:
        print(f"처리 중: {fp}")
        df = load_file(fp)

        # 미리보기(선택) — 문제 없으면 주석 처리해도 됩니다.
        print(df.head(3))

        # MySQL에 적재 (append)
        df.to_sql(
            name=TABLE_NAME,
            con=engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )
        total_rows += len(df)

    print(f"적재 완료: 총 {total_rows}행을 '{TABLE_NAME}' 테이블에 추가했습니다.")

if __name__ == "__main__":
    main()
