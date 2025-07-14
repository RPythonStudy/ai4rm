# Artificial Intelligence for Radiation Medicine (AI4RM)   

## 개요

AI4RM 프로젝트는 병원 내 의료 데이터를 안전하게 가명화·복호화하여, 개인정보 보호법 및 보건의료정보 가이드라인에 적합하게 임상 연구 및 AI 학습에 활용할 수 있도록 지원합니다. EMR, 병리보고서, 영상판독보고서 등 다양한 비정형 의료 데이터의 가명화 및 정형화, 익명화 연구용 PACS 연계, 선량분석, 자동화 및 보안 감사까지 일련의 워크플로우를 업계 표준에 따라 구현합니다.

## 주요 기능

### 가명화 및 복호화

- 등록번호, 환자이름 등 개인정보에 대해 FF3 FPE(Format-Preserving Encryption) 기반 일관 가명화 및 복호화 기능 제공

- 텍스트 파일 내 등록번호/이름 등 치환 자동화 (비정형→정형화 지원)

### 메타데이터 추출 및 검증

- NLP 기반 보고서 메타데이터 추출(nlp_extractor), 변환 결과 비교 및 오류 검증 후 DB 저장

### 연구용 PACS 및 영상 분석

- 연구용 PACS(rPACS) 구축, DICOM 데이터 가명화 수집 및 선량정보/영상품질/auto segmentation/AI학습 등 모듈화

### 보안 및 감사

- KeyCloak 기반 인증, Vault 기반 비밀/키관리, Bitwarden 연동 auto-unseal, 감사로그(ELK 연동) 등

### 자동화된 인프라 배포/운영

- Docker Compose 기반 인프라 통합 배포, 인증서 자동발급/복사, 구조화된 폴더 자동 생성

> 문의: benkorea.ai@gmail.com
> 각 기능별 설치 방법과 운영에 필요한 세부 사항은 본 프로젝트의 Wiki를 참고해 주십시오.




### Clone 및 초기화
- git clone
- .venv 가상환경 생성
-  pip upgrade
-  pip intsall -e .
-  pip install -r requirements.txt

### CLI 명령어
- `security-infra-cli.py`를 통해 CLI 명령어 실행

#### 필수폴더 자동 생성
```bash
python security-infra-cli.py create-directories
```
- 권한 문제시 --force 사용, 권한 에러는 sudo로 자동 재시도

#### 서비스 인증서/키 자동 생성
```bash
python security-infra-cli.py generate-certificates
```
- vault, elk, keycloak 등 SAN 자동구성, 덮어쓰기는 --overwrite 옵션 사용

#### 템플릿 config 복사
```bash
python security-infra-cli.py sync-templates
```
- ELK, Vault 등 템플릿 config를 config/ 폴더로 복# templates/ → docker/ 각 서비스 경로로 자동 복사

#### sudoers 설정 방법
- 자동화/무인화를 위해 아래와 같이 sudoers 파일에 docker 명령 패스워드 없이 허용을 추가해야 합니다.

```bash
whoami
```
- 예시: ben

- sudoers 편집 (visudo 권장)
```bash
sudo visudo /etc/sudoers.d.docker
```
- 아래 내용을 추가하여 docker, docker-compose 명령어를 sudo 없이 실행 가능하게 설정합니다.
```bash
<USERNAME> ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/docker-compose
```

- 검증
```bash
sudo -n docker ps
```

#### Bitwarden server 도커 컨테이너 설치
https://github.com/bitwarden/server#building
- DNS 설정은 패스
- Docker와 Docker Compose가 설치는 이미 되어 있어야 합니다.
- Bitwarden 서버를 설치하기 위해 아래 명령어를 실행합니다.


#### Docker 서비스 컨트롤
```bash
python security-infra-cli.py compose up --service all
python security-infra-cli.py compose down --service vault
python security-infra-cli.py compose restart --service elk
```
- `--service` 옵션으로 특정 서비스 컨트롤 가능# 모든 명령은 sudo docker compose 기반 (sudoers 설정 권장)

#### Vault 초기화 및 unseal 키 안전보관
- 보안을 위해 이 단계는 터미널에서 수동으로 진행됩니다.
```bash
sudo docker exec -it vault vault operator init -key-shares=5 -key-threshold=3
```
Unseal Key 1 ~5 까지를 Bitwarden에 안전하게 보관

#### 개인정보보호를 위한 역할분담 예시

1. Vault Unseal Key Keeper 역할 분장 설계

| Vault 내 역할명     | 계정ID         | 이메일                                                           | 역할설명                | Unseal Key 보관 | 비고 |
| --------------- | ------------ | ------------------------------------------------------------- | ------------------- | ------------- | -- |
| 볼트 최고관리자        | vault-root   | [vault-root@rpython.stdy](mailto:vault-root@rpython.stdy)     | Vault Root 권한       | 1번            |    |
| 볼트 운영자          | vault-ops    | [vault-ops@rpython.stdy](mailto:vault-ops@rpython.stdy)       | Vault 차기운영/복구 권한    | 2번            |    |
| 가명화정보담당자        | pseudo-info  | [pseudo-info@rpython.stdy](mailto:pseudo-info@rpython.stdy)   | 가명화 정보 총괄           | 3번            |    |
| pseudonymee 책임자 | pseudo-chief | [pseudo-chief@rpython.stdy](mailto:pseudo-chief@rpython.stdy) | pseudonymee 프로젝트 책임 | 4번            |    |
| pseudonymee 운영자 | pseudo-ops   | [pseudo-ops@rpython.stdy](mailto:pseudo-ops@rpython.stdy)     | pseudonymee 운영/일상관리 | 5번            |    |

2. Bitwarden/LDAP/서버 최고관리자 역할 분리 설계

| 시스템구분           | 계정ID        | 이메일                                                         | 역할설명                 | 비고    |
| --------------- | ----------- | ----------------------------------------------------------- | -------------------- | ----- |
| Bitwarden 최고관리자 | bw-admin    | [bw-admin@rpython.stdy](mailto:bw-admin@rpython.stdy)       | Bitwarden Root/Owner | 별도 보관 |
| LDAP 최고관리자      | ldap-admin  | [ldap-admin@rpython.stdy](mailto:ldap-admin@rpython.stdy)   | OpenLDAP 최고권한        | 별도 보관 |
| 서버(공통) 관리자      | infra-admin | [infra-admin@rpython.stdy](mailto:infra-admin@rpython.stdy) | 서버/OS/컨테이너 등 총괄      | 별도 보관 |
