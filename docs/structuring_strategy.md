"""
1단계 구조화 결과 저장 전략 구현 가이드
Path: docs/structuring_strategy.md

## 🎯 전략 개요
기존 YAML 설정을 최대한 보존하면서 1단계 구조화 결과를 저장하는 방법

## 📋 처리 흐름

### Stage 1: 구조화 (Structuring)
1. **입력**: 원본 병리보고서 (Excel)
2. **처리**: `sections` 설정에 따라 파싱
   - `policy: remove` → 텍스트에서 삭제만
   - `policy: extraction` → 별도 컬럼으로 추출
3. **출력**: 구조화된 데이터 (비식별화 전)
   - 저장 위치: `structured_output_dir`
   - 컬럼: `patient_info_raw`, `gross_findings_raw`, `pathologic_diagnosis_raw`

### Stage 2: 비식별화 (De-identification)
1. **입력**: Stage 1의 구조화 결과
2. **처리**: `targets` 설정에 따라 비식별화
3. **출력**: 최종 비식별화 데이터
   - 저장 위치: `output_dir`

## ⚙️ 설정 구조

```yaml
pathology_report:
  structuring:
    enabled: true
    save_intermediate_results: true  # 1단계 결과 저장
    preserve_original_text: true     # 원본 텍스트 보존
    
  sections:
    gross_findings:
      policy: extraction
      column_name: "gross_findings_raw"  # 비식별화 전 컬럼명
      
  targets:
    patient_name:
      # 2단계에서 비식별화 처리
```

## 🔧 구현 방법

### 함수 구조
```python
def process_pathology_reports(config):
    # Stage 1: 구조화
    if config['structuring']['enabled']:
        structured_df = structure_sections(df, config['sections'])
        
        if config['structuring']['save_intermediate_results']:
            save_structured_results(structured_df, config['paths']['structured_output_dir'])
    
    # Stage 2: 비식별화
    deidentified_df = deidentify_targets(structured_df, config['targets'])
    save_final_results(deidentified_df, config['paths']['output_dir'])
```

### 컬럼 명명 규칙
- **1단계 (구조화)**: `{section_name}_raw` (예: `gross_findings_raw`)
- **2단계 (비식별화)**: `{target_name}_deid` (예: `patient_name_deid`)

## 💡 장점
1. **기존 설정 보존**: 현재 YAML 구조 최대한 유지
2. **단계별 저장**: 중간 결과 확인 가능
3. **유연성**: 각 단계를 독립적으로 실행 가능
4. **호환성**: 기존 코드와의 호환성 유지

## 🎯 예상 결과

### 1단계 구조화 결과 (structured/)
```
patient_id | patient_info_raw        | gross_findings_raw      | pathologic_diagnosis_raw
P001      | "환자명: 홍길동\n나이: 45"  | "육안소견 내용..."        | "병리진단 내용..."
```

### 2단계 비식별화 결과 (deidentified/)
```
patient_id | patient_info_deid       | gross_findings_deid     | pathologic_diagnosis_deid
P001_XXXX | "환자명: OOOO\n나이: 40-49" | "육안소견 내용..."        | "병리진단 내용..."
```
"""
