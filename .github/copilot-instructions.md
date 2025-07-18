# AI4RM 의료데이터 가명화·활용 플랫폼 개발 가이드

## 프로젝트 개요

AI4RM은 의료 데이터 가명화·활용 플랫폼입니다. 전자의무기록, 병리보고서, 영상 판독 등의 의료 데이터를 개인정보보호법에 적합하도록 가명화하고, 이를 정형화/메타데이터화하여 AI 앱 개발을 포함한 임상연구를 지원하고자 합니다. 또한 가명화된 연구용 PACS 연계 및 방사선의학 영상검사 선량분석 관리도 지원하고자 합니다.

## 핵심 기능 및 Service Architecture

```
src/
├── pseudonymizer/    # FF1 FPE 알고리즘 기반 환자정보 가명화/복호화
├── metafier/        # ChatGPT API 기반 비정형→정형 메타데이터 변환  
├── verifier/        # 변환 결과 정합성 검증 (원본↔변환 일치성)
├── nmdose/          # 핵의학 선량정보 분석 (DICOM metadata 기반)
└── nmiq/            # 핵의학 영상품질 자동분석
```

### 보안 Infrastructure Stack
- **HashiCorp Vault**: 비밀관리 및 PKI 인증서
- **Keycloak**: 통합 인증 및 권한관리  
- **ELK Stack**: Elasticsearch/Logstash/Kibana 기반 로그관리
- **Bitwarden**: Password Manager 연동
- **OpenLDAP**: Directory Service

## 필수 개발 표준

### 1. 로깅 시스템 (Mandatory)

AI4RM은 의료데이터 처리 특성상 상세한 로깅과 감사 추적이 필수입니다.

```python
# 모든 코드에서 필수 사용 패턴
from logger import get_logger
logger = get_logger("service_name")

# 6단계 로그 레벨 사용
logger.critical("시스템 중단 수준 오류")  # DB 연결실패, 암호화 키 손실
logger.error("오류 발생")              # 파일 처리 실패, API 호출 오류  
logger.warning("주의 필요")            # 권한 부족, 설정 누락
logger.info("일반 정보")               # 작업 시작/완료, 처리 건수
logger.debug("디버깅 정보")             # 변수 값, 함수 호출 흐름
logger.trace("상세 추적")              # 데이터 변환 과정
```

**로깅 보안 원칙**:
```python
# ✅ 올바른 로깅 - 개인정보 제외
logger.info(f"환자데이터 처리 완료: 건수={count}, 소요시간={duration}초")

# ❌ 금지된 로깅 - 개인정보 포함 절대 금지
logger.info(f"환자ID: {patient_id}")  # 개인정보보호법 위반
logger.debug(f"환자명: {patient_name}")  # GDPR 위반
```

### 2. import 및 Module 구조

PYTHONPATH 기반 import 사용 (`sys.path` 조작 금지):
```python
# 프로젝트 루트 기준 import
from logger import get_logger
from config import settings  
from vault_utils import VaultClient
from pseudonymizer.ff3_engine import FF3Engine
```

### 3. Vault Integration Pattern

모든 비밀정보는 HashiCorp Vault를 통해 관리:
```python
# Vault 연동 표준 패턴
from vault_utils.auto_unseal import VaultManager

vault = VaultManager()
secrets = vault.get_secrets("pseudonymize/ff3")
encryption_key = secrets["key"]
```

### 4. 환자데이터 처리 표준

**개인정보 해싱 표준**:
```python
import hashlib

def hash_patient_id(patient_id: str, salt: str) -> str:
    """환자ID SHA-256 해싱 (개인정보보호법 준수)"""
    return hashlib.sha256(f"{patient_id}{salt}".encode()).hexdigest()
```

**FF3 FPE 가명화 표준**:
```python
from pseudonymizer.ff3_engine import FF3Engine

def anonymize_patient_data(data: dict) -> dict:
    """FF3 FPE 알고리즘 기반 환자데이터 가명화"""
    key = vault.get_key("ff3_encryption_key")
    engine = FF3Engine(key)
    
    return {
        "patient_id": engine.encrypt(data["patient_id"]),
        "record_date": data["record_date"],  # 날짜는 가명화하지 않음
        "department": data["department"]
    }
```

## 보안 및 컴플라이언스 요구사항

### 개인정보보호법 & GDPR 준수사항

- **데이터 최소화**: 필요 최소한의 데이터만 처리
- **목적 제한**: 명시된 목적에만 데이터 사용  
- **투명성**: 모든 처리 과정 문서화
- **책임성**: 처리 책임자 명확화

### 금지 사항 (Security Rules)

```python
# ❌ 절대 금지
- 개인정보를 로그에 기록
- 하드코딩된 비밀번호/키 
- sys.path 직접 조작
- 암호화되지 않은 개인정보 저장
```

### 필수 체크리스트

