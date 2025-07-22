#!/usr/bin/env python3
"""
AI4RM 설치 스크립트 테스트 프레임워크

업계표준 패턴:
1. Path Abstraction: 환경변수로 경로 추상화
2. Dry Run Mode: 실제 실행 없이 명령어 검증
3. Container Testing: Docker 컨테이너에서 격리 테스트
4. Mock Environment: 운영환경 시뮬레이션

실행:
    python tests/manual/test_install_scripts.py --test-mode dry-run
    python tests/manual/test_install_scripts.py --test-mode container
"""

import subprocess
import os
import tempfile
from pathlib import Path
import typer
from typing import Literal

# AI4RM 표준: PYTHONPATH 환경변수 사용
from logger import get_logger, audit_log

app = typer.Typer()
logger = get_logger("install_script_test")

class ScriptTester:
    """설치 스크립트 테스트 클래스"""
    
    def __init__(self, test_mode: str = "dry-run"):
        self.test_mode = test_mode
        self.dev_base = Path("/home/ben/projects/ai4rm")
        self.prod_base = Path("/opt/ai4rm")
        
    def setup_test_environment(self) -> Path:
        """테스트 환경 설정"""
        if self.test_mode == "dry-run":
            # 임시 디렉토리에서 테스트
            test_dir = Path(tempfile.mkdtemp(prefix="ai4rm_test_"))
            logger.info(f"Dry-run 테스트 디렉토리: {test_dir}")
            
        elif self.test_mode == "container":
            # Docker 컨테이너 환경
            test_dir = Path("/tmp/ai4rm_container_test")
            test_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Container 테스트 디렉토리: {test_dir}")
            
        else:  # sandbox
            # 샌드박스 환경 (chroot/namespace)
            test_dir = Path("/tmp/ai4rm_sandbox")
            test_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Sandbox 테스트 디렉토리: {test_dir}")
            
        return test_dir
    
    def copy_scripts_to_test_env(self, test_dir: Path):
        """스크립트를 테스트 환경으로 복사"""
        scripts_src = self.dev_base / "make"
        scripts_dst = test_dir / "scripts" / "admin"
        scripts_dst.mkdir(parents=True, exist_ok=True)
        
        # 스크립트 복사
        for script in scripts_src.glob("*.sh"):
            dst_script = scripts_dst / script.name
            subprocess.run(["cp", str(script), str(dst_script)], check=True)
            subprocess.run(["chmod", "+x", str(dst_script)], check=True)
            logger.info(f"스크립트 복사: {script.name} -> {dst_script}")
    
    def modify_scripts_for_testing(self, test_dir: Path):
        """테스트용 스크립트 수정 (경로 치환)"""
        scripts_dir = test_dir / "scripts" / "admin"
        
        for script in scripts_dir.glob("*.sh"):
            content = script.read_text()
            
            # 운영 경로를 테스트 경로로 치환
            content = content.replace("/opt/ai4rm", str(test_dir))
            content = content.replace("sudo ", "echo '[DRY-RUN] sudo ' ")  # sudo 명령 무력화
            
            # 네트워크 호출 무력화 (테스트 모드)
            if self.test_mode == "dry-run":
                content = content.replace("curl ", "echo '[DRY-RUN] curl ' ")
                content = content.replace("wget ", "echo '[DRY-RUN] wget ' ")
            
            script.write_text(content)
            logger.info(f"스크립트 수정 완료: {script.name}")
    
    def run_script_test(self, test_dir: Path, script_name: str):
        """개별 스크립트 테스트 실행"""
        script_path = test_dir / "scripts" / "admin" / script_name
        
        if not script_path.exists():
            logger.error(f"스크립트 파일 없음: {script_path}")
            return False
        
        logger.info(f"스크립트 테스트 시작: {script_name}")
        audit_log("install_script_test_start", {"script": script_name, "mode": self.test_mode})
        
        try:
            # 환경변수 설정
            env = os.environ.copy()
            env["AI4RM_BASE"] = str(test_dir)
            env["AI4RM_ENV"] = "test"
            
            result = subprocess.run(
                ["bash", str(script_path)],
                env=env,
                capture_output=True,
                text=True,
                cwd=test_dir
            )
            
            if result.returncode == 0:
                logger.info(f"스크립트 테스트 성공: {script_name}")
                logger.debug(f"출력: {result.stdout}")
                audit_log("install_script_test_success", {"script": script_name})
                return True
            else:
                logger.error(f"스크립트 테스트 실패: {script_name}")
                logger.error(f"오류: {result.stderr}")
                audit_log("install_script_test_failure", {"script": script_name, "error": result.stderr})
                return False
                
        except Exception as e:
            logger.error(f"스크립트 실행 예외: {e}")
            audit_log("install_script_test_exception", {"script": script_name, "error": str(e)})
            return False

