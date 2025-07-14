#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# File: setup_infra.sh
# Description: 인프라(ELK, Keycloak, Vault, OpenLDAP, Filebeat 등) 볼륨/디렉토리/권한/임시 인증서 초기화 자동화 스크립트 (모든 컨테이너, 정보최소화)
# Usage: sudo ./scripts/setup_infra.sh
# Author: BenKorea <benkorea.ai@gmail.com>
# Created: 2025-07-03
# ------------------------------------------------------------------------------

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()    { echo -e "${RED}[WARN]${NC} $1"; }
fail()    { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

# === 모든 서비스명에 대해 컨테이너 중복 자동 삭제 ===
SERVICES="elk keycloak vault openldap elasticsearch logstash kibana filebeat"
info "### 기존 컨테이너(동작/중지 불문) 자동 삭제"
for c in $SERVICES; do
    if sudo docker ps -a --format '{{.Names}}' | grep -qw "$c"; then
        info "기존 $c 컨테이너 발견, 삭제 진행"
        sudo docker rm -f "$c"
    fi
done

# 변수화 (출력 생략, 컨테이너 표준 권한 적용)
ELK_UID=1000
ELK_GID=1000
KEYCLOAK_UID=1000
KEYCLOAK_GID=0
VAULT_UID=100
VAULT_GID=100
LDAP_UID=101
LDAP_GID=103

info "### [0/4] 기존 docker 서비스 정지 및 docker 디렉토리 삭제"
sudo docker compose down || info "docker compose down 실패(무시)"
if [ -d ./docker ]; then
    sudo rm -rf ./docker
    if [ -d ./docker ]; then
        fail "./docker 디렉토리 삭제 실패"
    else
        info "./docker 디렉토리 삭제 성공"
    fi
else
    info "./docker 디렉토리 없음(생략)"
fi

info "### [1/4] 폴더 생성"
sudo mkdir -p ./docker/elk/esdata ./docker/elk/logstash/pipeline || fail "ELK 폴더 생성 실패"
sudo mkdir -p ./docker/keycloak/data || fail "Keycloak 폴더 생성 실패"
sudo mkdir -p ./docker/vault/config ./docker/vault/file ./docker/vault/certs ./docker/vault/logs || fail "Vault 폴더 생성 실패"
sudo mkdir -p ./docker/openldap/data ./docker/openldap/config || fail "OpenLDAP 폴더 생성 실패"

# 폴더 검증
for d in ./docker/elk/esdata ./docker/elk/logstash/pipeline ./docker/keycloak/data ./docker/vault/certs ./docker/openldap/data; do
    [ -d "$d" ] && info "$d 생성됨" || fail "$d 생성 실패"
done

info "### [1.5/4] logstash.conf 복사 및 권한 변경"
if [ -f ./config/logstash.conf ]; then
    sudo cp ./config/logstash.conf ./docker/elk/logstash/pipeline/logstash.conf
    sudo chown -R ${ELK_UID}:${ELK_GID} ./docker/elk/logstash/pipeline/logstash.conf
    sudo chmod -R 750 ./docker/elk/logstash/pipeline/logstash.conf
    [ -f ./docker/elk/logstash/pipeline/logstash.conf ] && info "logstash.conf 복사 완료" || fail "logstash.conf 복사 실패"
else
    warn "config/logstash.conf가 존재하지 않습니다. (건너뜀)"
fi

info "### [2/4] 권한 및 소유권 변경"
sudo chown -R ${ELK_UID}:${ELK_GID} ./docker/elk
sudo chmod -R 750 ./docker/elk
sudo chown -R ${KEYCLOAK_UID}:${KEYCLOAK_GID} ./docker/keycloak
sudo chmod -R 750 ./docker/keycloak
sudo chown -R ${VAULT_UID}:${VAULT_GID} ./docker/vault
sudo chmod -R 750 ./docker/vault
sudo chown -R ${LDAP_UID}:${LDAP_GID} ./docker/openldap
sudo chmod -R 750 ./docker/openldap

info "### [3/4] Vault 임시 인증서 (항상 새로 생성/덮어쓰기)"
CERT_DIR=./docker/vault/certs
CERT_KEY=${CERT_DIR}/vault.key
CERT_CRT=${CERT_DIR}/vault.crt

# openssl req 출력 감추기
sudo openssl req \
  -x509 -newkey rsa:2048 \
  -keyout "$CERT_KEY" \
  -out "$CERT_CRT" \
  -days 14 \
  -nodes \
  -subj "/CN=localhost" \
  -addext "subjectAltName = DNS:localhost, IP:127.0.0.1, DNS:elasticsearch, DNS:kibana, DNS:logstash, DNS:keycloak, DNS:vault, DNS:openldap" \
  >/dev/null 2>&1
sudo chown ${VAULT_UID}:${VAULT_GID} "$CERT_KEY" "$CERT_CRT"
sudo chmod 640 "$CERT_KEY" "$CERT_CRT"
if [ -f "$CERT_KEY" ] && [ -f "$CERT_CRT" ]; then
    CRT_TIME=$(stat -c %y "$CERT_CRT")
    info "임시 인증서 생성시각: $CRT_TIME"
else
    fail "Vault 임시 인증서 생성 실패"
fi

info "### [4/4] 권한 및 파일 검증"
{
    sudo ls -ld ./docker/elk ./docker/elk/esdata ./docker/elk/logstash ./docker/elk/logstash/pipeline
    sudo ls -ld ./docker/keycloak ./docker/keycloak/data
    sudo ls -ld ./docker/vault ./docker/vault/config ./docker/vault/file ./docker/vault/certs ./docker/vault/logs
    sudo ls -l ./docker/vault/certs
    sudo ls -ld ./docker/openldap ./docker/openldap/data ./docker/openldap/config
} && info "권한/파일 검증 명령 실행 완료" || warn "권한/파일 검증 중 오류"

info "초기화/권한/인증서 작업 완료"

info "### 모든 컨테이너 기동 (오류 여부 확인)"
sudo docker compose up -d
FAILED=$(sudo docker ps --filter "status=exited" --format '{{.Names}}')
if [ -n "$FAILED" ]; then
    warn "아래 컨테이너가 오류로 중지되었습니다:"
    echo "$FAILED"
    exit 1
else
    info "모든 컨테이너가 정상적으로 기동되었습니다."
fi

info "=== 컨테이너 전체 상태 ==="
sudo docker ps -a

info "=== 컨테이너별 리소스 사용량 (1회 스냅샷) ==="
sudo docker stats --no-stream

info "=== 호스트 시스템 메모리 상태 (free -h) ==="
free -h
