# 로깅 시스템 가이드

## 개요

> AI4RM 프로젝트는 의료 데이터 처리의 특성상 상세한 로깅과 감사 추적이 필요합니다.   
> 또한 협업 개발을 가정해도 필요합니다. 
> 이 가이드는 AI4RM 프로젝트에서 로깅 시스템을 설정하고 사용하는 방법을 설명합니다.

## 설계 원칙

### 1. **통합 로깅 아키텍처**
- **위치**: `ai4rm/logger/logger.py`
- **목적**: 프로젝트 전체에서 일관된 로깅 인터페이스 제공
- **ELK Stack 호환**: JSON 형태로 로그를 저장하여 Elasticsearch 연동 최적화

### 2. **이중 출력 방식**
- **stdout (콘솔)**: 사람이 읽기 쉬운 텍스트 형태
- **파일**: JSON 형태로 구조화된 로그 저장 (`logs/dev.log`)

### 3. **설정 우선순위**
1. **명령행 인자** (최우선)
2. **환경변수** (`.env` 파일 포함)
3. **YAML 설정 파일** (`config/logging.yaml`)
4. **기본값** (`INFO`)

## 로그 레벨 (6단계)

| 레벨 | 설명 | 사용 예시 |
|------|------|-----------|
| `CRITICAL` | 시스템 중단 수준의 심각한 오류 | 데이터베이스 연결 실패, 암호화 키 손실 |
| `ERROR` | 오류 발생하지만 시스템 계속 동작 | 파일 처리 실패, API 호출 오류 |
| `WARNING` | 주의가 필요한 상황 | 권한 부족, 설정 누락 |
| `INFO` | 일반적인 정보 (기본값) | 작업 시작/완료, 처리 건수 |
| `DEBUG` | 디버깅용 상세 정보 | 변수 값, 함수 호출 흐름 |
| `TRACE` | 가장 상세한 추적 정보 | 데이터 변환 과정, 세밀한 실행 단계 |

## 기본 사용법

### 전제조건
로깅 시스템을 사용하기 전에 다음 조건들이 충족되어야 합니다:

1. **`logger/__init__.py` 파일 존재**: 
   ```python
   # logger/__init__.py
   from .logger import get_logger
   
   __all__ = ['get_logger']
   ```

2. **실행 위치**: 프로젝트 루트 디렉토리(`ai4rm/`)에서 실행
3. **Python 경로**: `logger` 패키지가 Python 모듈 검색 경로에 포함되어야 함

### 1. **기본 로거 생성**

```python
# 프로젝트 루트에서 실행할 때
from logger import get_logger

# 기본 로거 생성
logger = get_logger("my_module")

# 사용 예시
logger.info("작업을 시작합니다.")
logger.debug(f"처리할 항목 수: {len(items)}")
logger.error("오류가 발생했습니다.", exc_info=True)
```

### 2. **모듈별 로거 생성**

```python
# 각 모듈에서 고유한 로거 사용
from logger import get_logger

logger = get_logger("my_module")         # 일반 모듈
logger = get_logger("data_processor")     # 데이터 처리 모듈
logger = get_logger("utils")              # 유틸리티 모듈
```

### 3. **다른 경로에서 실행할 때**

```python
# src/ 하위 폴더에서 실행할 때 (상대 경로 조정 필요)
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parents[2]  # src/module/file.py 기준
sys.path.insert(0, str(project_root))

from logger import get_logger
logger = get_logger("module_name")
```

### 4. **Typer/Click CLI에서 사용**

```python
import typer
from logger import get_logger

app = typer.Typer()

@app.command()
def process_data(
    log_level: str = typer.Option("INFO", help="로그 레벨 설정")
):
    # CLI 인자로 받은 로그 레벨을 전달
    logger = get_logger("cli_app", cli_log_level=log_level)
    
    logger.info("데이터 처리를 시작합니다.")
    # ... 작업 수행
    logger.info("데이터 처리가 완료되었습니다.")
```

## 설정 방법

### 1. **환경변수 설정 (.env 파일)**

```bash
# .env 파일
LOG_LEVEL=DEBUG
```

### 2. **YAML 설정 파일 (config/logging.yaml)**

```yaml
version: 1
disable_existing_loggers: false

formatters:
  simple:
    format: '[%(asctime)s] [%(levelname)s] %(name)s - %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'
  json:
    format: '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "pathname": "%(pathname)s", "lineno": %(lineno)d, "funcName": "%(funcName)s"}'
    datefmt: '%Y-%m-%dT%H:%M:%S'
    
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: simple
    stream: ext://sys.stdout
  file:
    class: logging.FileHandler
    level: INFO
    formatter: json
    filename: logs/dev.log
    encoding: utf-8

root:
  level: INFO
  handlers: [console, file]

loggers:
  ai4rm:
    level: INFO
    handlers: [console, file]
    propagate: no
```

### 3. **명령행에서 로그 레벨 지정**

