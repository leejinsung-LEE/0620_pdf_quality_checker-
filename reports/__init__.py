# reports/__init__.py
"""
Reports 패키지 초기화
기존 import 경로 호환성 유지를 위한 설정
"""

# 기존 코드와의 호환성을 위해 ReportGenerator를 직접 노출
from .report_generator import ReportGenerator

# 버전 정보
__version__ = '4.0.0'
__all__ = ['ReportGenerator']

# 패키지 정보
__author__ = 'PDF Quality Checker Team'
__description__ = 'PDF 분석 결과 보고서 생성 모듈'