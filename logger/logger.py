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
    """
    .env 파일이 있으면 환경변수를 로드합니다.
    """
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)

# 3. 로그레벨 결정 우선순위 함수
def _resolve_log_level(cli_log_level=None, yml_config=None):
    """
    로그레벨 결정 우선순위:
    1. 명령행 인자
    2. 환경변수 LOG_LEVEL
    3. yml 설정파일의 root.level
    4. 기본값 INFO
    """
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
    if yml_config:
        root_cfg = yml_config.get("root", {})
        yaml_level = str(root_cfg.get("level", "")).upper()
        if yaml_level in LOG_LEVELS:
            return yaml_level
    # 4. 기본값
    return "INFO"

# 4. 로깅 구성 함수
def setup_logging(cli_log_level=None):
    """
    로깅 설정을 초기화합니다.
    - 환경변수 LOG_LEVEL, 명령행 인자, 설정파일 우선순위 적용
    - 설정파일 파싱 실패 시 기본 핸들러로 fallback
    - 로그 파일 경로는 환경변수 LOG_PATH로 오버라이드 가능
    """
    _load_dotenv()
    config_path = Path("config/logging.yml")
    log_file_path = Path(os.getenv("LOG_PATH", "logs/dev.log"))
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    yml_config = None
    try:
        if config_path.exists():
            with open(config_path, "r") as f:
                yml_config = yaml.safe_load(f)
    except Exception as e:
        print(f"[WARN] logging.yml 파싱 실패: {e}. 기본 핸들러로 fallback.")
        yml_config = None

    level = _resolve_log_level(cli_log_level, yml_config)
    numeric_level = getattr(logging, level, logging.INFO)

    if yml_config:
        # 명령행/환경변수 값이 있으면 root.level 및 각 핸들러 level 강제 덮어쓰기
        yml_config.setdefault("root", {})
        yml_config["root"]["level"] = level
        # 핸들러별 레벨 분리 옵션: 환경변수 LOG_HANDLER_LEVEL_{HANDLER} 사용 가능
        if "handlers" in yml_config:
            for h_name, h in yml_config["handlers"].items():
                env_handler_level = os.getenv(f"LOG_HANDLER_LEVEL_{h_name.upper()}", None)
                if env_handler_level and env_handler_level.upper() in ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"]:
                    h["level"] = env_handler_level.upper()
                else:
                    h["level"] = level
        logging.config.dictConfig(yml_config)
    else:
        # 기본(내장) 핸들러: stdout(텍스트) + 파일(json)
        from logging import Formatter, StreamHandler, FileHandler
        import json

        class JsonLogFormatter(Formatter):
            """JSON 포맷 로그 핸들러"""
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
    - name: logger 이름 (ai4rm, audit 등)
    - cli_log_level: Typer/Click 인자로 받은 로그레벨 (없으면 None)
    """
    root_logger = logging.getLogger()
    if not root_logger.hasHandlers():
        setup_logging(cli_log_level)
    return logging.getLogger(name)


# 표준 감사로그 함수
import socket
from datetime import datetime, timezone

def audit_log(action: str, detail: dict = None, compliance: str = "개인정보보호법 제28조"):
    """
    AI4RM 표준 감사 로그 기록 함수
    - action: 이벤트명 (필수)
    - detail: dict (추가 상세정보, 선택)
    - compliance: 컴플라이언스 조항명 (기본값: 개인정보보호법 제28조)
    """
    audit_logger = get_logger("audit")
    user = os.getenv("USER") or "unknown"
    log = {
        "action": action,
        "user": user,
        "process_id": os.getpid(),
        "server_id": socket.gethostname(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "compliance_check": compliance
    }
    if detail:
        log.update(detail)
    audit_logger.info(log)
