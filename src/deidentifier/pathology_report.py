"""
파일명: src/deindentifier/pathology_report.py
목적: 병리보고서 비식별화
기능: 
  - 데이터프레임을 인자로 받아서 컬럼별로 정책에 따라 비식별화
  - 데이터프레임의 pathology_report 컬럼은 텍스트내부의 개인정보를 비식별화
  - config/deidentification.yml의 설정에서 검출정규식/비식별화정책/가명화정책/익명화정책을 참조
  - 비식별화가 완료되면 deid_파일명.xlsx로 저장
변경이력:
  - 2025-09-25: 데이터프레임으로 읽어오는 것을 범용함수로 변경 (BenKorea)
  - 2025-09-18: 최초 생성 (BenKorea)
"""

import os

import pandas as pd
import yaml

from common.excel_io import read_excels, save_deidentified_excels, save_structured_excels
from common.get_cipher import get_cipher
from common.logger import log_debug
from deidentifier.functions import *


def load_config_deidentification_pathology_report(yml_path="config/deidentification.yml"):
    with open(yml_path, encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f)
    log_debug(f"[load_config] path = {yml_path}")

    return yaml_config.get("pathology_report", {})



if __name__ == "__main__":

    config_pathology_report = load_config_deidentification_pathology_report()

    # 경로 설정 추출
    paths = config_pathology_report.get("paths", {})
    input_dir = paths.get("input_dir", "")
    output_dir = paths.get("output_dir", "")
    
    # 컬럼 설정 추출 (계층 구조 변경 반영)
    report_column_config = config_pathology_report.get("report_column", {})
    report_column_name = report_column_config.get("report_column_name", "pathology_report")
    existing_column_prefix = report_column_config.get("existing_column_prefix", "upto_policy")
    new_column_prefix = report_column_config.get("new_column_prefix", "upto_policy")
    column_name_policy = config_pathology_report.get("column_name_policy", "same_as_before")

    # 비식별화 대상들 추출
    targets = config_pathology_report.get("targets", {})
    
    log_debug(f"[load_config] input_dir: {input_dir}, output_dir: {output_dir}")
    log_debug(f"[load_config] report_column: {report_column_name}, targets: {len(targets)}개")

    cipher_alphanumeric = get_cipher(alphabet_type="alphanumeric")
    cipher_numeric = get_cipher(alphabet_type="numeric")  # 숫자 전용 alphabet

    # 구조화 설정 추출
    structuring_config = config_pathology_report.get("structuring", {})
    structured_output_dir = config_pathology_report.get("paths", {}).get("structured_output_dir", "")

    dfs = read_excels(input_dir)
    structured_dfs = {}  # 구조화 결과
    deid_dfs = {}  # 최종 비식별화 결과
    
    for fname, df in dfs.items():
        log_debug(f"[처리 시작] 파일: {fname}")
        
        # ========================================
        # STAGE 1: 구조화 (Structuring)
        # ========================================
        df = structure_pathology_reports(
            df=df,
            report_column_name=report_column_name,
            structuring_config=structuring_config
        )
        
        # 구조화 결과 저장 (중간 단계)
        if structured_output_dir:
            structured_dfs[fname] = df.copy()
        
        # ========================================  
        # STAGE 2: 비식별화 (De-identification)
        # ========================================
        
        # 2.1 개별 컬럼 비식별화
        df = deidentify_columns(
            df = df,
            targets = targets,
            cipher_alphanumeric = cipher_alphanumeric,
            cipher_numeric = cipher_numeric,
            column_name_policy = column_name_policy
        )

        # 2.2 리포트 컬럼 내부 텍스트 비식별화
        df = deidentify_report_column(
            df = df,  # 이전 단계 결과를 사용
            report_column_name = report_column_name,
            targets = targets,
            cipher_alphanumeric = cipher_alphanumeric,
            cipher_numeric = cipher_numeric,
            column_name_policy = column_name_policy,
            new_column_prefix = new_column_prefix
        )

        # 2.3 병리보고서 섹션 분리 (옵션) - 기존 로직
        separate_sections = report_column_config.get("separate_gross_and_diagnosis", False)
        if separate_sections:
            df = extract_pathology_sections(df, report_column_name, report_column_config)

        deid_dfs[fname] = df  # 최종 결과를 딕셔너리에 저장
        log_debug(f"[처리 완료] 파일: {fname}")

    # 구조화 결과 저장 (중간 단계 출력)
    if structured_dfs and structured_output_dir:
        save_deidentified_excels(structured_output_dir, structured_dfs)
        log_debug(f"[구조화 완료] 저장 경로: {structured_output_dir}")

    save_deidentified_excels(output_dir, deid_dfs)