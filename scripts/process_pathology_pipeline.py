#!/usr/bin/env python3
"""
병리보고서 전체 처리 통합 실행기
Path: scripts/process_pathology_pipeline.py
Purpose: 
    - 구조화 + 비식별화 전체 파이프라인 실행
    - 단계별 실행 제어 가능
    - 에러 발생시 중간 결과 보존
"""

import sys
import os
import argparse
from pathlib import Path

# 프로젝트 경로 설정
sys.path.append('/home/ben/projects/ai4rm/src')

from common.logger import log_info, log_error, log_warn

def main():
    """전체 파이프라인 실행"""
    
    parser = argparse.ArgumentParser(description='병리보고서 처리 파이프라인')
    parser.add_argument('--stage', choices=['structure', 'deidentify', 'both'], 
                       default='both', help='실행할 단계 선택')
    parser.add_argument('--skip-structure', action='store_true', 
                       help='구조화 단계 건너뛰기 (기존 결과 사용)')
    
    args = parser.parse_args()
    
    try:
        log_info("병리보고서 처리 파이프라인 시작")
        
        # Stage 1: 구조화
        if args.stage in ['structure', 'both'] and not args.skip_structure:
            log_info("=== 1단계: 구조화 시작 ===")
            import subprocess
            
            result = subprocess.run([
                sys.executable, 
                '/home/ben/projects/ai4rm/scripts/structure_pathology_reports.py'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                log_error(f"구조화 단계 실패: {result.stderr}")
                return False
            
            log_info("=== 1단계: 구조화 완료 ===")
        
        # Stage 2: 비식별화
        if args.stage in ['deidentify', 'both']:
            log_info("=== 2단계: 비식별화 시작 ===")
            
            result = subprocess.run([
                sys.executable, 
                '/home/ben/projects/ai4rm/scripts/deidentify_pathology_reports.py'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                log_error(f"비식별화 단계 실패: {result.stderr}")
                return False
            
            log_info("=== 2단계: 비식별화 완료 ===")
        
        log_info("전체 파이프라인 성공적으로 완료!")
        return True
        
    except Exception as e:
        log_error(f"파이프라인 실행 오류: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
