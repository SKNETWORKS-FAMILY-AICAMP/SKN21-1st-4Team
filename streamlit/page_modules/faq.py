# faq.py
import streamlit as st
import pymysql
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
import html, re, time

# ===== DB 설정 =====
DB_CONFIG = {
    "host": "192.168.0.23",
    "port": 3306,
    "user": "first_guest",
    "password": "1234",
    "db": "emergency",
    "charset": "utf8mb4",
    "autocommit": False,
}

# ===== 테이블 생성 / UPSERT =====
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS emergency_faq (
    idx INT NOT NULL AUTO_INCREMENT,
    faq_question VARCHAR(255) NOT NULL,
    faq_answer   TEXT NOT NULL,
    PRIMARY KEY (idx),
    UNIQUE KEY uq_faq_question (faq_question)
) CHARACTER SET utf8mb4;
"""
UPSERT_SQL = """
INSERT INTO emergency_faq (faq_question, faq_answer)
VALUES (%s, %s)
ON DUPLICATE KEY UPDATE faq_answer = VALUES(faq_answer);
"""

# ===== 질문 & 링크 =====
QUESTION_SOURCES = [
    {
        "q": "119 구급차 이용금액은 얼마인가요?",
        "url": "https://www.easylaw.go.kr/CSP/OnhunqueansInfoRetrieve.laf?onhunqnaAstSeq=86&onhunqueSeq=4729",
    },
    {
        "q": "응급처치시 알아두어야야 할 법적인 문제",
        "url": "https://www.safekorea.go.kr/idsiSFK/neo/sfk/cs/contents/prevent/SDIJK14433.html?cd1=33&cd2=999&menuSeq=128&pagecd=SDIJK144.33",
    },
    {
        "q": "119 구급신고 요령",
        "url": "https://www.nfa.go.kr/nfa/safetyinfo/emergencyservice/119emergencydeclaration/",
    },
    {
        "q": "119 구급차 도착 전 준비",
        "url": "https://www.nfa.go.kr/nfa/safetyinfo/emergencyservice/emergencydeclarationbefore/",
    },
    {
        "q": "긴급자동차(구급차) 특례",
        "url": "https://www.korea.kr/briefing/policyBriefingView.do?newsId=148883361&utm_source=chatgpt.com",
    },
]
ORDER_MAP = {item["q"]: i for i, item in enumerate(QUESTION_SOURCES)}

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ===== 공통 유틸 =====
def clean(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

def get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=UA, timeout=20)
    r.encoding = r.apparent_encoding or "utf-8"
    return BeautifulSoup(r.text, "html.parser")

def _table_to_markdown(tbl: Tag) -> str:
    headers, rows = [], []
    thead = tbl.find("thead")
    if thead:
        headers = [clean(x.get_text(" ", strip=True)) for x in thead.find_all(["th","td"])]
    for tr in tbl.find_all("tr"):
        cells = [clean(x.get_text(" ", strip=True)) for x in tr.find_all(["th","td"])]
        if not cells: continue
        if not headers:
            headers = cells
            continue
        rows.append(cells)
    if not headers: return ""
    coln = len(headers)
    rows = [r + [""] * (coln - len(r)) for r in rows]
    md = []
    md.append("| " + " | ".join(headers) + " |")
    md.append("| " + " | ".join(["---"] * coln) + " |")
    for r in rows:
        md.append("| " + " | ".join(r[:coln]) + " |")
    return "\n".join(md)

def node_to_markdown(node: Tag) -> str:
    """선택 노드를 Markdown으로 변환(P, DIV 텍스트 / TABLE → 표 / IMG → 이미지)"""
    if isinstance(node, NavigableString):
        return clean(str(node))
    if not isinstance(node, Tag):
        return ""
    name = node.name.lower()
    if name in ("p", "div", "span", "li", "strong"):
        return clean(node.get_text(" ", strip=True))
    if name == "table":
        return _table_to_markdown(node)
    if name == "img":
        src = node.get("src", "")
        alt = clean(node.get("alt", ""))
        if src and not src.startswith("http"):
            # 절대경로 보정(정책브리핑 등)
            src = "https://www.korea.kr" + src if src.startswith("/") else src
        return f"![{alt}]({src})" if src else (alt or "")
    return clean(node.get_text(" ", strip=True))

# =====================================================================
#                   ★★★ 질문 1 · 5 전용 '구간 크롤링' ★★★
# =====================================================================

# 1) 생활법령(질문 1): 지정 ID 시작 ~ 지정 ID 끝까지 크롤링
def parse_q1_easylaw_segment(url: str) -> str:
    soup = get_soup(url)

    # 사장님이 지정한 시작~끝 ID (포함)
    ids_in_order = [
        "divnull.4729.null.2214329",
        "divnull.4729.null.2214330",
        "divnull.4729.null.2214331",
        "divnull.4729.null.2214332",
        "divnull.4729.null.2214333",
    ]

    pieces = []
    for idv in ids_in_order:
        el = soup.find(id=idv)
        if el:
            pieces.append(node_to_markdown(el))

    # ✅ 표를 명시적으로 재생성(이 페이지 구조를 안 타고 항상 동일하게 렌더)
    fee_table_md = """
