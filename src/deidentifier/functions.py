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
        log_debug(f"[in_column] '{column_name}' & {deidentification_policy} → 1st result: {df[column_name].iloc[0] if len(df) > 0 else 'N/A'}")
    elif deidentification_policy == "anonymization":
        if anonymization_policy == "serial_number":
            df = serialize_id(df, column_name)
            log_debug(f"[in_column] '{column_name}' & {anonymization_policy} → 1st result: {df[column_name].iloc[0] if len(df) > 0 else 'N/A'}")
        elif anonymization_policy == "masking":
            df[column_name] = df[column_name].apply(lambda x: anonymization_value if pd.notnull(x) else x)
            log_debug(f"[in_column] '{column_name}' & {anonymization_policy} → 1st result: {df[column_name].iloc[0] if len(df) > 0 else 'N/A'}")
    else:
        log_debug(f"[in_column] '{column_name}' & {deidentification_policy} → no change applied.")
                  
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
        anonymization_policy = config.get("anonymization_policy")
        anonymization_value = config.get("anonymization_value")
        if anonymization_policy == "serial_number":
            df = serialize_id(df, column_name)
        elif anonymization_policy == "masking":
            df[column_name] = [replace_within_text(x, regex, anonymization_value) if pd.notnull(x) else x for x, y in zip(df[column_name], df[source_column])]
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
    deidentification_policy = config.get("deidentification_policy")
    pseudonymization_policy = config.get("pseudonymization_policy")
    anonymization_policy = config.get("anonymization_policy")
    anonymization_value = config.get("anonymization_value")
    
    if source_column is not None:
        df[column_name] = df[column_name].combine_first(df[source_column])
    if deidentification_policy == "pseudonymization":
        df[column_name] = df[column_name].apply(lambda x: pseudonymize_date_within_text(x, regex, pseudonymization_policy) if pd.notnull(x) else x)
        log_debug(f"[deidentify_date_in_dataframe]: '{source_column}' with policy '{pseudonymization_policy}'.")

    elif deidentification_policy == "anonymization":
        df[column_name] = [replace_within_text(text, regex, anonymization_value) if pd.notnull(text) else text
                           for text, serialized_id in zip(df[column_name], df[source_column])]
        log_debug(f"[deidentify_date_in_dataframe]: '{source_column}' with policy '{anonymization_policy}'.")
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
    # 현재 YAML 구조에 맞게 컬럼명 추출
    report_column_name = config_pathology_report.get("report_column_name", "pathology_report")
    
    # targets 섹션에서 비식별화 대상들 추출
    targets = config_pathology_report.get("targets", {})
    
    # 데이터프레임 복사
    deid_df = df.copy()
    
    # 각 비식별화 대상에 대해 순회 처리
    for target_name, target_config in targets.items():
        deid_df = process_text_pattern_in_column(
            deid_df, 
            report_column_name, 
            target_config, 
            cipher, 
            cipher_digit
        )
        log_debug(f"[processed_target] {target_name}")
    
    return deid_df


def process_text_pattern_in_column(df, column_name, pattern_config, cipher, cipher_digit):
    """
    텍스트 컬럼에서 특정 패턴을 찾아 비식별화하는 함수
    """
    regular_expression = pattern_config.get("regular_expression", "")
    deidentification_policy = pattern_config.get("deidentification_policy", "")
    
    if not regular_expression or deidentification_policy == "no_apply":
        return df
    
    def process_text_cell(text):
        if pd.isna(text):
            return text
        
        text = str(text)
        
        def replace_matched_item(match):
            """매칭된 개별 아이템을 정책에 따라 처리"""
            matched_value = match.group(0)
            
            if deidentification_policy == "pseudonymization":
                return pseudonymize_item(matched_value, pattern_config, cipher, cipher_digit)
            elif deidentification_policy == "anonymization":
                return anonymize_item(matched_value, pattern_config)
            else:
                return matched_value
        
        return re.sub(regular_expression, replace_matched_item, text)
    
    df[column_name] = df[column_name].apply(process_text_cell)
    return df


def pseudonymize_item(matched_value, pattern_config, cipher, cipher_digit):
    """개별 아이템 가명화 함수"""
    policy = pattern_config.get("pseudonymization_policy", "")
    
    if policy == "fpe":
        # 숫자만 있으면 cipher_digit, 그 외는 cipher 사용
        if re.search(r'\d+', matched_value):
            return cipher_digit.encrypt(matched_value.zfill(8))[:len(matched_value)]
        else:
            return cipher.encrypt(matched_value)
    elif policy == "year_to_january_first":
        # 날짜를 1월 1일로 변경
        return re.sub(r'(\d{4})-\d{2}-\d{2}', r'\1-01-01', matched_value)
    elif policy == "age_to_5year_group":
        # 나이를 5세 단위로 그룹화
        def age_group(match):
            age = int(match.group(0))
            return str((age // 5) * 5)
        return re.sub(r'\d+', age_group, matched_value)
    
    return matched_value


def anonymize_item(matched_value, pattern_config):
    """개별 아이템 익명화 함수"""
    policy = pattern_config.get("anonymization_policy", "")
    anonymization_value = pattern_config.get("anonymization_value", "")
    
    if policy == "masking":
        return anonymization_value
    elif policy == "serial_number":
        # 연번은 컬럼 레벨에서 처리해야 함
        return matched_value
    
    return matched_value


#    deid_df = deidentify_date_in_dataframe(df, pathology_report_column_name, result_date_regex, result_date_deidentification_policy, result_date_pseudonymization_policy, result_date_column_name)
#    deid_df[pathology_report_column_name] = deid_df[pathology_report_column_name].apply(redact_kirams_line)
#    log_debug(f"[redact_kirams_line] completed: --------------------------------------------")
#    deid_df = deidentify_id_in_dataframe(df, pathology_report_column_name, printer_id_regex, printer_id_deidentification_policy, printer_id_anonymization_policy, printer_id_anonymization_value, cipher_digit)

    return deid_df
