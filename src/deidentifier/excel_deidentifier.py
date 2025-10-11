"""
파일명: src/deindentifier/excel_deidentifier.py
목적: Excel 컬럼 범용 비식별화 모듈
사용법: python excel_deidentifier.py <excel_path> <yml_path> <output_path>
변경이력:
  - 2025-10-10: 최초 구현 (BenKorea)
"""

import warnings
from pathlib import Path

import pandas as pd
import typer

from common.excel_io import save_excels
from common.get_cipher import get_cipher
from common.logger import log_debug, log_error, log_info, log_warn
from common.load_config import load_config
from deidentifier.deid_utils import deidentify_columns

# OLE2 경고 전역 무시
warnings.filterwarnings("ignore", message=".*OLE2 inconsistency.*")

app = typer.Typer()

@app.command()
def main(
    excel_path: Path = typer.Argument(..., help="엑셀 파일 또는 디렉토리"),
    yml_path: Path = typer.Argument(..., help="비식별화 정책 YAML 파일"),
    output_path: Path = typer.Argument(..., help="출력 경로")
):
    """Excel 파일을 YAML 설정에 따라 비식별화 처리합니다."""
    
    try:
        log_info(f"[try] 시작 - 입력: {excel_path}, 정책: {yml_path}, 출력: {output_path}")
        
        # 설정 로드
        config = load_config(str(yml_path), section="pet")
        targets = config.get('targets', {})
        # 암호화 객체 초기화
        cipher_alphanumeric = get_cipher("alphanumeric")
        cipher_numeric = get_cipher("numeric")
        log_debug("[try] 암호화 객체 초기화 완료")
        
        # 엑셀 로드 (강력한 호환성)
        dfs = {}
        if excel_path.is_file():
            # 단일 파일: 다중 엔진으로 강제 읽기
            for engine in ['openpyxl', 'xlrd', 'calamine']:
                try:
                    df = pd.read_excel(excel_path, engine=engine)
                    dfs[excel_path.name] = df
                    log_info(f"[엑셀로드] {engine}로 성공: {excel_path.name}")
                    break
                except:
                    continue
        else:
            # 디렉토리: 각 파일별로 다중 엔진 시도
            for file in Path(excel_path).rglob("*.xls*"):
                for engine in ['openpyxl', 'xlrd', 'calamine']:
                    try:
                        df = pd.read_excel(file, engine=engine)
                        dfs[file.name] = df
                        log_debug(f"[엑셀로드] {engine}로 성공: {file.name}")
                        break
                    except Exception as e:
                        if engine == 'calamine':  # 마지막 엔진도 실패
                            log_error(f"[엑셀로드] 모든 엔진 실패: {file.name}")

        if not dfs:
            log_error("[엑셀로드] 읽을 수 있는 파일이 없습니다")
            raise typer.Exit(1)

        log_info(f"[엑셀로드] 로드 완료: {len(dfs)}개 파일")
        
        # 비식별화 처리
        for filename, df in dfs.items():
            dfs[filename] = deidentify_columns(df, targets, cipher_alphanumeric, cipher_numeric)
            log_debug(f"[엑셀비식별화] 처리 완료: {filename}")
        
        # 결과 저장
        output_path.mkdir(parents=True, exist_ok=True)
        save_excels(str(output_path), dfs, prefix="deid")
        
        log_info(f"[excel_deidentifier] 완료 - 출력: {output_path}, 파일: {len(dfs)}개")
        
    except Exception as e:
        log_error(f"[excel_deidentifier] 실패: {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()