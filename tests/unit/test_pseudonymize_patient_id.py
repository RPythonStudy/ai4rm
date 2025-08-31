# tests/unit/test_pseudonymize_patient_id.py
# 단위테스트 3: patient_id 가명화 및 복호화 기능 검증

import os
import re
import pytest
from dotenv import load_dotenv
from pseudonymizer.pseudonymizer_pathology_report import pseudonymize_patient_id
from ff3 import FF3Cipher
from common.get_cipher import get_cipher

# ------------------------
# 테스트 전용 복호화 함수
# ------------------------
def depseudonymize_patient_id(content: str):
    """
    테스트 전용 복호화 함수.
    - 개발/테스트: .env에서 FF3_KEY, FF3_TWEAK, FF3_ALPHABET 로드
    - 운영: Vault 연동 (테스트에는 사용하지 않음)
    """
    if content is None:
        return ""

    cipher = get_cipher()

    restored = content
    matches = re.findall(r"\d{8}", content)
    for enc_id in matches:
        dec_id = cipher.decrypt(enc_id)
        restored = restored.replace(enc_id, dec_id)

    return restored

# ------------------------
# 테스트 케이스
# ------------------------

def test_pseudonymize_patient_id_basic():
    content = "등록번호 12345678"
    pseudonymized = pseudonymize_patient_id(content)

    # 원본 ID가 그대로 남아 있으면 안 됨
    assert "12345678" not in pseudonymized

    # 여전히 8자리 숫자 형태 유지
    m = re.search(r"\d{8}", pseudonymized)
    assert m is not None

def test_pseudonymize_patient_id_consistency():
    content = "등록번호 12345678"
    result1 = pseudonymize_patient_id(content)
    result2 = pseudonymize_patient_id(content)
    assert result1 == result2

def test_pseudonymize_patient_id_no_match():
    content = "등록번호 없음"
    result = pseudonymize_patient_id(content)
    assert result == content

def test_pseudonymize_patient_id_none_input():
    result = pseudonymize_patient_id(None)
    assert result == ""

def test_patient_id_encrypt_decrypt_pair():
    """암호화-복호화 페어 검증"""
    content = "등록번호 12345678"
    pseudonymized = pseudonymize_patient_id(content)

    assert "12345678" not in pseudonymized  # 원본 그대로 노출되면 안 됨

    restored = depseudonymize_patient_id(pseudonymized)
    assert "12345678" in restored           # 복호화하면 원본 복원
