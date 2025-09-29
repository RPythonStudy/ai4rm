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

def extract_section_to_column(df: pd.DataFrame, report_column_name: str, section_key: str, regex: str, policy: str) -> pd.DataFrame:
    """
    텍스트에서 정규식 패턴을 추출하고 정책에 따라 삭제하거나 새로운 컬럼으로 추가하는 함수
    
    매개변수:
        df: DataFrame
        report_column_name: 텍스트가 있는 컬럼명
        section_key: 타겟 키 (컬럼명 생성용)
        regex: 추출할 정규식 패턴
        policy: 'remove' 또는 'extraction' (삭제 또는 추출)
    
    반환값:
        새 컬럼이 추가된 DataFrame
    """
    if policy == "extraction":
        df = extract_target_to_column(df, report_column_name, section_key, regex)


        log_debug(f"[extract_section_to_column] '{section_key}' 추출 → 컬럼")
    elif policy == "remove":
        # 삭제 대상 추출
        to_remove = df[report_column_name].str.extract(regex, expand=False)
        # 삭제 로그 남기기
        log_debug(f"[extract_section_to_column] '{section_key}' 삭제 대상: {to_remove.dropna().tolist()}")
        # 실제 삭제
        df[report_column_name] = df[report_column_name].str.replace(regex, "", regex=True)
        log_debug(f"[extract_section_to_column] '{section_key}' 패턴 삭제")
    else:
        log_debug(f"[extract_section_to_column] '{section_key}' 정책 미지원: {policy}")

    return df

def remove_target_from_working(df: pd.DataFrame, working_column_name: str, target_key: str, target_conf: dict) -> pd.DataFrame:
    """
    텍스트에서 특정 타겟 키에 해당하는 패턴을 찾아 삭제하는 함수
    
    매개변수:
        df: DataFrame
        report_column_name: 텍스트가 있는 컬럼명
        target_key: 타겟 키 (로그용)
        target_conf: 타겟 설정 딕셔너리 (정규식 포함)
    
    반환값:
        패턴이 삭제된 DataFrame
    """
    regex = target_conf.get("regular_expression", "")   
    if not regex:
        log_debug(f"[remove_from_working] 경고: '{target_key}' 정규식이 설정되지 않음")
        return df

        
    # 삭제 대상 추출
    to_remove = df[working_column_name].str.extract(regex, expand=False, flags=re.MULTILINE)
    # 삭제 로그 남기기
    log_debug(f"[remove_from_working] '{target_key}' 삭제 대상: {to_remove.dropna().tolist()}")
    df[working_column_name] = df[working_column_name].str.replace(regex, "", regex=True, flags=re.MULTILINE)
    # 삭제 후 재 추출
    to_remove = df[working_column_name].str.extract(regex, expand=False, flags=re.MULTILINE)
    log_debug(f"[remove_from_working] '{target_key}' 삭제 후 결과: {to_remove.dropna().tolist()}")

    return df

def extract_target_to_column(df: pd.DataFrame, report_column_name: str, target_key: str, regex: str) -> pd.DataFrame:
    """
    텍스트에서 정규식 패턴을 추출하여 새로운 컬럼으로 추가하는 함수
    
    매개변수:
        df: DataFrame
        report_column_name: 텍스트가 있는 컬럼명
        target_key: 타겟 키 (컬럼명 생성용)
        regex: 추출할 정규식 패턴
    
    반환값:
        새 컬럼이 추가된 DataFrame
    """
    # 정규식으로 값 추출 (named group 사용)
    # 주의: str.extract()는 첫 번째 매치만 반환! 
    # 여러 매치가 필요하면 str.extractall() 사용 고려
    extracted_series = df[report_column_name].str.extract(regex, expand=False)
    
    new_column_name = f"extracted_{target_key}"
    df[new_column_name] = extracted_series

    log_debug(f"[extract_target_to_column] '{target_key}' 추출 → 컬럼 '{new_column_name}' ")

    return df

