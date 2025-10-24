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

# 파일 패턴 (예: "2019_move.xlsx", "2020_move.xlsx", ...)
FILE_GLOB = "*_move.xlsx"  # 필요 시 "20??_move.xlsx" 등으로 제한 가능

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

# 읽을 때 사용할 원본 컬럼 순서(없으면 자동 드롭되지 않을 수 있음)
SOURCE_COLS = list(COLUMN_MAP.keys())
TARGET_COLS = list(COLUMN_MAP.values())   # 변환 후 MySQL 테이블에 들어가는 컬럼

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
    # 엑셀: 첫 번째 시트 기준
    df = pd.read_excel(path, dtype=str)

    # 필요한 원본 컬럼 체크
    missing = [c for c in SOURCE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{os.path.basename(path)}에 필요한 컬럼이 없습니다: {missing}")

    # 필요한 원본 컬럼만 사용
    df = df[SOURCE_COLS].copy()

    # 컬럼명 매핑 -> 타겟 컬럼명으로 변경
    df = df.rename(columns=COLUMN_MAP)

    # 문자열 공백 제거
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()

    # 빈 문자열을 NaN으로 치환 ("" -> <NA>)
    df = df.replace({"": pd.NA})

    # year 숫자 변환 (실패 시 NaN으로)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # 최종 컬럼 존재 확인
    missing_target = [c for c in TARGET_COLS if c not in df.columns]
    if missing_target:
        raise ValueError(
            f"매핑 후 누락된 타겟 컬럼: {missing_target}. COLUMN_MAP/TARGET_COLS 설정 확인 필요."
        )

    # 타겟 컬럼만 남기고 순서 고정
    df = df[TARGET_COLS]

    # ✅ 타겟 컬럼 중 하나라도 비어 있으면 행 제거
    df = df.dropna(subset=TARGET_COLS, how="any")

    # (선택) NaN -> None (to_sql에서 NULL로 인식되게 하고 싶다면 유지)
    df = df.where(pd.notnull(df), None)

    return df

def main():
    engine = get_engine()
    ensure_table(engine)

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
