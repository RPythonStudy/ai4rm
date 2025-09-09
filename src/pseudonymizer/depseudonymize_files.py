import re
from pathlib import Path
from ff3 import FF3Cipher
from charset_normalizer import from_path  # encoding 자동 인식
from common.logger import log_info, log_error


# 암호화 설정
KEY = '0123456789abcdef0123456789abcdef'
TWEAK = 'abcdef12345678'
ALPHABET = '0123456789'
cipher = FF3Cipher.withCustomAlphabet(KEY, TWEAK, ALPHABET)

ROOT = Path(__file__).resolve().parents[2]
PSEUDO_DIR = ROOT / "data/pseudonymized"
DEPSN_DIR = ROOT / "data/depseudonymized"
DEPSN_DIR.mkdir(parents=True, exist_ok=True)

def ff3_pad(msg: str, minlen: int = 6) -> str:
    return msg.rjust(minlen, '0')

def depseudonymize_patient_id(pseudonym_id: str) -> str:
    # 복호화 후 8자리가 안 되면 왼쪽을 "0"으로 패딩
    original_id = cipher.decrypt(pseudonym_id).lstrip("0")
    return original_id.rjust(8, "0")

def read_file_with_encoding(path: Path) -> tuple[str, str]:
    result = from_path(path).best()
    return str(result), result.encoding

def depseudonymize_file(file: Path):
    pseudonym_id = file.stem
    original_id = depseudonymize_patient_id(pseudonym_id)
    content, encoding = read_file_with_encoding(file)
    # 본문 내 등록번호 복원
    content = re.sub(
        r"(등록번호\s*:\s*)" + re.escape(pseudonym_id),
        lambda m: f"{m.group(1)}{original_id}",
        content
    )
    out_path = DEPSN_DIR / f"{original_id}.txt"
    out_path.write_text(content, encoding=encoding)
    log_info(f"{file.name} → {out_path.name} (encoding: {encoding})")

def main():
    log_info("복호화 작업 시작")
    total, success, fail = 0, 0, 0
    for file in PSEUDO_DIR.glob("*.txt"):
        total += 1
        try:
            depseudonymize_file(file)
            success += 1
        except Exception as e:
            log_error(f"복호화 실패: {file.name}")
            fail += 1
    log_info(f"복호화 완료: 전체 {total}건, 성공 {success}건, 실패 {fail}건")

if __name__ == "__main__":
    main()
