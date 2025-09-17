# src/pseudonymizer/pseudonymizer_pathology.py
# 엑셀 파일용
# last modified: 2025-09-17

import yaml
import os
import pandas as pd
from common.logger import log_debug
from deidentifier.deidentify import *

# ------------------------
# YAML 설정 로딩
# ------------------------
def load_config_pseudonymization_pathology_report(yml_path="config/pseudonymization.yml"):
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

    config_pathology_report = load_config_pseudonymization_pathology_report()
    input_dir = config_pathology_report.get("input_dir", "")
    output_dir = config_pathology_report.get("output_dir", "")
    excel_files = find_excel_files(input_dir)
    log_debug(f"총 {len(excel_files)}개 엑셀파일 발견")
    dfs = read_excel_files(excel_files)

    # patient_id 컬럼 가명화 적용 예시
    patient_id_conf = config_pathology_report.get("patient_id", {})
    # output_dir 없으면 생성
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    for fname, df in dfs.items():
        if "patient_id" in df.columns:
            df_pseudo = deidentify_patient_id_in_df(df, "patient_id", patient_id_conf)
            log_debug(f"[가명화] {fname}: patient_id preview → {df_pseudo['patient_id'].head().tolist()}")

            # 저장 경로 생성 및 확장자 처리
            base_fname = os.path.basename(fname)
            if base_fname.endswith('.xls'):
                base_fname = base_fname[:-4] + '.xlsx'
            deid_fname = os.path.join(output_dir, f"deidentified_{base_fname}")
            try:
                df_pseudo.to_excel(deid_fname, index=False)
                log_debug(f"[저장] {deid_fname} (shape={df_pseudo.shape})")
            except Exception as e:
                log_debug(f"[저장실패] {deid_fname}: {e}")
