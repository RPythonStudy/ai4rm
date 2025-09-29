"""
파일명: src/structuring/pathology_structurer.py
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
from deidentifier.functions import *


if __name__ == "__main__":

    config_pathology_report = load_config(yml_path="config/deidentification.yml", section="pathology_report")

    # 경로 설정
    paths = config_pathology_report.get("paths", {})
    input_dir = paths.get("input_dir", "")
    structured_dir = paths.get("structured_dir", "")

    # 컬럼 매핑
    column_mapping = config_pathology_report.get("column_mapping", {})
    report_column_name = column_mapping.get("report_column_name", None)

    # 구조화 섹션 추출
    targets = config_pathology_report.get("targets", {})
    targets_keys = list(targets.keys())
    
    log_debug(f"[load_config] input_dir: {input_dir}, structured_dir: {structured_dir}")
    log_debug(f"[load_config] report_column: {report_column_name}, sections: {len(targets_keys)}개")


    dfs = read_excels(input_dir)

    structured_dfs = {}  # 구조화 결과

    for fname, df in dfs.items():
        for key in targets_keys:
            target_conf = targets.get(key, {})
            structuralization_policy = target_conf.get("structuralization_policy", "extraction")
            if structuralization_policy == "remove":
                remove_target_from_report(df=df,
                                          report_column_name=report_column_name,
                                          target_key=key,
                                          target_conf=target_conf
                                          )

            # # section별로 컬럼 추가 또는 삭제
            # df = extract_section_to_column(
            #     df,
            #     report_column_name,
            #     key,
            #     reg_exp,
            #     policy
            #     )
            dfs[fname] = df  # 원래 파일에 컬럼 추가

    save_excels(structured_dir, dfs)