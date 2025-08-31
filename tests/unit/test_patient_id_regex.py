# tests/unit/test_patient_id_regex.py
# GS 인증: 기능 정확성 - patient_id 정규식 탐지
# last modified: 2025-08-31

import re
import pytest
from pseudonymizer.pseudonymizer_pathology_report import load_config_pseudonymization_pathology_report


@pytest.fixture(scope="module")
def patient_id_regex():
    cfg = load_config_pseudonymization_pathology_report()
    return re.compile(cfg["patient_id"]["regular_expression"])


@pytest.mark.parametrize("text,expected", [
    ("등록번호 12345678", ["12345678"]),
    ("등록번호:12345678", ["12345678"]),
    ("등록번호：12345678", ["12345678"]),  # 전각 콜론
    ("등록번호    12345678", ["12345678"]),
    ("환자의 등록번호 87654321 입니다.", ["87654321"]),
])
def test_regex_matches_valid_cases(patient_id_regex, text, expected):
    m = patient_id_regex.findall(text)
    assert m == expected


@pytest.mark.parametrize("text", [
    "등록번호1234567",      # 7자리 → 불일치
    "등록번호 123456789",   # 9자리 → 불일치
    "환자ID 12345678",     # '등록번호' 키워드 없으면 불일치
    "등록번호 ABCDEFGH",   # 숫자가 아님
])
def test_regex_does_not_match_invalid_cases(patient_id_regex, text):
    m = patient_id_regex.findall(text)
    assert m == []
