"""
파일명: src/structuring/preliminary_pathology_metafier.py
목적: 병리보고서 구조화
기능: 
  - 데이터프레임을 인자로 받아서 병리보고서 컬럼을 구조화
  - config/deidentification.yml의 설정에서 구조화 규칙 참조
  - 구조화가 완료되면 structured_파일명.xlsx로 저장
변경이력:
  - 2025-09-29: 최초 구현 (BenKorea)
"""

import os

import pandas as pd
import yaml

from common.excel_io import read_excels, save_excels
from common.load_config import load_config
from common.logger import log_debug
from deidentifier.deid_utils import *


if __name__ == "__main__":

    config_pathology_report = load_config(yml_path="config/deidentification.yml", section="pathology_report")

    # 경로 설정
    paths = config_pathology_report.get("paths", {})
    input_dir = paths.get("input_dir", "")
    structured_dir = paths.get("structured_dir", "")

    # 컬럼 매핑
    existing_column_mapping = config_pathology_report.get("existing_column_mapping", {})
    report_column = existing_column_mapping.get("report_column", None)

    # non-target 추출
    non_targets = config_pathology_report.get("non_targets", {})
    non_targets_keys = list(non_targets.keys())

    # 타겟 추출
    targets = config_pathology_report.get("targets", {})
    targets_keys = list(targets.keys())
        

    dfs = read_excels(input_dir)
    for fname, df in dfs.items():
        for key in non_targets_keys:
            non_target_conf = non_targets.get(key, {})
            remove_non_targets(
                df=df,
                report_column=report_column,
                target_key=key,
                target_conf=non_target_conf
            )

        for key in targets_keys:
            target_conf = targets.get(key, {})
            extract_targets(
                df=df,
                report_column=report_column,
                target_key=key,
                target_conf=target_conf
            )
            dfs[fname] = df
            
        print("\n****************************************************************************************************************")  # 단순 줄바꿈 출력
        log_debug(f"[main] 삭제 후 전문:\n{df[report_column]}")
        
        validation_extraction(df=df, report_column=report_column, existing_column_mapping=existing_column_mapping)

    save_excels(output_dir=structured_dir, 
                dataframes_dict=dfs, 
                prefix="structured_")