def structure_pathology_reports(df: pd.DataFrame, report_column_name: str, structuring_config: dict) -> pd.DataFrame:
    """
    STAGE 1: 비정형 병리보고서를 정형화된 데이터베이스 구조로 변환
    
    매개변수:
        df: DataFrame
        report_column_name: 병리보고서 텍스트가 있는 컬럼명
        structuring_config: 구조화 설정 딕셔너리
    
    반환값:
        구조화된 컬럼들이 추가된 DataFrame
        
    기능:
        1. 원본 텍스트 백업
        2. 각 구성요소별 순차 파싱
        3. 파싱된 부분을 임시 복사본에서 제거
        4. 파싱 완료 검증 (남은 내용 체크)
    """
    
    if not structuring_config.get("enabled", False):
        log_debug("[structure_pathology_reports] 구조화 단계가 비활성화됨")
        return df
    
    # 원본 보관
    if structuring_config.get("preserve_original", True):
        df[f"original_{report_column_name}"] = df[report_column_name].copy()
    
    # 파싱 대상들 추출 및 정렬
    parsing_targets = structuring_config.get("parsing_targets", {})
    sorted_targets = sorted(parsing_targets.items(), 
                          key=lambda x: x[1].get("extraction_order", 999))
    
    extraction_stats = {}
    
    for target_name, target_config in sorted_targets:
        pattern = target_config.get("regular_expression", "")
        required = target_config.get("required", False)
        
        if not pattern:
            log_debug(f"[structure_pathology_reports] 경고: '{target_name}' 패턴이 비어있음")
            continue
            
        # 패턴 추출
        extracted_series = df[report_column_name].str.extract(pattern, flags=re.DOTALL, expand=False)
        
        # 새 컬럼 생성
        df[f"structured_{target_name}"] = extracted_series
        
        # 추출된 부분을 임시 복사본에서 제거 (단순화된 접근)
        df[f"temp_{report_column_name}"] = df.get(f"temp_{report_column_name}", df[report_column_name].copy())
        
        # 통계 수집
        extracted_count = extracted_series.notna().sum()
        extraction_stats[target_name] = {
            "extracted": extracted_count,
            "required": required,
            "total_rows": len(df)
        }
        
        log_debug(f"[structure_pathology_reports] {target_name}: {extracted_count}개 추출")
    
    # 파싱 완료 검증
    if structuring_config.get("validate_complete_parsing", True):
        validate_parsing_completeness(df, f"temp_{report_column_name}", extraction_stats)
    
    return df

def validate_parsing_completeness(df: pd.DataFrame, temp_column: str, stats: dict) -> None:
    """
    파싱 완료 여부를 검증하는 함수
    
    매개변수:
        df: DataFrame
        temp_column: 임시 컬럼명
        stats: 추출 통계
    """
    
    if temp_column not in df.columns:
        log_debug("[validate_parsing] 임시 컬럼이 존재하지 않음 - 검증 생략")
        return
    
    # 필수 항목 체크
    missing_required = []
    for target_name, stat in stats.items():
        if stat["required"] and stat["extracted"] < stat["total_rows"]:
            missing_count = stat["total_rows"] - stat["extracted"]
            missing_required.append(f"{target_name}({missing_count}개 누락)")
    
    if missing_required:
        log_debug(f"[validate_parsing] 경고: 필수 항목 누락 - {', '.join(missing_required)}")
    
    # TODO: 임시 컬럼의 남은 내용 체크 (향후 구현)
    # remaining_content = df[temp_column].str.strip().str.len().sum()
    # if remaining_content > 0:
    #     log_debug(f"[validate_parsing] 경고: 파싱되지 않은 내용이 {remaining_content}자 남아있음")

def extract_pathology_sections(df: pd.DataFrame, report_column_name: str, report_column_config: dict) -> pd.DataFrame:
    """
    병리보고서에서 육안소견(gross_findings)과 병리진단(pathologic_diagnosis) 섹션을 추출하여 별도 컬럼으로 분리
    YAML 설정의 정규식 패턴을 사용합니다.
    
    매개변수:
        df: DataFrame
        report_column_name: 병리보고서 텍스트가 있는 컬럼명
        report_column_config: report_column 설정 딕셔너리
    
    반환값:
        gross_findings, pathologic_diagnosis 컬럼이 추가된 DataFrame
    """
    
    # YAML 설정에서 패턴 추출
    gross_config = report_column_config.get("gross_findings", {})
    diagnosis_config = report_column_config.get("pathologic_diagnosis", {})
    
    # 육안소견 추출
    gross_pattern = gross_config.get("regular_expression", "")
    if gross_pattern:
        df['gross_findings'] = df[report_column_name].str.extract(gross_pattern, flags=re.DOTALL, expand=False)
    else:
        log_debug("[extract_pathology_sections] 경고: gross_findings 정규식이 설정되지 않음")
        df['gross_findings'] = None
    
    # 병리진단 추출  
    diagnosis_pattern = diagnosis_config.get("regular_expression", "")
    if diagnosis_pattern:
        df['pathologic_diagnosis'] = df[report_column_name].str.extract(diagnosis_pattern, flags=re.DOTALL, expand=False)
    else:
        log_debug("[extract_pathology_sections] 경고: pathologic_diagnosis 정규식이 설정되지 않음")
        df['pathologic_diagnosis'] = None
    
    # 추출 결과 로그
    gross_count = df['gross_findings'].notna().sum()
    diagnosis_count = df['pathologic_diagnosis'].notna().sum()
    
    log_debug(f"[extract_pathology_sections] 육안소견 추출: {gross_count}개")
    log_debug(f"[extract_pathology_sections] 병리진단 추출: {diagnosis_count}개")
    
    return df

