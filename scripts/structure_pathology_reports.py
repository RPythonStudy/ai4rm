#!/usr/bin/env python3
"""
병리보고서 구조화 전용 스크립트
Path: scripts/structure_pathology_reports.py
Purpose: 
    - 1단계: 비정형 병리보고서 → 정형 데이터 구조화
    - 비식별화 없이 순수 구조화만 수행
    - 중간 결과 저장으로 검증 가능
"""

import sys
import os
import pandas as pd
from pathlib import Path

# 프로젝트 경로 설정
sys.path.append('/home/ben/projects/ai4rm/src')

from common.logger import log_info, log_error
from deidentifier.functions import structure_pathology_reports, load_config_deidentification_pathology_report
from common.excel_io import load_excel_files

def main():
    """병리보고서 구조화 메인 함수"""
    
    try:
        # 설정 로드
        config = load_config_deidentification_pathology_report()
        pathology_config = config.get('pathology_report', {})
        
        # 경로 설정
        input_dir = pathology_config.get('paths', {}).get('input_dir', '')
        structured_output_dir = pathology_config.get('paths', {}).get('structured_output_dir', '')
        
        log_info(f"구조화 시작: {input_dir} → {structured_output_dir}")
        
        # 입력 파일 로드
        input_files = load_excel_files(input_dir)
        structured_results = {}
        
        # 각 파일에 대해 구조화 수행
        for filename, df in input_files.items():
            log_info(f"구조화 처리: {filename}")
            
            # 구조화 실행 (비식별화 없음)
            structured_df = structure_pathology_reports(df, config)
            structured_results[filename] = structured_df
            
            log_info(f"구조화 완료: {filename} ({len(structured_df)} 건)")
        
        # 구조화 결과 저장
        save_structured_results(structured_results, structured_output_dir)
        log_info("전체 구조화 작업 완료")
        
    except Exception as e:
        log_error(f"구조화 처리 오류: {e}")
        raise

def save_structured_results(results_dict: dict, output_dir: str):
    """구조화 결과 저장"""
    os.makedirs(output_dir, exist_ok=True)
    
    for filename, df in results_dict.items():
        output_path = os.path.join(output_dir, f"structured_{filename}")
        df.to_excel(output_path, index=False)
        log_info(f"저장 완료: {output_path}")

if __name__ == "__main__":
    main()
