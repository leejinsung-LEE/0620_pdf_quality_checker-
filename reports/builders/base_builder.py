# reports/builders/base_builder.py
"""
보고서 빌더 기본 클래스
모든 보고서 빌더가 상속받는 인터페이스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path

from config import Config


class BaseReportBuilder(ABC):
    """보고서 빌더 기본 클래스"""
    
    def __init__(self, config: Config):
        """
        빌더 초기화
        
        Args:
            config: 설정 객체
        """
        self.config = config
    
    @abstractmethod
    def build(self, analysis_result: Dict[str, Any], prepared_data: Dict[str, Any]) -> str:
        """
        보고서 생성 (추상 메서드)
        
        Args:
            analysis_result: PDF 분석 결과
            prepared_data: 준비된 추가 데이터
            
        Returns:
            str: 생성된 보고서 내용
        """
        pass
    
    def get_file_extension(self) -> str:
        """
        파일 확장자 반환
        
        Returns:
            str: 파일 확장자
        """
        return '.txt'
    
    def validate_data(self, analysis_result: Dict[str, Any]) -> bool:
        """
        데이터 유효성 검사
        
        Args:
            analysis_result: 분석 결과
            
        Returns:
            bool: 유효성 여부
        """
        # 필수 키 확인
        required_keys = ['filename', 'basic_info']
        for key in required_keys:
            if key not in analysis_result:
                return False
        
        return True
    
    def format_file_info(self, analysis_result: Dict[str, Any]) -> Dict[str, str]:
        """
        파일 정보 포맷팅
        
        Args:
            analysis_result: 분석 결과
            
        Returns:
            dict: 포맷된 파일 정보
        """
        return {
            'filename': analysis_result.get('filename', 'unknown.pdf'),
            'file_size': analysis_result.get('file_size_formatted', 'N/A'),
            'profile': analysis_result.get('preflight_profile', 'N/A'),
            'analysis_time': analysis_result.get('analysis_time', 'N/A')
        }
    
    def format_basic_info(self, basic_info: Dict[str, Any]) -> Dict[str, str]:
        """
        기본 정보 포맷팅
        
        Args:
            basic_info: 기본 정보
            
        Returns:
            dict: 포맷된 기본 정보
        """
        return {
            'page_count': str(basic_info.get('page_count', 0)),
            'pdf_version': basic_info.get('pdf_version', 'N/A'),
            'title': basic_info.get('title') or '(없음)',
            'author': basic_info.get('author') or '(없음)',
            'creator': basic_info.get('creator') or '(없음)',
            'producer': basic_info.get('producer') or '(없음)',
            'is_linearized': basic_info.get('is_linearized', False)
        }