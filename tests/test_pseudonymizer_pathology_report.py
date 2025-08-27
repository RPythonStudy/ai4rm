# pytest for pseudonymizer_pathology_report.py
# - 인코딩 감지, 파일 읽기, patient_id 가명화, 엣지케이스(값 없음) 등 주요 함수의 동작을 검증
# - 파일 입출력은 임시파일/임시디렉토리로 테스트
# - 설정 기반 정규식 및 정책 적용 결과를 확인
# last-modified: 2025-08-27

import os
import tempfile
import pytest
from pseudonymizer.pseudonymizer_pathology_report import (
    detect_text_file_encoding,
    read_text_files,
    pseudonymize_patient_id,
)

def test_detect_text_file_encoding_utf8():
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as f:
        f.write('테스트')
        fname = f.name
    enc, raw = detect_text_file_encoding(fname)
    assert enc.lower().startswith('utf')
    os.remove(fname)

def test_read_text_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        fname = os.path.join(tmpdir, 'sample.txt')
        with open(fname, 'w', encoding='utf-8') as f:
            f.write('등록번호: 12345678 환 자 명: 홍길동 ')
        result = read_text_files(tmpdir)
        assert 'sample.txt' in result
        assert '12345678' in result['sample.txt']

def test_pseudonymize_patient_id():
    text = '등록번호: 12345678 환 자 명: 홍길동 '
    pseudonymized = pseudonymize_patient_id(text)
    assert '87654321' in pseudonymized
    assert '12345678' not in pseudonymized


def test_edge_case_no_patient_id():
    text = '환 자 명: 홍길동 '
    pseudonymized = pseudonymize_patient_id(text)
    assert pseudonymized == text

