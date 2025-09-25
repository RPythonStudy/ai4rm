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

def deidentify_id_in_column(df, column_name, config, cipher=None):
    deidentification_policy = config.get("deidentification_policy")
    anonymization_policy = config.get("anonymization_policy")
    anonymization_value = config.get("anonymization_value")

    if deidentification_policy == "pseudonymization":
        df[column_name] = df[column_name].apply(lambda x: pseudonymize_id(x, cipher) if pd.notnull(x) else x)
    elif deidentification_policy == "anonymization":
        if anonymization_policy == "serial_number":
            df = serialize_id(df, column_name)
        elif anonymization_policy == "masking":
            df[column_name] = df[column_name].apply(lambda x: anonymization_value if pd.notnull(x) else x)
            log_debug(f"[deidentify_id_in_column]: '{column_name}' with policy '{anonymization_policy}'.")
    else:
        pass
    return df

def pseudonymize_id_within_text(text, regex, cipher=None):
    def repl(match):
        # 그룹명이 있으면 그룹값만 치환, 없으면 전체 매치 치환
        if match.groupdict():
            # 가장 첫 번째 그룹값만 치환 (예: pid)
            group_keys = list(match.groupdict().keys())
            group_val = match.group(group_keys[0])
            pseudo_val = pseudonymize_id(group_val, cipher)
            return match.group(0).replace(group_val, pseudo_val)
        else:
            val = match.group(0)
            return pseudonymize_id(val, cipher)
    try:
        text = re.sub(regex, repl, text)
    except Exception as e:
        log_debug(f"[ERROR] Exception: {e}")
    return text

def replace_within_text(text, regex, replace_value):
    log_debug(f"[replace_within_text]: Replacing '{regex}' with '{replace_value}'.")
    return re.sub(regex, replace_value, text)


def deidentify_id_in_dataframe(df, column_name, config, cipher=None, source_column=None):
    regex = config.get("regular_expression")
    deidentification_policy = config.get("deidentification_policy")    
    if source_column is not None:
        df[column_name] = [
            replace_within_text(x, regex, str(y)) if pd.notnull(x) else x
            for x, y in zip(df[column_name], df[source_column])
        ]
    if deidentification_policy == "pseudonymization":
        df[column_name] = df[column_name].apply(lambda x: pseudonymize_id_within_text(x, regex, cipher) if pd.notnull(x) else x)
        log_debug(f"[deidentify_id_in_dataframe]: '{source_column}' with policy '{deidentification_policy}'.")
    elif deidentification_policy == "anonymization":
        if anonymization_policy == "serial_number":
            df = serialize_id(df, column_name)
        elif anonymization_policy == "masking":
            df[column_name] = [replace_within_text(x, regex, y) if pd.notnull(x) else x for x, y in zip(df[column_name], df[source_column])]
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


def deidentify_date_in_dataframe(df, column_name, config, cipher=None, source_column=None):
    regex = config.get("regular_expression")
    if source_column is not None:
        df[column_name] = df[column_name].combine_first(df[source_column])
    if deidentification_policy == "pseudonymization":
        df[column_name] = df[column_name].apply(lambda x: pseudonymize_date_within_text(x, regex, pseudonymization_policy) if pd.notnull(x) else x)
        log_debug(f"[deidentify_date_in_dataframe]: '{source_column}' with policy '{pseudonymization_policy}'.")

    elif deidentification_policy == "anonymization":
        df[column_name] = [replace_within_text(text, regex, serialized_id) if pd.notnull(text) else text
                           for text, serialized_id in zip(df[column_name], df[source_column])]
        log_debug(f"[deidentify_date_in_dataframe]: '{source_column}' with policy '{pseudonymization_policy}'.")
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
        config=patient_id_conf, 
        cipher=cipher_digit, 
        source_column=patient_id_column_name
    )


#    deid_df = deidentify_date_in_dataframe(df, pathology_report_column_name, result_date_regex, result_date_deidentification_policy, result_date_pseudonymization_policy, result_date_column_name)
#    deid_df[pathology_report_column_name] = deid_df[pathology_report_column_name].apply(redact_kirams_line)
#    log_debug(f"[redact_kirams_line] completed: --------------------------------------------")
#    deid_df = deidentify_id_in_dataframe(df, pathology_report_column_name, printer_id_regex, printer_id_deidentification_policy, printer_id_anonymization_policy, printer_id_anonymization_value, cipher_digit)

    return deid_df
