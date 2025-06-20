# reports/core/issue_analyzer.py
"""
PDF 문제점 분석 및 분류 모듈
이슈 그룹화, 심각도 분석, 페이지 정보 처리
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict

from config import Config


class IssueAnalyzer:
    """PDF 문제점 분석 클래스"""
    
    # 이슈 타입 우선순위 (표시 순서)
    TYPE_PRIORITY = {
        'font_not_embedded': 1,
        'high_ink_coverage': 2,
        'low_resolution_image': 3,
        'insufficient_bleed': 4,
        'page_size_inconsistent': 5,
        'spot_colors': 6,
        'transparency_detected': 7,
        'overprint_detected': 8,
        'small_text_detected': 9,
        'high_compression_detected': 10,
        'rgb_only': 11,
        'medium_resolution_image': 12,
        'preflight_failed': 13,
        'preflight_warning': 14,
        'preflight_info': 15
    }
    
    # 이슈 타입별 정보
    TYPE_INFO = {
        'font_not_embedded': {
            'title': '폰트 미임베딩',
            'icon': '🔤',
            'color': '#e74c3c'
        },
        'high_ink_coverage': {
            'title': '잉크량 초과',
            'icon': '💧',
            'color': '#e74c3c'
        },
        'low_resolution_image': {
            'title': '저해상도 이미지',
            'icon': '🖼️',
            'color': '#e74c3c'
        },
        'medium_resolution_image': {
            'title': '중간해상도 이미지',
            'icon': '🖼️',
            'color': '#3498db'
        },
        'insufficient_bleed': {
            'title': '재단 여백 부족',
            'icon': '📐',
            'color': '#3498db'
        },
        'page_size_inconsistent': {
            'title': '페이지 크기 불일치',
            'icon': '📄',
            'color': '#f39c12'
        },
        'spot_colors': {
            'title': '별색 사용',
            'icon': '🎨',
            'color': '#3498db'
        },
        'transparency_detected': {
            'title': '투명도 사용',
            'icon': '👻',
            'color': '#f39c12'
        },
        'overprint_detected': {
            'title': '중복인쇄 설정',
            'icon': '🔄',
            'color': '#3498db'
        },
        'small_text_detected': {
            'title': '작은 텍스트',
            'icon': '🔍',
            'color': '#f39c12'
        },
        'high_compression_detected': {
            'title': '과도한 이미지 압축',
            'icon': '🗜️',
            'color': '#f39c12'
        },
        'rgb_only': {
            'title': 'RGB 색상만 사용',
            'icon': '🌈',
            'color': '#f39c12'
        },
        'preflight_failed': {
            'title': '프리플라이트 실패',
            'icon': '❌',
            'color': '#e74c3c'
        },
        'preflight_warning': {
            'title': '프리플라이트 경고',
            'icon': '⚠️',
            'color': '#f39c12'
        },
        'preflight_info': {
            'title': '프리플라이트 정보',
            'icon': 'ℹ️',
            'color': '#3498db'
        }
    }
    
    # 심각도별 정보
    SEVERITY_INFO = {
        'critical': {
            'name': 'CRITICAL',
            'color': '#8b0000',
            'icon': '🚫'
        },
        'error': {
            'name': 'ERROR',
            'color': '#dc3545',
            'icon': '❌'
        },
        'warning': {
            'name': 'WARNING',
            'color': '#ffc107',
            'icon': '⚠️'
        },
        'info': {
            'name': 'INFO',
            'color': '#007bff',
            'icon': 'ℹ️'
        },
        'ok': {
            'name': 'OK',
            'color': '#28a745',
            'icon': '✅'
        }
    }
    
    def __init__(self):
        """이슈 분석기 초기화"""
        pass
    
    def get_error_summary(self, analysis_result: Dict[str, Any]) -> List[str]:
        """
        주요 오류 요약 정보 생성 - 모든 레벨의 문제점 포함
        
        Args:
            analysis_result: 분석 결과
            
        Returns:
            list: 주요 오류 요약 리스트
        """
        issues = analysis_result.get('issues', [])
        summary = []
        
        # 심각도별로 그룹화
        severity_groups = {
            'error': [],
            'warning': [],
            'info': []
        }
        
        for issue in issues:
            severity = issue.get('severity', 'info')
            if severity in severity_groups:
                severity_groups[severity].append(issue)
        
        # 오류 먼저 추가 (최대 2개)
        for issue in severity_groups['error'][:2]:
            type_info = self.get_issue_type_info(issue.get('type', 'unknown'))
            summary.append(f"❌ {type_info['title']}: {issue.get('message', '')}")
        
        # 경고 추가 (최대 2개)
        for issue in severity_groups['warning'][:2]:
            type_info = self.get_issue_type_info(issue.get('type', 'unknown'))
            summary.append(f"⚠️ {type_info['title']}: {issue.get('message', '')}")
        
        # 정보 추가 (공간이 남으면 1개)
        if len(summary) < 4 and severity_groups['info']:
            issue = severity_groups['info'][0]
            type_info = self.get_issue_type_info(issue.get('type', 'unknown'))
            summary.append(f"ℹ️ {type_info['title']}: {issue.get('message', '')}")
        
        # 페이지 크기 불일치 정보 추가 (특별 처리)
        page_size_issues = [i for i in issues if i.get('type') == 'page_size_inconsistent']
        if page_size_issues:
            issue = page_size_issues[0]
            if 'page_details' in issue:
                # 페이지별 크기 집계
                size_count = {}
                for detail in issue['page_details']:
                    size_key = f"{detail['paper_size']} ({detail['size']})"
                    if size_key not in size_count:
                        size_count[size_key] = 0
                    size_count[size_key] += 1
                
                # 요약 문자열 생성
                size_summary = ", ".join([f"{size} {count}p" for size, count in size_count.items()])
                summary.append(f"📄 페이지 크기: {issue['base_paper']} 기준, 다른 크기 - {size_summary}")
        
        return summary[:5]  # 최대 5개까지만 반환
    
    def get_all_check_items(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        모든 검수 항목 반환 (문제가 없는 항목도 포함)
        
        Args:
            analysis_result: 분석 결과
            
        Returns:
            list: 모든 검수 항목 리스트
        """
        check_items = []
        issues = analysis_result.get('issues', [])
        
        # 이미 발견된 이슈 타입들
        found_issue_types = set()
        for issue in issues:
            issue_type = issue.get('type', 'unknown')
            found_issue_types.add(issue_type)
            check_items.append({
                'type': issue_type,
                'status': 'issue',
                'severity': issue.get('severity', 'info'),
                'data': issue
            })
        
        # 검사했지만 문제가 없는 항목들 추가
        all_check_types = [
            ('font_not_embedded', '폰트 임베딩'),
            ('high_ink_coverage', '잉크량'),
            ('low_resolution_image', '이미지 해상도'),
            ('insufficient_bleed', '재단 여백'),
            ('page_size_inconsistent', '페이지 크기 일관성'),
            ('spot_colors', '별색 사용'),
            ('transparency_detected', '투명도'),
            ('overprint_detected', '중복인쇄'),
            ('small_text_detected', '텍스트 크기'),
            ('rgb_only', '색상 모드')
        ]
        
        for check_type, check_name in all_check_types:
            if check_type not in found_issue_types:
                # 해당 검사에서 문제가 없었던 경우
                check_items.append({
                    'type': check_type,
                    'status': 'ok',
                    'severity': 'ok',
                    'data': {
                        'type': check_type,
                        'severity': 'ok',
                        'message': f'{check_name} 검사 통과',
                        'suggestion': '정상입니다'
                    }
                })
        
        # 심각도 순으로 정렬 (error > warning > info > ok)
        severity_order = {'error': 0, 'warning': 1, 'info': 2, 'ok': 3}
        check_items.sort(key=lambda x: severity_order.get(x['severity'], 99))
        
        return check_items
    
    def group_issues_by_type(self, analysis_result: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        문제점들을 유형별로 그룹화
        
        Args:
            analysis_result: 분석 결과
            
        Returns:
            dict: 유형별로 그룹화된 문제점
        """
        type_groups = defaultdict(list)
        
        # 모든 이슈 수집
        issues = analysis_result.get('issues', [])
        
        # 유형별로 그룹화
        for issue in issues:
            issue_type = issue.get('type', 'unknown')
            type_groups[issue_type].append(issue)
        
        # 우선순위에 따라 정렬
        sorted_groups = dict(sorted(
            type_groups.items(),
            key=lambda x: self.TYPE_PRIORITY.get(x[0], 999)
        ))
        
        return sorted_groups
    
    def format_page_list(self, pages: List[int], max_display: int = 10) -> str:
        """
        페이지 리스트를 읽기 쉬운 형식으로 변환
        
        Args:
            pages: 페이지 번호 리스트
            max_display: 최대 표시 개수
            
        Returns:
            str: 포맷된 페이지 리스트
        """
        if not pages:
            return ""
        
        pages = sorted(set(pages))
        
        if len(pages) == 1:
            return f"{pages[0]}페이지"
        elif len(pages) <= max_display:
            return f"{', '.join(map(str, pages))} 페이지"
        else:
            # 연속된 페이지를 범위로 표시
            ranges = []
            start = pages[0]
            end = pages[0]
            
            for i in range(1, len(pages)):
                if pages[i] == end + 1:
                    end = pages[i]
                else:
                    if start == end:
                        ranges.append(str(start))
                    else:
                        ranges.append(f"{start}-{end}")
                    start = pages[i]
                    end = pages[i]
            
            # 마지막 범위 추가
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            
            # 범위가 너무 많으면 요약
            if len(ranges) > 5:
                return f"{ranges[0]}, {ranges[1]}, ... {ranges[-1]} ({len(pages)}개 페이지)"
            else:
                return f"{', '.join(ranges)} 페이지"
    
    def get_issue_type_info(self, issue_type: str) -> Dict[str, str]:
        """
        이슈 타입에 대한 표시 정보 반환
        
        Args:
            issue_type: 이슈 타입
            
        Returns:
            dict: 제목, 아이콘 등의 정보
        """
        return self.TYPE_INFO.get(issue_type, {
            'title': '기타 문제',
            'icon': 'ℹ️',
            'color': '#95a5a6'
        })
    
    def get_severity_info(self, severity: str) -> Dict[str, str]:
        """
        심각도별 정보 반환
        
        Args:
            severity: 심각도
            
        Returns:
            dict: 심각도 정보
        """
        return self.SEVERITY_INFO.get(severity, self.SEVERITY_INFO['info'])
    
    def analyze_issue_statistics(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        이슈 통계 분석
        
        Args:
            issues: 이슈 목록
            
        Returns:
            dict: 통계 정보
        """
        stats = {
            'total_count': len(issues),
            'by_severity': defaultdict(int),
            'by_type': defaultdict(int),
            'affected_pages': set()
        }
        
        for issue in issues:
            # 심각도별 집계
            severity = issue.get('severity', 'info')
            stats['by_severity'][severity] += 1
            
            # 타입별 집계
            issue_type = issue.get('type', 'unknown')
            stats['by_type'][issue_type] += 1
            
            # 영향받는 페이지 수집
            if 'affected_pages' in issue:
                stats['affected_pages'].update(issue['affected_pages'])
            elif 'pages' in issue:
                stats['affected_pages'].update(issue['pages'])
            elif 'page' in issue and issue['page']:
                stats['affected_pages'].add(issue['page'])
        
        # set을 list로 변환
        stats['affected_pages'] = sorted(list(stats['affected_pages']))
        
        # defaultdict를 일반 dict로 변환
        stats['by_severity'] = dict(stats['by_severity'])
        stats['by_type'] = dict(stats['by_type'])
        
        return stats
    
    def get_auto_fixable_issues(self, issues: List[Dict[str, Any]]) -> List[str]:
        """
        자동 수정 가능한 이슈 타입 목록
        
        Args:
            issues: 이슈 목록
            
        Returns:
            list: 자동 수정 가능한 이슈 타입들
        """
        auto_fixable_types = ['font_not_embedded', 'rgb_only']
        
        fixable = []
        for issue in issues:
            issue_type = issue.get('type')
            if issue_type in auto_fixable_types and issue_type not in fixable:
                fixable.append(issue_type)
        
        return fixable