```python
# ✅ 모든 코드에서 확인 필요
- Vault 연동 검증
- 로그 레벨 설정 확인
- 개인정보보호법 준수 
- 단위 테스트 구현
- 감사 로그 구현
```

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

## Service별 구현 패턴

### Pseudonymizer Service
```python
from pseudonymizer.ff3_engine import FF3Engine
from pseudonymizer.vault_utils import get_encryption_key

def process_medical_data(raw_data: dict) -> dict:
    """의료데이터 가명화 처리"""
    logger = get_logger("pseudonymizer")
    
    try:
        key = get_encryption_key("ff3")
        engine = FF3Engine(key)
        
        anonymized = {
            "patient_id": engine.encrypt(raw_data["patient_id"]),
            "record_date": raw_data["record_date"],
            "department": raw_data["department"]
        }
        
        logger.info(f"가명화 처리 완료: 건수=1")
        return anonymized
        
    except Exception as e:
        logger.error(f"가명화 처리 실패: {str(e)}")
        raise
```

### Metafier Service  
```python
from metafier.chatgpt_client import ChatGPTClient
from metafier.medical_schema import MedicalReportSchema

async def convert_report_to_metadata(report_text: str) -> dict:
    """비정형 의료보고서 → 정형 메타데이터 변환"""
    logger = get_logger("metafier")
    
    client = ChatGPTClient()
    schema = MedicalReportSchema()
    
    try:
        metadata = await client.extract_metadata(report_text, schema)
        logger.info("메타데이터 변환 완료")
        return metadata
    except Exception as e:
        logger.error(f"메타데이터 변환 실패: {str(e)}")
        raise
```

### Verifier Service
```python
from verifier.integrity_checker import IntegrityChecker

def verify_data_consistency(original: dict, converted: dict) -> bool:
    """데이터 정합성 검증"""
    logger = get_logger("verifier")
    
    checker = IntegrityChecker()
    is_valid = checker.validate_consistency(original, converted)
    
    if is_valid:
        logger.info("데이터 정합성 검증 통과")
    else:
        logger.warning("데이터 정합성 검증 실패")
        
    return is_valid
```

## 운영 및 모니터링

### ELK Stack 활용
- **Elasticsearch**: 로그 저장 및 검색
- **Logstash**: 로그 pipeline 처리
- **Kibana**: Dashboard 및 시각화

### 감사 로깅 (Audit Logging)
```python
# 개인정보 처리 감사 로그
logger.info({
    "action": "patient_data_anonymized",
    "user_id": current_user.id,
    "record_count": len(processed_records),
    "timestamp": datetime.utcnow().isoformat(),
    "compliance_check": "개인정보보호법_제28조"
})
```

## 핵심 명령어 (Workflow Commands)

### Vault 초기화
```bash
# Vault 완전 자동화 설정
bash make/setup_vault.sh

# USB Token 기반 Auto-unseal
python src/pseudonymizer/vault_utils/auto_unseal.py
```

### 서비스 관리
```bash
# 전체 서비스 시작
docker compose up -d

# 상태 확인  
docker compose ps

# 로그 확인
docker compose logs -f vault
```

## Git Workflow 및 협업 가이드

### 브랜치 전략
```bash
# 개발 전 동기화
git pull origin main

# Feature 브랜치 작업
git checkout -b feature/pseudonymizer-enhancement

# Commit 메시지 표준
git commit -m "feat(pseudonymizer): FF3 암호화 성능 개선

- 배치 처리 크기 최적화
- 메모리 사용량 50% 감소  
- 개인정보보호법 Article 28 컴플라이언스 유지"
```

### Code Review 체크포인트
1. **보안**: 개인정보 처리 적절성 검증
2. **컴플라이언스**: 개인정보보호법/GDPR 요구사항 준수
3. **로깅**: 감사 로그 구현 여부 확인
4. **테스트**: 단위/통합 테스트 커버리지
5. **문서화**: API 문서 및 주석 완성도

---

## 프로젝트 특수성 고려사항

이 프로젝트는 **의료데이터 처리 플랫폼**으로서 다음을 최우선으로 합니다:
- 환자 개인정보 보호가 성능 최적화보다 우선
- 개인정보보호법/GDPR 완전 준수  
- 포괄적인 감사 추적(Audit Trail) 필수
- Zero-Trust Architecture 기반 다층 보안

코드 작성 시 항상 환자 프라이버시와 법적 컴플라이언스를 성능보다 우선하여 고려하세요.



## 지원 및 문의
- **Email**: benkorea.ai@gmail.com  
- **Wiki**: 개발 과정 중 시행착오 기록
- **운영 문서**: 별도 Wiki에서 운영 가이드 제공

> 이 문서는 AI4RM 프로젝트의 AI 코딩 어시스턴트 및 개발팀을 위한 핵심 가이드입니다. ChatGPT 지원으로 작성되었으며 개발 진행에 따라 지속 업데이트됩니다.

