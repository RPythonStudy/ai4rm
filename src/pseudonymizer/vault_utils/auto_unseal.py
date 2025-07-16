#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ========================================================
# 파일명: auto_unseal.py
# 설명: Vault 서버를 자동으로 언실하는 유틸리티
#
# 실행 예시:
#   $ python3 src/pseudonymizer/vault_utils/auto_unseal.py
#
# 환경변수:
#   VAULT_ADDR         → Vault 서버 주소 (예: https://vault:8200)
#   UNSEAL_KEYS_FILE   → Unseal 키가 담긴 JSON 파일 경로
#
# 요구 사항:
#   - requests
#   - logger (src/pseudonymizer/logger.py 사용)
# ========================================================

import os
import json
import requests
from logger import get_logger

logger = get_logger("auto_unseal")

VAULT_ADDR = os.getenv("VAULT_ADDR", "https://vault:8200")
UNSEAL_KEYS_FILE = os.getenv("UNSEAL_KEYS_FILE", "/opt/ai4rm/secrets/vault_unseal_keys.json")

def unseal_vault():
    if not os.path.exists(UNSEAL_KEYS_FILE):
        logger.error(f"Unseal 키 파일이 존재하지 않습니다: {UNSEAL_KEYS_FILE}")
        return False

    try:
        with open(UNSEAL_KEYS_FILE, "r") as f:
            keys = json.load(f).get("unseal_keys_b64", [])
            if not keys:
                logger.error("Unseal 키가 존재하지 않습니다.")
                return False

        for i, key in enumerate(keys):
            response = requests.put(
                f"{VAULT_ADDR}/v1/sys/unseal",
                json={"key": key},
                verify=False  # 운영 환경에서는 True로 설정하거나 CA 인증서 필요
            )
            if response.status_code == 200:
                result = response.json()
                logger.info(f"[{i+1}] Vault unseal 응답: sealed={result.get('sealed')}")
                if not result.get("sealed"):
                    logger.info("[SUCCESS] Vault 언실 완료")
                    return True
            else:
                logger.error(f"[{i+1}] Vault 언실 실패: {response.status_code} {response.text}")
                return False

    except Exception as e:
        logger.exception(f"Vault 언실 중 예외 발생: {e}")
        return False

if __name__ == "__main__":
    success = unseal_vault()
    if not success:
        logger.error("[FAIL] Vault 언실 실패")
