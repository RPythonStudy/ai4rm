"""비식별화함수 모음
Path: src/deidentifier/functions.py
Purpose:
    병리보고서 및 의료 데이터의 개인정보를 HIPAA/개인정보보호법에 따라 
    안전하게 비식별화하는 함수들을 제공합니다.

Functions:
    - pseudonymize_id: FF3 형태보존암호화를 통한 ID 가명화
    - pseudonymize_date: 날짜 정보 가명화 (연도/월 단위)
    - deidentify_columns: DataFrame 컬럼 레벨 비식별화
    - process_text_pattern_in_column: 정규식 기반 텍스트 패턴 비식별화

Security:
    - FF3 (Format Preserving Encryption) 알고리즘 사용
    - 원본 데이터 형태 보존으로 분석 가능성 유지
    - 복호화 불가능한 일방향 가명화 지원

Compliance:
    - HIPAA (Health Insurance Portability and Accountability Act)
    - 개인정보보호법 (Personal Information Protection Act)
    - 의료법상 개인정보 처리 규정 준수

Author: BenKorea <ben@ai4rm.org>
Created: 2025-09-18
Modified: 2025-09-27
version: 0.0.1

Example:
    >>> from common.get_cipher import get_cipher
    >>> cipher = get_cipher(alphabet_type="numeric")
    >>> pseudonymized = pseudonymize_id("P123456", cipher)
    >>> print(f"Original: P123456 → Pseudonymized: {pseudonymized}")
"""

# 표준 라이브러리
import os
import re
from typing import Any, Union

# 서드파티 라이브러리
import chardet
import pandas as pd
import yaml
from dotenv import load_dotenv

# 로컬 애플리케이션
from common.get_cipher import get_cipher
from common.logger import log_debug


#############################
# deidentify 계열 함수들
#############################
def pseudonymize_id(id_value: Union[str, int], cipher: Any) -> str:
    """ID 값을 FF3(형태보존암호화) 알고리즘으로 가명화합니다.
    
    원본 ID의 형태를 유지하면서 가명화된 값으로 변환합니다.
    하이픈이 포함된 ID의 경우 암호화 후에도 하이픈 위치를 보존합니다.
    
    매개변수:
        id_value (Union[str, int]): 가명화할 원본 ID 값
        cipher: get_cipher() 함수로 생성된 FF3 암호화 객체
    
    반환값:
        str: 원본 형태를 유지한 가명화된 ID 값
    
    사용예시:
        >>> cipher = get_cipher(alphabet_type="numeric")
        >>> pseudonymize_id("12345", cipher)
        '84729361'
        >>> pseudonymize_id("ABC1-2345", cipher)
        'XYZ7-8901'
        >>> pseudonymize_id(12345, cipher)
        '84729361'
    
    주의사항:
        - 모든 입력값은 암호화 전에 8자리로 0-패딩 처리됩니다
        - 하이픈이 여러 개인 경우 첫 번째 하이픈 위치만 보존됩니다
        - cipher 객체는 호환 가능한 알파벳 타입을 사용해야 합니다
    
    예외발생:
        TypeError: cipher가 None이거나 잘못된 타입인 경우
        ValueError: 호환되지 않는 입력으로 인해 암호화가 실패한 경우
    
    변경이력:
        2025-09-27: docstring 표준화 (BenKorea)
        2025-09-22: 최초 구현 (BenKorea)
    """
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
    
def pseudonymize_date(date_value: Union[str, Any], policy: str) -> str:
    # date_value가 Timestamp일 경우 문자열로 변환
    date_str = str(date_value)
    parts = date_str.split("-")
    if policy == "month_to_first_day" and len(parts) == 3:
        return f"{parts[0]}-{parts[1]}-01"
    elif policy == "year_to_january_first" and len(parts) == 3:
        return f"{parts[0]}-01-01"
    else:
        return date_str

def pseudonymize_age(age_value: Union[str, int, Any], policy: str) -> str:
    # age_value가 Timestamp일 경우 문자열로 변환
    age_str = str(age_value)
    if policy == "age_to_5year_group":
        return f"{age_str[:-1]}0"
    elif policy == "age_to_10year_group":
        return f"{age_str[:-2]}00"
    else:
        return age_str

