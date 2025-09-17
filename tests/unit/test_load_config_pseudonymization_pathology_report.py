# tests/unit/test_load_config_pseudonymization_pathology_report.py
# last modified: 2025-08-29
# pseudonymization.yml이 로딩되는지 assert
# 파일이 없을 때 예외 발생하는지 assert
# YAML 문법 오류일 때 예외 발생하는지 assert

import os
import pytest
import yaml
from deidentifier.pseudonymizer_pathology_report import load_config_pseudonymization_pathology_report


def test_load_config_success(tmp_path):
    config_content = """
    pathology_report:
      input_dir: data/raw/pathology_report
      output_dir: data/pseudonymized/pathology_report
      patient_id:
        pattern_description: "등록번호 공백 아라비아숫자8개 공백"
        regular_expression: '(?<!\\S)등록번호\\s*[:：]?\\s*(?P<pid>[0-9]{8})(?!\\S)'
        anonymization_policy: pseudonymization
    """
    cfg_file = tmp_path / "pseudonymization.yml"
    cfg_file.write_text(config_content, encoding="utf-8")

    config = load_config_pseudonymization_pathology_report(cfg_file)

    # 함수는 pathology_report 내부 dict를 바로 반환하므로,
    # 최상위에서 patient_id 등을 확인해야 함
    assert "input_dir" in config
    assert "output_dir" in config
    assert "patient_id" in config

    patient = config["patient_id"]
    assert "regular_expression" in patient
    assert "anonymization_policy" in patient

def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config_pseudonymization_pathology_report("no_such_file.yml")

def test_load_config_invalid_yaml(tmp_path):
    cfg_file = tmp_path / "broken.yml"
    cfg_file.write_text("::: invalid :::", encoding="utf-8")
    with pytest.raises(Exception):   # YAML 파싱 에러 발생
        load_config_pseudonymization_pathology_report(cfg_file)
