#!/usr/bin/env python3
"""
개선된 deidentification.yml의 키 추출 및 직관성 테스트
"""
import yaml

def test_key_extraction():
    # YAML 파일 로드
    with open("config/deidentification.yml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # targets 키들 추출
    targets = config["pathology_report"]["targets"]
    target_keys = list(targets.keys())

    print("=== 💡 개선된 비식별화 대상 키들 ===")
    print(f"총 {len(target_keys)}개의 대상:")
    
    # 카테고리별로 분류
    patient_info = [k for k in target_keys if k.startswith('patient_')]
    date_info = [k for k in target_keys if 'date' in k]
    id_info = [k for k in target_keys if 'id' in k]
    physician_info = [k for k in target_keys if 'physician' in k]
    others = [k for k in target_keys if k not in patient_info + date_info + id_info + physician_info]
    
    print(f"\n📋 환자 정보 ({len(patient_info)}개):")
    for key in patient_info:
        print(f"   • {key}")
    
    print(f"\n📅 날짜 정보 ({len(date_info)}개):")
    for key in date_info:
        print(f"   • {key}")
        
    print(f"\n🆔 ID 정보 ({len(id_info)}개):")
    for key in id_info:
        print(f"   • {key}")
        
    print(f"\n👨‍⚕️ 의료진 정보 ({len(physician_info)}개):")
    for key in physician_info:
        print(f"   • {key}")
        
    print(f"\n🔧 기타 ({len(others)}개):")
    for key in others:
        print(f"   • {key}")

    print(f"\n=== 🎯 .keys() 메서드 활용 예시 ===")
    print("# Python 코드에서 사용:")
    print("targets = config['pathology_report']['targets']")
    print("target_keys = list(targets.keys())")
    print(f"# 결과: {target_keys[:3]}... (총 {len(target_keys)}개)")
    
    return target_keys

if __name__ == "__main__":
    target_keys = test_key_extraction()