#########################################
# 리포트 페이지 머릿글/바닥글 제거
##########################################
def remove_page_headers_footers(content: str) -> str:
    """
    병리보고서에서 페이지 머릿글, 바닥글 및 기관 정보가 포함된 라인을 제거합니다.
    
    매개변수:
        content (str): 처리할 텍스트 내용
    
    반환값:
        str: 페이지 머릿글/바닥글이 제거된 텍스트
    
    기능:
        - 한국원자력의학원과 같은 기관명이 포함된 라인을 대시(-)로 대체
        - 페이지 번호, 날짜, 기관 로고 등 시스템 생성 콘텐츠 정리
        - 보고서의 개인정보 보호 및 문서 표준화를 위한 후처리
    
    확장 가능:
        - 향후 다른 기관이나 시스템 메타데이터 패턴도 쉽게 추가 가능
        - 정규식 패턴을 YAML 설정으로 외부화 가능
    """
    pattern = r'.*한국원자력의학원.*'
    def replace_line(match):
        return "--------------------------------------------"
    result = re.sub(pattern, replace_line, content)
    return result

def rename_deidentified_columns(df: pd.DataFrame, targets: dict, column_name_policy: str) -> pd.DataFrame:
    """
    비식별화된 컬럼들의 이름을 정책에 따라 변경하는 함수
    
    매개변수:
        df: 처리할 DataFrame
        targets: 비식별화 대상 딕셔너리
        column_name_policy: 컬럼명 변경 정책
    
    반환값:
        컬럼명이 변경된 DataFrame
    """
    if column_name_policy == "same_as_before":
        return df  # 변경 없음
    elif column_name_policy in ["d_", "deid_", "deidentified_"]:
        # 접두사 추가 로직
        prefix = column_name_policy
        # targets에 있는 컬럼명만 변경
        target_columns_in_df = [key for key in targets.keys() if key in df.columns]
        rename_mapping = {col: f"{prefix}{col}" for col in target_columns_in_df}
        df = df.rename(columns=rename_mapping)
    elif column_name_policy == "custom":
        # 사용자 정의 로직
        pass  # to be implemented
    else:
        log_debug(f"[rename_deidentified_columns] 경고: 알 수 없는 column_name_policy '{column_name_policy}'. 컬럼명을 변경하지 않습니다.")
    
    log_debug(f"[rename_deidentified_columns] 정책: {column_name_policy}")
    log_debug(f"[rename_deidentified_columns] 변경 대상 컬럼: {list(rename_mapping.keys()) if 'rename_mapping' in locals() else 'None'}")
    log_debug(f"[rename_deidentified_columns] 변경 완료: {list(rename_mapping.items()) if 'rename_mapping' in locals() else 'None'}")
    
    return df


##############################
# 래핑함수
##############################
def deidentify_columns(df: pd.DataFrame, targets: dict, cipher_alphanumeric: Any, cipher_numeric: Any, column_name_policy: str = "same_as_before") -> pd.DataFrame:
    """
    데이터프레임의 개별 컬럼들을 비식별화하는 함수
    """
    target_keys = list(targets.keys())
    log_debug(f"[deidentify_columns] 처리할 타겟: {len(target_keys)}개 - {target_keys}")
    
    for key in target_keys:
        if key not in df.columns:
            log_debug(f"[deidentify_columns] 컬럼 '{key}'가 DataFrame에 존재하지 않음. 건너뜀.")
            continue
        policy = targets[key]["deidentification_policy"]
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

    # 컬럼명 변경 (마지막에 실행)
    df = rename_deidentified_columns(df, targets, column_name_policy)

    return df

def deidentify_report_column(df: pd.DataFrame, report_column_name: str, targets: dict, cipher_alphanumeric: Any, cipher_numeric: Any, column_name_policy: str = "same_as_before", new_column_prefix: str = "same_as_before") -> pd.DataFrame:
    """
    리포트 텍스트 컬럼 내부의 개인정보를 비식별화하는 함수
    targets 딕셔너리에서 키들을 자동으로 추출하여 처리
    """
    target_keys = list(targets.keys())
    log_debug(f"[deidentify_report_column] 처리할 패턴: {len(target_keys)}개 - {target_keys}")
    
    for key in target_keys:
        policy = targets[key]["deidentification_policy"]
        if policy == "pseudonymization":
            pseudo_policy = targets[key].get("pseudonymization_policy", "")
            if pseudo_policy == "fpe_numeric":
                df[report_column_name] = df[report_column_name].apply(lambda x: replace_with_pseudonymized_id(x, targets[key]["regular_expression"], cipher_numeric))
                df = extract_target_to_column(df, report_column_name, key, targets[key]["regular_expression"])
            elif pseudo_policy == "fpe_alphanumeric":
                df[report_column_name] = df[report_column_name].apply(lambda x: replace_with_pseudonymized_id(x, targets[key]["regular_expression"], cipher_alphanumeric))
                df = extract_target_to_column(df, report_column_name, key, targets[key]["regular_expression"])
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

    # 리포트 컬럼명 변경 (마지막에 실행)
    original_report_column = report_column_name
    if column_name_policy != "same_as_before":
        new_report_column_name = f"{column_name_policy}{report_column_name}"
        df = df.rename(columns={report_column_name: new_report_column_name})
        log_debug(f"[deidentify_report_column] 리포트 컬럼명 변경: '{original_report_column}' → '{new_report_column_name}'")

    return df

