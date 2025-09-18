# src/pseudonymizer/pseudonymizer.py
# 비식별화함수를 모아둔 파일
# last updated: 2025-09-17


import os
import re
import yaml
import chardet
from dotenv import load_dotenv
from common.logger import log_debug
from common.get_cipher import get_cipher
import pandas as pd


def deidentify_patient_id_in_column(df, field: str, config: dict):
    deidentification_policy = config.get("deidentification_policy", "anonymization")
    if deidentification_policy == "pseudonymization":
        cipher = get_cipher()
        df[field] = df[field].apply(lambda x: cipher.encrypt(str(x)))
    elif deidentification_policy == "anonymization":
        df[field] = [str(i+1) for i in range(len(df))]
    elif deidentification_policy == "no_apply":
        pass
    return df


def deidentify_result_date_in_column(df, field: str, config: dict):
    from common.logger import log_debug
    log_debug(f"[result_date] config: {config}")
    deidentification_policy = config.get("deidentification_policy", "anonymization")
    log_debug(f"[result_date] deidentification_policy: {deidentification_policy}")
    if deidentification_policy == "pseudonymization":
        pseudonymization_policy = config.get("pseudonymization_policy", "yyyy-mm-dd")
        log_debug(f"[result_date] pseudonymization_policy: {pseudonymization_policy}")
        if pseudonymization_policy == "month_to_first_day":
            df[field] = df[field].apply(lambda x: x.replace(day=1) if pd.notnull(x) else x)
        elif pseudonymization_policy == "year_to_january_first":
            df[field] = df[field].apply(lambda x: x.replace(month=1, day=1) if pd.notnull(x) else x)
        log_debug(f"[result_date] preview after pseudonymization: {df[field].head().tolist()}")
    elif deidentification_policy == "anonymization":
        anonymization_value = config.get("anonymization_value", "yyyy-mm-dd")
        df[field] = anonymization_value
        log_debug(f"[result_date] preview after anonymization: {df[field].head().tolist()}")
    elif deidentification_policy == "no_apply":
        log_debug(f"[result_date] no_apply policy, no change.")
        pass  
    return df


def deidentify_pathology_id_in_column(df, field: str, config: dict):
    deidentification_policy = config.get("deidentification_policy", "anonymization")
    if deidentification_policy == "pseudonymization":
        cipher = get_cipher()
        df[field] = df[field].apply(lambda x: cipher.encrypt(str(x)))
    elif deidentification_policy == "anonymization":
        anonymization_value = config.get("anonymization_value", "OOO-OOOO")
        df[field] = anonymization_value
    elif deidentification_policy == "no_apply":
        pass  
    return df


def deidentify_pathology_report_in_column(df, field, config_pathology_report):

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
    patient_id_regex = patient_id_conf.get("regular_expression", r'\b\d{8}\b')
    patient_id_policy = patient_id_conf.get("deidentification_policy", "anonymization")
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


    df[field] = df[field].apply(redact_kirams_line)
    df[field] = df[field].apply(lambda x: deidentification_printer_id(x, printer_id_regex, printer_id_policy, printer_id_anonymization_value))
    df[field] = df[field].apply(lambda x: deidentification_pgm_id(x, pgm_id_regex, pgm_id_policy, pgm_id_anonymization_value))
    df[field] = df[field].apply(lambda x: deidentification_print_date(x, print_date_regex, print_date_policy, print_date_anonymization_value, pseudonymization_policy=print_date_pseudonymization_values))


    return df

# ------------------------
# 한국원자력의학원 포함 줄 전체 ----로 대체
# ------------------------
def redact_kirams_line(content: str):
    pattern = r'.*한국원자력의학원.*'
    def replace_line(match):
        log_debug(f"[KIRAMS] 원본 줄: {match.group(0)} → --------------------------------------------")
        return "--------------------------------------------"
    result = re.sub(pattern, replace_line, content)
    log_debug(f"[KIRAMS] 적용 결과 preview: {result[:80]}")
    return result

