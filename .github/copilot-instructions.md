# AI4RM 의료데이터 가명화·활용 플랫폼 개발 가이드

## 프로젝트 개요

AI4RM은 의료 데이터 가명화·활용 플랫폼입니다. 병리보고서, 영상 판독 등의 의료 데이터를 개인정보보호법에 적합하도록 가명화하고, 이를 정형화/메타데이터화하여 AI 앱 개발을 포함한 임상연구를 지원하고자 합니다. 또한 가명화된 연구용 PACS 연계 및 방사선의학 영상검사 선량분석도 지원하고자 합니다.

## 핵심 기능 및 Service Architecture

src/
├── pseudonymizer/   # FF1 FPE 알고리즘 기반 환자정보 가명화/복호화
├── metafier/        # 생성형AI API 기반 비정형→정형 메타데이터 변환  
├── verifier/        # 변환 결과 정합성 검증 (원본↔변환 일치성)
└── nmidose/         # 핵의학 선량정보 분석 (DICOM metadata 기반)


### 보안 Infrastructure Stack
- **HashiCorp Vault**: 비밀관리 및 PKI 인증서
- **Keycloak**: 통합 인증 및 권한관리  
- **ELK Stack**: Elasticsearch/Logstash/Kibana 기반 로그관리
- **Bitwarden**: Password Manager 연동
- **OpenLDAP**: Directory Service


## 프로젝트 전반 지침

**이모지/이모티콘 사용 금지:**
AI4RM 프로젝트의 모든 코드, 문서, 커밋 메시지, 로그, 주석, 출력 등에서 이모지(emoji) 및 이모티콘(emoticon)은 사용하지 않습니다. 
의료/컴플라이언스 환경에 맞는 전문적이고 일관된 표현만 허용합니다.
생성형AI에서는 업계표준과 초고수입장에서의 코드와 시스템을 제안합니다.

## 필수 개발 표준

### 1. 로깅/감사 시스템 (필수)

AI4RM 프로젝트는 의료데이터 처리 특성상 **운영 로그와 감사 로그(Audit Logging)를  기록**해야 하며, 컴플라이언스(개인정보보호법/GDPR) 준수와 감사 추적이 필수입니다.

#### 1.1 표준 로거 사용
```python
from logger import get_logger
logger = get_logger("service_name")
```

#### 1.2 6단계 로그 레벨
```python
logger.critical("시스템 중단 수준 오류")  # DB 연결실패, 암호화 키 손실
logger.error("오류 발생")              # 파일 처리 실패, API 호출 오류  
logger.warning("주의 필요")            # 권한 부족, 설정 누락
logger.info("일반 정보")               # 작업 시작/완료, 처리 건수
logger.debug("디버깅 정보")             # 변수 값, 함수 호출 흐름
logger.trace("상세 추적")              # 데이터 변환 과정
```

#### 1.3 감사 로그(Audit Log) 기록 패턴
모든 개인정보 처리, 인증서 생성, 주요 이벤트는 운영 로그와 별도로 감사 로그로도 기록해야 합니다.
감사 로그에는 반드시 아래 정보가 포함되어야 합니다:
- action(이벤트명)
- user(처리자)
- process_id, server_id
- timestamp(UTC)
- compliance_check(예: 개인정보보호법 제28조)
예시:
```python
import logging
from datetime import datetime, timezone
import os, socket

def audit_log(action: str, detail: dict = None, compliance: str = "개인정보보호법 제28조"):
    audit_logger = logging.getLogger("audit")
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
```

#### 1.4 감사 로그 핸들러 분리 (logging.yaml 예시)
감사 로그는 별도 파일(`logs/audit.log`) 및 ELK Stack으로 전송되도록 핸들러를 분리합니다.
```yaml
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: simple
    stream: ext://sys.stdout
  service_file:
    class: logging.FileHandler
    level: INFO
    formatter: json
    filename: /var/log/ai4rm/service.log
    encoding: utf-8
  audit_file:
    class: logging.FileHandler
    level: INFO
    formatter: json
    filename: /var/log/ai4rm/audit.log
    encoding: utf-8

```

### 2. import 및 Module 구조
PYTHONPATH 기반 import 사용 (`sys.path` 조작 금지):


## 보안 및 컴플라이언스 요구사항

### 개인정보보호법 & GDPR 준수사항

- **데이터 최소화**: 필요 최소한의 데이터만 처리
- **목적 제한**: 명시된 목적에만 데이터 사용  
- **투명성**: 모든 처리 과정 문서화
- **책임성**: 처리 책임자 명확화


## Docker Infrastructure 패턴

### 표준 docker-compose.yml 구조
```yaml
services:
  pseudonymizer:
    build: ./infra/Dockerfile.pseudonymizer
    environment:
      - VAULT_ADDR=https://vault:8200
      - LOG_LEVEL=INFO
    volumes:
      - ./docker/vault/certs:/vault/certs
    networks:
      - ai4rm-network
```

### 디렉토리 구조 일관성
- **개발환경**: `projects/ai4rm/`
- **운영환경**: `/opt/ai4rm/`  
- **일관성 유지**: 개발-테스트-운영 동일 경로


## 테스트 전략

### pytest 기반 테스트 구조
```python
# tests/ 디렉토리 구조
tests/
├── unit/           # 단위 테스트
├── integration/    # 통합 테스트  
└── manual/         # 수동 테스트

# Vault Mocking 패턴
import pytest
from unittest.mock import patch

@pytest.fixture
def mock_vault():
    with patch('vault_utils.VaultClient') as mock:
        yield mock
```


## 운영 및 모니터링

### ELK Stack 활용
- **Elasticsearch**: 로그 저장 및 검색
- **Logstash**: 로그 pipeline 처리
- **Kibana**: Dashboard 및 시각화

## 지원 및 문의
- **Email**: benkorea.ai@gmail.com  
- **Wiki**: 개발 과정 중 시행착오 기록
- **운영 문서**: 별도 Wiki에서 운영 가이드 제공

> 이 문서는 AI4RM 프로젝트의 AI 코딩 어시스턴트 및 개발팀을 위한 핵심 가이드입니다. 생성형AI 지원으로 작성되었으며 개발 진행에 따라 지속 업데이트됩니다.

