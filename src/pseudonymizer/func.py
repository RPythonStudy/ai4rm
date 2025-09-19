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


def pseudonymize_patient_id(patient_id, cipher):
    patient_id_zfilled = str(patient_id).zfill(8)
    pseudonymized_patient_id = cipher.encrypt(patient_id_zfilled)
    return pseudonymized_patient_id

def serialize_patient_id(df, column_name):
    df[column_name] = [str(i+1).zfill(8) for i in range(len(df))]
    return df

def deidentify_patient_id_in_column(df, column_name, deidentification_policy, cipher=None):
    log_debug(f"[deidentify_patient_id_in_column] policy: {deidentification_policy}, column: {column_name}")
    if deidentification_policy == "pseudonymization":
        log_debug(f"[deidentify_patient_id_in_column] pseudonymization 실행")
        df[column_name] = df[column_name].apply(lambda x: pseudonymize_patient_id(x, cipher) if pd.notnull(x) else x)
        log_debug(f"[deidentify_patient_id_in_column] pseudonymized preview: {df[column_name].head().tolist()}")
    elif deidentification_policy == "anonymization":
        log_debug(f"[deidentify_patient_id_in_column] anonymization 실행")
        df = serialize_patient_id(df, column_name)
        log_debug(f"[deidentify_patient_id_in_column] anonymized preview: {df[column_name].head().tolist()}")
    else:
        log_debug(f"[deidentify_patient_id_in_column] no action (policy: {deidentification_policy})")
    return df

def pseudonymize_patient_id_within_text(text, regex, cipher=None):
    patient_ids = re.findall(regex, text)
    for patient_id in patient_ids:
        try:
            pseudonymized_patient_id = pseudonymize_patient_id(patient_id, cipher)
            text = text.replace(patient_id, pseudonymized_patient_id)
        except Exception as e:
            pass
    return text

def serialize_patient_id_within_text(text, regex, serialized_patient_id, cipher=None):
    patient_ids = re.findall(regex, text)
    for patient_id in patient_ids:
        try:
            text = text.replace(patient_id, serialized_patient_id)
        except Exception as e:
            pass
    return text


def deidentify_patient_id_in_dataframe(df, column_name, regex, deidentification_policy, cipher=None, serialized_column=None):
    if deidentification_policy == "pseudonymization":
        df[column_name] = df[column_name].apply(lambda x: pseudonymize_patient_id_within_text(x, regex, cipher) if pd.notnull(x) else x)
    elif deidentification_policy == "anonymization":
        # pathology_report 텍스트 내 patient_id를 해당 row의 serialize된 patient_id로 치환
        if serialized_column is None:
            raise ValueError("serialized_column 인자가 필요합니다 (예: df['patient_id'])")
        df[column_name] = [serialize_patient_id_within_text(text, regex, serialized_pid) if pd.notnull(text) else text
                           for text, serialized_pid in zip(df[column_name], df[serialized_column])]
    return df



def deidentify_pathology_report_in_column(df, column_name, config_pathology_report, cipher=None):



    patient_id_conf = config_pathology_report.get("patient_id", {})
    patient_id_regex = patient_id_conf.get("regular_expression", r'\b\d{8}\b')
    patient_id_deidentification_policy = patient_id_conf.get("deidentification_policy", "anonymization")

  
    # 익명화 정책일 때 serialized_column 인자 추가
    if patient_id_deidentification_policy == "anonymization":
        patient_id_column_name = config_pathology_report.get("patient_id_column_name", "patient_id")
        df = deidentify_patient_id_in_dataframe(
            df, column_name, patient_id_regex, patient_id_deidentification_policy, cipher,
            serialized_column=patient_id_column_name
        )
    else:
        df = deidentify_patient_id_in_dataframe(df, column_name, patient_id_regex, patient_id_deidentification_policy, cipher)
    return df
