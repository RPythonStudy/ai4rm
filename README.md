# ai4rm (AI for Radiation Medicine) 프로젝트 안내

본 프로젝트는 의료 데이터(예: 전자의무기록, 병리보고서, 영상 판독 등)의 가명화 및 정형화, 개인정보보호 인프라, 연구용 PACS 연계, 선량분석 자동화 등을 포괄적으로 지원합니다.  
아래의 개발-운영 전략, 시스템 구성 및 주요 기능별 아키텍처, 폴더 구조, 협업 지침, 그리고 기타 안내 사항을 참고하시기 바랍니다.

## 1. 프로젝트 목적 및 범위

- **가명화 및 정형화**: 환자등록번호/이름 등 주요 식별자에 대해 FPE(Format-Preserving Encryption) 기반 일관성 가명화 및 복호화 지원.
- **메타데이터화 및 오류 검증**: 비정형 텍스트 보고서(예: 병리보고서)를 ChatGPT API 기반으로 메타데이터화하며, 이 과정에서 변환 오류 및 데이터 정합성 검증 수행.
- **연구용 PACS 연계**: 병원 PACS로부터 DICOM 데이터를 가명화·수집하며, 연구용 PACS에서 핵의학 영상/선량정보/품질평가 등 연구 지원 기능을 제공.
- **보안 인프라**: Vault 기반 비밀관리, Keycloak 기반 인증, ELK 기반 로그 관리, Bitwarden 기반 패스워드 관리 등, 법적/정책적 요구를 충족하는 보안 감사 및 인증 체계를 운영 환경과 완전히 동일하게 구현.

## 2. 기능별 오픈소스 및 커스텀 개발 구성

### 2.1 오픈소스 활용

- **DICOM 서버/도구**: Orthanc, dcm4chee, DCMTK 등
- **보안/인증/비밀관리**: Vault, Keycloak, Bitwarden, OpenLDAP
- **로그/모니터링**: ELK Stack (Elasticsearch, Logstash, Kibana), Filebeat
- **데이터베이스**: PostgreSQL, MySQL

### 2.2 Python 기반 커스텀 개발

- **pseudonymizer**: FF3 FPE 알고리즘을 활용한 등록번호 등 식별자 가명화 및 복호화 (파일: `pseudonymize_files.py`, `depseudonymize_files.py`)
- **metafier**: ChatGPT Assistant API 등 LLM 기반으로, 가명화된 의료 보고서 비정형 텍스트를 임상연구 및 AI 학습 목적의 정형 메타데이터로 변환
- **verifier**: metafier 변환 결과(비정형→정형화)가 원본 정보와 일치하는지, 오류·누락 없이 정합성 있게 변환되었는지 자동 검증
    - *참고*: verifier는 "가명화 전후"의 비교가 아니라, **비정형 데이터에서 정형화된 결과로의 변환 과정**의 무결성 검증에 초점을 둠
- **nmdose**: 핵의학 영상 및 선량정보 분석 자동화 도구로, PACS에서 DICOM 데이터를 수집하고 분석하여 연구용 데이터셋 생성

## 3. 개발-배포-운영 원칙 및 협업 가이드

- **폴더구조**: monorepo 및 서비스별 디렉터리 구조를 통일적으로 적용하며, 프로젝트 개발, 테스트, 운영, 배포의 모든 단계에서 **동일한 경로 및 레이아웃**을 유지합니다.
- **협업 방식**: 개별 서비스는 폴더 단위로 분화되어 있으며, 코드를 추가·수정할 때는 본인의 서비스 폴더를 중심으로 개발하는 것을 검토해 주시길 바랍니다.
- **버전관리**: Git/GitHub 기반으로 관리되며, 협업자는 로컬 저장소와 원격 저장소의 버전 동기화(git pull/push 등)에 유의하여 작업하는 것을 검토해 주시길 바랍니다.
- **지침 및 문서화**: 본 안내 외에 상세한 개발/운영 안내는 wiki 등 별도 문서로 작성될 예정이며, 각 서비스 폴더 하위에 운영/설치 템플릿과 자동화 스크립트가 제공됩니다.

## 4. 폴더 구조 예시

### 4.1 원격 저장소(개발용) 구조 예시

```plaintext
projects/ai4rm/
          ├── src/ # 서비스별 파이썬 코드
          │   ├── pseudonymizer/
          │   ├── metafier/
          │   ├── verifier/
          │   └── ...
          ├── infra/ # 도커/인프라(IaC), 자동화 스크립트, 배포 템플릿
          │   ├── Dockerfile.all.services-init
          │   ├── Dockerfile.pseudonymizer
          │   ├── requirements.vault-init.txt
          │   ├── docker-compose.yml
          │   ├── ca/
          │   └── ...
          ├── scripts/ # 운영·설치·관리 스크립트
          ├── templates/ # 각 서비스별 설정 템플릿
          │   ├── vault/
          │   ├── elk/
          │   └── ...
          ├── data/ # 샘플·테스트 데이터(운영시 외부 마운트)
          ├── tests/ # 테스트 코드
          ├── .env, .secrets # 환경설정(예시 파일만 Git에 포함)
          ├── README.md
          └── Makefile
```


---

### 4.2 운영서버(운영 환경) 구조 예시
```plaintext
/opt/ai4rm/
      ├── src/
      │   └── ...
      ├── infra/
      │   └── ...
      ├── bitwarden/ # Bitwarden만 서비스명/docker 구조
      │   └── bwdata
      │       └── docker/
      │           └── dock-compose.yml
      ├── docker/
          ├── all.services-init
          ├── elk/
          │   ├── esdata/
          │   └── logstash/
          │       └── pipeline/
          ├── keycloak/
          │   └── data/
          ├── vault/
          │   ├── config/
          │   ├── file/
          │   ├── certs/
          │   └── logs/
          ├── openldap/
          │   ├── data/
          │   └── config/
          └── ...
```

## 5. 기타 안내 및 주의사항

- 본 README 및 안내문은 ChatGPT로부터 프로젝트 초기 지침 및 프롬프트를 토대로 생성되었습니다.  
  개발 이후 변경된 내용은 실시간으로 반영되지 않을 수 있으며, 프로젝트 관리자가 개발 실무 경험이 충분하지 않을 수 있으니  
  일부 내용이 현실과 다를 수 있음을 양해해 주시길 바랍니다.
- 상세 설치/운영/개발 안내는 별도 Wiki 문서로 추후 작성될 예정이며,  
  Wiki에는 반복적 설치·테스트 과정, 각 개발 환경에서의 재현성 확보, 시행착오 및 우회적 조치의 사유 등도 최대한 상세히 기록하여  
  개발자 및 협업자의 이해를 돕는 자료로 활용할 계획입니다.
- 본 프로젝트의 모든 설치·설정·자동화 및 데이터 경로는 실제 운영 환경과 **완전히 동일하게** 동작하도록 설계되었습니다.
