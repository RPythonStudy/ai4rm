from logger import get_logger

logger = get_logger("ai4rm")
logger.info("테스트 로그: 서비스 로그입니다.")

audit_logger = get_logger("audit")
audit_logger.info("테스트 로그: 감사 로그입니다.")