# 전역 일련번호 카운터 (여러 파일에서 공유)
_global_serial_counter = 0

def serialize_id(id_value: Union[str, int]) -> str:
    """ID 값을 순차적 일련번호로 변환합니다 (익명화).
    
    호출할 때마다 새로운 일련번호를 할당합니다.
    여러 파일을 처리할 때도 중복되지 않는 고유한 번호를 보장합니다.
    
    매개변수:
        id_value (Union[str, int]): 원본 ID 값 (실제로는 사용하지 않음)
    
    반환값:
        str: 8자리 일련번호 (예: "00000001", "00000002", ...)
    
    주의사항:
        - 동일한 입력이라도 호출할 때마다 다른 번호 반환 (익명화)
        - 전역 카운터로 여러 파일에서도 중복 없는 번호 보장
    """
    global _global_serial_counter
    
    # 매번 새로운 일련번호 할당
    _global_serial_counter += 1
    return str(_global_serial_counter).zfill(8)


#############################
# replace 계열 함수들
#############################
def replace_with_pseudonymized_id(text: str, regex: str, cipher: Any) -> str:
    """텍스트에서 ID 패턴을 찾아 가명화하여 대체하는 함수

    매개변수:
        text (str): 처리할 텍스트
        regex (str): ID를 찾기 위한 정규식
        cipher: get_cipher() 함수로 생성된 FF3 암호화 객체

    반환값:
        str: ID가 가명화로 대체된 텍스트
    """
    matches = re.findall(regex, text)
    if not matches:
        return text
    pseudo_id = pseudonymize_id(matches[0], cipher)
    text = text.replace(matches[0], pseudo_id)
    log_debug(f"[replace_id] with {regex} → {pseudo_id}")
    return text    
  
def replace_with_pseudonymized_date(text: str, regex: str, policy: str) -> str:
    """텍스트에서 날짜 패턴을 찾아 가명화하는 함수.
    
    매개변수:
        text (str): 처리할 텍스트
        regex (str): 날짜를 찾기 위한 정규식
        policy (str): 가명화 정책 ('year_to_january_first', 'month_to_first_day')
    
    반환값:
        str: 날짜가 가명화된 텍스트
    """
    matches = re.findall(regex, text)
    if not matches:
        return text
    pseudo_date = pseudonymize_date(matches[0], policy)
    text = text.replace(matches[0], pseudo_date)
    log_debug(f"[replace_date] with {regex} → {pseudo_date}")
    return text

def replace_with_pseudonymized_age(text: str, regex: str, policy: str) -> str:
    """텍스트에서 나이 패턴을 찾아 가명화하는 함수.

    매개변수:
        text (str): 처리할 텍스트
        regex (str): 나이를 찾기 위한 정규식
        policy (str): 가명화 정책 ('age_to_5year_group', 'age_to_10year_group')

    반환값:
        str: 나이가 가명화된 텍스트
    """
    matches = re.findall(regex, text)
    if not matches:
        return text
    pseudo_age = pseudonymize_age(matches[0], policy)
    text = text.replace(matches[0], pseudo_age)
    log_debug(f"[replace_age] with {regex} → {pseudo_age}")
    return text

def replace_with_serialized_id(text: str, regex: str) -> str:
    """텍스트에서 ID 패턴을 찾아 일련번호로 대체하는 함수.
    
    매개변수:
        text (str): 처리할 텍스트
        regex (str): ID를 찾기 위한 정규식 패턴

    반환값:
        str: ID가 일련번호로 대체된 텍스트
    """
    matches = re.findall(regex, text)
    if not matches:
        return text
    
    serialized_id = serialize_id(matches[0])
    result = text.replace(matches[0], serialized_id)
    log_debug(f"[replace_serialized_id] with {regex} → {serialized_id}")
    return result

def replace_with_masked_id(text: str, regex: str, anonymization_value: str) -> str:
    """텍스트에서 ID 패턴을 찾아 마스킹 값으로 대체하는 함수.
    
    매개변수:
        text (str): 처리할 텍스트
        regex (str): ID를 찾기 위한 정규식 패턴 (named group 포함)
        anonymization_value (str): 대체할 마스킹 값

    반환값:
        str: ID가 마스킹된 텍스트
    """
    def replace_func(match):
        # named group이 있는 경우, 해당 그룹만 anonymization_value로 대체
        # 나머지 부분은 원본 유지
        result = match.group(0)  # 전체 매치 문자열
        for group_name, group_value in match.groupdict().items():
            if group_value is not None:
                result = result.replace(group_value, anonymization_value)
        return result
    
    result = re.sub(regex, replace_func, text)
    log_debug(f"[replace_with_masked_id] with {regex} → {anonymization_value}")
    return result


