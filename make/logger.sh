#!/bin/bash
# AI4RM 쉘스크립트 표준 로거 (make/logger.sh)

# 로그레벨 매핑
declare -A LOG_LEVELS=(
  [CRITICAL]=0
  [ERROR]=1
  [WARNING]=2
  [INFO]=3
  [DEBUG]=4
  [TRACE]=5
)

LOG_LEVEL="${LOG_LEVEL:-INFO}"
LOG_PATH="${LOG_PATH:-logs/dev.log}"
AUDIT_PATH="${AUDIT_PATH:-logs/audit.log}"

# 로그레벨 비교 함수
function _should_log() {
  local level="$1"
  [[ ${LOG_LEVELS[$level]} -le ${LOG_LEVELS[$LOG_LEVEL]} ]]
}

# 운영 로그 기록 (콘솔+JSON 파일)
function log_msg() {
  local level="$1"
  local msg="$2"
  local ts
  ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  if _should_log "$level"; then
    # 콘솔 출력
    echo "[$ts] [$level] $msg"
    # 파일(JSON) 기록
    printf '{"timestamp":"%s","level":"%s","message":"%s"}\n' "$ts" "$level" "$msg" >> "$LOG_PATH"
  fi
}

# 감사 로그 기록 (JSON)
function audit_log() {
  local action="$1"
  local detail="$2"
  local compliance="${3:-개인정보보호법_제28조}"
  local user="${USER:-unknown}"
  local pid="$$"
  local host
  host="$(hostname)"
  local ts
  ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  printf '{"action":"%s","user":"%s","process_id":"%s","server_id":"%s","timestamp":"%s","compliance_check":"%s"%s}\n' \
    "$action" "$user" "$pid" "$host" "$ts" "$compliance" \
    "${detail:+,$detail}" >> "$AUDIT_PATH"
}

# 사용 예시
# log_msg INFO "백업 시작"
# audit_log "backup_started" '"target":"bitwarden"'
