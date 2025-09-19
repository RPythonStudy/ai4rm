# src/pseudonymizer/pseudonymizer_pathology_report.py
# 병리보고서 비식별화 모듈
# last updated: 2025-09-17

def deidentify_date_field(content: str, field_conf: dict, fname: str = None):
    """
    날짜형 비식별화 범용 함수
    :param content: 원본 텍스트
    :param field_conf: yml에서 읽은 해당 필드 설정(dict)
    :param fname: 파일명(옵션, 로그용)
    :return: 비식별화된 텍스트
    """
    import re
    regex = field_conf.get("regular_expression", r'\d{4}-\d{2}-\d{2}')
    policy = field_conf.get("deidentification_policy", "no_apply")
    anonymization_value = field_conf.get("anonymization_value", "XXXX-XX-XX")
    pseudo_type = field_conf.get("pseudonymization_values", "month_to_first_day")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    def month_to_first_day(date_str):
        parts = date_str.split("-")
        if len(parts) == 3:
            return f"{parts[0]}-{parts[1]}-01"
        return date_str

    def year_to_january_first(date_str):
        parts = date_str.split("-")
        if len(parts) == 3:
            return f"{parts[0]}-01-01"
        return date_str

    def replace_date(match):
        date_str = match.group(1) if match.lastindex else match.group(0)
        if policy == "anonymization":
            log_debug(f"date 원본: {date_str}, 익명화 결과: {anonymization_value}")
            return match.group(0).replace(date_str, anonymization_value)
        elif policy == "pseudonymization":
            if pseudo_type == "month_to_first_day":
                new_date = month_to_first_day(date_str)
            elif pseudo_type == "year_to_january_first":
                new_date = year_to_january_first(date_str)
            else:
                new_date = date_str
            log_debug(f"date 원본: {date_str}, 가명화 결과: {new_date}")
            return match.group(0).replace(date_str, new_date)
        else:
            return match.group(0)

    result = re.sub(regex, replace_date, content)
    log_debug(f"[date_field] 적용 결과 preview: {result[:80]}")
    return result

# ------------------------
# pathologists(병리전문의) 비식별화 (정책에 따라 익명화/가명화/원본 반환)
# ------------------------
def deidentification_pathologists(content: str, fname: str = None):
    import re
    config_pathology_report = load_config_pseudonymization_pathology_report()
    path_conf = config_pathology_report.get("pathologists", {})
    regex = path_conf.get("regular_expression", r'병리전문의\s*[:：]?\s*(?P<pathologists>[가-힣/\s]+)')
    policy = path_conf.get("deidentification_policy", "anonymization")
    anonymization_value = path_conf.get("anonymization_value", "OOO")
    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""
    def replace_path(match):
        orig = match.group("pathologists")
        if policy == "anonymization":
            log_debug(f"pathologists 원본: {orig}, 익명화 결과: {anonymization_value}")
            return match.group(0).replace(orig, anonymization_value)
        elif policy == "pseudonymization":
            # 가명화 정책이 필요할 경우 여기에 추가
            log_debug(f"pathologists 원본: {orig}, 가명화 결과: {anonymization_value}")
            return match.group(0).replace(orig, anonymization_value)
        else:
            return match.group(0)
    result = re.sub(regex, replace_path, content, flags=re.MULTILINE)
    log_debug(f"[pathologists] 비식별화 적용 결과 preview: {result[:80]}")
    return result
# ------------------------
# result_inputter(결과 입력자) 비식별화 (정책에 따라 익명화/가명화/원본 반환)
# ------------------------
def deidentification_result_inputter(content: str, fname: str = None):
    import re
    config_pathology_report = load_config_pseudonymization_pathology_report()
    ri_conf = config_pathology_report.get("result_inputter", {})
    regex = ri_conf.get("regular_expression", r'결과 입력\s*[:：]?\s*(?P<result_inputter>[가-힣]+)')
    policy = ri_conf.get("deidentification_policy", "anonymization")
    anonymization_value = ri_conf.get("anonymization_value", "OOO")
    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""
    def replace_ri(match):
        orig = match.group("result_inputter")
        if policy == "anonymization":
            log_debug(f"result_inputter 원본: {orig}, 익명화 결과: {anonymization_value}")
            return match.group(0).replace(orig, anonymization_value)
        elif policy == "pseudonymization":
            # 가명화 정책이 필요할 경우 여기에 추가
            log_debug(f"result_inputter 원본: {orig}, 가명화 결과: {anonymization_value}")
            return match.group(0).replace(orig, anonymization_value)
        else:
            return match.group(0)
    result = re.sub(regex, replace_ri, content)
    log_debug(f"[result_inputter] 비식별화 적용 결과 preview: {result[:80]}")
    return result
