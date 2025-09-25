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

from common.excel_io import read_excels
from common.get_cipher import get_cipher
from common.logger import log_debug
from deidentifier.functions import *


def load_config_deidentification_pathology_report(yml_path="config/deidentification.yml"):
    with open(yml_path, encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f)
    log_debug(f"[load_config] path = {yml_path}")

    return yaml_config.get("pathology_report", {})


def save_deidentified_excels(output_dir, deid_dfs):
    """
    비식별화된 데이터프레임들을 output_dir에 deid_파일명.xlsx로 저장
    :param output_dir: 저장할 디렉토리 경로
    :param deid_dfs: {원본파일명: 비식별화된 데이터프레임} 딕셔너리
    """
    if not output_dir or not isinstance(output_dir, str) or output_dir.strip() == "":
        log_debug("[save_deidentified_excels] output_dir가 설정되지 않았습니다. config를 확인하세요.")
        return
    if not os.path.exists(output_dir):
        log_debug(f"[save_deidentified_excels] output_dir가 존재하지 않아 생성합니다: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
    for fname, deid_df in deid_dfs.items():
        base_fname = os.path.basename(fname)
        if base_fname.endswith('.xls'):
            base_fname = base_fname[:-4] + '.xlsx'
        deid_fname = os.path.join(output_dir, f"deid_{base_fname}")
        try:
            deid_df.to_excel(deid_fname, index=False)
            log_debug(f"[save_excels]: {deid_fname}")
        except Exception as e:
            log_debug(f"[save_excels] 실패: {deid_fname}: {e}")



if __name__ == "__main__":

    config_pathology_report = load_config_deidentification_pathology_report()

    anonymization_policy = config_pathology_report.get("anonymization_policy", "")
    input_dir = config_pathology_report.get("input_dir", "")
    output_dir = config_pathology_report.get("output_dir", "")
    patient_id_column_name = config_pathology_report.get("patient_id_column_name", "")
    result_date_column_name = config_pathology_report.get("result_date_column_name", "")
    pathology_id_column_name = config_pathology_report.get("pathology_id_column_name", "")
    pathology_report_column_name = config_pathology_report.get("pathology_report_column_name", "")

    cipher = get_cipher()
    cipher_digit = get_cipher(alphabet_type="digit")  # 숫자 전용 alphabet

    dfs = read_excels(input_dir)
    deid_dfs = {}  # 딕셔너리 미리 선언
    for fname, df in dfs.items():
        deid_df = deidentify_id_in_column(df, 
                                          patient_id_column_name, 
                                          config_pathology_report.get("patient_id", {}), 
                                          cipher_digit
                                          )

        # deid_df = deidentify_pathology_report_in_column(deid_df, 
        #                                                 config_pathology_report, 
        #                                                 cipher, 
        #                                                 cipher_digit
        #                                                 )
        deid_dfs[fname] = deid_df  # 결과를 딕셔너리에 저장

    save_deidentified_excels(output_dir, deid_dfs)