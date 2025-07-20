
from pathlib import Path
import subprocess
import os
from datetime import datetime, timezone
import socket
import logging
from logger import get_logger

def run_cmd(cmd: str):
    """명령어 실행 및 오류 처리"""
    logger = get_logger("cert_utils")
    logger.debug(f"명령 실행: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        logger.error(f"명령어 실패: {cmd}")
        raise RuntimeError(f"명령어 실패: {cmd}")



def audit_log(action: str, detail: dict = None, compliance: str = "예시 개인정보보호법 제28조"):
    audit_logger = logging.getLogger("audit")
    user = os.getenv("USER") or os.getenv("LOGNAME") or "unknown"
    process_id = os.getpid()
    server_id = socket.gethostname()
    log = {
        "action": action,
        "user": user,
        "process_id": process_id,
        "server_id": server_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "compliance_check": compliance
    }
    if detail:
        log.update(detail)
    audit_logger.info(log)

def generate_self_signed_cert(key_path, crt_path, cn="localhost", san_list=None, days=14, owner="100:100"):
    """
    자가서명 인증서 생성 함수 (공통)
    Args:
        key_path (str or Path): 키 파일 경로
        crt_path (str or Path): 인증서 파일 경로
        cn (str): Common Name
        san_list (list): Subject Alternative Name 리스트
        days (int): 유효기간(일)
        owner (str): chown 소유자
    """
    logger = get_logger("cert_utils")
    key_path = str(key_path)
    crt_path = str(crt_path)
    san = ", ".join(san_list) if san_list else "DNS:localhost"
    if Path(key_path).exists() and Path(crt_path).exists():
        logger.info(f"인증서가 이미 존재하여 생성하지 않음: {crt_path}")
        audit_log(
            action="cert_exists",
            detail={"crt_path": crt_path},
        )
        return
    cmd = (
        f"sudo openssl req -x509 -newkey rsa:2048 "
        f"-keyout {key_path} -out {crt_path} -days {days} -nodes "
        f'-subj "/CN={cn}" '
        f'-addext "subjectAltName = {san}" '
        f">/dev/null 2>&1"
    )
    logger.debug(f"인증서 생성 명령: {cmd}")
    try:
        run_cmd(cmd)
        run_cmd(f"sudo chown {owner} {key_path} {crt_path}")
        run_cmd(f"sudo chmod 640 {key_path} {crt_path}")
        logger.info(f"인증서 생성 완료: {crt_path}")
        audit_log(
            action="cert_created",
            detail={"crt_path": crt_path, "key_path": key_path},
        )
    except Exception as e:
        logger.error(f"인증서 생성 실패: {e}")
        audit_log(
            action="cert_create_failed",
            detail={"error": str(e), "crt_path": crt_path},
        )
