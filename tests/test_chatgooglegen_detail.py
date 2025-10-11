"""
ChatGoogleGenerativeAI 상세 테스트
목적: 인자 및 반환값 상세 분석
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from common.logger import log_info, log_debug

def test_detailed_usage():
    """상세 사용법 테스트"""
    
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    # 다양한 인자로 초기화
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        google_api_key=api_key,
        temperature=0.1,                    # 낮은 창의성
        max_output_tokens=100,              # 최대 100토큰
        top_p=0.8,                         # 상위 80% 확률 토큰만
        stop=[".", "!"],                   # 마침표나 감탄표에서 중단
        verbose=True                       # 상세 로그
    )
    
    # 호출 및 결과 분석
    result = llm.invoke("병리보고서를 요약해주세요")
    
    log_info(f"응답 내용: {result.content}")
    log_debug(f"응답 타입: {type(result)}")
    log_debug(f"메타데이터: {result.response_metadata}")
    
    # 속성 접근
    print(f"📝 생성된 텍스트: {result.content}")
    print(f"🔧 사용된 모델: {result.response_metadata.get('model_name', 'N/A')}")
    print(f"📊 토큰 사용량: {getattr(result, 'usage_metadata', {})}")
    
    return result

if __name__ == "__main__":
    test_detailed_usage()