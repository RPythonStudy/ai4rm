#!/usr/bin/env python3
"""
AI4RM sudo subprocess 테스트 스크립트 (logger 포함)

기능:
- sudo 명령 실행 가능 여부 테스트
- AI4RM 표준 로거 사용

실행:
    python tests/manual/test_sudo_subprocess.py
"""

import subprocess
import typer

# AI4RM 표준: PYTHONPATH 환경변수 사용 (sys.path 조작 금지)
from logger import get_logger

app = typer.Typer()
logger = get_logger("sudo_test")

@app.command()
def test():
    """sudo 실행 가능 여부 테스트"""
    base_path = "/tmp/ai4rm_test"
    logger.info("sudo 테스트 시작")
    subprocess.run(["sudo", "mkdir", "-p", f"{base_path}/scripts/admin"], check=True)
    logger.info(f"sudo 테스트 완료: {base_path}")

if __name__ == "__main__":
    app()
