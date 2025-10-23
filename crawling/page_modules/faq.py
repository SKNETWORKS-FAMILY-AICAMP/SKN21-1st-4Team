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
    "autocommit": False,   # 커밋은 수동으로
}

# ===== UPSERT만 사용 (CREATE TABLE 제거) =====
UPSERT_SQL = """
INSERT INTO emergency_faq (faq_question, faq_answer)
VALUES (%s, %s)
ON DUPLICATE KEY UPDATE faq_answer = VALUES(faq_answer);
"""

# ===== 질문 & 링크 =====
QUESTION_SOURCES = [
    { "q": "119 구급차 이용금액은 얼마인가요?",
      "url": "https://www.easylaw.go.kr/CSP/OnhunqueansInfoRetrieve.laf?onhunqnaAstSeq=86&onhunqueSeq=4729" },
    { "q": "응급처치시 알아두어야야 할 법적인 문제",
      "url": "https://www.safekorea.go.kr/idsiSFK/neo/sfk/cs/contents/prevent/SDIJK14433.html?cd1=33&cd2=999&menuSeq=128&pagecd=SDIJK144.33" },
    { "q": "119 구급신고 요령",
      "url": "https://www.nfa.go.kr/nfa/safetyinfo/emergencyservice/119emergencydeclaration/" },
    { "q": "119 구급차 도착 전 준비",
      "url": "https://www.nfa.go.kr/nfa/safetyinfo/emergencyservice/emergencydeclarationbefore/" },
    { "q": "긴급자동차(구급차) 특례",
      "url": "https://www.korea.kr/briefing/policyBriefingView.do?newsId=148883361&utm_source=chatgpt.com" },
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
        if not cells: 
            continue
        if not headers:
            headers = cells
            continue
        rows.append(cells)
    if not headers:
        return ""
    coln = len(headers)
    rows = [r + [""] * (coln - len(r)) for r in rows]
    md = []
    md.append("| " + " | ".join(headers) + " |")
    md.append("| " + " | ".join(["---"] * coln) + " |")
    for r in rows:
        md.append("| " + " | ".join(r[:coln]) + " |")
    return "\n".join(md)

def node_to_markdown(node: Tag) -> str:
    """선택 노드를 Markdown으로 변환"""
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
            src = "https://www.korea.kr" + src if src.startswith("/") else src
        return f"![{alt}]({src})" if src else (alt or "")
    return clean(node.get_text(" ", strip=True))

# =====================================================================
#                   ★★★ 질문 1 · 5 전용 '구간 크롤링' ★★★
# =====================================================================

# 1) 생활법령(질문 1): 지정한 div ID 5개 구간만 수집
def parse_q1_easylaw_segment(url: str) -> str:
    soup = get_soup(url)
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
    if not any(pieces):
        container = soup.select_one("#conBody, .conBody, #content, .contents, article") or soup
        txt = clean(container.get_text(" ", strip=True))
        pieces = [txt[:4000] + (" …" if len(txt) > 4000 else "")]
    body = "\n\n".join([p for p in pieces if p])
    return f"{body}\n\n[출처] {url}"

# 5) 정책브리핑(질문 5): 시작 p ~ (중간 table 포함) ~ 끝 p 범위 수집
def parse_q5_koreakr_segment(url: str) -> str:
    soup = get_soup(url)
    root = soup.select_one("div.view_con, div.article_area, #contents, #content, article") or soup
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
                md = node_to_markdown(cur)  # p/table/img/캡션 모두 처리
                if md:
                    collected.append(md)
            if cur == end_node:
                break
            cur = cur.find_next_sibling()
            if cur is None:
                break

    # 보완 수집(이미지/캡션/끝문단)
    if not collected:
        p1 = root.find("p", string=lambda s: s and start_text in s)
        if p1:
            collected.append(node_to_markdown(p1))
        tbl = root.find("table")
        if tbl:
            img = tbl.find("img")
            if img:
                collected.append(node_to_markdown(img))
            cap = tbl.find(class_="captions")
            if cap:
                collected.append(node_to_markdown(cap))
        p2 = root.find("p", string=lambda s: s and end_text in s)
        if p2:
            collected.append(node_to_markdown(p2))

    if not collected:
        text = clean(root.get_text(" ", strip=True))
        collected = [text[:1500] + (" …" if len(text) > 1500 else "")]

    body = "\n\n".join([c for c in collected if c])
    return f"{body}\n\n[출처] {url}"

# =====================================================================
#                        (2~4번) 기존 전용/간단 파서
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
        return parse_q1_easylaw_segment(url)   # 1번
    if "법적인 문제" in q_text:
        return parse_q2_safekorea(url)         # 2번
    if "구급신고 요령" in q_text:
        return parse_q3_nfa(url)               # 3번
    if "도착 전 준비" in q_text:
        return parse_q4_nfa(url)               # 4번
    if "긴급자동차" in q_text:
        return parse_q5_koreakr_segment(url)   # 5번
    # fallback
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

# ===== 크롤링 & 저장 (CREATE TABLE 제거) =====
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
            for q, a in results:
                cur.execute(UPSERT_SQL, (q, a))   # ★ CREATE TABLE 실행 안 함
        conn.commit()
        st.success(f"✅ 총 {len(results)}건 DB 저장/갱신 완료")
        return True
    except Exception as e:
        conn.rollback()
        # 테이블이 없다면 1146 오류가 날 수 있음
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
