# src/common/get_cipher.py
# last modified: 2025-09-10

import os
from ff3 import FF3Cipher
from dotenv import load_dotenv
from common.logger import log_critical

def get_cipher(alphabet_type="default"):
    load_dotenv()
    KEY = os.getenv("FF3_KEY")
    TWEAK = os.getenv("FF3_TWEAK")
    if alphabet_type == "digit":
        ALPHABET = os.getenv("FF3_ALPHABET_digit")
    else:
        ALPHABET = os.getenv("FF3_ALPHABET")
    if not KEY or not TWEAK or not ALPHABET:
        log_critical("필수 환경변수(FF3_KEY, FF3_TWEAK, FF3_ALPHABET)가 누락되었습니다.")
        raise RuntimeError("필수 환경변수(FF3_KEY, FF3_TWEAK, FF3_ALPHABET)가 누락되었습니다.")
    return FF3Cipher.withCustomAlphabet(KEY, TWEAK, ALPHABET)