#############################
# extract 계열 함수들
#############################
def remove_non_targets(df, report_column, target_key, target_conf):
    regex = target_conf.get("regular_expression", "")
    extracted_all = df[report_column].str.extractall(regex, flags=re.M)
    df[report_column] = df[report_column].str.replace(regex, '', regex=True, flags=re.M)

    # 캡처 그룹 검증
    if extracted_all.shape[1] != 1:
        raise ValueError(
            f"[ remvoe_non] '{target_key}' 정규식은 반드시 캡처 그룹 하나만 포함해야 합니다. "
            f"현재 컬럼 수={extracted_all.shape[1]}, regex={regex}"
        )

    colname = extracted_all.columns[0]

    # 각 행당 첫 번째 매치만 사용
    first_matches = (
        extracted_all.groupby(level=0)[colname]
        .first()
        .reindex(df.index)
    )

    # 새로운 컬럼 추가
    new_column_name = f"extracted_{target_key}"
    df[new_column_name] = first_matches

#    log_debug(f"[extract_targets] '{target_key}' 삭제 후 전문:\n{df[report_column].iloc[1]}")
    
    return df

def extract_targets(df, report_column, target_key, target_conf):
    regex = target_conf.get("regular_expression", "")
    extracted_all = df[report_column].str.extractall(regex, flags=re.M)
    # log_debug(f"[extract_targets] target: {target_key}' regex: {regex} \n{extracted_all}")
    # df[report_column] = df[report_column].str.replace(regex, '', regex=True, flags=re.M)
      
    # 캡처 그룹 검증
    if extracted_all.shape[1] != 1:
        raise ValueError(
            f"[extract_targets] '{target_key}' 정규식은 반드시 캡처 그룹 하나만 포함해야 합니다. "
            f"현재 컬럼 수={extracted_all.shape[1]}, regex={regex}"
        )

    colname = extracted_all.columns[0]

    # 각 행당 첫 번째 매치만 사용
    first_matches = (
        extracted_all.groupby(level=0)[colname]
        .first()
        .reindex(df.index)
    )

    # 새로운 컬럼 추가
    new_column_name = f"extracted_{target_key}"
    df[new_column_name] = first_matches

    if target_key == "specimen":
        # "육"이 포함된 경우는 "검 체 :"만 삭제, 아닌 경우는 정규식으로 삭제
        mask = df[new_column_name].str.contains("육", na=False)
        # "육"이 포함된 행: "검 체 :"만 삭제
        df.loc[mask, report_column] = df.loc[mask, report_column].str.replace(r'검\s*체\s*:', '', regex=True)
        # "육"이 포함되지 않은 행: 정규식으로 삭제
        df.loc[~mask, report_column] = df.loc[~mask, report_column].str.replace(regex, '', regex=True, flags=re.M)
        # 디버깅 로그
        log_debug(f"[extract_targets] specimen '육' 포함 mask: {mask.value_counts().to_dict()}")
        log_debug(f"[extract_targets] specimen '육' 포함 행:\n{df.loc[mask, new_column_name]}")

    else:
        df[report_column] = df[report_column].str.replace(regex, '', regex=True, flags=re.M)

    ###로그 출력 (치환 후 데이터 기준)
    print("\n")  # 단순 줄바꿈 출력
    log_debug(
       f"[extract_targets] {target_key} 추출: "
       f"{len(df[report_column])}행, {len(extracted_all)}회\n"
       f"정규식 {regex}\n"
       f"각보고서 첫번째 추출결과:{df[new_column_name].to_string()}"
    )
    # with pd.option_context('display.max_colwidth', None):
    #     log_debug(f"[extract_targets] '{target_key}' 삭제 후 전문:\n{df[report_column].head(2).to_string()}")
    log_debug(f"[extract_targets] '{target_key}' 삭제 후 전문:\n{df[report_column].iloc[1]}")
    return df

