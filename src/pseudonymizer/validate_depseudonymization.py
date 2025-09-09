import logging
from pathlib import Path
from charset_normalizer import from_path
from common.logger import log_info, log_error, log_warn

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data/raw"
DEPSN_DIR = ROOT / "data/depseudonymized"


def read_file_with_encoding(path: Path) -> tuple[str, str]:
    result = from_path(path).best()
    return str(result), result.encoding

def validate_depseudonymization():
    mismatches = []
    total = 0

    for orig_file in RAW_DIR.glob("*.txt"):
        total += 1
        depseudo_file = DEPSN_DIR / orig_file.name

        if not depseudo_file.exists():
            log_warn(f"파일 없음: {depseudo_file.name}")
            mismatches.append((orig_file.name, "파일 없음"))
            continue

        orig_content, orig_encoding = read_file_with_encoding(orig_file)
        depseudo_content, depseudo_encoding = read_file_with_encoding(depseudo_file)

        if orig_content == depseudo_content:
            log_info(f"{orig_file.name}: 내용 일치")
        else:
            log_error(f"{orig_file.name}: 내용 불일치")
            mismatches.append((orig_file.name, "내용 불일치"))

    # 결과 요약
    log_info("==== 검증 요약 ====")
    log_info(f"총 파일: {total}, 불일치: {len(mismatches)}")
    if mismatches:
        log_info("불일치 파일 목록:")
        for fname, reason in mismatches:
            log_info(f" - {fname}: {reason}")

if __name__ == "__main__":
    validate_depseudonymization()
