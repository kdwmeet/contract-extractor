# Contract Obligation Tracker (계약서 핵심 조항 및 의무 사항 추출 엔진)

## 1. 프로젝트 개요

Contract Obligation Tracker는 수십 페이지에 달하는 복잡한 법률 계약서 텍스트를 분석하여, 계약의 핵심 메타데이터(당사자, 체결일, 만료일)와 주요 의무 조항, 위약금 내용 등을 구조화된 JSON 데이터로 자동 추출하는 파이프라인입니다.

자연어로 작성된 법률 문서에서 발생하는 모호성을 제거하고 사내 법무 및 영업 시스템과 즉시 연동하기 위해, LangChain의 `with_structured_output` API와 `Pydantic` 라이브러리를 적용했습니다. 이를 통해 AI는 날짜 포맷을 강제 통일하고, 자동 갱신 여부를 논리값(Boolean)으로 판별하며, 계약 당사자와 의무 사항을 독립된 배열(List) 형태로 정확히 분리하여 반환합니다.

## 2. 시스템 아키텍처



본 시스템은 Pydantic을 활용한 엄격한 스키마 검증을 기반으로 작동합니다.

1. **Schema Definition:** `Pydantic`을 활용하여 계약서 메타데이터(제목, 체결일, 만료일, 자동 갱신 여부), 당사자 정보(이름, 역할), 의무 사항(이행 당사자, 상세 내용, 기한)에 대한 엄격한 데이터 클래스와 계층 구조를 정의합니다.
2. **Input Processing:** 사용자가 검토가 필요한 법률 계약서 원본 텍스트를 입력합니다.
3. **Structured Extraction & Inference:** LLM(gpt-5-mini)이 문맥을 분석하여 정보를 추출합니다. "서면 통지가 없는 한 연장된다"와 같은 자연어 문맥을 `True/False` 논리값으로 추론하고, 명시되지 않은 체결일이나 만료일을 문맥에 맞게 'YYYY-MM-DD' 형식으로 계산 및 정제합니다. 정보가 전혀 없는 항목은 `null`로 안전하게 처리합니다.
4. **Validation & Output:** 스키마 검증을 완벽히 통과한 데이터만이 관제 대시보드에 JSON 형태로 렌더링되며, 사내 데이터베이스나 알림 시스템(예: 만료 30일 전 알림)에 연동 가능한 상태로 출력됩니다.

## 3. 기술 스택

* **Language:** Python 3.10+
* **Package Manager:** uv
* **LLM:** OpenAI gpt-5-mini (법률 문맥 추론 및 구조화된 데이터 추출 수행)
* **Data Validation:** Pydantic (v2)
* **Orchestration:** LangGraph, LangChain (langchain_core)
* **Web Framework:** Streamlit

## 4. 프로젝트 구조

```text
contract-extractor/
├── .env                  # OpenAI API 키 설정
├── requirements.txt      # 의존성 패키지 목록
├── main.py               # Streamlit 기반 실시간 계약서 분석 관제 UI
└── app/
    ├── __init__.py
    └── graph.py          # Pydantic 스키마 정의 및 구조화된 추출 노드 구현
```

## 5. 설치 및 실행 가이드
### 5.1. 환경 변수 설정
프로젝트 루트 경로에 .env 파일을 생성하고 API 키를 입력하십시오.

```Ini, TOML
OPENAI_API_KEY=sk-your-api-key-here
```
### 5.2. 의존성 설치 및 앱 실행
독립된 가상환경을 구성하고 애플리케이션을 구동합니다.

```Bash
uv venv
uv pip install -r requirements.txt
uv run streamlit run main.py
```
## 6. 테스트 시나리오 및 검증 방법
애플리케이션 구동 후, NDA(비밀유지계약서)나 라이선스 계약서 원본 텍스트를 입력하여 다음 사항을 검증합니다.

* **논리값(Boolean) 변환 검증**: 원문의 자동 연장 조항을 AI가 문맥적으로 분석하여 is_auto_renewal 필드를 True로 정확히 평가하는지 확인합니다.

* **날짜 포맷 정제**: "체결일로부터 1년간 유효"와 같은 문장을 해석하여, 명시된 체결일 기준으로 정확히 1년 뒤의 날짜가 expiration_date 필드에 'YYYY-MM-DD' 형식으로 추론되어 기입되는지 확인합니다.

* **계층 구조 분리**: parties 배열과 obligations 배열이 각각의 스키마 구조에 맞게 논리적으로 분리되어 누락 없이 추출되었는지 점검합니다.

## 7. 실행 화면