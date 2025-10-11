"""
파일명: src/metafier/metafier_cli.py  
목적: 병리 또는 PET 판독보고서 LLM 처리기 (CLI 버전)
설명: Gemini 2.0 Flash를 이용 배치 처리 및 정형화 - Typer CLI
변경이력:
  - 2025-10-12: 전역변수 문제 해결 - 파일 기반 상태 저장 (BenKorea)
"""

import os
import pickle
from pathlib import Path
from typing import Optional

import pandas as pd
import typer
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from common.logger import log_debug, log_error, log_info, log_warn

# 환경변수 로딩
load_dotenv()
google_api_key = os.getenv('GEMINI_API_KEY')

app = typer.Typer(help="AI4RM Metafier - PET 판독 분석기")

# 임시 상태 파일 경로
TEMP_STATE_FILE = Path.cwd() / ".pet_data_state.pkl"

def save_pet_state(pet_df: pd.DataFrame) -> None:
    """PET 데이터 상태 저장"""
    try:
        with open(TEMP_STATE_FILE, 'wb') as f:
            pickle.dump(pet_df, f)
        log_debug(f"[상태저장] PET 데이터 상태 저장: {len(pet_df)}행")
    except Exception as e:
        log_error(f"[상태저장] 저장 실패: {e}")

def load_pet_state() -> Optional[pd.DataFrame]:
    """PET 데이터 상태 로드"""
    try:
        if TEMP_STATE_FILE.exists():
            with open(TEMP_STATE_FILE, 'rb') as f:
                pet_df = pickle.load(f)
            log_debug(f"[상태로드] PET 데이터 상태 로드: {len(pet_df)}행")
            return pet_df
        else:
            log_debug("[상태로드] 상태 파일 없음")
            return None
    except Exception as e:
        log_error(f"[상태로드] 로드 실패: {e}")
        return None

def clear_pet_state() -> None:
    """PET 데이터 상태 파일 삭제"""
    try:
        if TEMP_STATE_FILE.exists():
            TEMP_STATE_FILE.unlink()
            log_debug("[상태삭제] PET 데이터 상태 파일 삭제")
    except Exception as e:
        log_warn(f"[상태삭제] 삭제 실패: {e}")

