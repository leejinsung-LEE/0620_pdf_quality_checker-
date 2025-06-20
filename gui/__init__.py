# gui/__init__.py
# GUI 패키지 초기화 파일

"""
PDF 품질 검수 시스템 GUI 패키지
이 패키지는 모든 GUI 관련 모듈을 포함합니다.
"""

# 버전 정보
__version__ = "4.0.0"
__author__ = "PDF Quality Checker Team"

# 주요 클래스를 패키지 레벨에서 임포트 가능하게 함
from .main_window import EnhancedPDFCheckerGUI

# 패키지 레벨에서 사용 가능한 것들
__all__ = ['EnhancedPDFCheckerGUI']