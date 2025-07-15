# ai4rm 프로젝트 안내

본 프로젝트(ai4rm)는 의료 데이터의 가명화, 정형화, 연구·AI 학습 데이터화, 그리고 개인정보보호법 준수 및 인프라 자동화에 최적화된 오픈소스 기반 통합 플랫폼을 개발하는 것을 목표로 하고 있습니다. 의료기관의 연구·임상 환경에서 발생하는 다양한 비정형·정형 의료 데이터(예: EMR, 병리·영상 판독 보고서 등)를 안전하게 처리하여 임상 연구 및 AI 개발을 지원하는 일련의 프로세스 및 도구를 구현하고 있습니다.

본 안내문은 ChatGPT를 통해 프로젝트 관리자가 직접 입력한 프로젝트 지침과 프롬프트를 기반으로 작성되었습니다. 안내문 작성 이후의 개발과정에서 변경된 사항이 실시간으로 반영되지 않을 수 있으니 이 점 양해해 주시기 바랍니다. 또한, 프로젝트 관리자는 의료인으로서 개발 경험이 부족할 수 있으므로 일부 안내와 실제 운영·코드·설계 사이에 차이가 있을 수 있습니다.

---

## 개발, 배포, 운영 원칙

- **모든 단계(개발, 테스트, 운영, 배포)는 동일한 폴더 구조, 동일한 경로 체계를 원칙으로 진행합니다.**  
  개발자는 로컬 환경(예: `~/projects/ai4rm`)에서 작업하더라도, 운영 서버의 경로(`/opt/ai4rm`)를 기준으로 모든 코드, 설정, 스크립트를 작성해 주시길 바랍니다.

- **운영 서버에는 `/opt/ai4rm` 전체를 git clone하여 사용합니다.**  
  각 서비스 컨테이너(예: pseudonymizer, metafier, vault, elk 등)는 `/opt/ai4rm/서비스명/docker` 구조로 마운트됩니다.

- **설치, 초기화, 권한설정, 인증서 발급 등 모든 인프라 관련 자동화는 도커 기반 install/init 컨테이너(예: `infra/Dockerfile.[서비스]-init`)로 처리합니다.**

- **운영 서버에는 docker만 설치되어 있으면 추가적인 python/pip/의존성 설치 없이 완전 자동 설치가 가능해야 합니다.**  
  환경설정 파일(.env, .secrets 등)은 예시만 버전관리하고 실제 값은 운영 서버에서만 직접 세팅합니다.

- **보안 및 감사(감사 로그, 비밀관리, 인증, 계정관리 등)는 각 오픈소스 툴을 연계하여 통합적으로 관리합니다.**

- **협업자는**  
  - _개별 서비스/모듈의 작업 시 자신의 코드 및 설정을 본 저장소(monorepo)의 각 서비스 폴더에 추가하는 것을 검토해 주시길 바랍니다._
  - _로컬 저장소와 원격 저장소의 동기화(버전관리) 원칙 및 방법에 대해서도 안내 문서를 참고해 주시길 바랍니다._  
  - _기본적으로 모놀리식 저장소(monorepo) 및 폴더 단위 협업 방식을 적용하고 있습니다. 각 서비스별로 분리 개발하되, 전체 프로젝트의 관리 및 배포 효율성을 높이기 위함입니다._

---

## 사용 오픈소스 및 주요 구성요소

- **의료 데이터 및 PACS**
  - Orthanc (DICOM 서버, 연구용 PACS)
  - dcm4chee (대안 DICOM 서버, 필요시)
  - DCMTK (DICOM 툴킷 및 명령어 도구)
- **보안/비밀/계정 관리**
  - HashiCorp Vault (비밀 관리)
  - KeyCloak (인증 및 SSO)
  - OpenLDAP (계정관리 및 인증 연동)
  - Bitwarden (비밀번호 관리, vault auto-unseal)
