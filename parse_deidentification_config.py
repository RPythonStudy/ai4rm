#!/usr/bin/env python3
"""
파일명: parse_deidentification_config.py
목적: 개선된 deidentification.yml 구조에서 비식별화 대상 키들을 추출하는 예제
"""

import yaml
from pathlib import Path

def load_deidentification_config(yml_path="config/deidentification.yml"):
    """
    개선된 구조의 deidentification.yml 파일을 로드
    """
    with open(yml_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def get_deidentification_targets_list(config, document_type="pathology_report"):
    """
    비식별화 대상 키들을 리스트로 추출
    
    Args:
        config: YAML에서 로드한 설정
        document_type: 문서 타입 (예: pathology_report)
    
    Returns:
        list: 비식별화 대상 키들의 리스트
    """
    targets = config.get(document_type, {}).get("targets", {})
    return list(targets.keys())


def get_paths_config(config, document_type="pathology_report"):
    """
    경로 설정을 추출
    """
    return config.get(document_type, {}).get("paths", {})


def get_columns_config(config, document_type="pathology_report"):
    """
    컬럼 매핑 설정을 추출
    """
    return config.get(document_type, {}).get("columns", {})


def get_target_config(config, target_name, document_type="pathology_report"):
    """
    특정 비식별화 대상의 설정을 추출
    
    Args:
        config: YAML 설정
        target_name: 대상 이름 (예: 'patient_name', 'printer_id')
        document_type: 문서 타입
    
    Returns:
        dict: 해당 대상의 비식별화 정책 설정
    """
    targets = config.get(document_type, {}).get("targets", {})
    return targets.get(target_name, {})


def filter_targets_by_policy(config, policy_type, policy_value, document_type="pathology_report"):
    """
    특정 정책으로 필터링된 비식별화 대상들을 반환
    
    Args:
        config: YAML 설정
        policy_type: 정책 타입 ('deidentification_policy', 'pseudonymization_policy', 'anonymization_policy')
        policy_value: 정책 값 ('pseudonymization', 'anonymization', 'fpe', 'masking' 등)
        document_type: 문서 타입
    
    Returns:
        list: 해당 정책을 사용하는 대상들의 리스트
    """
    targets = config.get(document_type, {}).get("targets", {})
    filtered_targets = []
    
    for target_name, target_config in targets.items():
        if target_config.get(policy_type) == policy_value:
            filtered_targets.append(target_name)
    
    return filtered_targets


def main():
    """
    사용 예제
    """
    print("=== 개선된 deidentification.yml 파싱 예제 ===\n")
    
    # 1. 설정 로드
    config = load_deidentification_config()
    print("1. 설정 파일 로드 완료\n")
    
    # 2. 경로 설정 확인
    paths = get_paths_config(config)
    print("2. 경로 설정:")
    for key, value in paths.items():
        print(f"   {key}: {value}")
    print()
    
    # 3. 컬럼 매핑 설정 확인
    columns = get_columns_config(config)
    print("3. 컬럼 매핑 설정:")
    for key, value in columns.items():
        print(f"   {key}: {value}")
    print()
    
    # 4. 모든 비식별화 대상 키 리스트 추출
    targets_list = get_deidentification_targets_list(config)
    print("4. 모든 비식별화 대상 키들:")
    print(f"   총 {len(targets_list)}개: {targets_list}")
    print()
    
    # 5. 정책별 필터링 예제
    print("5. 정책별 필터링:")
    
    # 가명화 정책을 사용하는 대상들
    pseudonymization_targets = filter_targets_by_policy(config, "deidentification_policy", "pseudonymization")
    print(f"   가명화 대상 ({len(pseudonymization_targets)}개): {pseudonymization_targets}")
    
    # 익명화 정책을 사용하는 대상들
    anonymization_targets = filter_targets_by_policy(config, "deidentification_policy", "anonymization")
    print(f"   익명화 대상 ({len(anonymization_targets)}개): {anonymization_targets}")
    
    # FPE를 사용하는 대상들
    fpe_targets = filter_targets_by_policy(config, "pseudonymization_policy", "fpe")
    print(f"   FPE 사용 대상 ({len(fpe_targets)}개): {fpe_targets}")
    
    # 마스킹을 사용하는 대상들
    masking_targets = filter_targets_by_policy(config, "anonymization_policy", "masking")
    print(f"   마스킹 사용 대상 ({len(masking_targets)}개): {masking_targets}")
    print()
    
    # 6. 특정 대상의 상세 설정 확인
    print("6. 특정 대상 설정 예제:")
    patient_name_config = get_target_config(config, "patient_name")
    print(f"   patient_name 설정: {patient_name_config}")
    print()


if __name__ == "__main__":
    main()
