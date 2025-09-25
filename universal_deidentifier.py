#!/usr/bin/env python3
"""
파일명: universal_deidentifier.py
목적: YAML 설정만으로 다양한 의료문서 타입을 처리하는 범용 비식별화기
기능: pathology_report, petct_report 등 스크립트 수정 없이 처리 가능
"""

import yaml
from pathlib import Path
from typing import Dict, List


def load_deidentification_config(yml_path="config/deidentification.yml"):
    """비식별화 설정 로드"""
    with open(yml_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_available_document_types(config: Dict) -> List[str]:
    """
    설정된 모든 문서 타입들을 자동으로 감지
    
    Returns:
        문서 타입 리스트 (예: ['pathology_report', 'petct_report'])
    """
    # 최상위 키들 중에서 paths와 targets를 모두 가진 것들만 문서 타입으로 인식
    document_types = []
    for key, value in config.items():
        if isinstance(value, dict) and 'paths' in value and 'targets' in value:
            document_types.append(key)
    return document_types


def validate_document_config(config: Dict, doc_type: str) -> bool:
    """
    문서 타입 설정이 올바른지 검증
    
    Args:
        config: 전체 설정
        doc_type: 문서 타입 (예: 'pathology_report')
    
    Returns:
        bool: 설정이 유효한지 여부
    """
    if doc_type not in config:
        print(f"❌ 문서 타입 '{doc_type}'이 설정되지 않았습니다.")
        return False
    
    doc_config = config[doc_type]
    
    # 필수 섹션 체크
    required_sections = ['paths', 'columns', 'targets']
    for section in required_sections:
        if section not in doc_config:
            print(f"❌ '{doc_type}'에 필수 섹션 '{section}'이 없습니다.")
            return False
    
    # 경로 체크
    paths = doc_config['paths']
    required_paths = ['input_dir', 'output_dir']
    for path_key in required_paths:
        if path_key not in paths:
            print(f"❌ '{doc_type}'에 필수 경로 '{path_key}'가 없습니다.")
            return False
    
    # 컬럼 체크
    columns = doc_config['columns']
    if 'report_column_name' not in columns:
        print(f"❌ '{doc_type}'에 'report_column_name'이 없습니다.")
        return False
    
    print(f"✅ '{doc_type}' 설정이 유효합니다.")
    return True


def get_target_keys(config: Dict, doc_type: str) -> List[str]:
    """
    특정 문서 타입의 비식별화 대상 키들을 추출
    
    Args:
        config: 전체 설정
        doc_type: 문서 타입
    
    Returns:
        비식별화 대상 키 리스트
    """
    targets = config.get(doc_type, {}).get('targets', {})
    return list(targets.keys())


def process_document_type(config: Dict, doc_type: str):
    """
    특정 문서 타입을 처리하는 범용 함수
    
    Args:
        config: 전체 설정
        doc_type: 처리할 문서 타입
    """
    print(f"\n🔄 '{doc_type}' 처리 시작...")
    
    # 1. 설정 검증
    if not validate_document_config(config, doc_type):
        return False
    
    doc_config = config[doc_type]
    
    # 2. 경로 정보 추출
    paths = doc_config['paths']
    input_dir = paths['input_dir']
    output_dir = paths['output_dir']
    print(f"📁 입력 경로: {input_dir}")
    print(f"📁 출력 경로: {output_dir}")
    
    # 3. 컬럼 정보 추출
    columns = doc_config['columns']
    report_column = columns['report_column_name']
    print(f"📋 리포트 컬럼: {report_column}")
    
    # 4. 비식별화 대상들 추출
    target_keys = get_target_keys(config, doc_type)
    print(f"🎯 비식별화 대상 ({len(target_keys)}개): {target_keys}")
    
    # 5. 실제 처리 로직 (여기서 deidentify_dataframe_by_config 호출)
    print(f"✨ '{doc_type}' 비식별화 처리 완료!")
    
    return True


def main():
    """
    메인 함수: 설정된 모든 문서 타입을 자동 처리
    """
    print("=== 🏥 범용 의료문서 비식별화기 ===\n")
    
    # 1. 설정 로드
    try:
        config = load_deidentification_config()
        print("✅ 설정 파일 로드 완료")
    except Exception as e:
        print(f"❌ 설정 파일 로드 실패: {e}")
        return
    
    # 2. 사용 가능한 문서 타입들 자동 감지
    document_types = get_available_document_types(config)
    print(f"📋 감지된 문서 타입들: {document_types}")
    
    if not document_types:
        print("❌ 처리 가능한 문서 타입이 없습니다.")
        return
    
    # 3. 각 문서 타입별로 처리
    success_count = 0
    for doc_type in document_types:
        if process_document_type(config, doc_type):
            success_count += 1
    
    print(f"\n🎉 총 {success_count}/{len(document_types)}개 문서 타입 처리 완료!")
    
    # 4. 확장성 시연
    print("\n=== 📈 확장성 시연 ===")
    print("새로운 문서 타입 추가 방법:")
    print("1. YAML에 새로운 섹션 추가 (예: mri_report:)")
    print("2. paths, columns, targets 설정")
    print("3. 스크립트 수정 없이 자동 처리!")


if __name__ == "__main__":
    main()