def validation_extraction(df, report_column):
    """
    모든 텍스트 추출이 완료된 후, report_column에 줄바꿈(\n, \r, \r\n) 이외의 문자가 남아있는지 검사.
    남아있으면 경고 메시지, 모두 줄바꿈만 남았으면 성공 메시지 출력.
    """
    import re
    # 줄바꿈 문자만 남은 행은 True, 그 외는 False
    only_newline = df[report_column].fillna("").apply(
        lambda x: re.sub(r'[\r\n]', '', x).strip() == ""
    )
    if only_newline.all():
        log_debug("[validation_extraction] 모든 리포트 컬럼이 줄바꿈 문자 이외에는 비어 있습니다. (정상)")
    else:
        remain_idx = only_newline[~only_newline].index.tolist()
        log_debug(f"[validation_extraction][경고] 줄바꿈 이외의 문자가 남아있는 행이 {len(remain_idx)}개 있습니다. index: {remain_idx}")


##############################
# 래핑함수
##############################
def deidentify_columns(df: pd.DataFrame, targets: dict, cipher_alphanumeric: Any, cipher_numeric: Any) -> pd.DataFrame:
    """
    데이터프레임의 개별 컬럼들을 비식별화하는 함수
    """
    target_keys = list(targets.keys())
    log_debug(f"[deidentify_columns] 처리할 타겟: {len(target_keys)}개 - {target_keys}")
    
    for key in target_keys:
        if key not in df.columns:
            log_debug(f"[deidentify_columns] 컬럼 '{key}'가 DataFrame에 존재하지 않음. 건너뜀.")
            continue
        policy = targets[key].get("deidentification_policy", "no_apply")
        if policy == "pseudonymization":
            pseudo_policy = targets[key].get("pseudonymization_policy", "")
            if pseudo_policy == "fpe_numeric":
                df[key] = df[key].apply(lambda x: pseudonymize_id(x, cipher_numeric))
                log_debug(f"[deidentify_columns] 컬럼 '{key}''{ pseudo_policy }' → 1st result: {df[key].iloc[0] if len(df) > 0 else 'N/A'}")
            elif pseudo_policy == "fpe_alphanumeric":
                df[key] = df[key].apply(lambda x: pseudonymize_id(x, cipher_alphanumeric))
                log_debug(f"[deidentify_columns] 컬럼 '{key}''{ pseudo_policy }' → 1st result: {df[key].iloc[0] if len(df) > 0 else 'N/A'}")
            elif pseudo_policy in ("year_to_january_first", "month_to_first_day"):
                df[key] = df[key].apply(lambda x: pseudonymize_date(x, pseudo_policy))
                log_debug(f"[deidentify_columns] 컬럼 '{key}''{ pseudo_policy }' → 1st result: {df[key].iloc[0] if len(df) > 0 else 'N/A'}")    
            elif pseudo_policy in ("age_to_5year_group", "age_to_10year_group"):
                df[key] = df[key].apply(lambda x: pseudonymize_age(x, pseudo_policy))
                log_debug(f"[deidentify_columns] 컬럼 '{key}''{ pseudo_policy }' → 1st result: {df[key].iloc[0] if len(df) > 0 else 'N/A'}")    
            else:
                log_debug(f"[deidentify_columns] 경고: 지원하지 않는 pseudonymization_policy '{pseudo_policy}' (컬럼: '{key}'). 처리를 건너뜁니다.")

        elif policy == "anonymization":
            anonymization_policy = targets[key].get("anonymization_policy", "")
            anonymization_value = targets[key].get("anonymization_value", "")
            if anonymization_policy == "serial_number":
                df[key] = df[key].apply(lambda x: serialize_id(x) if pd.notnull(x) else x)
                log_debug(f"[deidentify_columns] 컬럼 '{key}''{ anonymization_policy }' → 1st result: {df[key].iloc[0] if len(df) > 0 else 'N/A'}")
            elif anonymization_policy == "masking":
                df[key] = df[key].apply(lambda x: anonymization_value if pd.notnull(x) else x)
                log_debug(f"[deidentify_columns] 컬럼 '{key}''{ anonymization_policy }' → 1st result: {df[key].iloc[0] if len(df) > 0 else 'N/A'}")
            else:
                log_debug(f"[deidentify_columns] 경고: 지원하지 않는 anonymization_policy '{anonymization_policy}' (컬럼: '{key}'). 처리를 건너뜁니다.")
        elif policy == "no_apply":
            pass
        else:
            log_debug(f"[deidentify_columns] 지원하지 않는 정책: {policy} (컬럼: {key})")


    return df

