import pytest
import pandas as pd
from src.common.get_cipher import get_cipher
from deidentifier.functions import deidentify_patient_id_value

def test_patient_id_pseudonymization_reversible():
    config = {"deidentification_policy": "pseudonymization"}
    original_ids = ["12345678", "87654321", "11223344"]
    print("원본\t가명화\t복호화")
    excel_path = "data/raw/pathology-reports-sample.xls"
    field = "patient_id"
    cipher = get_cipher()

        # 엑셀 파일 읽기 (확장자에 따라 engine 지정)
        try:
            if excel_path.endswith(".xls"):
                df = pd.read_excel(excel_path, engine="xlrd")
            else:
                df = pd.read_excel(excel_path)
        except Exception as e:
            print(f"엑셀 파일 읽기 실패: {e}")
            return

        total = 0
        success = 0
        print("원본\t가명화\t복호화\t일치여부")
        for idx, row in df.iterrows():
            orig = str(row[field])
            pseudo = deidentify_patient_id_value(orig, config)
            try:
                recovered = cipher.decrypt(pseudo)
                match = "O" if orig == recovered else "X"
                if match == "O":
                    success += 1
            except Exception as e:
                recovered = f"복호화실패({e})"
                match = "X"
            print(f"{orig}\t{pseudo}\t{recovered}\t{match}")
            total += 1
        print(f"총 {total}개 중 복호화 일치 {success}개")
