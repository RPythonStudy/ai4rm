"""
파일명: src/deindentifier/pathology_report.py
목적: 병리보고서 비식별화
기능: 
  - 데이터프레임을 인자로 받아서 컬럼별로 정책에 따라 비식별화
  - 데이터프레임의 pathology_report 컬럼은 텍스트내부의 개인정보를 비식별화
  - config/deidentification.yml의 설정에서 검출정규식/비식별화정책/가명화정책/익명화정책을 참조
  - 비식별화가 완료되면 deid_파일명.xlsx로 저장
변경이력:
  - 2025-10-02: 병리보고서를 미리 컬럼으로 추출하였기에 보고서자체에서 파싱하는 함수는 불용처리 (BenKorea)
  - 2025-09-25: 데이터프레임으로 읽어오는 것을 범용함수로 변경 (BenKorea)
  - 2025-09-18: 최초 구현 (BenKorea)
"""

import os

import pandas as pd
import yaml

from common.excel_io import read_excels, save_excels
from common.get_cipher import get_cipher
from common.load_config import load_config
from common.logger import log_debug
from deidentifier.deid_utils import *


if __name__ == "__main__":

    config_pathology_report = load_config(yml_path="config/deidentification.yml", section="pathology_report")

    # 경로 설정
    paths = config_pathology_report.get("paths", {})
    input_dir = paths.get("input_dir", "")
    structured_dir = paths.get("structured_dir", "")
    output_dir = paths.get("output_dir", "")
    
    # 컬럼 매핑
    existing_column_mapping = config_pathology_report.get("existing_column_mapping", {})
    report_column = existing_column_mapping.get("report_column", None)

    # 비식별화 대상들 추출
    targets = config_pathology_report.get("targets", {})
    
    log_debug(f"[load_config] structured_dir: {structured_dir}, output_dir: {output_dir}")
    log_debug(f"[load_config] targets: {len(targets)}개")

    cipher_alphanumeric = get_cipher(alphabet_type="alphanumeric")
    cipher_numeric = get_cipher(alphabet_type="numeric")  # 숫자 전용 alphabet

    
    dfs = read_excels(structured_dir)
    deid_dfs = {}  # 최종 비식별화 결과
    
    for fname, df in dfs.items():
        log_debug(f"[처리 시작] 파일: {fname}")
        
        
        df = deidentify_columns(
            df = df,
            targets = targets,
            cipher_alphanumeric = cipher_alphanumeric,
            cipher_numeric = cipher_numeric
        )

        # # 2.2 리포트 컬럼 내부 텍스트 비식별화
        # df = deidentify_report_column(
        #     df = df,  # 이전 단계 결과를 사용
        #     report_column = report_column,
        #     targets = targets,
        #     cipher_alphanumeric = cipher_alphanumeric,
        #     cipher_numeric = cipher_numeric,
        # )

        dfs[fname] = df  # 원래 파일에 컬럼 추가

    save_excels(output_dir=output_dir, 
                dataframes_dict=dfs, 
                prefix="deid_")