# ------------------------
# gross_id(육안사진촬영 ID) 비식별화 (정책에 따라 익명화/가명화/원본 반환)
# ------------------------
def deidentification_gross_id(content: str, fname: str = None):
    import re
    config_pathology_report = load_config_pseudonymization_pathology_report()
    gross_conf = config_pathology_report.get("gross_id", {})
    regex = gross_conf.get("regular_expression", r'(?P<gross_id>[A-Za-z]{2,4}[0-9]{2,4}-[0-9]{4})\s*육안사진촬영')
    policy = gross_conf.get("deidentification_policy", "pseudonymization")
    anonymization_value = gross_conf.get("anonymization_value", "OOOO-OOOO")
    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""
    from common.get_cipher import get_cipher
    cipher = get_cipher()
    def replace_gross(match):
        orig = match.group("gross_id")
        if policy == "anonymization":
            log_debug(f"gross_id 원본: {orig}, 익명화 결과: {anonymization_value}")
            return match.group(0).replace(orig, anonymization_value)
        elif policy == "pseudonymization":
            try:
                pseudo_val = cipher.encrypt(orig.replace('-', ''))
                # OOOO-OOOO 형식으로 변환
                if len(pseudo_val) >= 8:
                    pseudo_val = pseudo_val[:4] + '-' + pseudo_val[4:8]
                log_debug(f"gross_id 원본: {orig}, 가명화 결과: {pseudo_val}")
                return match.group(0).replace(orig, pseudo_val)
            except Exception as e:
                log_debug(f"gross_id 가명화 실패: {e}")
                return match.group(0)
        else:
            return match.group(0)
    result = re.sub(regex, replace_gross, content)
    log_debug(f"[gross_id] 비식별화 적용 결과 preview: {result[:80]}")
    return result
# ------------------------
# phone_number(전화번호) 비식별화 (정책에 따라 익명화/가명화/원본 반환)
# ------------------------
def deidentification_phone_number(content: str, fname: str = None):
    import re
    config_pathology_report = load_config_pseudonymization_pathology_report()
    pn_conf = config_pathology_report.get("phone_number", {})
    regex = pn_conf.get("regular_expression", r'(\d{2,4}-\d{3,4}(-\d{4})?)')
    policy = pn_conf.get("deidentification_policy", "anonymization")
    anonymization_value = pn_conf.get("anonymization_value", "000-0000-0000")
    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""
    def replace_pn(match):
        orig = match.group(0)
        if policy == "anonymization":
            log_debug(f"phone_number 원본: {orig}, 익명화 결과: {anonymization_value}")
            return anonymization_value
        elif policy == "pseudonymization":
            # 가명화 정책이 필요할 경우 여기에 추가
            log_debug(f"phone_number 원본: {orig}, 가명화 결과: {anonymization_value}")
            return anonymization_value
        else:
            return orig
    result = re.sub(regex, replace_pn, content)
    log_debug(f"[phone_number] 비식별화 적용 결과 preview: {result[:80]}")
    return result
# ------------------------
# 한국원자력의학원 포함 줄 전체 ----로 대체
# ------------------------
def redact_kirams_line(content: str, fname: str = None):
    import re
    pattern = r'.*한국원자력의학원.*'
    def replace_line(match):
        log_debug(f"[KIRAMS] 원본 줄: {match.group(0)} → ----")
        return "----"
    result = re.sub(pattern, replace_line, content)
    log_debug(f"[KIRAMS] 적용 결과 preview: {result[:80]}")
    return result
# ------------------------
# attending_physician(담당의사) 비식별화 (정책에 따라 익명화/가명화/원본 반환)
# ------------------------
def deidentification_attending_physician(content: str, fname: str = None):
    import re
    config_pathology_report = load_config_pseudonymization_pathology_report()
    ap_conf = config_pathology_report.get("attending_physician", {})
    regex = ap_conf.get("regular_expression", r'담당의사\s+[:：]\s*(?P<attending_physician>[가-힣]+)')
    policy = ap_conf.get("deidentification_policy", "anonymization")
    anonymization_value = ap_conf.get("anonymization_value", "OOO")
    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""
    def replace_ap(match):
        orig = match.group("attending_physician")
        if policy == "anonymization":
            log_debug(f"attending_physician 원본: {orig}, 익명화 결과: {anonymization_value}")
            return match.group(0).replace(orig, anonymization_value)
        elif policy == "pseudonymization":
            # 가명화 정책이 필요할 경우 여기에 추가
            log_debug(f"attending_physician 원본: {orig}, 가명화 결과: {anonymization_value}")
            return match.group(0).replace(orig, anonymization_value)
        else:
            return match.group(0)
    result = re.sub(regex, replace_ap, content)
    log_debug(f"[attending_physician] 비식별화 적용 결과 preview: {result[:80]}")
    return result
