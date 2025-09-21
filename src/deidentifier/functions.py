# src/deidentifier/functions.py
# 비식별화함수를 모아둔 파일
# last updated: 2025-09-21


import os
import re
import yaml
import chardet
from dotenv import load_dotenv
from common.logger import log_debug
from common.get_cipher import get_cipher
import pandas as pd

#############################
# id 관련 함수들
#############################
def pseudonymize_id(id_value, cipher):
    id_str = str(id_value)
    if '-' in id_str:
        hyphen_pos = id_str.index('-')
        id_no_hyphen = id_str.replace('-', '')
        id_padded = id_no_hyphen.zfill(8)
        pseudo_id = cipher.encrypt(id_padded)
        pseudo_id = pseudo_id[:hyphen_pos] + '-' + pseudo_id[hyphen_pos:]
        return pseudo_id
    else:
        id_padded = id_str.zfill(8)
        return cipher.encrypt(id_padded)

def serialize_id(df, column_name):
    df[column_name] = [str(i+1).zfill(8) for i in range(len(df))]
    return df

def deidentify_id_in_column(df, column_name, deidentification_policy, cipher=None):
    if deidentification_policy == "pseudonymization":
        df[column_name] = df[column_name].apply(lambda x: pseudonymize_id(x, cipher) if pd.notnull(x) else x)
    elif deidentification_policy == "anonymization":
        df = serialize_id(df, column_name)
    else:
        pass
    return df

def pseudonymize_id_within_text(text, regex, cipher=None):
    ids = re.findall(regex, text)
    for id in ids:
        try:
            pseudonymized_id = pseudonymize_id(id, cipher)
            text = text.replace(id, pseudonymized_id)
        except Exception as e:
            log_debug(f"[ERROR] Exception: {e}")

    return text

def replace_within_text(text, regex, replace_value):
    return re.sub(regex, replace_value, text)


def deidentify_id_in_dataframe(df, column_name, regex, deidentification_policy, anonymization_policy, anonymization_value=None, cipher=None, source_column=None):
    if deidentification_policy == "pseudonymization":
        df[column_name] = df[column_name].apply(lambda x: pseudonymize_id_within_text(x, regex, cipher) if pd.notnull(x) else x)
        log_debug(f"[deidentify_id_in_dataframe]: '{source_column}' with policy '{deidentification_policy}'.")
    elif deidentification_policy == "anonymization":
        if anonymization_policy == "serial_number":
            df = serialize_id(df, column_name)
        elif anonymization_policy == "masking":
            df[column_name] = [replace_within_text(text, regex, anonymization_value) if pd.notnull(text) else text
                           for text in df[column_name]]
    else:
        pass
    
    return df

#############################
# date 관련 함수들
#############################
def pseudonymize_date_by_policy(date_value, policy):
    # date_value가 Timestamp일 경우 문자열로 변환
    date_str = str(date_value)
    parts = date_str.split("-")
    if policy == "month_to_first_day" and len(parts) == 3:
        return f"{parts[0]}-{parts[1]}-01"
    elif policy == "year_to_january_first" and len(parts) == 3:
        return f"{parts[0]}-01-01"
    else:
        return date_str

def deidentify_date_in_column(df, column_name, deidentification_policy, pseudonymization_policy):
    if deidentification_policy == "pseudonymization":
        df[column_name] = df[column_name].apply(lambda x: pseudonymize_date_by_policy(x, pseudonymization_policy) if pd.notnull(x) else x)
    elif deidentification_policy == "anonymization":
        df[column_name] = "yyyy-mm-dd"
    else:
        pass
    return df    

def pseudonymize_date_within_text(text, regex, pseudonymization_policy):
    dates = re.findall(regex, text)
    for date in dates:
        try:
            pseudonymized_date = pseudonymize_date_by_policy(date, pseudonymization_policy)
            text = text.replace(date, pseudonymized_date)
        except Exception as e:
            pass
    return text


def deidentify_date_in_dataframe(df, column_name, regex, deidentification_policy, pseudonymization_policy, source_column=None):
    if deidentification_policy == "pseudonymization":
        df[column_name] = df[column_name].apply(lambda x: pseudonymize_date_within_text(x, regex, pseudonymization_policy) if pd.notnull(x) else x)
        log_debug(f"[deidentify_date_in_dataframe]: '{source_column}' with policy '{pseudonymization_policy}'.")

    elif deidentification_policy == "anonymization":
        df[column_name] = [replace_within_text(text, regex, serialized_id) if pd.notnull(text) else text
                           for text, serialized_id in zip(df[column_name], df[source_column])]
    return df

