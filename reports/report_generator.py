# reports/report_generator.py
"""
report_generator.py - 보고서 생성 메인 래퍼
기존 인터페이스를 유지하면서 내부 모듈을 사용
Phase 4.0: 모듈화된 구조로 리팩토링
"""

from pathlib import Path
from typing import Dict, Optional, Union, Any
import json

# 프로젝트 모듈
from config import Config
from utils import format_datetime

# 내부 모듈
from .core.thumbnail_generator import ThumbnailGenerator
from .core.issue_analyzer import IssueAnalyzer
from .core.comparison_analyzer import ComparisonAnalyzer
from .builders.text_builder import TextReportBuilder
from .builders.html_builder import HTMLReportBuilder
from .builders.json_builder import JSONReportBuilder


class ReportGenerator:
    """
    분석 결과를 읽기 쉬운 보고서로 만드는 클래스
    기존 인터페이스를 유지하면서 내부적으로 모듈화된 구조 사용
    """
    
    def __init__(self):
        """ReportGenerator 초기화"""
        self.config = Config()
        
        # 내부 모듈 초기화
        self.thumbnail_generator = ThumbnailGenerator()
        self.issue_analyzer = IssueAnalyzer()
        self.comparison_analyzer = ComparisonAnalyzer()
        
        # 보고서 빌더들
        self.text_builder = TextReportBuilder(self.config)
        self.html_builder = HTMLReportBuilder(self.config)
        self.json_builder = JSONReportBuilder(self.config)
    
    def generate_reports(self, analysis_result: Dict[str, Any], format_type: str = 'both') -> Dict[str, Path]:
        """
        보고서 생성 메인 메서드
        
        Args:
            analysis_result: PDFAnalyzer의 분석 결과
            format_type: 'text', 'html', 또는 'both'
            
        Returns:
            dict: 생성된 보고서 경로들
        """
        report_paths = {}
        
        if format_type in ['text', 'both']:
            text_path = self.save_text_report(analysis_result)
            report_paths['text'] = text_path
        
        if format_type in ['html', 'both']:
            html_path = self.save_html_report(analysis_result)
            report_paths['html'] = html_path
        
        return report_paths
    
    def create_pdf_thumbnail(self, pdf_path: Union[str, Path], max_width: int = 300, page_num: int = 0) -> Dict[str, Any]:
        """
        PDF 첫 페이지의 썸네일 생성
        
        Args:
            pdf_path: PDF 파일 경로
            max_width: 썸네일 최대 너비 (픽셀)
            page_num: 썸네일로 만들 페이지 번호 (0부터 시작)
            
        Returns:
            dict: 썸네일 데이터
        """
        return self.thumbnail_generator.create_thumbnail(pdf_path, max_width, page_num)
    
    def create_page_preview(self, pdf_path: Union[str, Path], page_num: int, max_width: int = 200) -> Optional[str]:
        """
        특정 페이지의 미리보기 생성
        
        Args:
            pdf_path: PDF 파일 경로
            page_num: 페이지 번호 (0부터 시작)
            max_width: 미리보기 최대 너비 (픽셀)
            
        Returns:
            str: Base64 인코딩된 이미지 데이터 URL
        """
        return self.thumbnail_generator.create_page_preview(pdf_path, page_num, max_width)
    
    def get_error_summary(self, analysis_result: Dict[str, Any]) -> list:
        """
        주요 오류 요약 정보 생성
        
        Args:
            analysis_result: 분석 결과
            
        Returns:
            list: 주요 오류 요약 리스트
        """
        return self.issue_analyzer.get_error_summary(analysis_result)
    
    def group_issues_by_type(self, analysis_result: Dict[str, Any]) -> Dict[str, list]:
        """
        문제점들을 유형별로 그룹화
        
        Args:
            analysis_result: 분석 결과
            
        Returns:
            dict: 유형별로 그룹화된 문제점
        """
        return self.issue_analyzer.group_issues_by_type(analysis_result)
    
    def format_page_list(self, pages: list, max_display: int = 10) -> str:
        """
        페이지 리스트를 읽기 쉬운 형식으로 변환
        
        Args:
            pages: 페이지 번호 리스트
            max_display: 최대 표시 개수
            
        Returns:
            str: 포맷된 페이지 리스트
        """
        return self.issue_analyzer.format_page_list(pages, max_display)
    
    def get_issue_type_info(self, issue_type: str) -> Dict[str, str]:
        """
        이슈 타입에 대한 표시 정보 반환
        
        Args:
            issue_type: 이슈 타입
            
        Returns:
            dict: 제목, 아이콘 등의 정보
        """
        return self.issue_analyzer.get_issue_type_info(issue_type)
    
    def get_severity_info(self, severity: str) -> Dict[str, str]:
        """
        심각도별 정보 반환 (5단계 체계)
        
        Args:
            severity: 심각도
            
        Returns:
            dict: 심각도 정보
        """
        return self.issue_analyzer.get_severity_info(severity)
    
    def format_fix_comparison(self, fix_comparison: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        수정 전후 비교 데이터를 보고서용으로 포맷
        
        Args:
            fix_comparison: 수정 전후 비교 데이터
            
        Returns:
            dict: 포맷된 비교 데이터
        """
        return self.comparison_analyzer.format_fix_comparison(fix_comparison)
    
    def generate_text_report(self, analysis_result: Dict[str, Any]) -> str:
        """
        텍스트 형식의 보고서 생성
        
        Args:
            analysis_result: PDFAnalyzer의 분석 결과
            
        Returns:
            str: 보고서 내용
        """
        # 필요한 데이터 준비
        prepared_data = self._prepare_report_data(analysis_result)
        
        # 텍스트 빌더에 위임
        return self.text_builder.build(analysis_result, prepared_data)
    
    def generate_html_report(self, analysis_result: Dict[str, Any]) -> str:
        """
        HTML 형식의 보고서 생성
        
        Args:
            analysis_result: PDFAnalyzer의 분석 결과
            
        Returns:
            str: HTML 보고서 내용
        """
        # 필요한 데이터 준비
        prepared_data = self._prepare_report_data(analysis_result)
        
        # 썸네일 생성
        pdf_path = analysis_result.get('file_path', '')
        if pdf_path and Path(pdf_path).exists():
            prepared_data['thumbnail'] = self.create_pdf_thumbnail(pdf_path)
        else:
            prepared_data['thumbnail'] = {'data_url': '', 'page_shown': 0, 'total_pages': 0}
        
        # HTML 빌더에 위임
        return self.html_builder.build(analysis_result, prepared_data)
    
    def save_text_report(self, analysis_result: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """
        텍스트 보고서를 파일로 저장
        
        Args:
            analysis_result: 분석 결과
            output_path: 저장할 경로 (None이면 기본 경로 사용)
            
        Returns:
            Path: 저장된 파일 경로
        """
        # 보고서 내용 생성
        report_content = self.generate_text_report(analysis_result)
        
        # 저장 경로 결정
        if output_path is None:
            from utils import create_report_filename
            filename = analysis_result.get('filename', 'unknown.pdf')
            report_name = create_report_filename(filename, 'text')
            output_path = self.config.REPORTS_PATH / report_name
        
        # 파일로 저장
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_content, encoding='utf-8')
        
        print(f"  ✓ 텍스트 보고서 저장: {output_path.name}")
        return output_path
    
    def save_html_report(self, analysis_result: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """
        HTML 보고서를 파일로 저장
        
        Args:
            analysis_result: 분석 결과
            output_path: 저장할 경로 (None이면 기본 경로 사용)
            
        Returns:
            Path: 저장된 파일 경로
        """
        # 보고서 내용 생성
        report_content = self.generate_html_report(analysis_result)
        
        # 저장 경로 결정
        if output_path is None:
            from utils import create_report_filename
            filename = analysis_result.get('filename', 'unknown.pdf')
            report_name = create_report_filename(filename, 'html')
            output_path = self.config.REPORTS_PATH / report_name
        
        # 파일로 저장
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_content, encoding='utf-8')
        
        print(f"  ✓ HTML 보고서 저장: {output_path.name}")
        return output_path
    
    def save_json_report(self, analysis_result: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """
        JSON 형식으로 분석 결과 저장 (API 연동용)
        
        Args:
            analysis_result: 분석 결과
            output_path: 저장할 경로
            
        Returns:
            Path: 저장된 파일 경로
        """
        if output_path is None:
            filename = analysis_result.get('filename', 'unknown.pdf')
            json_name = filename.replace('.pdf', '_data.json')
            output_path = self.config.REPORTS_PATH / json_name
        
        # JSON으로 저장
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # JSON 빌더 사용
        json_content = self.json_builder.build(analysis_result)
        output_path.write_text(json_content, encoding='utf-8')
        
        return output_path
    
    def _prepare_report_data(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        보고서 생성을 위한 데이터 준비
        
        Args:
            analysis_result: 분석 결과
            
        Returns:
            dict: 준비된 데이터
        """
        # 오류 요약
        error_summary = self.get_error_summary(analysis_result)
        
        # 문제 그룹화
        issue_groups = self.group_issues_by_type(analysis_result)
        
        # 수정 전후 비교 (있는 경우)
        fix_comparison = None
        if 'fix_comparison' in analysis_result:
            fix_comparison = self.format_fix_comparison(analysis_result['fix_comparison'])
        
        return {
            'error_summary': error_summary,
            'issue_groups': issue_groups,
            'fix_comparison': fix_comparison,
            'datetime': format_datetime()
        }