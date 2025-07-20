# debug_pythonpath.py
import sys
import os
from pathlib import Path

print("=== PYTHONPATH 환경변수 ===")
print(os.environ.get("PYTHONPATH", "(설정되지 않음)"))

print("\n=== sys.path 목록 ===")
for p in sys.path:
    print(p)

print("\n=== 현재 작업 디렉토리 ===")
print(os.getcwd())

print("\n=== logger 모듈 import 테스트 ===")
try:
    from logger import get_logger
    print("logger 모듈 import 성공!")
except Exception as e:
    print(f"logger 모듈 import 실패: {e}")

print("\n=== logger 폴더 경로 존재 여부 ===")
logger_path = Path(__file__).resolve().parent.parent / "logger"
print(f"logger 폴더: {logger_path} - {'존재함' if logger_path.exists() else '존재하지 않음'}")