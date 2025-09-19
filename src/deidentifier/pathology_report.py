# src/pseudonymizer/pathology_report.py
# last modified: 2025-09-18

import yaml
import os
import pandas as pd
from common.logger import log_debug
from common.get_cipher import get_cipher
from deidentifier.functions import *

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
    patient_id_column_name = config_pathology_report.get("patient_id_column_name", "")
    result_date_column_name = config_pathology_report.get("result_date_column_name", "")
    pathology_id_column_name = config_pathology_report.get("pathology_id_column_name", "")
    pathology_report_column_name = config_pathology_report.get("pathology_report_column_name", "")

    printer_id_conf = config_pathology_report.get("printer_id", {})
    printer_id_regex = printer_id_conf.get("regular_expression", r'출력자ID\s*:\s*(?P<printer_id>[0-9]{4,8})')
    printer_id_policy = printer_id_conf.get("deidentification_policy", "anonymization")
    printer_id_anonymization_value = printer_id_conf.get("anonymization_value", "OOOO")

    pgm_id_conf = config_pathology_report.get("PGM_ID", {})
    pgm_id_regex = pgm_id_conf.get("regular_expression", r'PGM_ID\s*:\s*(?P<pgm_id>[A-Za-z0-9]{8})')
    pgm_id_policy = pgm_id_conf.get("deidentification_policy", "no_apply")
    pgm_id_anonymization_value = pgm_id_conf.get("anonymization_value", "OOOOOOOO")

    print_date_conf = config_pathology_report.get("print_date", {})
    print_date_regex = print_date_conf.get("regular_expression", r'출력일\s*:\s*(?P<print_date>\d{4}-\d{2}-\d{2})')
    print_date_policy = print_date_conf.get("deidentification_policy", "pseudonymization")
    print_date_pseudonymization_values = print_date_conf.get("pseudonymization_values", "year_to_january_first")
    print_date_anonymization_value = print_date_conf.get("anonymization_value", "yyyy-mm-dd")

    pathology_id_conf = config_pathology_report.get("pathology_id", {})
    pathology_id_regex = pathology_id_conf.get("regular_expression", r'병리번호\s*:\s*(?P<pathology_id>[A-Za-z0-9]{3,4}-[0-9]{4,5})')
    pathology_id_policy = pathology_id_conf.get("deidentification_policy", "pseudonymization")
    pathology_id_anonymization_value = pathology_id_conf.get("anonymization_value", "OOO-OOOOO")

    receipt_date_conf = config_pathology_report.get("receipt_date", {})
    receipt_date_regex = receipt_date_conf.get("regular_expression", r'접 수 일\s*:\s*(?P<receipt_date>\d{4}-\d{2}-\d{2})')
    receipt_date_policy = receipt_date_conf.get("deidentification_policy", "pseudonymization")
    receipt_date_pseudonymization_values = receipt_date_conf.get("pseudonymization_values", "year_to_january_first")
    receipt_date_anonymization_value = receipt_date_conf.get("anonymization_value", "yyyy-mm-dd")

    patient_name_conf = config_pathology_report.get("patient_name", {})
    patient_name_regex = patient_name_conf.get("regular_expression", r'환 자 명\s*:\s*(?P<pname>[가-힣]+)')
    patient_name_policy = patient_name_conf.get("deidentification_policy", "anonymization")
    patient_name_anonymization_value = patient_name_conf.get("anonymization_value", "OOO")

    referring_physician_conf = config_pathology_report.get("referring_physician", {})
    referring_physician_regex = referring_physician_conf.get("regular_expression", r'의뢰의사\s*:\s*(?P<ref_physician>[가-힣]+)')
    referring_physician_policy = referring_physician_conf.get("deidentification_policy", "anonymization")
    referring_physician_anonymization_value = referring_physician_conf.get("anonymization_value", "OOO")

    patient_id_conf = config_pathology_report.get("patient_id", {})
    patient_id_regex = patient_id_conf.get("regular_expression", r'등록번호\s*:\s*(?P<pid>[0-9]{8})')
    patient_id_deidentification_policy = patient_id_conf.get("deidentification_policy", "anonymization")
    patient_id_pseudonymization_policy = patient_id_conf.get("pseudonymization_policy", "format_preserve_encryption")
    patient_id_anonymization_value = patient_id_conf.get("anonymization_value", "OOOOOOOO")

    referring_department_conf = config_pathology_report.get("referring_department", {})
    referring_department_regex = referring_department_conf.get("regular_expression", r'의뢰과\s*:\s*(?P<ref_department>[가-힣]+)')
    referring_department_policy = referring_department_conf.get("deidentification_policy", "anonymization")
    referring_department_anonymization_value = referring_department_conf.get("anonymization_value", "OOOOOOOO")

    sex_conf = config_pathology_report.get("sex", {})
    sex_regex = sex_conf.get("regular_expression", r'성별/나이\s*:\s*(?P<sex>[FM])')
    sex_policy = sex_conf.get("deidentification_policy", "anonymization")
    sex_anonymization_value = sex_conf.get("anonymization_value", "O")

    age_conf = config_pathology_report.get("age", {})
    age_regex = age_conf.get("regular_expression", r'성별/나이\s*:\s*[FM]\s*/\s*(?P<age>\d{1,3})')
    age_policy = age_conf.get("deidentification_policy", "pseudonymization")
    age_pseudonymization_values = age_conf.get("pseudonymization_values", "age_to_5year_group")
    age_anonymization_value = age_conf.get("anonymization_value", "OOO")

    ward_room_conf = config_pathology_report.get("ward_room", {})
    ward_room_regex = ward_room_conf.get("regular_expression", r'병동/병실\s*:\s*(?P<ward>[A-Z][0-9]+)\s*/\s*(?P<room>[0-9]{2})')
    ward_room_policy = ward_room_conf.get("deidentification_policy", "anonymization")
    ward_room_anonymization_value = ward_room_conf.get("anonymization_value", "OO / OO")

    out_inpatient_conf = config_pathology_report.get("out_inpatient", {})
    out_inpatient_regex = out_inpatient_conf.get("regular_expression", r'외래/입원\s*:\s*(?P<oi>입원|외래)')
    out_inpatient_policy = out_inpatient_conf.get("deidentification_policy", "anonymization")
    out_inpatient_anonymization_value = out_inpatient_conf.get("anonymization_value", "OO")

    result_date_conf = config_pathology_report.get("result_date", {})
    result_date_regex = result_date_conf.get("regular_expression", r'결 과 일\s*:\s*(?P<result_date>\d{4}-\d{2}-\d{2})')
    result_date_policy = result_date_conf.get("deidentification_policy", "anonymization")
    result_date_pseudonymization_policy = result_date_conf.get("pseudonymization_policy", "year_to_january_first")
    result_date_anonymization_value = result_date_conf.get("anonymization_value", "yyyy-mm-dd")

    attending_physician_conf = config_pathology_report.get("attending_physician", {})
    attending_physician_regex = attending_physician_conf.get("regular_expression", r'담당의사\s*:\s*(?P<attending_physician>[가-힣]+)')
    attending_physician_policy = attending_physician_conf.get("deidentification_policy", "anonymization")
    attending_physician_anonymization_value = attending_physician_conf.get("anonymization_value", "OOO")
    
    phone_number_conf = config_pathology_report.get("phone_number", {})
    phone_number_regex = phone_number_conf.get("regular_expression", r'검사실\s*:\s*(?P<phone_number>[0-9]{3}-[0-9]{4})')
    phone_number_policy = phone_number_conf.get("deidentification_policy", "anonymization")
    phone_number_anonymization_value = phone_number_conf.get("anonymization_value", "OOO-OOOO") 
    
    gross_id_conf = config_pathology_report.get("gross_id", {})
    gross_id_regex = gross_id_conf.get("regular_expression", r'(?P<gross_id>[A-Za-z0-9]{4}-[0-9]{4})\s*육안사진촬영')
    gross_id_policy = gross_id_conf.get("deidentification_policy", "pseudonymization")
    gross_id_anonymization_value = gross_id_conf.get("anonymization_value", "OOOO-OOOO")
    
    result_inputter_conf = config_pathology_report.get("result_inputter", {})
    result_inputter_regex = result_inputter_conf.get("regular_expression", r'결과 입력\s*:\s*(?P<result_inputter>[가-힣]+)')
    result_inputter_policy = result_inputter_conf.get("deidentification_policy", "anonymization")
    result_inputter_anonymization_value = result_inputter_conf.get("anonymization_value", "OOO")
    
    pathologists_conf = config_pathology_report.get("pathologists", {})
    pathologists_regex = pathologists_conf.get("regular_expression", r'병리전문의\s*:\s*(?P<pathologists>[가-힣\s*/\s*가-힣]+)$')
    pathologists_policy = pathologists_conf.get("deidentification_policy", "anonymization")
    pathologists_anonymization_value = pathologists_conf.get("anonymization_value", "OOO/OOO")


    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    excel_files = find_excel_files(input_dir)
    log_debug(f"총 {len(excel_files)}개 엑셀파일 발견")
    dfs = read_excel_files(excel_files)

    cipher = get_cipher()

    for fname, df in dfs.items():
        deid_df = deidentify_patient_id_in_column(df, patient_id_column_name, patient_id_regex, patient_id_policy, patient_id_anonymization_value)
        log_debug(f"[가명화] {fname}: patient_id preview → {deid_df[patient_id_column_name].head().tolist()}")

        deid_df = deidentify_result_date_in_column(deid_df, result_date_column_name, result_date_regex, result_date_policy, result_date_anonymization_value)
        log_debug(f"[가명화] {fname}: result_date preview → {deid_df[result_date_column_name].head().tolist()}")

        deid_df = deidentify_pathology_id_in_column(deid_df, pathology_id_column_name, pathology_id_regex, pathology_id_policy, pathology_id_anonymization_value)
        log_debug(f"[가명화] {fname}: pathology_id preview → {deid_df[pathology_id_column_name].head().tolist()}")

        deid_df = deidentify_pathology_report_in_column(deid_df, pathology_report_column_name, config_pathology_report)
        log_debug(f"[가명화] {fname}: pathology_report preview → {deid_df[pathology_report_column_name].head().tolist()}")

        base_fname = os.path.basename(fname)
        if base_fname.endswith('.xls'):
            base_fname = base_fname[:-4] + '.xlsx'
        deid_fname = os.path.join(output_dir, f"deid_{base_fname}")
        try:
            deid_df.to_excel(deid_fname, index=False)
            log_debug(f"[저장] {deid_fname} (shape={deid_df.shape})")
        except Exception as e:
            log_debug(f"[저장실패] {deid_fname}: {e}")
