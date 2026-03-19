import streamlit as st
from app.graph import app_graph

st.set_page_config(page_title="계약서 데이터 추출 엔진", layout="wide")

st.title("계약서 핵심 조항 및 의무 사항 추출 엔진")
st.markdown("복잡한 법률 계약서를 입력하면, AI가 Pydantic 스키마를 기반으로 메타데이터와 의무 조항을 구조화된 JSON으로 추출합니다.")
st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("계약서 원본 입력")
    raw_input = st.text_area(
        "계약서 텍스트를 붙여넣으십시오.",
        height=400,
        placeholder="소프트웨어 라이선스 계약서\n\n본 계약은 2026년 3월 19일, 글로벌테크(이하 '갑')와 로컬솔루션(이하 '을') 간에 체결된다..."
    )
    submit_btn = st.button("구조화된 데이터 추출 시작", type="primary", use_container_width=True)

with col2:
    st.subheader("추출된 계약 데이터 (JSON)")
    result_container = st.container(border=True)

    if submit_btn:
        if raw_input.strip():
            initial_state = {
                "raw_text": raw_input,
                "parsed_data": {},
                "error": ""
            }

            with st.spinner("계약서 분석 및 Pydantic 스키마 매핑 중..."):
                final_state = app_graph.invoke(initial_state)
            
            with result_container:
                if final_state.get("error"):
                    st.error(final_state.get("error"))
                else:
                    st.success("계약서 분석 및 구조화 완료")
                    st.json(final_state.get("parsed_data"))
        else:
            st.warning("계약서 원본 텍스트를 입력해주십시오.")