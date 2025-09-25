"""
파일명: src/common/excel_io.py
목적: 지정된 폴더의 엑셀파일의 입출력 담당
기능: 
- input_dir를 인자로 받아 폴더 내 모든 xls/xlsx 파일을 탐색
- Path 객체 및 pandas 라이브러리 사용
- {파일명: 데이터프레임} 형태의 딕셔너리 반환
변경이력:
  - 2025-09-24: 최초 생성 (BenKorea)
"""

import inspect
from pathlib import Path
import pandas as pd
from typing import Dict
from common.logger import log_error

def read_excels(input_dir: str) -> Dict[str, pd.DataFrame]:
  excel_files = Path(input_dir).rglob("*.xls*")
  dfs = {}
  for file in excel_files:
    try:
      df = pd.read_excel(file)
      dfs[file.name] = df
    except Exception as e:
      log_error(f"[{inspect.currentframe().f_code.co_name}] 엑셀 파일 읽기 오류: {file} - {e}")
  return dfs
