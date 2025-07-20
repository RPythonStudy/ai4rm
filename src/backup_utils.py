import subprocess
import os
from pathlib import Path

def run_cmd(cmd: str):
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        raise RuntimeError(f"명령어 실패: {cmd}")

def backup_container(service: str, backup_path: str):
    backup_dir = Path(backup_path)
    backup_dir.mkdir(parents=True, exist_ok=True)
    if service == "vault":
        run_cmd(f"docker cp vault:/vault/file {backup_dir}/vault_file_backup")
    elif service == "bitwarden":
        run_cmd(f"docker cp bitwarden:/data {backup_dir}/bitwarden_data_backup")
    else:
        raise ValueError(f"지원하지 않는 서비스: {service}")

def restore_container(service: str, backup_path: str):
    backup_dir = Path(backup_path)
    if service == "vault":
        run_cmd(f"docker cp {backup_dir}/vault_file_backup vault:/vault/file")
    elif service == "bitwarden":
        run_cmd(f"docker cp {backup_dir}/bitwarden_data_backup bitwarden:/data")
    else:
        raise ValueError(f"지원하지 않는 서비스: {service}")

def reset_container(service: str):
    run_cmd(f"docker compose stop {service}")
    if service == "vault":
        run_cmd("sudo rm -rf /opt/ai4rm/docker/vault/file/*")
    elif service == "bitwarden":
        run_cmd("sudo rm -rf /opt/ai4rm/docker/bitwarden/data/*")
    else:
        raise ValueError(f"지원하지 않는 서비스: {service}")
    run_cmd(f"docker compose up -d {service}")
