#!/bin/bash
# Bitwarden 서버 컨테이너 설치 준비 스크립트 (sudo로 실행 필요)

# 아래의 사전준비는 보안을 위해 매뉴얼로 진행합니다.
# Bitwarden 사용자 생성
# Bitwarden 그룹 생성

# 설치 디렉토리 생성 및 소유자/권한 설정
sudo mkdir -p /opt/ai4rm/docker/bitwarden/bwdata/
sudo chown -R bitwarden:bitwarden /opt/ai4rm/docker/bitwarden
sudo chmod -R 750 /opt/ai4rm/docker/bitwarden

# 백업 디렉토리 생성 및 소유자/권한 설정
sudo mkdir -p /opt/ai4rm/.backup/bitwarden/bwdata/
sudo chown -R bitwarden:bitwarden /opt/ai4rm/.backup/bitwarden/

# 운영 스크립트 디렉토리 생성 및 소유자/권한 설정
sudo mkdir -p /opt/ai4rm/scripts/
sudo cp /home/ben/projects/ai4rm/make/install_bitwarden.sh /opt/ai4rm/scripts/install_bitwarden.sh
sudo cp /home/ben/projects/ai4rm/make/backup_bitwarden.sh /opt/ai4rm/scripts/backup_bitwarden.sh
sudo cp /home/ben/projects/ai4rm/make/restore_bitwarden.sh /opt/ai4rm/scripts/restore_bitwarden.sh
sudo chown -R bitwarden:bitwarden /opt/ai4rm/scripts/
sudo chmod 750 /opt/ai4rm/scripts/install_bitwarden.sh
sudo chmod 750 /opt/ai4rm/scripts/backup_bitwarden.sh
sudo chmod 750 /opt/ai4rm/scripts/restore_bitwarden.sh  

# 결과 확인: 주요 폴더/파일 상태 출력
echo "[DEBUG] 디렉토리/권한/소유자 상태 확인"
ls -ld /opt/ai4rm/docker/bitwarden
ls -ld /opt/ai4rm/docker/bitwarden/bwdata
ls -ld /opt/ai4rm/.backup/bitwarden
ls -ld /opt/ai4rm/.backup/bitwarden/bwdata
ls -ld /opt/ai4rm/scripts
ls -l /opt/ai4rm/scripts/install_bitwarden.sh
ls -l /opt/ai4rm/scripts/backup_bitwarden.sh
ls -l /opt/ai4rm/scripts/restore_bitwarden.sh

echo "[INFO] Bitwarden 설치 준비 완료"
tree -L 4 -a /opt/ai4rm/