"""
파일명: src/common/get_cipher.py
목적: Format Preserver Encryption 제공
기능: 
  - .env 파일에서 FF3_KEY, FF3_TWEAK, FF3_ALPHABET 읽어옴
  - alphabet 인자로 숫자로만 출력할지 결정  
변경이력:
  - 2025-09-18: 최초 생성 (BenKorea)
"""

import os

from common.logger import log_critical, log_debug
from dotenv import load_dotenv
from ff3 import FF3Cipher

def get_cipher(alphabet_type="default"):
    load_dotenv()
    KEY = os.getenv("FF3_KEY")
    TWEAK = os.getenv("FF3_TWEAK")
    if alphabet_type == "digit":
        ALPHABET = os.getenv("FF3_ALPHABET_digit")
    else:
        ALPHABET = os.getenv("FF3_ALPHABET")
    log_debug(f"[get_cipher] alphabet_type = {alphabet_type}")

    if not KEY or not TWEAK or not ALPHABET:
        log_critical("필수 환경변수(FF3_KEY, FF3_TWEAK, FF3_ALPHABET)가 누락되었습니다.")
        raise RuntimeError("필수 환경변수(FF3_KEY, FF3_TWEAK, FF3_ALPHABET)가 누락되었습니다.")
    return FF3Cipher.withCustomAlphabet(KEY, TWEAK, ALPHABET)