**🚑 구급차 요금표**

| 구분 | 요금의 종류 | 「응급의료에 관한 법률」 제44조제1항제1호부터 제4호까지에 따른 의료기관 등 | 「응급의료에 관한 법률」 제44조제1항제5호에 따른 비영리법인 |
|---|---|---|---|
| 일반구급차 | 기본요금 (이송거리 10km 이내) | 30,000원 | 20,000원 |
|  | 추가요금 (이송거리 10km 초과) | 1,000원/km | 800원/km |
|  | 부가요금 (의사·간호사 또는 응급구조사 탑승) | 15,000원 | 10,000원 |
| 특수구급차 | 기본요금 (이송거리 10km 이내) | 75,000원 | 50,000원 |
|  | 추가요금 (이송거리 10km 초과) | 1,300원/km | 1,000원/km |
| 공통 | 할증요금 (00:00~04:00) | 기본 및 추가요금 각 20% 가산 |  |
""".strip()

    # 지정 구간을 못 찾았을 때의 안전망
    if not any(pieces):
        container = soup.select_one("#conBody, .conBody, #content, .contents, article") or soup
        txt = clean(container.get_text(" ", strip=True))
        txt = txt[:4000] + (" …" if len(txt) > 4000 else "")
        pieces = [txt]

    body = "\n\n".join([p for p in pieces if p]) + "\n\n" + fee_table_md
    return f"{body}\n\n[출처] {url}"


def parse_q5_koreakr_segment(url: str) -> str:
    soup = get_soup(url)

    # 본문 루트 후보
    root = (
        soup.select_one("div.view_con, div.article_area, #contents, #content, article")
        or soup
    )

    start_text = "긴급자동차는 말 그대로 신속하게 현장에 도착하는 것이 목표다"
    end_text   = "개정안의 핵심은 이렇다"

    def find_p_contains(t):
        for p in root.find_all("p"):
            if t in p.get_text():
                return p
        return None

    start_node = find_p_contains(start_text)
    end_node   = find_p_contains(end_text)

    collected = []
    if start_node and end_node:
        cur = start_node
        while cur:
            if isinstance(cur, Tag):
                # ⚠️ 이미지/표(이미지+캡션) 스킵
                if cur.name in ("img",):
                    pass
                elif cur.name == "table":
                    pass  # 테이블(이미지/캡션 포함) 통째로 생략
                else:
                    md = node_to_markdown(cur)
                    if md:
                        collected.append(md)
            if cur == end_node:
                break
            cur = cur.find_next_sibling()

    # 보완: 못 모았으면 시작/끝 단락만이라도 확보
    if not collected:
        p1 = root.find("p", string=lambda s: s and start_text in s)
        if p1: collected.append(clean(p1.get_text(" ", strip=True)))
        p2 = root.find("p", string=lambda s: s and end_text in s)
        if p2: collected.append(clean(p2.get_text(" ", strip=True)))

    if not collected:
        text = clean(root.get_text(" ", strip=True))
        collected = [text[:1500] + (" …" if len(text) > 1500 else "")]

    # 🚫 캡션 문구 제거 + 이미지 마크다운(혹시 들어왔으면) 제거
    ban_phrase = "개정된 긴급자동차에 대한 특례 조항이다"
    filtered = []
    for line in collected:
        if not line:
            continue
        # 이미지 마크다운 제거
        if re.search(r'!\[.*\]\(.*\)', line):
            continue
        # 캡션(출처=소방청) 문구 제거
        if ban_phrase in line:
            continue
        filtered.append(line)

    body = "\n\n".join(filtered)
    return f"{body}\n\n[출처] {url}"

# =====================================================================
#                        (2~4번) 기존 전용/일반 파서
# =====================================================================

def parse_q2_safekorea(url: str) -> str:
    soup = get_soup(url)
    container = soup.select_one("#content, .contents, article, .cont, .board-view") or soup
    keep = []
    for p in container.find_all(["p", "li"]):
        t = clean(p.get_text(" ", strip=True))
        if not t or len(t) < 6: 
            continue
        if any(k in t for k in ["응급처치", "동의", "명시적 동의", "위법", "법적", "윤리"]):
            keep.append(t)
        if len(keep) >= 12:
            break
    body = "\n".join(f"- {k}" for k in keep) if keep else clean(container.get_text(" ", strip=True))[:4000]
    return f"{body}\n\n[출처] {url}"

def parse_q3_nfa(url: str) -> str:
    soup = get_soup(url)
    items = []
    for img in soup.select("ul.safety_sense img[alt]"):
        alt = clean(img.get("alt", ""))
        if alt:
            items.append(alt)
    if not items:
        content = soup.select_one("#content, .contents, article, .view") or soup
        text = clean(content.get_text(" ", strip=True))
        return text[:4000] + "\n\n[출처] " + url
    body = "\n".join(f"- {x}" for x in items)
    return f"{body}\n\n[출처] {url}"

def parse_q4_nfa(url: str) -> str:
    soup = get_soup(url)
    items = []
    for img in soup.select("ul.safety_sense img[alt]"):
        alt = clean(img.get("alt", ""))
        if alt:
            items.append(alt)
    if not items:
        content = soup.select_one("#content, .contents, article, .view") or soup
        text = clean(content.get_text(" ", strip=True))
        return text[:4000] + "\n\n[출처] " + url
    body = "\n".join(f"- {x}" for x in items)
    return f"{body}\n\n[출처] {url}"

# 질문→파서 매핑
def extract_answer(q_text: str, url: str) -> str:
    if "구급차 이용금액" in q_text:
        return parse_q1_easylaw_segment(url)        # ★ 1번: 구간 지정 추출
    if "법적인 문제" in q_text:
        return parse_q2_safekorea(url)
    if "구급신고 요령" in q_text:
        return parse_q3_nfa(url)
    if "도착 전 준비" in q_text:
        return parse_q4_nfa(url)
    if "긴급자동차" in q_text:
        return parse_q5_koreakr_segment(url)        # ★ 5번: 구간 지정 추출
    # 일반 fallback
    soup = get_soup(url)
    content = soup.select_one("article, #content, .contents, .cont, .view, section, main, div") or soup
    text = clean(content.get_text(" ", strip=True))
    return text[:4000] + "\n\n[출처] " + url

# ===== DB I/O =====
def _conn():
    return pymysql.connect(**DB_CONFIG)

def load_faq_from_db():
    try:
        conn = _conn()
        with conn.cursor() as cur:
            qs = list(ORDER_MAP.keys())
            ph = ",".join(["%s"] * len(qs))
            cur.execute(
                f"SELECT faq_question, faq_answer FROM emergency_faq WHERE faq_question IN ({ph})",
                qs,
            )
            rows = cur.fetchall()
        conn.close()
        data = [{"question": q, "answer": a} for (q, a) in rows]
        return sorted(data, key=lambda x: ORDER_MAP.get(x["question"], 999))
    except Exception:
        return []

def crawl_and_update():
    st.info("📌 크롤링 중입니다. 잠시만 기다려주세요...")
    results = []
    for item in QUESTION_SOURCES:
        q, url = item["q"], item["url"]
        try:
            a = extract_answer(q, url)
            results.append((q, a))
            st.success(f"✅ {q} (완료)")
            time.sleep(0.2)
        except Exception as e:
            st.error(f"❌ {q} 실패: {e}")

    if not results:
        st.error("⛔ 크롤링 실패 — 결과 없음")
        return False

    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
            for q, a in results:
                cur.execute(UPSERT_SQL, (q, a))
        conn.commit()
        st.success(f"✅ 총 {len(results)}건 DB 저장/갱신 완료")
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"⛔ DB 오류: {e}")
        return False
    finally:
        conn.close()

# ===== Streamlit UI =====
def show_faq_page():
    st.markdown('<div class="section-header"><h2>❓ 자주 묻는 질문 (FAQ)</h2></div>', unsafe_allow_html=True)

    faqs = load_faq_from_db()
    if not faqs:
        st.warning("아직 FAQ 데이터가 없습니다. 아래 버튼으로 크롤링을 먼저 실행하세요.")
        if st.button("🔄 크롤링 실행하기"):
            if crawl_and_update():
                safe_rerun()
        return

    for faq in faqs:
        with st.expander(faq["question"]):
            st.markdown(faq["answer"])

    st.markdown("---")
    st.markdown("### 📞 응급상황 연락처")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""**응급상황**
- 🚑 **119**: 소방서(구급·화재)
- 🚓 **112**: 경찰
- ⛑️ **1339**: 응급의료정보센터""")
    with c2:
        st.markdown("""**의료상담**
- 📱 **1577-1199**: 응급의료정보센터
- 🏥 **1644-9999**: 심평원
- 💊 **1661**: 약물중독정보센터""")
    with c3:
        st.markdown("""**기타 도움**
- 🆘 **1588-9191**: 생명의전화
- 👨‍⚕️ **129**: 보건복지상담
- 🔥 **1661-2119**: 소방안전신고""")

def main():
    st.title("🚒 119 긴급 FAQ 시스템")
    show_faq_page()

if __name__ == "__main__":
    main()
