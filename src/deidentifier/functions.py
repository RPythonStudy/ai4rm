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
    deidentification_policy = config.get("deidentification_policy", "anonymization")
    if deidentification_policy == "pseudonymization":
        pseudonymization_policy = config.get("pseudonymization_policy", "yyyy-mm-dd")
        if pseudonymization_policy == "month_to_first_day":
            df[field] = df[field].apply(lambda x: x.replace(day=1) if pd.notnull(x) else x)
        elif pseudonymization_policy == "year_to_january_first":
            df[field] = df[field].apply(lambda x: x.replace(month=1, day=1) if pd.notnull(x) else x)
    elif deidentification_policy == "anonymization":
        anonymization_value = config.get("anonymization_value", "yyyy-mm-dd")
        df[field] = anonymization_value
    elif deidentification_policy == "no_apply":
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

def deidentify_pathology_report_in_column(df, field, config):
    df[field] = df[field].apply(redact_kirams_line)
    df[field] = df[field].apply(lambda x: deidentification_printer_id(x, config))
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
def deidentification_printer_id(content: str, config: dict = {}):
    printer_id_conf = config.get("printer_id", {})
    regex = printer_id_conf.get("regular_expression", r'출력자ID\s*:\s*(?P<printer_id>[0-9]{4,8})')
    policy = printer_id_conf.get("deidentification_policy", "anonymization")
    anonymization_value = printer_id_conf.get("anonymization_value", "OOOO")

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

