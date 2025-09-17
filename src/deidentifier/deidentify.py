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
    policy = config.get("deidentification_policy", "anonymization")
    if policy == "anonymization":
        df[field] = [str(i+1) for i in range(len(df))]
    elif policy == "pseudonymization":
        cipher = get_cipher()
        df[field] = df[field].apply(lambda x: cipher.encrypt(str(x)))
    return df

def deidentify_result_date_in_column(df, field: str, config: dict):
    policy = config.get("deidentification_policy", "anonymization")
    if policy == "anonymization":
        anonymization_value = config.get("anonymization_value", "yyyy-mm-dd")
        df[field] = anonymization_value
    elif policy == "pseudonymization":
        pseudonymization_policy = config.get("pseudonymization_policy", "yyyy-mm-dd")
        if pseudonymization_policy == "month_to_first_day":
            df[field] = df[field].apply(lambda x: x.replace(day=1) if pd.notnull(x) else x)
        elif pseudonymization_policy == "year_to_january_first":
            df[field] = df[field].apply(lambda x: x.replace(month=1, day=1) if pd.notnull(x) else x)
    return df

def deidentify_patient_id_within_text(df, report_field: str, config: dict):
    policy = config.get("deidentification_policy", "no_apply")
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

