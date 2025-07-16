import os
import sys
import logging
import logging.config
import yaml
from pathlib import Path
from dotenv import load_dotenv

# 1. TRACE 레벨 추가
TRACE_LEVEL_NUM = 5
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")
def trace(self, message, *args, **kwargs):
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        self._log(TRACE_LEVEL_NUM, message, args, **kwargs)
logging.Logger.trace = trace

# 2. .env에서 환경변수 로드 (.env가 없으면 무시)
def _load_dotenv():
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)

# 3. 로그레벨 결정 우선순위 함수
def _resolve_log_level(cli_log_level=None, yaml_config=None):
    LOG_LEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"]
    # 1. 명령행 인자
    if cli_log_level:
        level = cli_log_level.upper()
        if level in LOG_LEVELS:
            return level
    # 2. 환경변수(.env 포함)
    env_level = os.getenv("LOG_LEVEL", "").upper()
    if env_level in LOG_LEVELS:
        return env_level
    # 3. yaml 설정
    if yaml_config:
        root_cfg = yaml_config.get("root", {})
        yaml_level = str(root_cfg.get("level", "")).upper()
        if yaml_level in LOG_LEVELS:
            return yaml_level
    # 4. 기본값
    return "INFO"

# 4. 로깅 구성 함수
def setup_logging(cli_log_level=None):
    _load_dotenv()
    config_path = Path("config/logging.yaml")
    log_file_path = Path("logs/dev.log")
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    yaml_config = None
    if config_path.exists():
        with open(config_path, "r") as f:
            yaml_config = yaml.safe_load(f)
    level = _resolve_log_level(cli_log_level, yaml_config)
    numeric_level = getattr(logging, level, logging.INFO)

    if yaml_config:
        # 명령행/환경변수 값이 있으면 root.level 및 각 핸들러 level 강제 덮어쓰기
        yaml_config.setdefault("root", {})
        yaml_config["root"]["level"] = level
        if "handlers" in yaml_config:
            for h in yaml_config["handlers"].values():
                h["level"] = level
        logging.config.dictConfig(yaml_config)
    else:
        # 기본(내장) 핸들러: stdout(텍스트) + 파일(json)
        from logging import Formatter, StreamHandler, FileHandler
        import json

        class JsonLogFormatter(Formatter):
            def format(self, record):
                record_dict = {
                    "timestamp": self.formatTime(record, self.datefmt),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "pathname": record.pathname,
                    "lineno": record.lineno,
                    "funcName": record.funcName,
                }
                if record.exc_info:
                    record_dict["exc_info"] = self.formatException(record.exc_info)
                return json.dumps(record_dict, ensure_ascii=False)

        stream_formatter = Formatter("[%(asctime)s] [%(levelname)s] %(name)s - %(message)s")
        stream_handler = StreamHandler(sys.stdout)
        stream_handler.setLevel(numeric_level)
        stream_handler.setFormatter(stream_formatter)

        file_formatter = JsonLogFormatter()
        file_handler = FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(file_formatter)

        logging.basicConfig(
            level=numeric_level,
            handlers=[stream_handler, file_handler]
        )

# 5. 외부 제공 함수
def get_logger(name: str = "ai4rm", cli_log_level=None) -> logging.Logger:
    """
    ai4rm 프로젝트 표준 로거 인스턴스 생성  
    최초 호출 시 로깅설정, 이후엔 캐시
    - cli_log_level: Typer/Click 인자로 받은 로그레벨 (없으면 None)
    """
    root_logger = logging.getLogger()
    if not root_logger.hasHandlers():
        setup_logging(cli_log_level)
    return logging.getLogger(name)
