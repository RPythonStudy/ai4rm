# {PROJECT_ROOT}/src/pseudonymizer/pseudonymizer_pathology_report.py
# last modified: 2025-08-27

import os
import re

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

def load_config_pseudonymization_pathology_report(yml_path="config/pseudonymization.yml"):
    with open(yml_path, encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f)
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

def pseudonymize_patient_id(content: str, fname: str = None):
# 정책 로딩 및 디버깅 출력
    config_pathology_report = load_config_pseudonymization_pathology_report()
    patient_id_conf = config_pathology_report.get("patient_id", {})
    patient_id_policy = patient_id_conf.get("anonymization_policy", "(설정없음)")
    regex = patient_id_conf.get("regular_expression", r'\b\d{8}\b')
    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""
    ids = re.findall(regex, content)
    pseudonymized_content = content
    for pid in ids:
        pseudo_pid = pid[::-1]  # 예시: 뒤집기
        pseudonymized_content = pseudonymized_content.replace(pid, pseudo_pid)
    if fname:
        log_debug(f"{fname}: patient_ids={ids} -> pseudonymized_content preview: {pseudonymized_content[:50]}")
    else:
        log_debug(f"patient_ids={ids} -> pseudonymized_content preview: {pseudonymized_content[:50]}")
    return pseudonymized_content


if __name__ == "__main__":

    config_pathology_report = load_config_pseudonymization_pathology_report()
    input_dir = config_pathology_report.get("input_dir", "")
    output_dir = config_pathology_report.get("output_dir", "")

    file_list = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    for fname in file_list:
        file_path = os.path.join(input_dir, fname)
        enc, raw = detect_text_file_encoding(file_path)
        try:
            file_content = raw.decode(enc)
            pseudonymized_content = pseudonymize_patient_id(file_content, fname)
            # output_dir에 pseudonymized_파일이름으로 저장
            output_fname = f"pseudonymized_{fname}"
            output_path = os.path.join(output_dir, output_fname)
            with open(output_path, "w", encoding=enc if enc else "utf-8") as out_f:
                out_f.write(pseudonymized_content)
            log_debug(f"{output_path}: 저장 완료")
        except Exception as e:
            log_debug(f"{file_path}: 디코딩 실패 - {e}")

