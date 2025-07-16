# logger/__init__.py
"""
AI4RM 프로젝트 표준 로깅 시스템

이 패키지는 프로젝트 전체에서 일관된 로깅 인터페이스를 제공합니다.
- stdout: 사람이 읽기 쉬운 형태
- 파일: JSON 형태 (ELK Stack 호환)
"""

from .logger import get_logger

__all__ = ['get_logger']
__version__ = '1.0.0'