# tests/test_detect_text_file_encoding.py
# GS 인증: 기능 정확성/일관성 검증
# utf-8, euc-kr, cp949, utf-16, ascii에 대해서 인코딩이 올바르게 감지되는지 assert (반환값에 flexibility 인정하여 두 개의 후보 인코딩을 반환할 수 있음)
# binary로 열었는지에 대해서도 assert
# iso2022_kr에 대해서도 assert
# edge 빈 파일에 대해서도 assert

import os
import tempfile
import pytest
from pseudonymizer.pseudonymizer_pathology_report import detect_text_file_encoding


@pytest.mark.parametrize("encoding,text,expect_candidates", [
    ("utf-8", "테스트 데이터", ["utf-8", "utf8"]),
    ("euc-kr", "한글 데이터", ["euc-kr", "cp949", "949"]),
    ("cp949", "한글 데이터", ["euc-kr", "cp949", "949"]),
    ("utf-16", "테스트 데이터", ["utf-16"]),
    ("ascii", "test data", ["ascii"]),
])
def test_various_encodings(encoding, text, expect_candidates):
    with tempfile.NamedTemporaryFile("w", encoding=encoding, delete=False) as f:
        f.write(text)
        fname = f.name
    enc, raw = detect_text_file_encoding(fname)
    enc_lower = enc.lower()
    assert any(candidate in enc_lower for candidate in expect_candidates), f"Got {enc} for {encoding}"
    assert isinstance(raw, bytes)
    os.remove(fname)

def test_iso2022kr_encoding():
    """환경에 따라 실패할 수 있으므로 LookupError 허용"""
    try:
        with tempfile.NamedTemporaryFile("w", encoding="iso2022_kr", delete=False) as f:
            f.write("한글 데이터")
            fname = f.name
        enc, raw = detect_text_file_encoding(fname)
        assert "2022" in enc or "kr" in enc.lower()
        assert isinstance(raw, bytes)
        os.remove(fname)
    except LookupError:
        pytest.skip("ISO-2022-KR not supported in this environment")


def test_empty_file():
    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        fname = f.name
    enc, raw = detect_text_file_encoding(fname)
    assert enc is None or enc.lower() == "ascii"
    assert raw == b""
    os.remove(fname)


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        detect_text_file_encoding("non_existent_file.txt")
