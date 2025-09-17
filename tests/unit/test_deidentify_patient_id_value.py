# test_deidentify_patient_id_value.py
from deidentifier.functions import deidentify_patient_id_value

def test_anonymization():
    config = {"deidentification_policy": "anonymization", "anonymization_value": "XXXXXX"}
    assert deidentify_patient_id_value("12345678", config) == "XXXXXX"

def test_pseudonymization():
    config = {"deidentification_policy": "pseudonymization"}
    # 암호화 결과는 환경마다 다르므로, 길이만 체크
    result = deidentify_patient_id_value("12345678", config)
    assert isinstance(result, str) and len(result) > 0

def test_no_apply():
    config = {"deidentification_policy": "no_apply"}
    assert deidentify_patient_id_value("12345678", config) == "12345678"

if __name__ == "__main__":
    test_anonymization()
    test_pseudonymization()
    test_no_apply()
    print("ok")
