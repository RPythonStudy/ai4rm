# ---
# ai_agent_instructions:
# - 모든 import는 파일 상단에 위치하고 PEP 8 스타일 가이드를 준수할 것
# - 함수는 역할별로 분리하고, 함수명은 직관적으로 작성
# - 인코딩 감지, 파일 입출력, 로깅 등은 업계표준 패키지/방식 사용
# - 코드 예시는 항상 간결하고 디버그 친화적으로 작성
# ---
# {PROJECT_ROOT}/src/pseudonymizer/pseudonymizer_pathology_report.py
# last modified: 2023-10-01

import os

import yaml
import chardet
from dotenv import load_dotenv

from common.logger import log_debug

load_dotenv()
FF3_KEY = os.getenv("FF3_KEY")
FF3_TWEAK = os.getenv("FF3_TWEAK")
FF3_ALPHABET = os.getenv("FF3_ALPHABET")

def detect_text_file_encoding(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read()
    result = chardet.detect(raw)
    return result['encoding'], raw

def load_config_pseudonimization_pathology_report(yml_path="config/pseudonynmization.yml"):
    with open(yml_path, encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f)
    log_debug(f"Pathology Report Config: {yaml_config.get('pathology_report', {})}")
    return yaml_config.get("pathology_report", {})

def read_text_files(input_dir: str):
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    log_debug(f"텍스트 파일 개수: {len(txt_files)}")
    contents = {}
    for f in txt_files:
        path = os.path.join(input_dir, f)
        enc, raw = detect_text_file_encoding(path)
        if enc:
            try:
                contents[f] = raw.decode(enc)
                log_debug(f"{f}: 인코딩={enc}")
            except Exception:
                contents[f] = None
                log_debug(f"{f}: 인코딩 감지 실패 (감지결과: {enc})")
        else:
            contents[f] = None
            log_debug(f"{f}: 인코딩 감지 실패 (감지결과: None)")
    return contents

if __name__ == "__main__":
    config_pathology_report = load_config_pseudonimization_pathology_report()
    read_text_files(config_pathology_report.get("input_dir", ""))