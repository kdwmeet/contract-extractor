from typing import TypedDict, List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END

load_dotenv()

# Pydantic 스키마 정의
class Party(BaseModel):
    """계약 당사자 정보"""
    name: str = Field(description="계약 당사자 (기업명 또는 인명)")
    role: str = Field(description="계약상 역할 (예: 갑, 을, 공급자, 구매자, 라이선서 등)")

class Obligation(BaseModel):
    """주요 의무 사항"""
    responsible_party: str = Field(description="의무를 이해해야 하는 당사자명")
    description: str = Field(description="의무 조항 상세 내용 요약")
    deadline: Optional[str] = Field(description="이행 기한 (YYYY-MM-DD 형식), 명시되지 않은 경우 null")

class ContractSchema(BaseModel):
    """전체 계약서 추출 구조"""
    contract_title: str = Field(description="계약서의 공식 제목")
    execution_date: Optional[str] = Field(description="계약 체결일 (YYYY-MM-DD 형식), 없으면 null")
    expiration_date: Optional[str] = Field(description="계약 만료일 (YYYY-MM-DD 형식), 없으면 null")
    is_auto_renewal: bool = Field(description="자동 갱신 조항이 포함되어 있으면 True, 없으면 False")
    parties: List[Party] = Field(description="계약 당사자 목록")
    obligations: List[Obligation] = Field(description="당사자들의 주요 의무 및 역할 목록")
    penalty_clause: Optional[str] = Field(description="위약금, 지연 이자, 또는 손해배상 조항 요약, 없으면 null")

# 상태 정의
class ContractState(TypedDict):
    raw_text: str               # 원본 계약서 텍스트
    parsed_data: dict           # Pydantic을 통해 구조화된 추출 데이터
    error: str                  # 파싱 실패 시 에러 메시지

# 노드 구현
def extract_contract_node(state: ContractState):
    """원본 계약서 텍스트에서 지정된 스키마에 맞춰 핵심 정보를 추출합니다."""
    llm = ChatOpenAI(model="gpt-5-mini", reasoning_effort="low")

    # LLM에 Pydantic 스키마를 바인딩
    structured_llm = llm.with_structured_output(ContractSchema)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 기업 법무팀의 시니어 AI 변호사입니다.
제공된 법률 계약서 텍스트를 분석하여, 요청된 데이터 스키마 규격에 완벽하게 일치하도록 핵심 정보를 추출하십시오.
- 날짜는 반드시 'YYYY-MM-DD' 형식으로 변환하십시오.
- 자동 갱신 여부는 문맥을 파악하여 정확한 Boolean 값(True/False)으로 출력하십시오.
- 정보가 누락된 항목은 지어내지 말고 null 처리하십시오."""),
        ("user", "계약서 원본:\n{raw_text}")
    ])
    
    chain = prompt | structured_llm

    try:
        result: ContractSchema = chain.invoke({"raw_text": state.get("raw_text", "")})
        return {"parsed_data": result.model_dump(), "error": ""}
    except Exception as e:
        return {"error": f"계약서 구조화 추출 실패: {str(e)}"}

# 그래프 조립 및 컴파일
workflow = StateGraph(ContractState)

workflow.add_node("extract_contract", extract_contract_node)

workflow.add_edge(START, "extract_contract")
workflow.add_edge("extract_contract", END)

app_graph = workflow.compile()