# ------------------------
# result_date(결 과 일) 비식별화 (정책에 따라 익명화/가명화/원본 반환)
# ------------------------
def deidentification_result_date(content: str, fname: str = None):
    import re
    config_pathology_report = load_config_pseudonymization_pathology_report()
    rd_conf = config_pathology_report.get("result_date", {})
    regex = rd_conf.get("regular_expression", r'결 과 일\s*[:：]?\s*(?P<result_date>\d{4}-\d{2}-\d{2})')
    policy = rd_conf.get("deidentification_policy", "pseudonymization")
    anonymization_value = rd_conf.get("anonymization_value", "yyyy-mm-dd")
    pseudo_type = rd_conf.get("pseudonymization_values", "year_to_january_first")
    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""
    def pseudo_date(date_str):
        # year_to_january_first: 2022-05-17 -> 2022-01-01
        if pseudo_type == "year_to_january_first":
            year = date_str[:4]
            return f"{year}-01-01"
        elif pseudo_type == "month_to_first_day":
            year, month = date_str[:4], date_str[5:7]
            return f"{year}-{month}-01"
        return anonymization_value
    def replace_rd(match):
        orig = match.group("result_date")
        if policy == "anonymization":
            log_debug(f"result_date 원본: {orig}, 익명화 결과: {anonymization_value}")
            return match.group(0).replace(orig, anonymization_value)
        elif policy == "pseudonymization":
            pseudo = pseudo_date(orig)
            log_debug(f"result_date 원본: {orig}, 가명화 결과: {pseudo}")
            return match.group(0).replace(orig, pseudo)
        else:
            return match.group(0)
    result = re.sub(regex, replace_rd, content)
    log_debug(f"[result_date] 비식별화 적용 결과 preview: {result[:80]}")
    return result