@app.command()
def load_pet(
    excel_folder: Path = typer.Argument(..., help="PET 엑셀 파일들 폴더"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="저장 경로")
) -> None:
    """엑셀 파일들을 PET 데이터프레임으로 통합"""
    
    log_info(f"[load_pet] PET 엑셀 로딩 시작: {excel_folder}")
    
    # 이전 상태 초기화
    clear_pet_state()
    
    # 엑셀 로드 (강력한 호환성)
    dfs = {}
    
    if excel_folder.is_file():
        # 단일 파일 처리
        log_info(f"[load_pet] 단일 파일 모드: {excel_folder}")
        for engine in ['openpyxl', 'xlrd', 'calamine']:
            try:
                df = pd.read_excel(excel_folder, engine=engine)
                dfs[excel_folder.name] = df
                log_info(f"[load_pet] {engine}로 성공: {excel_folder.name} ({len(df)}행)")
                break
            except Exception as e:
                log_debug(f"[load_pet] {engine} 실패: {excel_folder.name} - {e}")
                continue
        else:
            log_error(f"[load_pet] 모든 엔진 실패: {excel_folder.name}")
            raise typer.Exit(1)
    
    elif excel_folder.is_dir():
        # 디렉토리 처리
        log_info(f"[load_pet] 디렉토리 모드: {excel_folder}")
        excel_files = list(excel_folder.rglob("*.xls*"))
        
        if not excel_files:
            log_error(f"[load_pet] 엑셀 파일이 없음: {excel_folder}")
            print(f"❌ 엑셀 파일(.xlsx, .xls)이 없습니다: {excel_folder}")
            raise typer.Exit(1)
        
        log_info(f"[load_pet] 발견된 엑셀 파일: {len(excel_files)}개")
        
        for file in excel_files:
            file_loaded = False
            for engine in ['openpyxl', 'xlrd', 'calamine']:
                try:
                    df = pd.read_excel(file, engine=engine)
                    dfs[file.name] = df
                    log_debug(f"[load_pet] {engine}로 성공: {file.name} ({len(df)}행)")
                    file_loaded = True
                    break
                except Exception as e:
                    log_debug(f"[load_pet] {engine} 실패: {file.name} - {e}")
                    continue
            
            if not file_loaded:
                log_error(f"[load_pet] 모든 엔진 실패: {file.name}")
    
    else:
        log_error(f"[load_pet] 잘못된 경로: {excel_folder}")
        print(f"❌ 파일 또는 디렉토리가 존재하지 않습니다: {excel_folder}")
        raise typer.Exit(1)
    
    # 로딩 결과 확인
    if not dfs:
        log_error("[load_pet] 읽을 수 있는 엑셀 파일이 없습니다")
        print("❌ 읽을 수 있는 엑셀 파일이 없습니다")
        raise typer.Exit(1)
    
    log_info(f"[load_pet] 로드 완료: {len(dfs)}개 파일")
    
    # DataFrame 통합
    all_dfs = []
    for filename, df in dfs.items():
        df['source_file'] = filename  # 원본 파일명 추가
        all_dfs.append(df)
    
    pet_df = pd.concat(all_dfs, ignore_index=True)
    log_info(f"[load_pet] DataFrame 통합 완료: {len(pet_df)}행 {len(pet_df.columns)}컬럼")
    
    # 상태 저장
    save_pet_state(pet_df)
    
    # 결과 출력
    print(f"✅ PET 데이터 로딩 완료!")
    print(f"📊 총 레코드: {len(pet_df)}건")
    print(f"📋 컬럼: {list(pet_df.columns)}")
    print(f"📁 원본 파일: {len(dfs)}개")
    print(f"💾 상태 저장: {TEMP_STATE_FILE}")
    
    # 저장 (선택사항)
    if output:
        try:
            pet_df.to_excel(output, index=False)
            log_info(f"[load_pet] 데이터 저장 완료: {output}")
            print(f"💾 엑셀 저장: {output}")
        except Exception as e:
            log_error(f"[load_pet] 저장 실패: {e}")
            print(f"❌ 저장 실패: {e}")

@app.command()
def add_staging(
    column: str = typer.Option("판독소견", "--column", "-c", help="검색할 컬럼명"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="저장 경로")
) -> None:
    """staging 키워드로 scan_purpose 컬럼 파생"""
    
    # 상태 로드
    pet_df = load_pet_state()
    
    if pet_df is None:
        log_error("[add_staging] PET 데이터가 로딩되지 않음. load-pet 명령을 먼저 실행하세요")
        print("❌ PET 데이터 없음. load-pet 명령 먼저 실행")
        print(f"💡 해결방법: python src/metafier/metafier_cli.py load-pet 폴더경로")
        raise typer.Exit(1)
    
    # 컬럼 존재 확인
    if column not in pet_df.columns:
        available_cols = list(pet_df.columns)
        log_error(f"[add_staging] '{column}' 컬럼이 없음. 사용 가능한 컬럼: {available_cols}")
        print(f"❌ '{column}' 컬럼 없음")
        print(f"📋 사용 가능한 컬럼: {available_cols}")
        raise typer.Exit(1)
    
    log_info(f"[add_staging] staging 키워드 검색: '{column}' 컬럼")
    
    # scan_purpose 컬럼 추가
    pet_df['scan_purpose'] = ''
    
    # staging 키워드 검색 및 값 할당
    staging_mask = pet_df[column].str.contains('staging', case=False, na=False)
    pet_df.loc[staging_mask, 'scan_purpose'] = 'staging'
    
    staging_count = staging_mask.sum()
    log_info(f"[add_staging] staging 케이스 발견: {staging_count}건")
    
    # 상태 저장
    save_pet_state(pet_df)
    
    print(f"✅ scan_purpose 컬럼 추가 완료!")
    print(f"📊 staging 케이스: {staging_count}건")
    print(f"💾 상태 업데이트: {TEMP_STATE_FILE}")
    
    # 저장 (선택사항)
    if output:
        try:
            pet_df.to_excel(output, index=False)
            log_info(f"[add_staging] staging 결과 저장: {output}")
            print(f"💾 엑셀 저장: {output}")
        except Exception as e:
            log_error(f"[add_staging] 저장 실패: {e}")
            print(f"❌ 저장 실패: {e}")

