#!/bin/bash

set -e

# [1] 디렉토리 생성 및 권한 설정
sudo mkdir -p \
  /opt/ai4rm/vault/docker/config \
  /opt/ai4rm/vault/docker/file \
  /opt/ai4rm/vault/docker/certs \
  /opt/ai4rm/vault/docker/logs \
  /opt/ai4rm/vault/docker/agent/config \
  /opt/ai4rm/vault/docker/agent/sink

sudo chown -R 100:100 \
  /opt/ai4rm/vault/docker/config \
  /opt/ai4rm/vault/docker/file \
  /opt/ai4rm/vault/docker/certs \
  /opt/ai4rm/vault/docker/logs \
  /opt/ai4rm/vault/docker/agent/config \
  /opt/ai4rm/vault/docker/agent/sink

sudo chmod -R 750 \
  /opt/ai4rm/vault/docker/config \
  /opt/ai4rm/vault/docker/file \
  /opt/ai4rm/vault/docker/certs \
  /opt/ai4rm/vault/docker/logs \
  /opt/ai4rm/vault/docker/agent/config \
  /opt/ai4rm/vault/docker/agent/sink

# [2] 인증서 발급(Intermediate CA로 서명)
CERT_DIR="/opt/ai4rm/vault/docker/certs"
CA_DIR="/opt/ai4rm/ca"
SERVICE="vault"

SVC_KEY="$CERT_DIR/$SERVICE.key"
SVC_CSR="$CERT_DIR/$SERVICE.csr"
SVC_CRT="$CERT_DIR/$SERVICE.crt"
SVC_CHAIN="$CERT_DIR/ca_chain.crt"

EXTFILE=$(mktemp)
echo "subjectAltName=DNS:$SERVICE, DNS:localhost, IP:127.0.0.1, DNS:elasticsearch, DNS:kibana, DNS:logstash, DNS:keycloak, DNS:openldap" | sudo tee "$EXTFILE" > /dev/null

# 1. 프라이빗 키 생성
if [ ! -f "$SVC_KEY" ]; then
  sudo openssl genrsa -out "$SVC_KEY" 2048
fi

# 2. CSR 생성
if [ ! -f "$SVC_CSR" ]; then
  sudo openssl req -new -key "$SVC_KEY" -out "$SVC_CSR" -subj "/CN=$SERVICE"
fi

# 3. Intermediate CA로 서명된 서버 인증서 발급
if [ ! -f "$SVC_CRT" ]; then
  sudo openssl x509 -req -in "$SVC_CSR" -CA "$CA_DIR/intCA.crt" -CAkey "$CA_DIR/intCA.key" \
    -CAcreateserial -out "$SVC_CRT" -days 365 -sha256 \
    -extfile "$EXTFILE"
fi
sudo rm -f "$EXTFILE"

# 4. 체인 파일 생성 (Intermediate CA → Root CA)
sudo cat "$CA_DIR/intCA.crt" "$CA_DIR/rootCA.crt" | sudo tee "$SVC_CHAIN" > /dev/null

# 5. 인증서/키/체인 권한 및 소유자 설정
sudo chown 100:100 "$SVC_KEY" "$SVC_CSR" "$SVC_CRT" "$SVC_CHAIN"
sudo chmod 640 "$SVC_KEY"
sudo chmod 600 "$SVC_CSR"
sudo chmod 644 "$SVC_CRT" "$SVC_CHAIN"

# [3] Vault 설정 파일/컴포즈 파일 복사
sudo cp ./templates/vault/docker-compose.yml  /opt/ai4rm/vault/
sudo cp ./templates/vault/conf/vault.hcl  /opt/ai4rm/vault/docker/config/
sudo cp ./templates/vault/conf/config.hcl /opt/ai4rm/vault/docker/agent/config/

sudo chown 100:100 /opt/ai4rm/vault/docker/config/vault.hcl
sudo chmod 640 /opt/ai4rm/vault/docker/config/vault.hcl
sudo chown 100:100 /opt/ai4rm/vault/docker/agent/config/config.hcl
sudo chmod 640 /opt/ai4rm/vault/docker/agent/config/config.hcl

echo "[OK] Vault 서비스 프로비저닝 및 인증서(Intermediate CA 서명) 배포 완료."