# ------------------------
# printer_id 비식별화 (정책에 따라 가명화/익명화/원본 반환)
# ------------------------
def deidentification_printer_id(content: str, regex, policy, anonymization_value):
    if policy == "pseudonymization":
        cipher = get_cipher()
        def replace_printer_id(match):
            pid = match.group("printer_id")
            padded_pid = pid.zfill(6)
            log_debug(f"printer_id 원본: {pid}, 패딩 적용: {padded_pid}")
            try:
                pseudo_pid = cipher.encrypt(padded_pid)
                log_debug(f"printer_id 암호화 입력값: {padded_pid}, 암호화 결과: {pseudo_pid}")
                return match.group(0).replace(pid, pseudo_pid)
            except Exception as e:
                log_debug(f"printer_id 암호화 실패 - {e}")
                return match.group(0)
        result = re.sub(regex, replace_printer_id, content)
        return result
    elif policy == "anonymization":
        def replace_printer_id(match):
            pid = match.group("printer_id")
            return match.group(0).replace(pid, anonymization_value)
        result = re.sub(regex, replace_printer_id, content)
        return result
    else:
        return content


def deidentification_pgm_id(content: str, regex, policy, anonymization_value):
    if policy == "pseudonymization":
        cipher = get_cipher()
        def replace_pgm_id(match):
            pid = match.group("pgm_id")
            pseudo_pid = cipher.encrypt(pid)
            log_debug(f"PGM_ID 원본: {pid}, 암호화 결과: {pseudo_pid}")
            return match.group(0).replace(pid, pseudo_pid)
        result = re.sub(regex, replace_pgm_id, content)
        return result
    elif policy == "anonymization":
        def replace_pgm_id(match):
            pid = match.group("pgm_id")
            return match.group(0).replace(pid, anonymization_value)
        result = re.sub(regex, replace_pgm_id, content)
        return result
    else:
        return content
    

def deidentification_print_date(content, regex, policy, anonymization_value, pseudo_type=None, group_name=None):
    def replace_date(match):
        date_str = match.group(group_name) if group_name and group_name in match.groupdict() else match.group(1) if match.lastindex else match.group(0)
        if policy == "anonymization":
            return match.group(0).replace(date_str, anonymization_value)
        elif policy == "pseudonymization":
            if pseudo_type == "month_to_first_day":
                parts = date_str.split("-"); new_date = f"{parts[0]}-{parts[1]}-01" if len(parts)==3 else date_str
            elif pseudo_type == "year_to_january_first":
                parts = date_str.split("-"); new_date = f"{parts[0]}-01-01" if len(parts)==3 else date_str
            else:
                new_date = date_str
            return match.group(0).replace(date_str, new_date)
        else:
            return match.group(0)
    return re.sub(regex, replace_date, content)

def deidentify_patient_id_within_text(df, report_field: str, config: dict):
    policy = config.get("deidentification_policy", "anonymization")
    patient_id_regex = config.get("patient_id_regex", r'\b\d{8}\b')
    cipher = get_cipher() if policy == "pseudonymization" else None

    def replace_patient_id(text):
        if policy == "anonymization":
            return re.sub(patient_id_regex, anonymization_value, str(text))
        elif policy == "pseudonymization":
            def repl(match):
                pid = match.group(0)
                return cipher.encrypt(pid)
            return re.sub(patient_id_regex, repl, str(text))
        else:
            return text

    df[report_field] = df[report_field].apply(replace_patient_id)
    return df

def deidentify_report_text(text, config):
    # 필요한 모든 비식별화 함수들을 순차 적용
    text = deidentify_patient_id_in_text(text)

    return text

def pseudonymize_date_value(date_str, deidentification_policy, pseudonymization_policy, anonymization_value):
    if deidentification_policy == "pseudonymization":
        if pseudonymization_policy == "month_to_first_day":
            parts = date_str.split("-")
            return f"{parts[0]}-{parts[1]}-01" if len(parts)==3 else date_str
        elif pseudonymization_policy == "year_to_january_first":
            parts = date_str.split("-")
            return f"{parts[0]}-01-01" if len(parts)==3 else date_str
        else:
            return date_str
    elif deidentification_policy == "anonymization":
        return anonymization_value
    else:
        return date_str
    
def pseudonymize_date_in_text(text, regex, deidentification_policy, pseudonymization_policy, anonymization_value, group_name=None):
    def repl(match):
        date_str = match.group(group_name) if group_name else match.group(1)
        new_date = pseudonymize_date_value(date_str, deidentification_policy, pseudonymization_policy, anonymization_value)
        return match.group(0).replace(date_str, new_date)
    return re.sub(regex, repl, text)

def pseudonymize_date_in_column(df, field, policy, pseudonymization_policy, anonymization_value):
    df[field] = df[field].apply(lambda x: pseudonymize_date_value(str(x), policy, pseudonymization_policy, anonymization_value) if pd.notnull(x) else x)
    return df

