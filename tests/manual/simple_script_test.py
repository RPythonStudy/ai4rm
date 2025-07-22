#!/usr/bin/env python3
"""
AI4RM 설치 스크립트 단순 테스트 프레임워크

기능:
- 개발환경 스크립트를 임시 디렉토리에서 테스트
- Dry-run 모드로 안전한 테스트 수행
- 운영 경로 시뮬레이션

실행:
    python tests/manual/simple_script_test.py install_bitwarden.sh
"""

import subprocess
import tempfile
import shutil
from pathlib import Path
import typer

# AI4RM 표준: PYTHONPATH 환경변수 사용
from logger import get_logger, audit_log

app = typer.Typer()
logger = get_logger("script_test")

@app.command()
def test_script(script_name: str = typer.Argument(..., help="테스트할 스크립트 파일명")):
    """개발환경 설치 스크립트를 안전하게 테스트"""
    
    # 1. 원본 스크립트 경로
    dev_scripts_dir = Path("/home/ben/projects/ai4rm/make")
    original_script = dev_scripts_dir / script_name
    
    if not original_script.exists():
        logger.error(f"스크립트 파일이 존재하지 않습니다: {original_script}")
        raise typer.Exit(1)
    
    # 2. 임시 테스트 환경 생성
    test_dir = Path(tempfile.mkdtemp(prefix="ai4rm_test_"))
    logger.info(f"테스트 디렉토리: {test_dir}")
    
    try:
        # 3. 스크립트 복사 및 수정
        test_script = test_dir / script_name
        shutil.copy2(original_script, test_script)
        
        # 4. 테스트용 경로 치환
        content = test_script.read_text()
        
        # 운영 경로 → 테스트 경로 치환
        content = content.replace("/opt/ai4rm", str(test_dir))
        
        # 위험한 명령어 dry-run 변환
        content = content.replace("sudo ", "echo '[DRY-RUN] sudo ' ")
        content = content.replace("curl ", "echo '[DRY-RUN] curl ' ")
        content = content.replace("wget ", "echo '[DRY-RUN] wget ' ")
        
        test_script.write_text(content)
        test_script.chmod(0o755)
        
        logger.info(f"테스트용 스크립트 준비 완료: {test_script}")
        
        # 5. 스크립트 실행
        logger.info("스크립트 테스트 시작")
        audit_log("install_script_test", {"script": script_name, "test_dir": str(test_dir)})
        
        result = subprocess.run(
            ["bash", str(test_script)],
            cwd=test_dir,
            capture_output=True,
            text=True
        )
        
        # 6. 결과 출력
        if result.stdout:
            logger.info("스크립트 출력:")
            for line in result.stdout.strip().split('\n'):
                logger.info(f"  {line}")
        
        if result.stderr:
            logger.warning("스크립트 오류:")
            for line in result.stderr.strip().split('\n'):
                logger.warning(f"  {line}")
        
        if result.returncode == 0:
            logger.info("스크립트 테스트 성공")
            audit_log("install_script_test_success", {"script": script_name})
        else:
            logger.error(f"스크립트 테스트 실패 (exit code: {result.returncode})")
            audit_log("install_script_test_failure", {"script": script_name, "exit_code": result.returncode})
            raise typer.Exit(1)
            
    finally:
        # 7. 임시 디렉토리 정리
        shutil.rmtree(test_dir)
        logger.info("테스트 디렉토리 정리 완료")

@app.command()
def list_scripts():
    """사용 가능한 설치 스크립트 목록 출력"""
    scripts_dir = Path("/home/ben/projects/ai4rm/make")
    
    if not scripts_dir.exists():
        logger.error("scripts 디렉토리가 존재하지 않습니다.")
        return
    
    scripts = list(scripts_dir.glob("*.sh"))
    
    if not scripts:
        logger.warning("사용 가능한 스크립트가 없습니다.")
        return
    
    logger.info("사용 가능한 설치 스크립트:")
    for script in scripts:
        logger.info(f"  {script.name}")

if __name__ == "__main__":
    app()