@app.command()
def analyze_metastasis(
    limit: int = typer.Option(10, "--limit", "-l", help="분석할 레코드 수"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="저장 경로"),
    show_full: bool = typer.Option(False, "--full", "-f", help="판독소견 전체 출력")
) -> None:
    """staging 케이스 원격전이 분석 (Gemini API)"""
    
    # 상태 로드
    pet_df = load_pet_state()
    
    if pet_df is None:
        log_error("[analyze_metastasis] PET 데이터가 로딩되지 않음")
        print("❌ PET 데이터 없음. load-pet → add-staging 순서로 실행")
        print(f"💡 1단계: python src/metafier/metafier_cli.py load-pet 폴더경로")
        print(f"💡 2단계: python src/metafier/metafier_cli.py add-staging")
        raise typer.Exit(1)
    
    # scan_purpose 컬럼 확인
    if 'scan_purpose' not in pet_df.columns:
        log_error("[analyze_metastasis] scan_purpose 컬럼이 없음. add-staging 명령을 먼저 실행하세요")
        print("❌ scan_purpose 컬럼 없음. add-staging 명령 먼저 실행")
        print(f"💡 해결방법: python src/metafier/metafier_cli.py add-staging")
        raise typer.Exit(1)
    
    # staging 케이스 필터링
    staging_df = pet_df[pet_df['scan_purpose'] == 'staging']
    
    if len(staging_df) == 0:
        log_warn("[analyze_metastasis] staging 케이스가 없음")
        print("⚠️ staging 케이스 없음. add-staging 명령 먼저 실행")
        return
    
    # 분석 대상 제한
    analysis_df = staging_df.head(limit)
    log_info(f"[analyze_metastasis] 원격전이 분석 시작: {len(analysis_df)}건")
    
    # API 키 확인
    if not google_api_key:
        log_error("[analyze_metastasis] GEMINI_API_KEY 환경변수가 설정되지 않음")
        print("❌ GEMINI_API_KEY가 필요합니다. .env 파일을 확인하세요")
        raise typer.Exit(1)
    
    # LLM 초기화
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=google_api_key,
            temperature=0.0
        )
    except Exception as e:
        log_error(f"[analyze_metastasis] LLM 초기화 실패: {e}")
        print(f"❌ LLM 초기화 실패: {e}")
        raise typer.Exit(1)
    
    # 원격전이 컬럼 추가
    if '원격전이' not in pet_df.columns:
        pet_df['원격전이'] = ''
    
    # 분석 결과 저장용 리스트
    analysis_results = []
    
    # 각 레코드 분석
    for i, (idx, row) in enumerate(analysis_df.iterrows(), 1):
        report = row['판독소견']
        patient_id = row.get('환자번호', f'ID_{idx}')
        
        if pd.isna(report) or str(report).strip() == '':
            metastasis_risk = '판독문없음'
            pet_df.at[idx, '원격전이'] = metastasis_risk
            print(f"  {i}/{len(analysis_df)}: {metastasis_risk}")
            
            analysis_results.append({
                '순번': i,
                '환자번호': patient_id,
                '원격전이': metastasis_risk,
                '판독소견': '판독문 없음'
            })
            continue
        
        try:
            # Gemini API 호출
            prompt = f"다음 PET 판독문에서 원격전이 가능성을 '높음/낮음/불명확' 중 하나로 답하세요:\n\n{report}"
            result = llm.invoke(prompt)
            
            # 결과 파싱
            response = result.content.strip()
            if '높음' in response:
                metastasis_risk = '높음'
            elif '낮음' in response:
                metastasis_risk = '낮음'
            else:
                metastasis_risk = '불명확'
            
            pet_df.at[idx, '원격전이'] = metastasis_risk
            print(f"  {i}/{len(analysis_df)}: {metastasis_risk}")
            log_debug(f"[analyze_metastasis] 분석 완료 [{idx}]: {metastasis_risk}")
            
            # 분석 결과 저장 - 전체/요약 선택
            if show_full:
                display_report = str(report)  # 전체 판독소견
            else:
                display_report = report[:100] + '...' if len(str(report)) > 100 else str(report)
            
            analysis_results.append({
                '순번': i,
                '환자번호': patient_id,
                '원격전이': metastasis_risk,
                '판독소견': display_report
            })
            
        except Exception as e:
            log_warn(f"[analyze_metastasis] API 호출 실패 [{idx}]: {e}")
            metastasis_risk = 'API오류'
            pet_df.at[idx, '원격전이'] = metastasis_risk
            print(f"  {i}/{len(analysis_df)}: {metastasis_risk}")
            
            analysis_results.append({
                '순번': i,
                '환자번호': patient_id,
                '원격전이': metastasis_risk,
                '판독소견': f'API 오류: {str(e)[:50]}...'
            })
    
    # 상태 저장
    save_pet_state(pet_df)
    
    # 결과 요약
    result_counts = pet_df['원격전이'].value_counts()
    
    print(f"\n✅ 원격전이 분석 완료!")
    print(f"📊 분석 결과:")
    for status, count in result_counts.items():
        if status:  # 빈 값 제외
            print(f"   {status}: {count}건")
    
    # 분석된 레코드 상세 출력
    display_mode = "전체" if show_full else "요약"
    print(f"\n📋 분석된 {len(analysis_df)}건 상세 결과 ({display_mode}):")
    print("=" * 100)
    
    for result in analysis_results:
        print(f"[{result['순번']}] 환자: {result['환자번호']} | 원격전이: {result['원격전이']}")
        print(f"판독소견:")
        
        # 판독소견을 줄바꿈으로 구분하여 출력
        report_lines = str(result['판독소견']).split('\n')
        for line in report_lines:
            if line.strip():  # 빈 줄 제외
                print(f"  {line}")
        
        print("=" * 100)
    
    print(f"💾 상태 업데이트: {TEMP_STATE_FILE}")
    
    if show_full:
        print(f"💡 판독소견 전체 출력 모드입니다. 요약 모드는 --full 옵션 없이 실행하세요.")
    else:
        print(f"💡 판독소견 전체 보기: --full 또는 -f 옵션 추가")
    
    log_info(f"[analyze_metastasis] 원격전이 분석 완료: {len(analysis_df)}건")
    
    # 저장 (선택사항)
    if output:
        try:
            pet_df.to_excel(output, index=False)
            log_info(f"[analyze_metastasis] 최종 결과 저장: {output}")
            print(f"💾 엑셀 저장: {output}")
        except Exception as e:
            log_error(f"[analyze_metastasis] 저장 실패: {e}")
            print(f"❌ 저장 실패: {e}")

