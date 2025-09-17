# src/pseudonymizer/pseudonymizer_pathology.py
# 엑셀 파일용
# last modified: 2025-09-17

import yaml
import os
import pandas as pd
from common.logger import log_debug
from deidentifier.deidentify import *

def load_config_deidentification_pathology_report(yml_path="config/deidentification.yml"):
    with open(yml_path, encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f)
    return yaml_config.get("pathology_report", {})


def find_excel_files(root_dir):
    excel_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.endswith('.xls') or fname.endswith('.xlsx'):
                excel_files.append(os.path.join(dirpath, fname))
    return excel_files


def read_excel_files(file_list):
    dfs = {}
    for f in file_list:
        try:
            df = pd.read_excel(f)
            dfs[f] = df
            log_debug(f"[OK] {f}: shape={df.shape}")
        except Exception as e:
            log_debug(f"[FAIL] {f}: {e}")
    return dfs


if __name__ == "__main__":

    config_pathology_report = load_config_deidentification_pathology_report()

    input_dir = config_pathology_report.get("input_dir", "")
    output_dir = config_pathology_report.get("output_dir", "")
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    patient_id_column_name = config_pathology_report.get("patient_id_column_name", "")
    result_date_column_name = config_pathology_report.get("result_date_column_name", "")
    pathology_id_column_name = config_pathology_report.get("pathology_id_column_name", "")
    pathology_report_column_name = config_pathology_report.get("pathology_report_column_name", "")

    excel_files = find_excel_files(input_dir)
    log_debug(f"총 {len(excel_files)}개 엑셀파일 발견")
    dfs = read_excel_files(excel_files)

    patient_id_conf = config_pathology_report.get("patient_id", {})
    result_date_conf = config_pathology_report.get("result_date", {})

    for fname, df in dfs.items():
        deid_df = deidentify_patient_id_in_column(df, patient_id_column_name, patient_id_conf)
        log_debug(f"[가명화] {fname}: patient_id preview → {deid_df[patient_id_column_name].head().tolist()}")

        deid_df = deidentify_result_date_in_column(deid_df, result_date_column_name, result_date_conf)
        log_debug(f"[가명화] {fname}: result_date preview → {deid_df[result_date_column_name].head().tolist()}")

        base_fname = os.path.basename(fname)
        if base_fname.endswith('.xls'):
            base_fname = base_fname[:-4] + '.xlsx'
            deid_fname = os.path.join(output_dir, f"deid_{base_fname}")
        try:
            deid_df.to_excel(deid_fname, index=False)
            log_debug(f"[저장] {deid_fname} (shape={deid_df.shape})")
        except Exception as e:
            log_debug(f"[저장실패] {deid_fname}: {e}")
