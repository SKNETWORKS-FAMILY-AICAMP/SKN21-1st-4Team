import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd


def get_mysql_connection():
    """MySQL 데이터베이스 연결"""
    try:
        connection = mysql.connector.connect(
            host=st.secrets.get("mysql", {}).get("host", "localhost"),
            database=st.secrets.get("mysql", {}).get("database", "emergency_db"),
            user=st.secrets.get("mysql", {}).get("user", "first_guest"),
            password=st.secrets.get("mysql", {}).get("password", "1234")
        )
        return connection
    except Error as e:
        st.error(f"MySQL 연결 오류: {e}")
        return None


@st.cache_data(ttl=3600)  # 1시간 캐시
def load_faq_data():
    """MySQL에서 FAQ 데이터 로드"""
    try:
        connection = get_mysql_connection()
        if connection is None:
            return get_fallback_faq_data()
        
        query = "SELECT faq_question, faq_answer FROM emergency_faq ORDER BY id"
        df = pd.read_sql(query, connection)
        connection.close()
        
        # DataFrame을 딕셔너리 리스트로 변환
        faqs = []
        for _, row in df.iterrows():
            faqs.append({
                "question": row['faq_question'],
                "answer": row['faq_answer']
            })
        
        return faqs
        
    except Exception as e:
        st.warning(f"FAQ 데이터 로드 중 오류가 발생했습니다: {e}")
        return get_fallback_faq_data()


def get_fallback_faq_data():
    """MySQL 연결 실패 시 기본 FAQ 데이터"""
    return [
        {
            "question": "💰 119 구급차는 유료인가요?",
            "answer": """
**소방서 119 구급차 이송은 위급 상황에서 전국 어디서나 무료**입니다.  
다만 **비응급 환자 이송·의료기관 간 이송** 등은 **민간(의료기관 등) 구급차** 이용 대상이며 아래와 같은 **요금 기준**이 적용됩니다.

**민간 구급차(응급의료법 제44조) 요금(요약)**  
- **일반구급차 기본요금(10km 이내)**: 30,000원(의료기관 등) / 20,000원(비영리법인)  
- **일반구급차 추가요금(10km 초과)**: 1,000원/km / 800원/km  
- **특수구급차 기본요금(10km 이내)**: 75,000원 / 50,000원  
- **특수구급차 추가요금(10km 초과)**: 1,300원/km / 1,000원/km  
- **할증(00:00~04:00)**: 기본·추가요금 각각 20% 가산  
- **별도 청구 금지**: 이송처치료 외 **장비·소모품·대기비·통행료·보호자 탑승료 등 별도 청구 금지**

_(출처: 찾기쉬운 생활법령정보 '구급차의 이용 방법', 최신기준 2025-09-15)_"""
        },
        {
            "question": "📞 119 구급신고는 어떻게 하나요?",
            "answer": """
**신고 핵심 절차(요약)**  
1) "환자가 있습니다" 등 **응급상황임을 먼저 알리기**  
2) **정확한 위치(주소·랜드마크)** 전달  
3) **무슨 일이 발생했는지/증상** 설명  
4) **환자 상태**(의식·호흡·연령·성별 등)  
5) **신고자 연락처**  
6) **상담원(구급상황관리사)의 안내**를 따라 **전화를 먼저 끊지 않기**

_(출처: 소방청 '119 구급신고 요령')_"""
        },
        {
            "question": "🏠 구급차 도착 전 무엇을 준비하나요?",
            "answer": """
**도착 전 준비 체크리스트**  
- **의료지도·응급처치**: 상담원 안내에 따라 침착하게 시행(필요 시 CPR)  
- **길 안내**: 동행자가 있다면 **도로까지 나가 안내**  
- **준비물**: 신분증/건강보험증/진찰권, 현금·카드·신발 등 생필품, **평소 복용약 목록**  
- **안전조치**: **문단속**, 전기·가스 **차단**  
- **영유아**: 우유·기저귀·모자보건수첩 등

_(출처: 소방청 '119 구급차 도착전 준비')_"""
        },
        {
            "question": "🩺 현장에서 임의로 옮겨도 되나요? 응급처치는 어떻게?",
            "answer": """
**원칙**: **상담원 의료지도에 따름**. 척추손상 등 위험이 의심되면 **임의 이동 최소화**.  
**응급처치**: 기도확보·호흡확인 등 **기본응급처치**를 수행하고, 필요 시 **심폐소생술(CPR)** 시행.  
**교육**: CPR 등 응급처치 교육은 **관내 소방서·보건소** 및 공인 교육기관에서 상시 운영.

_(출처: 소방청 '119 구급차 도착전 준비')_"""
        },
        {
            "question": "🚦 긴급자동차의 신호위반 등 '특례'가 있나요?",
            "answer": """
네. **골든타임 확보**를 위해 '도로교통법' 개정(시행: **2021-01-12**)으로 **긴급자동차 통행 특례가 확대**되었습니다.  
**대상**: 소방·구급·경찰·혈액 운반용 등 긴급자동차(생명 위급 환자 이송 차량 포함)  
**취지**: 신속 출동·이송 중 **업무 수행 보호** 및 **출동 시간 단축**

_(출처: 대한민국 정책브리핑 '긴급자동차 출동 시간 더 빨라진다!')_"""
        },
        {
            "question": "🚨 일반차량이 구급차 진로양보해야 하나요?",
            "answer": """
**의무입니다.**  
- **교차로·부근**: 긴급자동차가 접근하면 **교차로를 피하여 일시정지**해야 합니다.  
- **그 외 구간**: 긴급자동차가 **우선 통행**할 수 있도록 **도로 우측 가장자리로 피해서 진로를 양보**합니다. *(일방통행 등 구조상 좌측 양보가 안전한 경우는 좌측 가능)*

**법적 근거(요지):**  
- 「도로교통법」 **제29조(긴급자동차의 우선 통행)**  
  - 제4항: *교차로나 그 부근에서 긴급자동차가 접근하는 경우 차마와 노면전차의 운전자는 **교차로를 피하여 일시정지***  
- 찾기쉬운 생활법령정보(법제처) **'자동차 운전 시 긴급자동차가 접근하면 진로양보는?'**  
  - 교차로·그 부근: **일시정지** / 그 외 구간: **우측 가장자리로 피양(양보)**  
  - 좁은 도로 등 **예외 상황별 양보 방법** 안내

**출처:**  
- 도로교통법 제29조(긴급자동차의 우선 통행): law.go.kr  
- 찾기쉬운 생활법령정보(진로 양보 안내): easylaw.go.kr
"""
        },
    ]


def show_faq_page():
    st.markdown('<div class="section-header"><h2>❓ 자주 묻는 질문 (FAQ)</h2></div>', unsafe_allow_html=True)

    # MySQL에서 FAQ 데이터 로드
    faqs = load_faq_data()
    
    # 데이터 로드 상태 표시
    if not faqs:
        st.warning("FAQ 데이터를 불러올 수 없습니다.")
        return
    
    # 데이터베이스 연결 상태 정보 (개발용)
    if st.sidebar.checkbox("🔧 DB 연결 정보 표시", value=False):
        try:
            connection = get_mysql_connection()
            if connection:
                st.sidebar.success("✅ MySQL 연결 성공")
                connection.close()
            else:
                st.sidebar.error("❌ MySQL 연결 실패 - Fallback 데이터 사용")
        except Exception as e:
            st.sidebar.error(f"❌ 연결 오류: {e}")

    # FAQ 항목들을 expander로 표시
    for i, faq in enumerate(faqs):
        with st.expander(faq["question"]):
            st.markdown(faq["answer"])