#########################################
# 한국원자력의학원 포함 줄 전체 ----로 대체
##########################################
def redact_kirams_line(content: str):
    pattern = r'.*한국원자력의학원.*'
    def replace_line(match):
        return "--------------------------------------------"
    result = re.sub(pattern, replace_line, content)
    return result


##############################
# pathology_report 래핑함수
##############################
def deidentify_pathology_report_in_column(df, config_pathology_report, cipher, cipher_digit):
    patient_id_column_name = config_pathology_report.get("patient_id_column_name", {})
    pathology_id_column_name = config_pathology_report.get("pathology_id_column_name", {})
    result_date_column_name = config_pathology_report.get("result_date_column_name", "result_date")
    pathology_report_column_name = config_pathology_report.get("pathology_report_column_name", "pathology_report")

    patient_id_conf = config_pathology_report.get("patient_id", {})
    patient_id_regex = patient_id_conf.get("regular_expression", r'\b\d{8}\b')
    patient_id_deidentification_policy = patient_id_conf.get("deidentification_policy", "anonymization")
    patient_id_anonymization_policy = patient_id_conf.get("anonymization_policy", "masking")
    patient_id_anonymization_value = patient_id_conf.get("anonymization_value", "OOOO")

    pathology_id_conf = config_pathology_report.get("pathology_id", {})
    pathology_id_regex = pathology_id_conf.get("regular_expression", r'병리번호\s*:\s*(?P<pathology_id>[A-Za-z0-9]{3,4}-[0-9]{4,5})')
    pathology_id_deidentification_policy = pathology_id_conf.get("deidentification_policy", "pseudonymization")
    pathology_id_anonymization_policy = pathology_id_conf.get("anonymization_policy", "masking")
    pathology_id_anonymization_value = pathology_id_conf.get("anonymization_value", "OOO-OOOOO")

    result_date_conf = config_pathology_report.get("result_date", {})
    result_date_regex = result_date_conf.get("regular_expression", r'결 과 일\s*:\s*(?P<result_date>\d{4}-\d{2}-\d{2})')
    result_date_deidentification_policy = result_date_conf.get("deidentification_policy", "pseudonymization")
    result_date_pseudonymization_policy = result_date_conf.get("pseudonymization_policy", "year_to_january_first")

    printer_id_conf = config_pathology_report.get("printer_id", {})
    printer_id_regex = printer_id_conf.get("regular_expression", r'출력자ID\s*:\s*(?P<printer_id>[0-9]{4,8})')
    printer_id_deidentification_policy = printer_id_conf.get("deidentification_policy", "anonymization")
    printer_id_anonymization_policy = printer_id_conf.get("anonymization_policy", "masking")
    printer_id_anonymization_value = printer_id_conf.get("anonymization_value", "OOOO")

    deid_df = deidentify_id_in_dataframe(
        df=df, 
        column_name=pathology_report_column_name, 
        regex=patient_id_regex, 
        deidentification_policy=patient_id_deidentification_policy, 
        anonymization_policy=patient_id_anonymization_policy, 
        cipher=cipher_digit, 
        source_column=patient_id_column_name
    )
#    deid_df = deidentify_id_in_dataframe(df, pathology_report_column_name, pathology_id_regex, pathology_id_deidentification_policy, pathology_id_anonymization_policy, pathology_id_anonymization_value, cipher, pathology_id_column_name)
#    deid_df = deidentify_date_in_dataframe(df, pathology_report_column_name, result_date_regex, result_date_deidentification_policy, result_date_pseudonymization_policy, result_date_column_name)
#    deid_df[pathology_report_column_name] = deid_df[pathology_report_column_name].apply(redact_kirams_line)
#    log_debug(f"[redact_kirams_line] completed: --------------------------------------------")
#    deid_df = deidentify_id_in_dataframe(df, pathology_report_column_name, printer_id_regex, printer_id_deidentification_policy, printer_id_anonymization_policy, printer_id_anonymization_value, cipher_digit)

    return deid_df






def old_deidentify_pathology_report_in_column(df, column_name, config_pathology_report, cipher=None):

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
    patient_id_deidentification_policy = patient_id_conf.get("deidentification_policy", "anonymization")

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


    # df[field] = df[field].apply(redact_kirams_line)
    # df[field] = df[field].apply(lambda x: deidentification_printer_id(x, printer_id_regex, printer_id_policy, printer_id_anonymization_value))
    # df[field] = df[field].apply(lambda x: deidentification_pgm_id(x, pgm_id_regex, pgm_id_policy, pgm_id_anonymization_value))
    # df[field] = df[field].apply(lambda x: deidentification_print_date(x, print_date_regex, print_date_policy, print_date_anonymization_value, pseudonymization_policy=print_date_pseudonymization_values))
  




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


