# -*- coding: utf-8 -*-
"""
파일명: src/security_infra/auto_unseal.py

기능:
    - /mnt/usb 디렉토리에 "[계정이메일].enc" 형태로 저장된
      비밀번호 파일을 모두 읽어서, 각 Bitwarden 계정별로
      logout → login → unlock → unseal key 추출 → vault unseal 자동화
    - vault가 해제되면 루프 즉시 중단 (미래지향적 버전)
    - 디버깅 및 예외 처리 강화

실행:
    python src/security_infra/auto_unseal.py

설정:
    .env 또는 환경변수로 VAULT_ADDR, BW_SERVER 등 지정 (미지정시 기본값)
"""

import os
import subprocess
import json
import requests
import urllib3
import traceback

from logger import get_logger




# Bitwarden 인증서 문제 회피용 환경변수 설정
# (self-signed 인증서로 인한 node fetch 오류 방지)
import os
os.environ["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"

# 표준 로거 사용 (.env의 LOG_LEVEL 자동 반영)
logger = get_logger("vault_unseal")

USB_PATH = "/mnt/usb"
VAULT_ADDR = os.environ.get("VAULT_ADDR", "https://localhost:8200")
UNSEAL_KEY_FIELD = "unseal key"   # Bitwarden 필드명 (필요시 변경)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_bw_accounts_and_passwords(usb_path):
    accounts = []
    for filename in os.listdir(usb_path):
        if filename.endswith(".enc"):
            account = filename.replace(".enc", "")
            pw_file = os.path.join(usb_path, filename)
            with open(pw_file, "r") as f:
                password = f.read().strip()
            accounts.append((account, password))
    return accounts

def login_bw_account(account, password):
    env = os.environ.copy()
    env["BW_PASSWORD"] = password
    try:
        subprocess.run(
            ["bw", "logout"], env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        subprocess.check_output(
            ["bw", "login", account, "--passwordenv", "BW_PASSWORD"],
            env=env,
            stderr=subprocess.STDOUT
        )
        print(f"[SUCCESS] {account} 로그인 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {account} 로그인 실패:\n{e.output.decode()}")
        return False

def unlock_bw_account(account, password):
    env = os.environ.copy()
    env["BW_PASSWORD"] = password
    try:
        bw_session = subprocess.check_output(
            ["bw", "unlock", "--raw", "--passwordenv", "BW_PASSWORD"],
            env=env,
            stderr=subprocess.STDOUT
        ).decode().strip()
        print(f"[SUCCESS] {account} 세션 획득 (앞8글자): {bw_session[:8]}...")
        return bw_session
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {account} unlock 실패:\n{e.output.decode()}")
        return None

def extract_unseal_key(bw_session, field_name=UNSEAL_KEY_FIELD):
    try:
        print(f"[DEBUG] bw list items 호출 시작")
        result = subprocess.check_output(
            ["bw", "list", "items", "--session", bw_session],
            stderr=subprocess.STDOUT,
            timeout=60
        )
        try:
            preview = result.decode(errors="replace")[:500]
        except Exception:
            preview = str(result[:200])
        print(f"[DEBUG] bw list items 결과 미리보기:\n{preview}")

        print(f"[DEBUG] JSON 파싱 시도")
        items = json.loads(result)
        print(f"[DEBUG] JSON 파싱 성공, 항목 수: {len(items)}")
        for item in items:
            if 'fields' in item:
                for field in item['fields']:
                    print(f"[DEBUG] field.name: {field.get('name')}")
                    if field['name'].lower() == field_name.lower():
                        print(f"[DEBUG] 언실키 발견: {field['value'][:8]}... (길이 {len(field['value'])})")
                        return field['value']
        print("[WARN] 언실키 필드가 없습니다.")
        return None
    except subprocess.TimeoutExpired:
        print("[ERROR] bw list items 명령이 60초 이상 걸려 중단되었습니다. (timeout)")
        traceback.print_exc()
        return None
    except KeyboardInterrupt:
        print("[INTERRUPT] 사용자가 Ctrl+C로 중단했습니다.")
        traceback.print_exc()
        return None
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 언실키 추출 실패 (subprocess):\n{e.output.decode()}")
        traceback.print_exc()
        return None
    except Exception as e:
        print(f"[ERROR] 언실키 추출 실패 (기타): {e}")
        traceback.print_exc()
        return None

def vault_unseal(unseal_key, vault_addr=VAULT_ADDR):
    try:
        url = f"{vault_addr}/v1/sys/unseal"
        logger.debug(f"VAULT_ADDR: {vault_addr}")
        logger.debug(f"Vault 요청 URL: {url}")
        logger.debug(f"Vault 요청 프로토콜: {'HTTPS' if url.startswith('https://') else 'HTTP'}")
        resp = requests.put(url, json={"key": unseal_key}, verify=False, timeout=5)
        logger.debug(f"Vault 응답 status_code: {resp.status_code}")
        try:
            resp_json = resp.json()
        except Exception:
            resp_json = resp.text
        logger.info(f"Vault 응답: {resp_json}")
        # sealed가 False면 더 이상 언실 필요 없음
        if isinstance(resp_json, dict) and not resp_json.get('sealed', True):
            return True
        return False
    except Exception as e:
        logger.error(f"Vault 언실 요청 실패: {e}")
        return False

def main():
    logger.info("Vault Auto-unseal 프로세스 시작")
    
    try:
        accounts = get_bw_accounts_and_passwords(USB_PATH)
        logger.info(f"감지된 계정/비밀번호 쌍: {len(accounts)}개")
        
        if not accounts:
            logger.warning("USB 경로에서 계정 파일을 찾을 수 없습니다")
            return
            
        for account, password in accounts:
            logger.info(f"Bitwarden login 시도: {account}")
            login_ok = login_bw_account(account, password)
            if not login_ok:
                logger.warning(f"{account} 로그인 실패 - 다음 계정으로 진행")
                continue
                
            logger.info(f"Bitwarden unlock 시도: {account}")
            bw_session = unlock_bw_account(account, password)
            if not bw_session:
                logger.error(f"{account} unlock 실패 - 세션 획득 불가")
                continue
                
            logger.info(f"{account} 언실키 추출 시도")
            unseal_key = extract_unseal_key(bw_session)
            if unseal_key:
                logger.debug(f"언실키 길이 확인: {len(unseal_key)} 문자")
                logger.info(f"{account} 언실 시도")
                unsealed = vault_unseal(unseal_key, VAULT_ADDR)
                if unsealed:
                    logger.info("Vault 언실 성공 - 프로세스 완료")
                    break
                else:
                    logger.error(f"{account} Vault 언실 실패")
            else:
                logger.warning(f"{account} 언실키 추출 실패")
                
        logger.info("Vault Auto-unseal 프로세스 종료")
        
    except Exception as e:
        logger.critical(f"Auto-unseal 프로세스 중대 오류: {str(e)}")
        raise

if __name__ == "__main__":
    main()
