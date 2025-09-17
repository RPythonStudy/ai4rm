# tests/unit/test_detect_text_file_encoding.py
# GS 인증: 기능 정확성/일관성 검증
# utf-8, euc-kr, cp949, utf-16, ascii에 대해서 인코딩이 올바르게 감지되는지 assert (반환값에 flexibility 인정하여 두 개의 후보 인코딩을 반환할 수 있음)
# binary로 열었는지에 대해서도 assert
# iso2022_kr에 대해서도 assert
# edge 빈 파일에 대해서도 assert
# 인코딩이 인식되지 않더라도 crash 없이 utf-8로 fallback 되는지 assert
# 메모리누수 점검
# last modified: 2025-09-10

import os
import tempfile
import psutil

import pytest
from deidentifier.pseudonymizer_pathology_report import detect_text_file_encoding


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
    """환경에 따라 utf-8 등으로 감지될 수 있음"""
    try:
        with tempfile.NamedTemporaryFile("w", encoding="iso2022_kr", delete=False) as f:
            f.write("한글 데이터")
            fname = f.name
        enc, raw = detect_text_file_encoding(fname)
        # iso2022_kr로 저장했지만, utf-8로 감지될 수도 있음
        assert any(cand in enc.lower() for cand in ["2022", "kr", "utf-8"])
        assert isinstance(raw, bytes)
        os.remove(fname)
    except LookupError:
        pytest.skip("iso2022_kr not supported in this environment")


def test_empty_file():
    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        fname = f.name
    enc, raw = detect_text_file_encoding(fname)
    # chardet는 빈 파일을 ascii 또는 utf-8로 추측 가능
    assert enc is None or enc.lower() in ["ascii", "utf-8"]
    assert raw == b""
    os.remove(fname)


def test_corrupted_file(tmp_path):
    # 손상된 파일
    fname = tmp_path / "corrupted.txt"
    with open(fname, "wb") as f:
        f.write(b"\xff\xfe\xfa\xfb")

    enc, raw = detect_text_file_encoding(fname)
    # 크래시 없이 결과만 나오면 됨 (utf-16 등도 가능)
    allowed = ["ascii", "utf-8", "utf-16", "iso-8859-1"]
    assert enc is None or any(enc.lower().startswith(a) for a in allowed)
    assert isinstance(raw, bytes)

def test_fallback_on_unknown_encoding(monkeypatch, tmp_path):
    # 1. 임시 파일 생성 (내용은 아무거나)
    fname = tmp_path / "dummy.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write("테스트 데이터")

    # 2. chardet.detect를 강제로 잘못된 인코딩 리턴하게 패치
    def fake_detect(_):
        return {"encoding": "unknown-charset"}
    monkeypatch.setattr("pseudonymizer.pseudonymizer_pathology_report.chardet.detect", fake_detect)

    # 3. 함수 실행
    enc, raw = detect_text_file_encoding(fname)

    # 4. 검증: unknown 인코딩은 utf-8로 fallback 되어야 함
    assert enc == "utf-8"
    assert isinstance(raw, bytes)
        
def test_memory_leak_on_repeated_calls(tmp_path):
    """detect_text_file_encoding을 반복 호출했을 때 메모리 누수가 없는지 확인"""
    # 1. 임시 파일 생성
    fname = tmp_path / "repeat.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write("테스트 데이터")

    # 2. 현재 프로세스 메모리 사용량 기록
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss

    # 3. 반복 호출 (횟수는 성능 고려해서 조절 가능: 5천~1만)
    for i in range(5000):
        enc, raw = detect_text_file_encoding(fname)
        assert enc is not None
        assert isinstance(raw, bytes)

    # 4. 호출 후 메모리 사용량 기록
    mem_after = process.memory_info().rss

    # 5. 검증: 메모리 사용량이 과도하게 늘지 않아야 함 (예: 5MB 이내 증가 허용)
    leak_bytes = mem_after - mem_before
    assert leak_bytes < 5 * 1024 * 1024, f"메모리 누수 의심: {leak_bytes/1024/1024:.2f} MB 증가"
