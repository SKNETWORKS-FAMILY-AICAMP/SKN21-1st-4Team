ERD 이미지에서 emergency_faq를 찾아 질문/답변을 DB에 삽입하는 스크립트 안내

필수 요구사항
- 로컬에 Python 3.8+ 설치
- Tesseract OCR 설치 (Windows 예시)
  1) https://github.com/tesseract-ocr/tesseract/releases 에서 최신 설치파일 다운로드
  2) 설치 후 환경변수 PATH에 tesseract 실행파일 경로 추가 (예: C:\Program Files\Tesseract-OCR)

필수 패키지 설치
```cmd
C:\> pip install pillow pytesseract pymysql
```

스크립트 사용법
- 기본 실행 (기본 이미지 경로: ../DATA/erd.png)
```cmd
C:\> python "c:\Users\Playdata\Desktop\1과제\SKN21-1st-4Team\streamlit\ocr_insert_erd.py" --host 192.168.0.23 --user first_guest --password 1234 --db emergency
```
- 다른 이미지나 질문/답변을 지정하려면:
```cmd
C:\> python ocr_insert_erd.py --image "..\\DATA\\erd.png" --host 192.168.0.23 --user first_guest --password 1234 --db emergency --question "질문 텍스트" --answer "답변 텍스트"
```

주의
- OCR 결과가 정확하지 않을 수 있으므로, 삽입 전에 콘솔에 출력되는 추정 컬럼명을 확인하고 SQL 실행을 최종 확인하세요.
- DB 계정 정보는 민감하므로 안전한 환경에서 실행하세요.