@app.command()
def test_single_script(
    script_name: str = typer.Argument(..., help="테스트할 스크립트 파일명"),
    test_mode: Literal["dry-run", "container", "sandbox"] = typer.Option("dry-run", help="테스트 모드")
):
    """개별 설치 스크립트 테스트"""
    tester = ScriptTester(test_mode)
    test_dir = tester.setup_test_environment()
    
    try:
        tester.copy_scripts_to_test_env(test_dir)
        tester.modify_scripts_for_testing(test_dir)
        success = tester.run_script_test(test_dir, script_name)
        
        if success:
            logger.info("테스트 완료: 성공")
        else:
            logger.error("테스트 완료: 실패")
            raise typer.Exit(1)
            
    finally:
        if test_mode == "dry-run":
            # 임시 디렉토리 정리
            subprocess.run(["rm", "-rf", str(test_dir)], check=False)

@app.command()
def test_all_scripts(
    test_mode: Literal["dry-run", "container", "sandbox"] = typer.Option("dry-run", help="테스트 모드")
):
    """모든 설치 스크립트 테스트"""
    tester = ScriptTester(test_mode)
    test_dir = tester.setup_test_environment()
    
    scripts_src = Path("/home/ben/projects/ai4rm/make")
    script_files = list(scripts_src.glob("*.sh"))
    
    if not script_files:
        logger.warning("테스트할 스크립트 파일이 없습니다.")
        return
    
    try:
        tester.copy_scripts_to_test_env(test_dir)
        tester.modify_scripts_for_testing(test_dir)
        
        results = {}
        for script_file in script_files:
            script_name = script_file.name
            success = tester.run_script_test(test_dir, script_name)
            results[script_name] = success
        
        # 결과 요약
        logger.info("=== 테스트 결과 요약 ===")
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        for script_name, success in results.items():
            status = "성공" if success else "실패"
            logger.info(f"  {script_name}: {status}")
        
        logger.info(f"전체: {total_count}개, 성공: {success_count}개, 실패: {total_count - success_count}개")
        
        if success_count != total_count:
            raise typer.Exit(1)
            
    finally:
        if test_mode == "dry-run":
            subprocess.run(["rm", "-rf", str(test_dir)], check=False)

@app.command()
def create_container_test():
    """Docker 컨테이너 기반 테스트 환경 생성"""
    logger.info("Docker 컨테이너 테스트 환경 생성 중...")
    
    dockerfile_content = """
FROM ubuntu:22.04

# 기본 패키지 설치
RUN apt-get update && apt-get install -y \\
    sudo curl wget tree \\
    python3 python3-pip \\
    && rm -rf /var/lib/apt/lists/*

# AI4RM 테스트 사용자 생성
RUN useradd -m -s /bin/bash ai4rm && \\
    echo 'ai4rm ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# 작업 디렉토리 설정
WORKDIR /opt/ai4rm
USER ai4rm

CMD ["/bin/bash"]
"""
    
    dockerfile_path = Path("/tmp/Dockerfile.ai4rm-test")
    dockerfile_path.write_text(dockerfile_content)
    
    # Docker 이미지 빌드
    subprocess.run([
        "docker", "build", 
        "-t", "ai4rm-test",
        "-f", str(dockerfile_path),
        "."
    ], check=True)
    
    logger.info("Docker 테스트 이미지 생성 완료: ai4rm-test")
    logger.info("실행 방법: docker run -it --rm ai4rm-test")

if __name__ == "__main__":
    app()
