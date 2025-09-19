import re
import shutil
from pathlib import Path
from ff3 import FF3Cipher
from charset_normalizer import from_path  # encoding 감지용
from common.logger import log_info, log_error
from dotenv import load_dotenv
import os


load_dotenv()

KEY = os.getenv("FF3_KEY")
TWEAK = os.getenv("FF3_TWEAK")
ALPHABET = os.getenv("FF3_ALPHABET")
if not KEY or not TWEAK or not ALPHABET:
    raise RuntimeError("필수 환경변수(FF3_KEY, FF3_TWEAK, FF3_ALPHABET)가 설정되어 있지 않습니다.")
cipher = FF3Cipher.withCustomAlphabet(KEY, TWEAK, ALPHABET)

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data/raw"
PSEUDO_DIR = ROOT / "data/pseudonymized"
PSEUDO_DIR.mkdir(parents=True, exist_ok=True)

def ff3_pad(msg: str, minlen: int = 6) -> str:
    return msg.rjust(minlen, '0')

def read_file_with_encoding(path: Path) -> tuple[str, str]:
    result = from_path(path).best()
    return str(result), result.encoding

def pseudonymize_patient_id(regno: str) -> str:
    return cipher.encrypt(ff3_pad(regno))

def pseudonymize_file(file: Path):
    original_id = file.stem
    pseudonym_id = pseudonymize_patient_id(original_id)
    try:
        content, encoding = read_file_with_encoding(file)
        # 등록번호 치환
        content = re.sub(
            r"(등록번호\s*:\s*)" + re.escape(original_id),
            lambda m: f"{m.group(1)}{pseudonym_id}",
            content
        )
        out_path = PSEUDO_DIR / f"{pseudonym_id}.txt"
        out_path.write_text(content, encoding=encoding)
        log_info(f"✔ {file.name} → {out_path.name} ({encoding})")
        return True
    except Exception as e:
        log_error(f"❌ 가명화 실패: {file.name}")
        return False

def main():
    log_info("가명화 처리 시작")
    total, success, fail = 0, 0, 0
    for file in RAW_DIR.glob("*.txt"):
        total += 1
        result = pseudonymize_file(file)
        if result:
            success += 1
        else:
            fail += 1
    log_info(f"가명화 처리 완료: 전체 {total}건, 성공 {success}건, 실패 {fail}건")

if __name__ == "__main__":
    main()