@app.command()
def pipeline(
    excel_folder: Path = typer.Argument(..., help="PET 엑셀 파일들 폴더"),
    limit: int = typer.Option(10, "--limit", "-l", help="분석할 staging 케이스 수"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="최종 저장 경로")
) -> None:
    """전체 파이프라인 실행: 로딩 → staging 추가 → 원격전이 분석"""
    
    log_info("[pipeline] PET 분석 파이프라인 시작")
    
    print("🚀 PET 분석 파이프라인 시작")
    print("=" * 50)
    
    try:
        # 1단계: 데이터 로딩
        print("📁 1단계: PET 데이터 로딩...")
        ctx = typer.Context(load_pet)
        ctx.invoke(load_pet, excel_folder=excel_folder)
        
        # 2단계: staging 파생
        print("\n🔍 2단계: staging 케이스 식별...")
        ctx = typer.Context(add_staging)
        ctx.invoke(add_staging)
        
        # 3단계: 원격전이 분석
        print(f"\n🤖 3단계: 원격전이 분석 (최대 {limit}건)...")
        ctx = typer.Context(analyze_metastasis)
        ctx.invoke(analyze_metastasis, limit=limit, output=output)
        
        print("\n🎉 파이프라인 완료!")
        log_info("[pipeline] PET 분석 파이프라인 완료")
        
    except Exception as e:
        log_error(f"[pipeline] 파이프라인 실행 중 오류: {e}")
        print(f"❌ 파이프라인 오류: {e}")
        raise typer.Exit(1)

@app.command()
def clear_state() -> None:
    """임시 상태 파일 삭제"""
    
    clear_pet_state()
    print(f"✅ 상태 파일 삭제 완료: {TEMP_STATE_FILE}")
    log_info("[clear_state] 상태 파일 삭제 완료")

if __name__ == "__main__":
    app()