# ------------------------
# out_inpatient(외래/입원) 비식별화 (정책에 따라 익명화/원본 반환)
# ------------------------
def deidentification_out_inpatient(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    oi_conf = config_pathology_report.get("out_inpatient", {})
    regex = oi_conf.get("regular_expression", r'외래/입원:\s*(입원|외래)')
    policy = oi_conf.get("deidentification_policy", "no_apply")
    anonymization_value = oi_conf.get("anonymization_value", "OO")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    if policy == "anonymization":
        def replace_oi(match):
            matched_str = match.group(0)
            log_debug(f"out_inpatient 원본: {matched_str}, 익명화 결과: 외래/입원: {anonymization_value}")
            # 이미 익명화된 값(외래/OO 등)은 치환하지 않음
            if matched_str in [f"외래/입원: {anonymization_value}", "외래/OO:", "외래/OO: {anonymization_value}"]:
                return matched_str
            return f"외래/입원: {anonymization_value}"
        result = re.sub(regex, replace_oi, content)
        log_debug(f"[out_inpatient] 익명화 적용 결과 preview: {result[:80]}")
        return result
    else:
        log_debug(f"[out_inpatient] 정책이 no_apply이므로 원본 반환")
        return content
# ------------------------
# ward_room(병동/병실) 비식별화 (정책에 따라 익명화/원본 반환)
# ------------------------
def deidentification_ward_room(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    ward_room_conf = config_pathology_report.get("ward_room", {})
    regex = ward_room_conf.get("regular_expression", r'병동/병실\s*[:：]?\s*(?P<ward>[가-힣A-Za-z0-9]+)\s*/\s*(?P<room>[A-Za-z0-9]+)(?!\S)')
    policy = ward_room_conf.get("deidentification_policy", "no_apply")
    anonymization_value = ward_room_conf.get("anonymization_value", "OOO/OO")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    if policy == "anonymization":
        def replace_ward_room(match):
            ward = match.group("ward")
            room = match.group("room")
            log_debug(f"ward_room 원본: {ward} / {room}, 익명화 결과: {anonymization_value}")
            return match.group(0).replace(f"{ward} / {room}", anonymization_value)
        result = re.sub(regex, replace_ward_room, content)
        log_debug(f"[ward_room] 익명화 적용 결과 preview: {result[:80]}")
        return result
    else:
        log_debug(f"[ward_room] 정책이 no_apply이므로 원본 반환")
        return content
# ------------------------
# age(나이) 비식별화 (정책에 따라 익명화/원본 반환)
# ------------------------
def deidentification_age(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    age_conf = config_pathology_report.get("age", {})
    regex = age_conf.get("regular_expression", r'성별/나이\s*[:：]?\s*[FM여남]\s*/\s*(?P<age>\d{1,3})')
    policy = age_conf.get("deidentification_policy", "no_apply")
    anonymization_value = age_conf.get("anonymization_value", "00")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    # 단계별 디버깅 로그 추가
    log_debug(f"[age] 정책: {policy}, 정규식: {regex}")
    matches = re.findall(regex, content)
    log_debug(f"[age] 매칭 결과: {matches}")

    if policy == "pseudonymization":
        pseudonymization_values = age_conf.get("pseudonymization_values", "5year")
        def age_to_5year(age_str):
            try:
                age = int(age_str)
                new_age = (age // 5) * 5
                log_debug(f"[age] 5년 단위 변환: {age_str} → {new_age}-{new_age+4}")
                return f"{new_age}-{new_age+4}"
            except Exception as e:
                log_debug(f"[age] 5년 변환 실패: {e}")
                return age_str
        def age_to_10year(age_str):
            try:
                age = int(age_str)
                new_age = (age // 10) * 10
                log_debug(f"[age] 10년 단위 변환: {age_str} → {new_age}-{new_age+9}")
                return f"{new_age}-{new_age+9}"
            except Exception as e:
                log_debug(f"[age] 10년 변환 실패: {e}")
                return age_str
        def replace_age(match):
            age_val = match.group("age")
            log_debug(f"[age] 치환 전 값: {age_val}")
            if pseudonymization_values in ["5year", "age_to_5year_group"]:
                new_age = age_to_5year(age_val)
            elif pseudonymization_values in ["10year", "age_to_10year_group"]:
                new_age = age_to_10year(age_val)
            else:
                new_age = age_val
            log_debug(f"[age] 최종 치환 값: {new_age}")
            return match.group(0).replace(age_val, new_age)
        result = re.sub(regex, replace_age, content)
        log_debug(f"[age] 가명화 적용 결과 preview: {result[:80]}")
        return result
    elif policy == "anonymization":
        def replace_age(match):
            age_val = match.group("age")
            log_debug(f"[age] 익명화 치환 전 값: {age_val}")
            log_debug(f"[age] 익명화 결과: {anonymization_value}")
            return match.group(0).replace(age_val, anonymization_value)
        result = re.sub(regex, replace_age, content)
        log_debug(f"[age] 익명화 적용 결과 preview: {result[:80]}")
        return result
    else:
        log_debug(f"[age] 정책이 no_apply이므로 원본 반환")
        return content
# ------------------------
# sex(성별) 비식별화 (정책에 따라 익명화/원본 반환)
# ------------------------
def deidentification_sex(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    sex_conf = config_pathology_report.get("sex", {})
    regex = sex_conf.get("regular_expression", r'성별\s*[:：]?\s*(?P<sex>[FM여남])')
    policy = sex_conf.get("deidentification_policy", "no_apply")
    anonymization_value = sex_conf.get("anonymization_value", "O")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    if policy == "anonymization":
        def replace_sex(match):
            sex_val = match.group("sex")
            log_debug(f"sex 원본: {sex_val}, 익명화 결과: {anonymization_value}")
            return match.group(0).replace(sex_val, anonymization_value)
        result = re.sub(regex, replace_sex, content)
        log_debug(f"[sex] 익명화 적용 결과 preview: {result[:80]}")
        return result
    else:
        log_debug(f"[sex] 정책이 no_apply이므로 원본 반환")
        return content
# ------------------------
# referring_department(의뢰과) 비식별화 (정책에 따라 익명화/원본 반환)
# ------------------------
def deidentification_referring_department(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    ref_department_conf = config_pathology_report.get("referring_department", {})
    regex = ref_department_conf.get("regular_expression", r'의뢰과\s*[:：]?\s*(?P<ref_department>[가-힣]+)')
    policy = ref_department_conf.get("deidentification_policy", "no_apply")
    anonymization_value = ref_department_conf.get("anonymization_value", "OOOOOOOO")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    if policy == "anonymization":
        def replace_department(match):
            dname = match.group("ref_department")
            log_debug(f"referring_department 원본: {dname}, 익명화 결과: {anonymization_value}")
            return match.group(0).replace(dname, anonymization_value)
        result = re.sub(regex, replace_department, content)
        log_debug(f"[referring_department] 익명화 적용 결과 preview: {result[:80]}")
        return result
    else:
        log_debug(f"[referring_department] 정책이 no_apply이므로 원본 반환")
        return content
# ------------------------
# patient_id 비식별화 (정책에 따라 가명화/익명화/원본 반환)
# ------------------------
def deidentification_patient_id(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    patient_id_conf = config_pathology_report.get("patient_id", {})
    regex = patient_id_conf.get("regular_expression", r'등록번호\s*[:：]?\s*(?P<pid>[0-9]{8})')
    policy = patient_id_conf.get("deidentification_policy", "no_apply")
    anonymization_value = patient_id_conf.get("anonymization_value", "OOOOOOOO")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    if policy == "pseudonymization":
        cipher = get_cipher()
        def replace_patient_id(match):
            pid = match.group("pid")
            pseudo_pid = cipher.encrypt(pid)
            log_debug(f"patient_id 원본: {pid}, 가명화 결과: {pseudo_pid}")
            return match.group(0).replace(pid, pseudo_pid)
        result = re.sub(regex, replace_patient_id, content)
        log_debug(f"[patient_id] 가명화 적용 결과 preview: {result[:80]}")
        return result
    elif policy == "anonymization":
        def replace_patient_id(match):
            pid = match.group("pid")
            log_debug(f"patient_id 원본: {pid}, 익명화 결과: {anonymization_value}")
            return match.group(0).replace(pid, anonymization_value)
        result = re.sub(regex, replace_patient_id, content)
        log_debug(f"[patient_id] 익명화 적용 결과 preview: {result[:80]}")
        return result
    else:
        log_debug(f"[patient_id] 정책이 no_apply이므로 원본 반환")
        return content
# ------------------------
# referring_physician(의뢰의사) 비식별화 (정책에 따라 익명화/원본 반환)
# ------------------------
def deidentification_referring_physician(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    ref_physician_conf = config_pathology_report.get("referring_physician", {})
    regex = ref_physician_conf.get("regular_expression", r'의뢰의사\s*[:：]?\s*(?P<ref_physician>[가-힣]+)')
    policy = ref_physician_conf.get("deidentification_policy", "no_apply")
    anonymization_value = ref_physician_conf.get("anonymization_value", "OOO")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    if policy == "anonymization":
        def replace_physician(match):
            pname = match.group("ref_physician")
            log_debug(f"referring_physician 원본: {pname}, 익명화 결과: {anonymization_value}")
            return match.group(0).replace(pname, anonymization_value)
        result = re.sub(regex, replace_physician, content)
        log_debug(f"[referring_physician] 익명화 적용 결과 preview: {result[:80]}")
        return result
    else:
        log_debug(f"[referring_physician] 정책이 no_apply이므로 원본 반환")
        return content
# ------------------------
# patient_name 비식별화 (정책에 따라 익명화/원본 반환)
# ------------------------
def deidentification_patient_name(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    patient_name_conf = config_pathology_report.get("patient_name", {})
    regex = patient_name_conf.get("regular_expression", r'환 자 명\s*[:：]?\s*(?P<pname>[가-힣]+)')
    policy = patient_name_conf.get("deidentification_policy", "no_apply")
    anonymization_value = patient_name_conf.get("anonymization_value", "OOO")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    # 매칭 결과 로그 추가
    matches = re.findall(regex, content)
    log_debug(f"[patient_name] 매칭 결과: {matches}, 정책: {policy}")

    if policy == "anonymization":
        def replace_name(match):
            pname = match.group("pname")
            log_debug(f"patient_name 원본: {pname}, 익명화 결과: {anonymization_value}")
            return match.group(0).replace(pname, anonymization_value)
        result = re.sub(regex, replace_name, content)
        log_debug(f"[patient_name] 익명화 적용 결과 preview: {result[:80]}")
        return result
    else:
        log_debug(f"[patient_name] 정책이 no_apply이므로 원본 반환")
        return content
# ------------------------
# receipt_date 비식별화 (정책에 따라 변환/익명화/원본 반환)
# ------------------------
def deidentification_receipt_date(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    receipt_date_conf = config_pathology_report.get("receipt_date", {})
    regex = receipt_date_conf.get("regular_expression", r'접수일\s*[:：]?\s*(?P<receipt_date>\d{4}-\d{2}-\d{2})')
    policy = receipt_date_conf.get("deidentification_policy", "no_apply")
    pseudonymization_values = receipt_date_conf.get("pseudonymization_values", "month_to_first_day")
    anonymization_value = receipt_date_conf.get("anonymization_value", "XXXX-XX-XX")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    def month_to_first_day(date_str):
        parts = date_str.split("-")
        if len(parts) == 3:
            return f"{parts[0]}-{parts[1]}-01"
        return date_str

    def year_to_january_first(date_str):
        parts = date_str.split("-")
        if len(parts) == 3:
            return f"{parts[0]}-01-01"
        return date_str

    if policy == "pseudonymization":
        def replace_receipt_date(match):
            date_str = match.group("receipt_date")
            if pseudonymization_values == "month_to_first_day":
                new_date = month_to_first_day(date_str)
            elif pseudonymization_values == "year_to_january_first":
                new_date = year_to_january_first(date_str)
            else:
                new_date = date_str
            log_debug(f"receipt_date 원본: {date_str}, 변환 결과: {new_date}")
            return match.group(0).replace(date_str, new_date)
        result = re.sub(regex, replace_receipt_date, content)
        return result
    elif policy == "anonymization":
        def replace_receipt_date(match):
            date_str = match.group("receipt_date")
            return match.group(0).replace(date_str, anonymization_value)
        result = re.sub(regex, replace_receipt_date, content)
        return result
    else:
        return content
# ------------------------
# pathology_id 비식별화 (정책에 따라 가명화/익명화/원본 반환)
# ------------------------
def deidentification_pathology_id(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    pathology_id_conf = config_pathology_report.get("pathology_id", {})
    regex = pathology_id_conf.get("regular_expression", r'병리번호\s*[:：]?\s*(?P<pathology_id>[0-9]{8})')
    policy = pathology_id_conf.get("deidentification_policy", "no_apply")
    anonymization_value = pathology_id_conf.get("anonymization_value", "OOO")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    if policy == "pseudonymization":
        cipher = get_cipher()
        def replace_pathology_id(match):
            pid = match.group("pathology_id")  # 예: S16-15569
            pid_nohyphen = pid.replace("-", "")
            pseudo_pid = cipher.encrypt(pid_nohyphen)
            # 원래 하이픈 위치(4번째)에 하이픈 삽입
            if "-" in pid and len(pseudo_pid) >= 4:
                pseudo_pid = pseudo_pid[:3] + "-" + pseudo_pid[3:]
            log_debug(f"pathology_id 원본: {pid}, 암호화 결과: {pseudo_pid}")
            return match.group(0).replace(pid, pseudo_pid)
        result = re.sub(regex, replace_pathology_id, content)
        return result
    elif policy == "anonymization":
        def replace_pathology_id(match):
            pid = match.group("pathology_id")
            return match.group(0).replace(pid, anonymization_value)
        result = re.sub(regex, replace_pathology_id, content)
        return result
    else:
        return content
# ------------------------
# print_date 비식별화 (정책에 따라 변환/익명화/원본 반환)
# ------------------------
def deidentification_print_date(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    print_date_conf = config_pathology_report.get("print_date", {})
    regex = print_date_conf.get("regular_expression", r'출력일\s*[:：]?\s*(?P<print_date>\d{4}-\d{2}-\d{2})')
    policy = print_date_conf.get("deidentification_policy", "no_apply")
    pseudonymization_values = print_date_conf.get("pseudonymization_values", "month_to_first_day")
    anonymization_value = print_date_conf.get("anonymization_value", "XXXX-XX-XX")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    def month_to_first_day(date_str):
        # yyyy-mm-dd → yyyy-mm-01
        parts = date_str.split("-")
        if len(parts) == 3:
            return f"{parts[0]}-{parts[1]}-01"
        return date_str

    def year_to_january_first(date_str):
        # yyyy-mm-dd → yyyy-01-01
        parts = date_str.split("-")
        if len(parts) == 3:
            return f"{parts[0]}-01-01"
        return date_str

    if policy == "pseudonymization":
        def replace_print_date(match):
            date_str = match.group("print_date")
            if pseudonymization_values == "month_to_first_day":
                new_date = month_to_first_day(date_str)
            elif pseudonymization_values == "year_to_january_first":
                new_date = year_to_january_first(date_str)
            else:
                new_date = date_str
            log_debug(f"print_date 원본: {date_str}, 변환 결과: {new_date}")
            return match.group(0).replace(date_str, new_date)
        result = re.sub(regex, replace_print_date, content)
        return result
    elif policy == "anonymization":
        def replace_print_date(match):
            date_str = match.group("print_date")
            return match.group(0).replace(date_str, anonymization_value)
        result = re.sub(regex, replace_print_date, content)
        return result
    else:
        return content
# ------------------------
# PGM_ID 비식별화 (정책에 따라 가명화/익명화/원본 반환)
# ------------------------
def deidentification_pgm_id(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    pgm_id_conf = config_pathology_report.get("PGM_ID", {})
    regex = pgm_id_conf.get("regular_expression", r'PGM_ID\s*[:：]?\s*(?P<pgm_id>[A-Za-z0-9]{8})')
    policy = pgm_id_conf.get("deidentification_policy", "no_apply")
    anonymization_value = pgm_id_conf.get("anonymization_value", "OOOOOOOO")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    if policy == "pseudonymization":
        cipher = get_cipher()
        def replace_pgm_id(match):
            pid = match.group("pgm_id")
            pseudo_pid = cipher.encrypt(pid)
            log_debug(f"PGM_ID 원본: {pid}, 암호화 결과: {pseudo_pid}")
            return match.group(0).replace(pid, pseudo_pid)
        result = re.sub(regex, replace_pgm_id, content)
        return result
    elif policy == "anonymization":
        def replace_pgm_id(match):
            pid = match.group("pgm_id")
            return match.group(0).replace(pid, anonymization_value)
        result = re.sub(regex, replace_pgm_id, content)
        return result
    else:
        return content
# ------------------------
# printer_id 비식별화 (정책에 따라 가명화/익명화/원본 반환)
# ------------------------
def deidentification_printer_id(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    printer_id_conf = config_pathology_report.get("printer_id", {})
    regex = printer_id_conf.get("regular_expression", r'출력자ID\s*[:：]?\s*(?P<printer_id>[0-9]{4,8})')
    policy = printer_id_conf.get("deidentification_policy", "no_apply")
    anonymization_value = printer_id_conf.get("anonymization_value", "OOOO")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    if policy == "pseudonymization":
        cipher = get_cipher()
        def replace_printer_id(match):
            pid = match.group("printer_id")
            padded_pid = pid.zfill(6)
            log_debug(f"printer_id 원본: {pid}, 패딩 적용: {padded_pid}")
            try:
                pseudo_pid = cipher.encrypt(padded_pid)
                log_debug(f"printer_id 암호화 입력값: {padded_pid}, 암호화 결과: {pseudo_pid}")
                return match.group(0).replace(pid, pseudo_pid)
            except Exception as e:
                log_debug(f"printer_id 암호화 실패 - {e}")
                return match.group(0)
        result = re.sub(regex, replace_printer_id, content)
        return result
    elif policy == "anonymization":
        def replace_printer_id(match):
            pid = match.group("printer_id")
            return match.group(0).replace(pid, anonymization_value)
        result = re.sub(regex, replace_printer_id, content)
        return result
    else:
        return content
# ------------------------
# print_id 가명화 (FF3 암호화 적용, 정책에 따라)
# ------------------------
def pseudonymize_print_id(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    print_id_conf = config_pathology_report.get("print_id", {})
    regex = print_id_conf.get("regular_expression", r'print_id\s*[:：]?\s*(?P<print_id>[A-Za-z0-9]{8})')
    policy = print_id_conf.get("deidentification_policy", "no_apply")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    if policy == "pseudonymization":
        cipher = get_cipher()
        def replace_print_id(match):
            pid = match.group("print_id")
            pseudo_pid = cipher.encrypt(pid)
            return match.group(0).replace(pid, pseudo_pid)
        pseudonymized_content = re.sub(regex, replace_print_id, content)
        return pseudonymized_content
    elif policy == "anonymization":
        anonymization_value = print_id_conf.get("anonymization_value", "OOOOOOOO")
        def replace_print_id(match):
            pid = match.group("print_id")
            return match.group(0).replace(pid, anonymization_value)
        anonymized_content = re.sub(regex, replace_print_id, content)
        return anonymized_content
    else:
        return content
# ------------------------
# PGM_ID 익명화 (무조건 OOO으로 대체)
# ------------------------
def anonymize_pgm_id(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    pgm_id_conf = config_pathology_report.get("PGM_ID", {})
    regex = pgm_id_conf.get("regular_expression", r'PGM_ID\s*[:：]?\s*(?P<pgm_id>[0-9]{8})')

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    anonymization_value = pgm_id_conf.get("anonymization_value", "OOO")
    def replace_pgm_id(match):
        pid = match.group("pgm_id")
        return match.group(0).replace(pid, anonymization_value)

    anonymized_content = re.sub(regex, replace_pgm_id, content)
    return anonymized_content
# ------------------------
# pathology_id 익명화 (무조건 OOO으로 대체)
# ------------------------
def anonymize_pathology_id(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    pathology_id_conf = config_pathology_report.get("pathology_id", {})
    regex = pathology_id_conf.get("regular_expression", r'병리번호\s*[:：]?\s*(?P<pathology_id>[0-9]{8})')

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    def replace_pathology_id(match):
        pid = match.group("pathology_id")
        return match.group(0).replace(pid, "OOO")

    anonymized_content = re.sub(regex, replace_pathology_id, content)
    return anonymized_content
# ------------------------
# printer_id 가명화 (FF3 암호화 적용)
# ------------------------
def pseudonymize_printer_id(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    printer_id_conf = config_pathology_report.get("printer_id", {})
    regex = printer_id_conf.get("regular_expression", r'출력자 ID\s*[:：]?\s*(?P<printer_id>[0-9]{6})')

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    anonymization_value = printer_id_conf.get("anonymization_value", "OOOO")
    def replace_printer_id(match):
        pid = match.group("printer_id")
        return match.group(0).replace(pid, anonymization_value)

    anonymized_content = re.sub(regex, replace_printer_id, content)
    return anonymized_content
# ------------------------
# patient_name 익명화 (무조건 OOO으로 대체)
# ------------------------
def anonymize_patient_name(content: str, fname: str = None):
    config_pathology_report = load_config_pseudonymization_pathology_report()
    patient_name_conf = config_pathology_report.get("patient_name", {})
    regex = patient_name_conf.get("regular_expression", r'환 자 명\s*[:：]?\s*(?P<pname>[가-힣]+)')

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    # 환자명 부분을 무조건 OOO으로 대체
    def replace_name(match):
        return match.group(0).replace(match.group("pname"), "OOO")

    anonymized_content = re.sub(regex, replace_name, content)
    return anonymized_content
# src/pseudonymizer/pseudonymizer_pathology_report.py
# last modified: 2025-09-10
# get_cipher() 함수로 FF3 암호화 적용
def deidentify_date_field(content: str, field_conf: dict, fname: str = None):
    """
    날짜형 비식별화 범용 함수
    :param content: 원본 텍스트
    :param field_conf: yml에서 읽은 해당 필드 설정(dict)
    :param fname: 파일명(옵션, 로그용)
    :return: 비식별화된 텍스트
    """
    import re
    regex = field_conf.get("regular_expression", r'\d{4}-\d{2}-\d{2}')
    policy = field_conf.get("deidentification_policy", "no_apply")
    anonymization_value = field_conf.get("anonymization_value", "XXXX-XX-XX")
    pseudo_type = field_conf.get("pseudonymization_values", "month_to_first_day")

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    def month_to_first_day(date_str):
        parts = date_str.split("-")
        if len(parts) == 3:
            return f"{parts[0]}-{parts[1]}-01"
        return date_str

    def year_to_january_first(date_str):
        parts = date_str.split("-")
        if len(parts) == 3:
            return f"{parts[0]}-01-01"
        return date_str

    def replace_date(match):
        if hasattr(match, 'groupdict') and match.groupdict():
            date_str = next(iter(match.groupdict().values()))
        else:
            date_str = match.group(0)
        if policy == "anonymization":
            log_debug(f"date 원본: {date_str}, 익명화 결과: {anonymization_value}")
            return match.group(0).replace(date_str, anonymization_value)
        elif policy == "pseudonymization":
            if pseudo_type == "month_to_first_day":
                new_date = month_to_first_day(date_str)
            elif pseudo_type == "year_to_january_first":
                new_date = year_to_january_first(date_str)
            else:
                new_date = date_str
            log_debug(f"date 원본: {date_str}, 가명화 결과: {new_date}")
            return match.group(0).replace(date_str, new_date)
        else:
            return match.group(0)

    result = re.sub(regex, replace_date, content)
    log_debug(f"[date_field] 적용 결과 preview: {result[:80]}")
    return result

import os
import re
import yaml
import chardet
from dotenv import load_dotenv
from common.logger import log_debug
from common.get_cipher import get_cipher


# ------------------------
# 텍스트 파일 인코딩 감지
# ------------------------
def detect_text_file_encoding(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read()
    result = chardet.detect(raw)
    enc = result.get('encoding')

    # 안전한 fallback: 환경마다 달라지는 인코딩은 기본 "utf-8"로 교체
    allowed = {"utf-8", "ascii", "euc-kr", "cp949", "utf-16", "iso2022_kr"}
    if enc is None:
        enc = "utf-8"
    else:
        enc = enc.lower()
        if enc not in allowed:
            enc = "utf-8"

    return enc, raw


# ------------------------
# YAML 설정 로딩
# ------------------------
def load_config_pseudonymization_pathology_report(yml_path="config/pseudonymization.yml"):
    with open(yml_path, encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f)
    return yaml_config.get("pathology_report", {})


# ------------------------
# 텍스트 파일 읽기
# ------------------------
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


# ------------------------
# patient_id 가명화 (FF3 암호화 적용)
# ------------------------
def pseudonymize_patient_id(content: str, fname: str = None):
    # 정책 로딩 및 디버깅 출력
    config_pathology_report = load_config_pseudonymization_pathology_report()
    patient_id_conf = config_pathology_report.get("patient_id", {})
    patient_id_policy = patient_id_conf.get("deidentification_policy", "(설정없음)")
    regex = patient_id_conf.get("regular_expression", r'\b\d{8}\b')

    if content is None:
        if fname:
            log_debug(f"{fname}: [읽기 실패]")
        else:
            log_debug("[읽기 실패]")
        return ""

    # FF3 암호화 준비
    cipher = get_cipher()

    ids = re.findall(regex, content)
    pseudonymized_content = content

    for pid in ids:
        try:
            pseudo_pid = cipher.encrypt(pid)   # ✅ FF3 암호화 적용
            pseudonymized_content = pseudonymized_content.replace(pid, pseudo_pid)
            log_debug(f"patient_id {pid} → {pseudo_pid}")
        except Exception as e:
            log_debug(f"patient_id {pid}: 가명화 실패 - {e}")

    if fname:
        log_debug(f"{fname}: patient_ids={ids} -> pseudonymized_content preview: {pseudonymized_content[:50]}")
    else:
        log_debug(f"patient_ids={ids} -> pseudonymized_content preview: {pseudonymized_content[:50]}")

    return pseudonymized_content


# ------------------------
# 메인 실행부
# ------------------------
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
            file_content = redact_kirams_line(file_content, fname)

            # 날짜군 비식별화 적용
            for date_field in ["print_date", "receipt_date", "result_date"]:
                field_conf = config_pathology_report.get(date_field, {})
                file_content = deidentify_date_field(file_content, field_conf, fname)

            # 기존 함수 적용
            file_content = deidentification_printer_id(file_content, fname)
            file_content = deidentification_pgm_id(file_content, fname)
            file_content = deidentification_pathology_id(file_content, fname)
            file_content = deidentification_patient_name(file_content, fname)
            file_content = deidentification_referring_physician(file_content, fname)
            file_content = deidentification_attending_physician(file_content, fname)
            file_content = deidentification_patient_id(file_content, fname)
            file_content = deidentification_referring_department(file_content, fname)
            file_content = deidentification_sex(file_content, fname)
            file_content = deidentification_age(file_content, fname)
            file_content = deidentification_ward_room(file_content, fname)
            file_content = deidentification_out_inpatient(file_content, fname)
            file_content = deidentification_phone_number(file_content, fname)
            file_content = deidentification_gross_id(file_content, fname)
            file_content = deidentification_result_inputter(file_content, fname)
            file_content = deidentification_pathologists(file_content, fname)

            output_fname = f"pseudonymized_{fname}"
            output_path = os.path.join(output_dir, output_fname)
            with open(output_path, "w", encoding=enc if enc else "utf-8") as out_f:
                out_f.write(file_content)
            log_debug(f"{output_path}: 저장 완료")
        except Exception as e:
            log_debug(f"{file_path}: 디코딩 실패 - {e}")
