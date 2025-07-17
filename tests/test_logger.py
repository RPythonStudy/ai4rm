import os
import logging
import tempfile
import shutil
import pytest
from pathlib import Path
from logger.logger import get_logger, _resolve_log_level, setup_logging, TRACE_LEVEL_NUM

def test_trace_level_addition():
    logger = get_logger("test_trace")
    assert hasattr(logger, "trace")
    logger.setLevel(TRACE_LEVEL_NUM)
    # TRACE 레벨 로그가 정상적으로 기록되는지 확인
    logger.trace("trace message")  # 예외 없이 동작하면 성공


def test_env_loading(monkeypatch, tmp_path):
    # .env 파일 생성 및 환경변수 반영 확인
    env_file = tmp_path / ".env"
    env_file.write_text("LOG_LEVEL=ERROR\n")
    monkeypatch.chdir(tmp_path)
    from logger.logger import _load_dotenv
    _load_dotenv()
    assert os.getenv("LOG_LEVEL") == "ERROR"


def test_resolve_log_level_priority(monkeypatch):
    # 1. 명령행 인자 우선
    assert _resolve_log_level("DEBUG", None) == "DEBUG"
    # 2. 환경변수 우선
    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    assert _resolve_log_level(None, None) == "ERROR"
    # 3. yaml 설정 우선
    yaml_cfg = {"root": {"level": "WARNING"}}
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    assert _resolve_log_level(None, yaml_cfg) == "WARNING"
    # 4. 기본값
    assert _resolve_log_level(None, None) == "INFO"


def test_setup_logging_creates_handlers(tmp_path, monkeypatch):
    # logs/dev.log 파일 생성 확인 및 핸들러 정상 동작
    log_dir = tmp_path / "logs"
    config_dir = tmp_path / "config"
    log_dir.mkdir()
    config_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    setup_logging("INFO")
    logger = get_logger("test_setup")
    logger.info("test message")
    log_file = log_dir / "dev.log"
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "test message" in content
