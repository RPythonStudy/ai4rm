import os
from dotenv import load_dotenv
import pandas as pd
from ff3 import FF3Cipher
from common.logger import log_info, log_error, log_critical
from pathlib import Path

load_dotenv()
KEY = os.getenv("FF3_KEY")
TWEAK = os.getenv("FF3_TWEAK")
ALPHABET = os.getenv("FF3_ALPHABET")

if not KEY or not TWEAK or not ALPHABET:
    log_critical("필수 환경변수(FF3_KEY, FF3_TWEAK, FF3_ALPHABET)가 누락되었습니다.")
    raise RuntimeError("필수 환경변수(FF3_KEY, FF3_TWEAK, FF3_ALPHABET)가 누락되었습니다.")

cipher = FF3Cipher.withCustomAlphabet(KEY, TWEAK, ALPHABET)

def pseudonymize_ptid(ptid):
    return cipher.encrypt(str(ptid).rjust(6, '0'))

def pseudonymize_excel(infile, outfile, target_col):
    log_info(f"엑셀 파일 가명화 시작: {infile} → {outfile}")
    try:
        df = pd.read_excel(infile)
    except Exception as e:
        log_error(f"엑셀 파일 읽기 실패: {infile}, 에러: {e}")
        return False
    if target_col not in df.columns:
        log_error(f"{target_col} 컬럼이 없습니다.")
        return False
    df[f"{target_col}_pseudo"] = df[target_col].apply(pseudonymize_ptid)
    try:
        df.to_excel(outfile, index=False)
        log_info(f"엑셀 파일 저장 완료: {outfile}")
        return True
    except Exception as e:
        log_error(f"엑셀 파일 저장 실패: {outfile}, 에러: {e}")
        return False

if __name__ == "__main__":
    import sys
    RAW_DIR = Path("data/raw")
    OUT_DIR = Path("data/pseudonymized")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) != 2:
        log_error("사용법: python excel_pseudonymizer.py <가명화할 컬럼명>")
        print("사용법: python excel_pseudonymizer.py <가명화할 컬럼명>")
        exit(1)

    target_col = sys.argv[1]
    files = list(RAW_DIR.glob("*.xlsx")) + list(RAW_DIR.glob("*.xls"))
    if not files:
        log_error(f"입력 폴더에 엑셀 파일이 없습니다: {RAW_DIR}")
        exit(1)
    total, success, fail = 0, 0, 0
    for infile in files:
        total += 1
        outfile = OUT_DIR / f"pseudonymized_{infile.name}"
        result = pseudonymize_excel(infile, outfile, target_col)
        if result:
            success += 1
        else:
            fail += 1
    log_info(f"가명화 처리 완료: 전체 {total}건, 성공 {success}건, 실패 {fail}건")
    