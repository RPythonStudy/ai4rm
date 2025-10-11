"""
파일명: test_gemini_api.py
목적: Gemini API 연결 및 사용량 제한 테스트
설명: 극단적으로 간결한 API 연결 검증 도구
변경이력:
  - 2025-10-11: 극단적 간결화 버전 생성 (BenKorea)
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from common.logger import log_info, log_error

def test_gemini_api():
    """Gemini API 연결 테스트"""
    
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        log_error("GEMINI_API_KEY 환경변수 없음")
        return False
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        google_api_key=api_key,
        temperature=0.0
    )
    
    result = llm.invoke("Hello")
    
    log_info(f"[test_gemini_api] API 연결 성공: {result.content[:30]}...")
    print(f"✅ API 정상: {result.content[:50]}...")

    return True

if __name__ == "__main__":
    test_gemini_api()