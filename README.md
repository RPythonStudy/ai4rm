# AI4RM 의료데이터 가명화·활용 플랫폼

본 프로젝트는 의료 데이터(예: 전자의무기록, 병리보고서, 영상 판독 등)를 개인정보보호에 적합하도록 가명화하고 이를 정형화/메타데이터화 및 연구용 PACS 연계, 핵의학영상검사 선량분석을 지원하고자 합니다.  

## 1. 프로젝트 목적 및 범위

- **가명화**: 환자등록번호/이름 등 개인정보들을 FPE(Format-Preserving Encryption) 기반 일관성 가명화 및 복호화 지원.
- **메타데이터화 및 검증**: 비정형 텍스트 보고서(예: 병리보고서/영상검사보고서)를 ChatGPT API 기반으로 메타데이터화하며, 이 과정에서 변환 오류 및 데이터 정합성 검증 수행.
- **연구용 PACS 연계**: 병원 PACS로부터 DICOM 데이터를 가명화·수집하며, 가명화된 연구용 PACS를 구축하고 핵의학 영상검사 선량정보/품질평가 등 연구 지원 기능을 제공.
- **보안 인프라**: Vault 기반 비밀관리, Keycloak 기반 인증, ELK 기반 로그 관리, Bitwarden 기반 패스워드 관리 등, 개인정보보호에 필요한 보안적용 및 감사자료를 자동생성

## 2. 기능별 오픈소스 및 커스텀 개발 구성

### 2.1 오픈소스 활용

- **DICOM 서버/도구**: Orthanc, dcm4chee, DCMTK 등
- **보안/인증/비밀관리**: Vault, Keycloak, Bitwarden, OpenLDAP
- **로그/모니터링**: ELK Stack (Elasticsearch, Logstash, Kibana), Filebeat
- **데이터베이스**: PostgreSQL, MySQL

### 2.2 Python 기반 커스텀 개발

- **pseudonymizer**: FF3 FPE 알고리즘을 활용한 등록번호 등 식별자 가명화 및 복호화
- **metafier**: ChatGPT Assistant API 등 LLM 기반으로, 가명화된 의료 보고서 비정형 텍스트를 임상연구 및 AI 학습 목적의 정형 메타데이터로 변환
- **verifier**: metafier 변환 결과(비정형→정형화)가 원본 정보와 일치하는지, 오류·누락 없이 정합성 있게 변환되었는지 비교 검증
- **nmdose**: 핵의학 영상 및 선량정보 분석 도구로, 가명화된 rPACS에서 DICOM metadata 분석하여 선량연구
- **nmiq**: 핵의학 영상품질 자동분석 도구로, 가명화된 rPACS에서 영상품질평가 수행


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

- 이 README 문서는 저자가 ChatGPT를 이용하여 초안을 생성히였으며, 개발 이후 변경된 내용은 반영이 늦을 수 있습니다.
- 저자가 개발 실무 경험이 사실상 처음인지라 일부 내용에 오류가 있더라도 너그러이 양해해 주시길 바랍니다.
- 설치/운영 안내는 별도 Wiki 문서로 추후 작성될 예정이며, 개발 기간 중의 Wiki는 스니펫등을 복사 가능하게 저장해두거나, 시행착오 및 때로는 이를 우회적으로 극복한 경우에는 그 사유 등을 기록하고자 합니다. 그래서 개발기간동안의 wiki 문서는 저자의 기억과 협업자의 이해를 돕는 자료로 활용하고 운영단계에서는 사용자의 이해을 위한 자료로 활용할 계획입니다.

## 6. 문의
benkorea.ai@gmail.com