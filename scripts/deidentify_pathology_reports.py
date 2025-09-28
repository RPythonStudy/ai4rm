#!/usr/bin/env python3
"""
병리보고서 비식별화 전용 스크립트
Path: scripts/deidentify_pathology_reports.py
Purpose: 
    - 2단계: 구조화된 데이터 → 비식별화된 데이터
    - 구조화 결과를 입력으로 받아 비식별화만 수행
    - HIPAA/개인정보보호법 준수
"""

import sys
import os
import pandas as pd

# 프로젝트 경로 설정
sys.path.append('/home/ben/projects/ai4rm/src')

from common.logger import log_info, log_error
from deidentifier.functions import (
    deidentify_columns, 
    deidentify_report_column,
    load_config_deidentification_pathology_report
)
from common.excel_io import load_excel_files
from common.get_cipher import get_cipher

def main():
    """병리보고서 비식별화 메인 함수"""
    
    try:
        # 설정 로드
        config = load_config_deidentification_pathology_report()
        pathology_config = config.get('pathology_report', {})
        
        # 경로 설정
        structured_input_dir = pathology_config.get('paths', {}).get('structured_output_dir', '')
        final_output_dir = pathology_config.get('paths', {}).get('output_dir', '')
        
        log_info(f"비식별화 시작: {structured_input_dir} → {final_output_dir}")
        
        # 암호화 키 준비
        cipher_alphanumeric = get_cipher(alphabet_type="alphanumeric")
        cipher_numeric = get_cipher(alphabet_type="numeric")
        
        # 구조화된 파일 로드
        structured_files = load_excel_files(structured_input_dir)
        deidentified_results = {}
        
        # 각 파일에 대해 비식별화 수행
        for filename, df in structured_files.items():
            log_info(f"비식별화 처리: {filename}")
            
            # 비식별화 실행
            deidentified_df = deidentify_structured_data(
                df, 
                pathology_config,
                cipher_alphanumeric,
                cipher_numeric
            )
            
            deidentified_results[filename] = deidentified_df
            log_info(f"비식별화 완료: {filename} ({len(deidentified_df)} 건)")
        
        # 최종 결과 저장
        save_deidentified_results(deidentified_results, final_output_dir)
        log_info("전체 비식별화 작업 완료")
        
    except Exception as e:
        log_error(f"비식별화 처리 오류: {e}")
        raise

def deidentify_structured_data(df: pd.DataFrame, config: dict, cipher_alpha, cipher_num) -> pd.DataFrame:
    """구조화된 데이터의 비식별화 수행"""
    
    targets = config.get('targets', {})
    column_mapping = config.get('column_mapping', {})
    
    # 1. 개별 컬럼 비식별화
    result_df = deidentify_columns(
        df=df,
        targets=targets,
        cipher_alphanumeric=cipher_alpha,
        cipher_numeric=cipher_num,
        column_name_policy=column_mapping.get('existing_column_prefix', 'upto_policy')
    )
    
    # 2. 리포트 컬럼 내부 텍스트 비식별화 (필요시)
    report_column_name = column_mapping.get('source_column_name', 'pathology_report')
    if report_column_name in result_df.columns:
        result_df = deidentify_report_column(
            df=result_df,
            report_column_name=report_column_name,
            targets=targets,
            cipher_alphanumeric=cipher_alpha,
            cipher_numeric=cipher_num,
            column_name_policy=column_mapping.get('existing_column_prefix', 'upto_policy'),
            new_column_prefix=column_mapping.get('new_column_prefix', 'upto_policy')
        )
    
    return result_df

def save_deidentified_results(results_dict: dict, output_dir: str):
    """비식별화 결과 저장"""
    os.makedirs(output_dir, exist_ok=True)
    
    for filename, df in results_dict.items():
        # 'structured_' 접두사 제거하고 'deidentified_' 추가
        clean_filename = filename.replace('structured_', '')
        output_path = os.path.join(output_dir, f"deidentified_{clean_filename}")
        df.to_excel(output_path, index=False)
        log_info(f"저장 완료: {output_path}")

if __name__ == "__main__":
    main()