```bash
# Typer CLI 예시
python my_script.py --log-level DEBUG

# 환경변수로 직접 설정
LOG_LEVEL=TRACE python my_script.py
```

## 실제 사용 예시

### 일반적인 모듈에서의 사용 패턴

```python
# 예시: 임의의 모듈에서 로거 사용
from logger import get_logger

logger = get_logger("my_module")

def process_data(data):
    logger.info("데이터 처리를 시작합니다.")
    try:
        # 데이터 처리 로직
        logger.debug(f"처리할 데이터 크기: {len(data)}")
        
        result = perform_operation(data)
        logger.debug(f"처리 결과: {result}")
        
        logger.info("데이터 처리가 완료되었습니다.")
        return result
        
    except Exception as e:
        logger.error("데이터 처리 중 오류 발생", exc_info=True)
        raise
```

## 로그 출력 예시

### 콘솔 출력 (사람 친화적)
```
[2025-07-16 10:30:15] [INFO] my_module - 데이터 처리를 시작합니다.
[2025-07-16 10:30:15] [DEBUG] my_module - 처리할 데이터 크기: 25
[2025-07-16 10:30:16] [INFO] my_module - 데이터 처리가 완료되었습니다.
[2025-07-16 10:30:17] [ERROR] my_module - 데이터 처리 중 오류 발생
```

### 파일 출력 (JSON, ELK 호환)
```json
{"timestamp": "2025-07-16T10:30:15", "level": "INFO", "logger": "my_module", "message": "데이터 처리를 시작합니다.", "pathname": "/home/user/ai4rm/src/my_module.py", "lineno": 45, "funcName": "process_data"}
{"timestamp": "2025-07-16T10:30:15", "level": "DEBUG", "logger": "my_module", "message": "처리할 데이터 크기: 25", "pathname": "/home/user/ai4rm/src/my_module.py", "lineno": 48, "funcName": "process_data"}
```

## 최적 사용 패턴

### 1. **감사 로깅 (Audit Logging)**
```python
logger = get_logger("audit")

def process_sensitive_data(data_id, user_id):
    logger.info(f"[AUDIT] 민감 데이터 처리 요청 - 데이터ID: {data_id}, 사용자: {user_id}")
    
    # 처리 과정
    result = process_data(data_id)
    
    logger.info(f"[AUDIT] 처리 완료 - 데이터ID: {data_id}, 결과: {result.status}")
```

### 2. **성능 모니터링**
```python
import time

def process_large_dataset(dataset):
    start_time = time.time()
    logger.info(f"대용량 데이터 처리 시작 - 크기: {len(dataset)}")
    
    # 처리 과정
    
    elapsed = time.time() - start_time
    logger.info(f"처리 완료 - 소요시간: {elapsed:.2f}초, 처리율: {len(dataset)/elapsed:.1f}건/초")
```

### 3. **오류 상황 상세 기록**
```python
def critical_operation():
    try:
        # 중요한 작업
        pass
    except CriticalError as e:
        logger.critical(f"치명적 오류 발생: {e}", exc_info=True)
        # 복구 로직
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}", exc_info=True)
        raise
```

## 주의사항

1. **개인정보 보호**: 로그에 민감한 개인정보(실제 환자 ID, 이름 등)를 기록하지 마세요.
2. **로그 레벨 적절성**: 운영 환경에서는 DEBUG/TRACE 레벨 사용을 신중히 고려하세요.
3. **로그 파일 관리**: `logs/` 디렉토리의 파일들이 과도하게 커지지 않도록 주기적으로 관리하세요.
4. **ELK 연동**: JSON 로그는 Logstash를 통해 Elasticsearch로 자동 수집됩니다.
5. **실제 구현**: 본 가이드의 예시 코드는 설명 목적이며, 실제 프로젝트 파일에서는 각 모듈의 구현에 맞게 적용해야 합니다.

## 문제 해결

### Import 오류가 발생하는 경우

#### 1. **ModuleNotFoundError: No module named 'logger'**
```bash
# 해결방법 1: 프로젝트 루트에서 실행
cd /path/to/ai4rm
python your_script.py

# 해결방법 2: logger/__init__.py 파일 생성 확인
ls logger/__init__.py

# 해결방법 3: Python 경로에 프로젝트 루트 추가
export PYTHONPATH="${PYTHONPATH}:/path/to/ai4rm"
```

#### 2. **상대 import 오류**
```python
# src/ 하위에서 실행할 때
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from logger import get_logger
```

### 로그가 출력되지 않는 경우
1. `logs/` 디렉토리 권한 확인
2. `.env` 파일의 `LOG_LEVEL` 설정 확인
3. `config/logging.yaml` 파일 문법 오류 확인

### 로그 레벨이 적용되지 않는 경우
- 설정 우선순위 확인: CLI 인자 > 환경변수 > YAML 설정 > 기본값

이 로깅 시스템을 통해 AI4RM 프로젝트의 모든 작업을 체계적으로 추적하고 문제를 신속히 진단할 수 있습니다.
