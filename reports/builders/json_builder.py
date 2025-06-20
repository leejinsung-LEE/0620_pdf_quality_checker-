# reports/builders/json_builder.py
"""
JSON 형식 보고서 생성 모듈
API 연동 및 데이터 교환을 위한 구조화된 JSON 생성
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from config import Config
from utils import format_datetime
from .base_builder import BaseReportBuilder
from ..core.issue_analyzer import IssueAnalyzer


class JSONReportBuilder(BaseReportBuilder):
    """JSON 보고서 빌더"""
    
    def __init__(self, config: Config):
        """JSON 빌더 초기화"""
        super().__init__(config)
        self.issue_analyzer = IssueAnalyzer()
    
    def get_file_extension(self) -> str:
        """파일 확장자 반환"""
        return '.json'
    
    def build(self, analysis_result: Dict[str, Any], prepared_data: Dict[str, Any] = None) -> str:
        """
        JSON 형식의 보고서 생성
        
        Args:
            analysis_result: PDF 분석 결과
            prepared_data: 준비된 추가 데이터 (JSON에서는 선택적)
            
        Returns:
            str: JSON 문자열
        """
        # 직접 분석 결과를 JSON으로 변환
        # 단, 일부 데이터는 정리하여 더 구조화된 형태로 제공
        
        report_data = self._structure_report_data(analysis_result)
        
        # JSON 문자열로 변환
        return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    def _structure_report_data(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        보고서 데이터를 구조화
        
        Args:
            analysis_result: 분석 결과
            
        Returns:
            dict: 구조화된 보고서 데이터
        """
        # 기본 메타데이터
        metadata = {
            'report_version': '4.0.0',
            'generated_at': datetime.now().isoformat(),
            'generator': 'PDF Quality Checker Phase 4.0',
            'analysis_profile': analysis_result.get('preflight_profile', 'unknown'),
            'analysis_time_seconds': self._parse_analysis_time(analysis_result.get('analysis_time', '0'))
        }
        
        # 파일 정보
        file_info = {
            'filename': analysis_result.get('filename', 'unknown.pdf'),
            'file_path': analysis_result.get('file_path', ''),
            'file_size': analysis_result.get('file_size', 0),
            'file_size_formatted': analysis_result.get('file_size_formatted', 'N/A'),
            'file_hash': analysis_result.get('file_hash', '')
        }
        
        # 문제점 분석
        issues_analysis = self._analyze_issues(analysis_result.get('issues', []))
        
        # 전체 상태 판단
        overall_status = self._determine_status(analysis_result, issues_analysis)
        
        # 수정 가능 여부
        fixable_issues = self._get_fixable_issues(analysis_result.get('issues', []))
        
        # 구조화된 데이터
        structured_data = {
            'metadata': metadata,
            'file_info': file_info,
            'overall_status': overall_status,
            'basic_info': analysis_result.get('basic_info', {}),
            'pages': self._structure_pages_info(analysis_result.get('pages', [])),
            'fonts': self._structure_fonts_info(analysis_result.get('fonts', {})),
            'colors': self._structure_colors_info(analysis_result.get('colors', {})),
            'images': self._structure_images_info(analysis_result.get('images', {})),
            'ink_coverage': self._structure_ink_info(analysis_result.get('ink_coverage', {})),
            'issues_summary': issues_analysis,
            'issues_detail': self._structure_issues(analysis_result.get('issues', [])),
            'preflight_result': analysis_result.get('preflight_result', {}),
            'fixable_issues': fixable_issues,
            'auto_fix_applied': analysis_result.get('auto_fix_applied', []),
            'fix_comparison': analysis_result.get('fix_comparison', {})
        }
        
        return structured_data
    
    def _parse_analysis_time(self, time_str: str) -> float:
        """분석 시간 문자열을 초 단위로 변환"""
        try:
            # "3.14초" 형식에서 숫자만 추출
            return float(time_str.replace('초', '').strip())
        except:
            return 0.0
    
    def _analyze_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """이슈 분석 및 통계"""
        stats = self.issue_analyzer.analyze_issue_statistics(issues)
        
        # 추가 분석
        return {
            'total_count': stats['total_count'],
            'by_severity': stats['by_severity'],
            'by_type': stats['by_type'],
            'affected_pages_count': len(stats['affected_pages']),
            'affected_pages': stats['affected_pages'][:50],  # 최대 50개만
            'critical_count': stats['by_severity'].get('critical', 0),
            'error_count': stats['by_severity'].get('error', 0),
            'warning_count': stats['by_severity'].get('warning', 0),
            'info_count': stats['by_severity'].get('info', 0)
        }
    
    def _determine_status(self, analysis_result: Dict[str, Any], issues_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """전체 상태 판단"""
        # 오류가 있는 경우
        if 'error' in analysis_result:
            return {
                'level': 'error',
                'code': 'ANALYSIS_FAILED',
                'message': '분석 실패',
                'details': analysis_result['error']
            }
        
        # 프리플라이트 결과 확인
        preflight = analysis_result.get('preflight_result', {})
        preflight_status = preflight.get('overall_status', 'unknown')
        
        # 이슈 수 확인
        error_count = issues_analysis['error_count']
        warning_count = issues_analysis['warning_count']
        
        if preflight_status == 'fail' or error_count > 0:
            return {
                'level': 'error',
                'code': 'NEEDS_FIX',
                'message': '수정 필요',
                'print_ready': False,
                'auto_fixable': len(self._get_fixable_issues(analysis_result.get('issues', []))) > 0
            }
        elif preflight_status == 'warning' or warning_count > 0:
            return {
                'level': 'warning',
                'code': 'NEEDS_REVIEW',
                'message': '확인 필요',
                'print_ready': True,
                'auto_fixable': False
            }
        else:
            return {
                'level': 'success',
                'code': 'PRINT_READY',
                'message': '인쇄 준비 완료',
                'print_ready': True,
                'auto_fixable': False
            }
    
    def _structure_pages_info(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """페이지 정보 구조화"""
        if not pages:
            return {
                'count': 0,
                'pages': []
            }
        
        # 페이지 크기 그룹화
        size_groups = {}
        for page in pages:
            size_key = f"{page['width_mm']:.1f}x{page['height_mm']:.1f}"
            if size_key not in size_groups:
                size_groups[size_key] = {
                    'size_mm': size_key,
                    'size_formatted': page['size_formatted'],
                    'paper_size': page['paper_size'],
                    'pages': []
                }
            size_groups[size_key]['pages'].append(page['page_number'])
        
        # 가장 일반적인 크기 찾기
        most_common_size = max(size_groups.items(), key=lambda x: len(x[1]['pages'])) if size_groups else None
        
        return {
            'count': len(pages),
            'size_consistency': len(size_groups) == 1,
            'unique_sizes': len(size_groups),
            'most_common_size': most_common_size[1] if most_common_size else None,
            'size_groups': list(size_groups.values()),
            'pages': pages[:10]  # 처음 10개 페이지만 포함
        }
    
    def _structure_fonts_info(self, fonts: Dict[str, Any]) -> Dict[str, Any]:
        """폰트 정보 구조화"""
        total_fonts = len(fonts)
        embedded_fonts = sum(1 for f in fonts.values() if f.get('embedded', False))
        
        # 미임베딩 폰트 목록
        not_embedded = [
            {
                'name': name,
                'type': info.get('type', 'unknown'),
                'pages': info.get('pages', [])[:20]  # 최대 20페이지
            }
            for name, info in fonts.items()
            if not info.get('embedded', False)
        ]
        
        return {
            'total_count': total_fonts,
            'embedded_count': embedded_fonts,
            'not_embedded_count': total_fonts - embedded_fonts,
            'embedding_rate': (embedded_fonts / total_fonts * 100) if total_fonts > 0 else 100.0,
            'not_embedded_fonts': not_embedded[:10],  # 최대 10개
            'font_types': self._count_font_types(fonts)
        }
    
    def _count_font_types(self, fonts: Dict[str, Any]) -> Dict[str, int]:
        """폰트 타입별 집계"""
        type_counts = {}
        for font_info in fonts.values():
            font_type = font_info.get('type', 'unknown')
            type_counts[font_type] = type_counts.get(font_type, 0) + 1
        return type_counts
    
    def _structure_colors_info(self, colors: Dict[str, Any]) -> Dict[str, Any]:
        """색상 정보 구조화"""
        # 색상 모드
        color_modes = []
        if colors.get('has_rgb'):
            color_modes.append('RGB')
        if colors.get('has_cmyk'):
            color_modes.append('CMYK')
        if colors.get('has_gray'):
            color_modes.append('Grayscale')
        
        return {
            'color_modes': color_modes,
            'has_rgb': colors.get('has_rgb', False),
            'has_cmyk': colors.get('has_cmyk', False),
            'has_gray': colors.get('has_gray', False),
            'has_spot_colors': len(colors.get('spot_color_names', [])) > 0,
            'spot_color_count': len(colors.get('spot_color_names', [])),
            'spot_color_names': colors.get('spot_color_names', [])[:20],  # 최대 20개
            'is_print_ready': colors.get('has_cmyk', False) and not colors.get('has_rgb', False)
        }
    
    def _structure_images_info(self, images: Dict[str, Any]) -> Dict[str, Any]:
        """이미지 정보 구조화"""
        if not images or images.get('total_count', 0) == 0:
            return {
                'total_count': 0,
                'has_images': False
            }
        
        total = images.get('total_count', 0)
        low_res = images.get('low_resolution_count', 0)
        
        return {
            'total_count': total,
            'has_images': total > 0,
            'low_resolution_count': low_res,
            'low_resolution_rate': (low_res / total * 100) if total > 0 else 0.0,
            'resolution_categories': images.get('resolution_categories', {}),
            'min_resolution': images.get('min_resolution', 0),
            'max_resolution': images.get('max_resolution', 0),
            'avg_resolution': images.get('avg_resolution', 0),
            'quality_score': ((total - low_res) / total * 100) if total > 0 else 100.0
        }
    
    def _structure_ink_info(self, ink_coverage: Dict[str, Any]) -> Dict[str, Any]:
        """잉크 정보 구조화"""
        if not ink_coverage or 'summary' not in ink_coverage:
            return {
                'analyzed': False
            }
        
        summary = ink_coverage.get('summary', {})
        
        return {
            'analyzed': True,
            'max_coverage': summary.get('max_coverage', 0),
            'avg_coverage': summary.get('avg_coverage', 0),
            'exceeds_limit': summary.get('max_coverage', 0) > Config.MAX_INK_COVERAGE,
            'pages_over_limit': ink_coverage.get('pages_over_limit', [])[:20],  # 최대 20페이지
            'coverage_distribution': {
                'under_280': summary.get('pages_under_280', 0),
                'between_280_300': summary.get('pages_280_300', 0),
                'over_300': summary.get('pages_over_300', 0)
            }
        }
    
    def _structure_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """이슈 상세 정보 구조화"""
        structured_issues = []
        
        for issue in issues[:100]:  # 최대 100개 이슈만
            structured_issue = {
                'type': issue.get('type', 'unknown'),
                'severity': issue.get('severity', 'info'),
                'message': issue.get('message', ''),
                'suggestion': issue.get('suggestion', ''),
                'auto_fixable': issue.get('type') in ['font_not_embedded', 'rgb_only'],
                'affected_pages': self._get_affected_pages(issue)[:50],  # 최대 50페이지
                'details': {}
            }
            
            # 타입별 추가 정보
            if issue.get('type') == 'font_not_embedded':
                structured_issue['details']['fonts'] = issue.get('fonts', [])[:20]
            elif issue.get('type') == 'low_resolution_image':
                structured_issue['details']['min_dpi'] = issue.get('min_dpi', 0)
            elif issue.get('type') == 'high_ink_coverage':
                structured_issue['details']['max_coverage'] = issue.get('max_coverage', 0)
            elif issue.get('type') == 'spot_colors':
                structured_issue['details']['spot_colors'] = issue.get('spot_colors', [])[:20]
            elif issue.get('type') == 'page_size_inconsistent':
                structured_issue['details']['base_size'] = issue.get('base_size', '')
                structured_issue['details']['variations'] = len(issue.get('page_details', []))
            
            structured_issues.append(structured_issue)
        
        return structured_issues
    
    def _get_affected_pages(self, issue: Dict[str, Any]) -> List[int]:
        """이슈의 영향받는 페이지 추출"""
        pages = []
        
        if 'affected_pages' in issue:
            pages = issue['affected_pages']
        elif 'pages' in issue:
            pages = issue['pages']
        elif 'page' in issue and issue['page']:
            pages = [issue['page']]
        
        return sorted(set(pages))
    
    def _get_fixable_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """자동 수정 가능한 이슈 목록"""
        fixable = []
        
        # 이슈 타입별로 확인
        issue_types = {}
        for issue in issues:
            issue_type = issue.get('type')
            if issue_type in ['font_not_embedded', 'rgb_only']:
                if issue_type not in issue_types:
                    issue_types[issue_type] = 0
                issue_types[issue_type] += 1
        
        # 수정 가능 목록 생성
        if 'font_not_embedded' in issue_types:
            fixable.append({
                'type': 'font_not_embedded',
                'description': '폰트 아웃라인 변환',
                'count': issue_types['font_not_embedded']
            })
        
        if 'rgb_only' in issue_types:
            fixable.append({
                'type': 'rgb_only',
                'description': 'RGB→CMYK 색상 변환',
                'count': issue_types['rgb_only']
            })
        
        return fixable