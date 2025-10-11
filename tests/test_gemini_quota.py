"""
Gemini API 사용량 및 할당량 확인
목적: AI4RM 의료데이터 플랫폼 API 사용량 모니터링
설명: ISMS-P 준수 - 극단적 간결화 및 디버그 친화적
변경이력:
  - 2025-10-11: 의료데이터 플랫폼 사용량 모니터링 (BenKorea)
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from common.logger import log_info, log_warn, log_error

def test_quota_status():
    """API 할당량 및 제한 상태 확인"""
    
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        log_error("GEMINI_API_KEY 환경변수 없음")
        print("❌ .env 파일에서 GEMINI_API_KEY를 설정하세요")
        return False
    
    print("🔍 Gemini API 사용량 확인 시작...")
    log_info("API 사용량 확인 시작")
    
    # 1. 기본 연결 테스트
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=api_key,
            temperature=0.0
        )
        
        start_time = time.time()
        result = llm.invoke("Test")
        response_time = time.time() - start_time
        
        print(f"✅ 기본 연결: 정상 ({response_time:.2f}초)")
        log_info(f"기본 연결 성공: {response_time:.2f}초")
        
    except Exception as e:
        error_msg = str(e).lower()
        
        # 할당량 초과 에러 패턴 분석
        if any(keyword in error_msg for keyword in ['quota', 'limit', 'rate', '429']):
            print("🚫 할당량 초과 또는 속도 제한")
            log_warn(f"할당량 문제: {e}")
            return analyze_quota_error(error_msg)
        else:
            print(f"❌ 연결 실패: {e}")
            log_error(f"연결 실패: {e}")
            return False
    
    # 2. 연속 호출 테스트 (RPM 제한 확인)
    print("\n🔄 연속 호출 테스트 (RPM 제한 확인)...")
    rpm_results = []
    
    for i in range(3):
        try:
            start_time = time.time()
            result = llm.invoke(f"Test {i+1}")
            response_time = time.time() - start_time
            
            rpm_results.append({
                'call': i+1,
                'success': True,
                'time': response_time,
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
            
            print(f"  호출 {i+1}: ✅ ({response_time:.2f}초)")
            time.sleep(1)  # 1초 간격
            
        except Exception as e:
            rpm_results.append({
                'call': i+1,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
            
            print(f"  호출 {i+1}: ❌ {str(e)[:50]}...")
            break
    
    # 3. 큰 요청 테스트 (토큰 제한 확인)
    print("\n📝 토큰 제한 테스트...")
    try:
        long_prompt = "병리보고서를 상세히 분석해주세요. " * 100  # 긴 프롬프트
        result = llm.invoke(long_prompt)
        
        token_count = len(result.content.split())
        print(f"✅ 토큰 테스트: {token_count}개 토큰 생성")
        log_info(f"토큰 테스트 성공: {token_count}개")
        
    except Exception as e:
        print(f"⚠️  토큰 제한: {str(e)[:100]}...")
        log_warn(f"토큰 제한 감지: {e}")
    
    # 결과 요약
    print("\n📊 사용량 확인 결과:")
    print(f"   기본 연결: ✅ 정상")
    print(f"   연속 호출: {len([r for r in rpm_results if r['success']])}/3 성공")
    print(f"   토큰 처리: 확인 완료")
    
    log_info("API 사용량 확인 완료")
    return True

def analyze_quota_error(error_msg):
    """할당량 에러 상세 분석"""
    
    quota_info = {
        'daily_limit': 'quota' in error_msg and 'daily' in error_msg,
        'rate_limit': 'rate' in error_msg or '429' in error_msg,
        'monthly_limit': 'monthly' in error_msg or 'billing' in error_msg,
        'token_limit': 'token' in error_msg or 'length' in error_msg
    }
    
    print("\n🚫 할당량 제한 상세:")
    
    if quota_info['daily_limit']:
        print("   📅 일일 한도 초과 (1,500 RPD)")
        print("   💡 해결: 24시간 후 재시도")
        
    if quota_info['rate_limit']:
        print("   ⏱️  속도 제한 (15 RPM)")
        print("   💡 해결: 요청 간격 늘리기")
        
    if quota_info['monthly_limit']:
        print("   📆 월간 한도 초과")
        print("   💡 해결: 유료 플랜 업그레이드")
        
    if quota_info['token_limit']:
        print("   📝 토큰 한도 초과")
        print("   💡 해결: 입력/출력 길이 줄이기")
    
    log_warn(f"할당량 제한 분석: {quota_info}")
    return quota_info

def estimate_remaining_quota():
    """간접적 할당량 추정"""
    
    print("\n🔢 간접적 할당량 추정...")
    
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        google_api_key=api_key,
        temperature=0.0,
        max_output_tokens=10  # 최소 토큰으로 테스트
    )
    
    success_count = 0
    max_attempts = 5
    
    print(f"   {max_attempts}회 연속 호출로 가용성 추정...")
    
    for i in range(max_attempts):
        try:
            result = llm.invoke(f"Hi {i}")
            success_count += 1
            print(f"   {i+1}/{max_attempts}: ✅")
            time.sleep(0.5)  # 속도 제한 고려
            
        except Exception as e:
            print(f"   {i+1}/{max_attempts}: ❌ ({str(e)[:30]}...)")
            break
    
    # 추정 결과
    quota_health = (success_count / max_attempts) * 100
    
    print(f"\n📈 추정 할당량 상태:")
    print(f"   성공률: {success_count}/{max_attempts} ({quota_health:.0f}%)")
    
    if quota_health >= 80:
        print(f"   상태: 🟢 양호 (충분한 할당량)")
    elif quota_health >= 50:
        print(f"   상태: 🟡 주의 (제한 접근 중)")
    else:
        print(f"   상태: 🔴 경고 (할당량 부족)")
    
    log_info(f"할당량 추정: {quota_health:.0f}% 가용")
    return quota_health

if __name__ == "__main__":
    print("🔍 AI4RM Gemini API 사용량 모니터링")
    print("="*50)
    
    # 기본 할당량 확인
    if test_quota_status():
        # 간접적 할당량 추정
        estimate_remaining_quota()
    
    print("\n💡 직접 확인 방법:")
    print("   🌐 Google AI Studio: https://aistudio.google.com")
    print("   📊 사용량 대시보드에서 실시간 확인 가능")