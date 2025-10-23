"""
ocr_insert_erd.py

이미지(ERD)에서 `emergency_faq` 테이블 정보를 자동으로 탐지하고,
지정한 질문/답변을 해당 테이블의 faq_question / faq_answer 컬럼으로 삽입하는 스크립트입니다.

사용 환경: 로컬에서 Tesseract OCR이 설치되어 있어야 하며, Python 패키지(pytesseract, pillow, pymysql)가 필요합니다.

주의: OCR 정확도는 이미지 품질에 따라 달라집니다. 스크립트는 ERD에서 컬럼명을 추정하지만, 자동 추출이 실패하면 기본 컬럼 이름(faq_question, faq_answer)을 사용합니다.

예시 실행:
python ocr_insert_erd.py --image "..\\DATA\\erd.png" --host 192.168.0.23 --user first_guest --password 1234 --db emergency

"""

import os
import sys
import re
import argparse
import getpass

try:
    from PIL import Image
except Exception:
    print("Pillow가 설치되어 있지 않습니다. 'pip install pillow'로 설치하세요.")
    sys.exit(1)

try:
    import pytesseract
except Exception:
    print("pytesseract가 설치되어 있지 않습니다. 'pip install pytesseract'로 설치하세요.")
    sys.exit(1)

try:
    import pymysql
except Exception:
    print("pymysql이 설치되어 있지 않습니다. 'pip install pymysql'로 설치하세요.")
    sys.exit(1)


DEFAULT_QUESTION = "💰 119 구급차는 유료인가요?"
DEFAULT_ANSWER = (
    "**소방서 119 구급차 이송은 위급 상황에서 전국 어디서나 무료**입니다.\n\n"
    "다만 **비응급 환자 이송·의료기관 간 이송** 등은 **민간(의료기관 등) 구급차** 이용 대상이며 아래와 같은 **요금 기준**이 적용됩니다.\n\n"
    "**민간 구급차(응급의료법 제44조) 요금(요약)**\n"
    "- **일반구급차 기본요금(10km 이내)**: 30,000원(의료기관 등) / 20,000원(비영리법인)\n"
    "- **일반구급차 추가요금(10km 초과)**: 1,000원/km / 800원/km\n"
    "- **특수구급차 기본요금(10km 이내)**: 75,000원 / 50,000원\n"
    "- **특수구급차 추가요금(10km 초과)**: 1,300원/km / 1,000원/km\n"
    "- **할증(00:00~04:00)**: 기본·추가요금 각각 20% 가산\n"
    "- **별도 청구 금지**: 이송처치료 외 장비·소모품·대기비·통행료·보호자 탑승료 등 별도 청구 금지\n\n"
    "_(출처: 찾기쉬운 생활법령정보 ‘구급차의 이용 방법’, 최신기준 2025-09-15)_"
)


def detect_table_block(text, table_name='emergency_faq'):
    """OCR 텍스트에서 table_name이 포함된 라인을 찾고 주변 라인(전후 10줄)을 반환한다."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if table_name.lower() in line.lower():
            start = max(0, i - 5)
            end = min(len(lines), i + 10)
            return '\n'.join(lines[start:end])
    return None


def extract_columns(block_text):
    """블록 텍스트에서 후보 컬럼명을 추출해 리스트로 반환한다."""
    if not block_text:
        return []
    # 단어 형태로 추출 (알파벳/숫자/밑줄)
    tokens = re.findall(r"[A-Za-z0-9_]+", block_text)
    # 자주 사용하는 컬럼명 후보 필터링
    candidates = [t for t in tokens if re.search(r'faq|idx|question|answer|created|date', t, re.IGNORECASE)]
    # 소문자 정렬 및 중복 제거
    seen = []
    for c in candidates:
        lc = c.lower()
        if lc not in seen:
            seen.append(lc)
    return seen


def main():
    parser = argparse.ArgumentParser(description='ERD 이미지에서 emergency_faq를 찾아 질문/답변을 DB에 삽입')
    parser.add_argument('--image', default=os.path.join('..', 'DATA', 'erd.png'), help='ERD 이미지 경로')
    parser.add_argument('--host', default=None, help='DB host')
    parser.add_argument('--port', type=int, default=3306, help='DB port')
    parser.add_argument('--user', default=None, help='DB user')
    parser.add_argument('--password', default=None, help='DB password')
    parser.add_argument('--db', default='emergency', help='DB name')
    parser.add_argument('--table', default='emergency_faq', help='테이블 이름')
    parser.add_argument('--question', default=None, help='삽입할 질문 텍스트')
    parser.add_argument('--answer', default=None, help='삽입할 답변 텍스트 (마크다운 허용)')

    args = parser.parse_args()

    image_path = args.image
    if not os.path.exists(image_path):
        print(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        sys.exit(1)

    # OCR
    print('이미지에서 텍스트 추출 중... (OCR)')
    try:
        img = Image.open(image_path)
    except Exception as e:
        print('이미지 열기 실패:', e)
        sys.exit(1)

    try:
        ocr_text = pytesseract.image_to_string(img)
    except Exception as e:
        print('OCR 실행 실패. Tesseract 설치 및 경로 설정을 확인하세요. 에러:', e)
        sys.exit(1)

    # 탐지
    block = detect_table_block(ocr_text, args.table)
    if block:
        print('ERD에서 다음 블록을 감지했습니다:\n')
        print(block)
    else:
        print('ERD에서 테이블 블록을 감지하지 못했습니다. 전체 OCR 텍스트 일부를 출력합니다.\n')
        print('\n'.join(ocr_text.splitlines()[:30]))

    cols = extract_columns(block)
    print('\n추정된 컬럼명:', cols)

    # 삽입 컬럼 결정
    if 'faq_question' in cols and 'faq_answer' in cols:
        col_question = 'faq_question'
        col_answer = 'faq_answer'
    else:
        # 후보 중 가장 근접한 이름 사용, 없으면 기본 사용
        col_question = next((c for c in cols if 'question' in c), 'faq_question')
        col_answer = next((c for c in cols if 'answer' in c), 'faq_answer')

    # 입력값 준비
    question = args.question if args.question is not None else DEFAULT_QUESTION
    answer = args.answer if args.answer is not None else DEFAULT_ANSWER

    host = args.host or input('DB host: ')
    user = args.user or input('DB user: ')
    password = args.password or getpass.getpass('DB password: ')
    dbname = args.db
    port = args.port
    table = args.table

    # DB 연결 및 삽입
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password, db=dbname, charset='utf8mb4')
    except Exception as e:
        print('DB 연결 실패:', e)
        sys.exit(1)

    try:
        with conn.cursor() as cur:
            sql = f"INSERT INTO {table} ({col_question}, {col_answer}) VALUES (%s, %s)"
            print('\n다음 SQL을 실행합니다:')
            print(sql)
            confirm = input('실행하시겠습니까? (y/N): ').strip().lower()
            if confirm != 'y':
                print('취소되었습니다.')
                return
            cur.execute(sql, (question, answer))
            conn.commit()
            print('삽입 완료: 질문이 테이블에 추가되었습니다.')
    except Exception as e:
        print('삽입 중 오류 발생:', e)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