def deidentify_report_column(df: pd.DataFrame, report_column: str, targets: dict, cipher_alphanumeric: Any, cipher_numeric: Any) -> pd.DataFrame:
    """
    리포트 텍스트 컬럼 내부의 개인정보를 비식별화하는 함수
    targets 딕셔너리에서 키들을 자동으로 추출하여 처리
    """
    target_keys = list(targets.keys())
    log_debug(f"[deidentify_report_column] 처리할 패턴: {len(target_keys)}개 - {target_keys}")
    
    for key in target_keys:
        policy = targets[key].get("deidentification_policy", "no_apply")
        if policy == "pseudonymization":
            pseudo_policy = targets[key].get("pseudonymization_policy", "")
            if pseudo_policy == "fpe_numeric":
                df[report_column] = df[report_column].apply(lambda x: replace_with_pseudonymized_id(x, targets[key]["regular_expression"], cipher_numeric))
                df = extract_target_to_column(df, report_column, key, targets[key]["regular_expression"])
            elif pseudo_policy == "fpe_alphanumeric":
                df[report_column] = df[report_column].apply(lambda x: replace_with_pseudonymized_id(x, targets[key]["regular_expression"], cipher_alphanumeric))
                df = extract_target_to_column(df, report_column, key, targets[key]["regular_expression"])
            elif pseudo_policy in ("year_to_january_first", "month_to_first_day"):
                df[report_column_name] = df[report_column_name].apply(lambda x: replace_with_pseudonymized_date(x, targets[key]["regular_expression"], pseudo_policy))
                df = extract_target_to_column(df, report_column_name, key, targets[key]["regular_expression"])
            elif pseudo_policy in ("age_to_5year_group", "age_to_10year_group"):
                df[report_column_name] = df[report_column_name].apply(lambda x: replace_with_pseudonymized_age(x, targets[key]["regular_expression"], pseudo_policy))
                df = extract_target_to_column(df, report_column_name, key, targets[key]["regular_expression"])
            else:
                log_debug(f"[deidentify_report_column] 경고: 지원하지 않는 pseudonymization_policy '{pseudo_policy}' (키: '{key}'). 처리를 건너뜁니다.")

        elif policy == "anonymization":
            anonymization_policy = targets[key].get("anonymization_policy", "")
            anonymization_value = targets[key].get("anonymization_value", "")
            if anonymization_policy == "serial_number":
                if key not in df.columns:
                    df[report_column_name] = df[report_column_name].apply(lambda x: replace_with_serialized_id(x, targets[key]["regular_expression"]))
                    df = extract_target_to_column(df, report_column_name, key, targets[key]["regular_expression"])
                else:  # key in df.columns
                    df[report_column_name] = df[report_column_name].apply(lambda x: replace_with_masked_id(x, targets[key]["regular_expression"], anonymization_value) if pd.notnull(x) else x)
            elif anonymization_policy == "masking":
                df[report_column_name] = df[report_column_name].apply(lambda x: replace_with_masked_id(x, targets[key]["regular_expression"], anonymization_value) if pd.notnull(x) else x)
            else:
                log_debug(f"[deidentify_report_column] 경고: 지원하지 않는 anonymization_policy '{anonymization_policy}' (컬럼: '{key}'). 처리를 건너뜁니다.")
        elif policy == "no_apply":
            pass
        else:
            log_debug(f"[deidentify_report_column] 지원하지 않는 정책: {policy} (컬럼: {key})")

    # 모든 개별 비식별화 작업 완료 후, 페이지 머릿글/바닥글 제거
    df[report_column_name] = df[report_column_name].apply(lambda x: remove_page_headers_footers(x) if pd.notnull(x) else x)
    log_debug(f"[deidentify_report_column] 페이지 머릿글/바닥글 제거 완료")

    return df