- **로그 및 감사**
  - ELK Stack (Elasticsearch, Logstash, Kibana)
  - Filebeat (로그 수집 에이전트)
- **데이터베이스**
  - PostgreSQL (메타데이터 및 운영 데이터 저장소)
  - MySQL (특정 서비스에서 필요 시)
- **인증/CA**
  - 자체 CA (Root/Intermediate CA, openssl 기반)
- **배포/자동화**
  - Docker, Docker Compose
  - Python (자동화 및 서비스 스크립트)
  - Typer, Click (설치/운영 CLI)
- **기타**
  - 3D Slicer (의료 영상 처리, 분석)
  - 기타 필요한 Python/R 패키지 등

※ 각 오픈소스는 서비스별 docker-compose로 배포되며, 운영환경에서 별도 컨테이너로 관리됩니다.


## 예상 폴더/파일 구조 예시

```plaintext
ai4rm/
├── src/                        # 핵심 서비스/모듈 소스코드
│   ├── pseudonymizer/          # 등록번호/이름 등 가명화 엔진
│   │   ├── pseudonymize_files.py
│   │   ├── depseudonymize_files.py
│   │   ├── validate_depseudonymization.py
│   │   └── ...
│   ├── metafier/               # 메타데이터화 및 NLP 처리
│   ├── nmdose/                 # 선량정보 추출·분석
│   ├── nmiq/                   # 영상검사 화질평가
│   ├── rpacs/                  # 연구용 PACS 데이터 연계
│   ├── segmentator/            # 영상 segmentation/AI 학습
│   └── ...
├── infra/                      # 인프라, IaC, 도커파일, 배포 자동화
│   ├── Dockerfile.vault-init
│   ├── Dockerfile.elk-init
│   ├── docker-compose.yml
│   ├── requirements.vault-init.txt
│   ├── vault_provision.sh
│   └── ...
├── scripts/                    # 관리/운영/설치 자동화 스크립트
│   ├── vault_install.py
│   ├── elk_install.py
│   ├── sync_templates.py
│   └── ...
├── templates/                  # 서비스별 설정/컴포즈/템플릿
│   ├── elk/
│   │   └── logstash.conf
│   ├── vault/
│   │   ├── vault.hcl
│   │   └── ...
│   └── ...
├── docker/                     # 도커 볼륨·설정 마운트 (운영시)
│   ├── elk/
│   ├── filebeat/               
│   ├── vault/
│   ├── keycloak/
│   ├── openldap/
│   └── bitwarden/
├── data/                       # 테스트/샘플 데이터 (운영시 별도 마운트)
│   ├── raw/
│   ├── pseudonymized/
│   ├── depseudonymized/
│   └── ...
├── tests/                      # 유닛/통합/시스템 테스트
├── logs/                       # 감사/설치/운영 로그
├── ca/                         # CA, 인증서 등 (운영시)
├── .env.example                # 예시 환경설정
├── .secrets.example            # 예시 비밀설정
├── README.md
└── Makefile
```


## 안내 및 참고사항

- **Wiki 및 기타 안내문**  
  현재 별도의 설치·운영 안내문서는 작성되어 있지 않으며, 향후 순차적으로 작성될 예정입니다.  
  개발 단계에서는 반복적으로 진행되는 설치 및 테스트 과정, 각 개발환경별 실행 명령, 시행착오, 우회 방법 등을 wiki에 실행 예시와 배경설명 위주로 기록하여 개발 편의성과 환경별 재현 가능성을 높이고자 합니다.  
  일반적이지 않은 절차나 시행착오가 있었던 경우, 그 이유와 배경을 함께 기술하여 본인 및 협업자의 이해를 돕고 있습니다.

- **추가 문의 및 제안**  
  본 안내, 폴더 구조, 협업 방식, 자동화 정책 등과 관련하여 궁금한 점이나 개선 사항이 있으실 경우, 프로젝트 관리자에게 직접 문의해 주시길 바랍니다.
