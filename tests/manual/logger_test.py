from logger import get_logger, audit_log

if __name__ == "__main__":
    # 운영 로그 샘플
    logger = get_logger("manual_test")
    logger.info("운영 로그 샘플: 시스템 점검 시작")

    # 감사 로그 샘플
    audit_log(
        action="system_check_started",
        detail={"initiator": "manual_test", "target": "logger_test"},
        compliance="개인정보보호법 제28조"
    )
