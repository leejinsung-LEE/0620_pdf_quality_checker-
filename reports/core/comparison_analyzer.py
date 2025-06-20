# reports/core/comparison_analyzer.py
"""
PDF 수정 전후 비교 분석 모듈
자동 수정 결과 비교 및 변경사항 분석
"""

from typing import Dict, List, Any, Optional


class ComparisonAnalyzer:
    """PDF 수정 전후 비교 분석 클래스"""
    
    def __init__(self):
        """비교 분석기 초기화"""
        pass
    
    def format_fix_comparison(self, fix_comparison: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        수정 전후 비교 데이터를 보고서용으로 포맷
        
        Args:
            fix_comparison: 수정 전후 비교 데이터
            
        Returns:
            dict: 포맷된 비교 데이터
        """
        if not fix_comparison:
            return None
        
        before = fix_comparison.get('before', {})
        after = fix_comparison.get('after', {})
        modifications = fix_comparison.get('modifications', [])
        
        # 주요 변경사항 추출
        changes = []
        
        # 폰트 변경 확인
        before_fonts = before.get('fonts', {})
        after_fonts = after.get('fonts', {})
        font_change = self._analyze_font_changes(before_fonts, after_fonts)
        if font_change:
            changes.append(font_change)
        
        # 색상 모드 변경 확인
        before_colors = before.get('colors', {})
        after_colors = after.get('colors', {})
        color_change = self._analyze_color_changes(before_colors, after_colors)
        if color_change:
            changes.append(color_change)
        
        # 이슈 개수 비교
        before_issues = before.get('issues', [])
        after_issues = after.get('issues', [])
        issue_stats = self._analyze_issue_changes(before_issues, after_issues)
        
        return {
            'modifications': modifications,
            'changes': changes,
            'before_errors': issue_stats['before_errors'],
            'after_errors': issue_stats['after_errors'],
            'fixed_count': issue_stats['fixed_count'],
            'issue_details': issue_stats['details']
        }
    
    def _analyze_font_changes(self, before_fonts: Dict, after_fonts: Dict) -> Optional[Dict]:
        """
        폰트 변경사항 분석
        
        Args:
            before_fonts: 수정 전 폰트 정보
            after_fonts: 수정 후 폰트 정보
            
        Returns:
            dict: 변경사항 정보
        """
        before_not_embedded = sum(1 for f in before_fonts.values() if not f.get('embedded', False))
        after_not_embedded = sum(1 for f in after_fonts.values() if not f.get('embedded', False))
        
        if before_not_embedded > 0 and after_not_embedded == 0:
            return {
                'type': 'font',
                'before': f"{before_not_embedded}개 폰트 미임베딩",
                'after': "모든 폰트 임베딩됨",
                'status': 'fixed',
                'improvement': True
            }
        elif before_not_embedded != after_not_embedded:
            return {
                'type': 'font',
                'before': f"{before_not_embedded}개 폰트 미임베딩",
                'after': f"{after_not_embedded}개 폰트 미임베딩",
                'status': 'partial',
                'improvement': after_not_embedded < before_not_embedded
            }
        
        return None
    
    def _analyze_color_changes(self, before_colors: Dict, after_colors: Dict) -> Optional[Dict]:
        """
        색상 변경사항 분석
        
        Args:
            before_colors: 수정 전 색상 정보
            after_colors: 수정 후 색상 정보
            
        Returns:
            dict: 변경사항 정보
        """
        if before_colors.get('has_rgb') and not after_colors.get('has_rgb'):
            return {
                'type': 'color',
                'before': "RGB 색상 사용",
                'after': "CMYK 색상으로 변환됨",
                'status': 'fixed',
                'improvement': True
            }
        
        # 별색 변경 확인
        before_spot = len(before_colors.get('spot_color_names', []))
        after_spot = len(after_colors.get('spot_color_names', []))
        
        if before_spot != after_spot:
            return {
                'type': 'color',
                'before': f"별색 {before_spot}개 사용",
                'after': f"별색 {after_spot}개 사용",
                'status': 'changed',
                'improvement': after_spot < before_spot
            }
        
        return None
    
    def _analyze_issue_changes(self, before_issues: List[Dict], after_issues: List[Dict]) -> Dict:
        """
        이슈 변경사항 분석
        
        Args:
            before_issues: 수정 전 이슈 목록
            after_issues: 수정 후 이슈 목록
            
        Returns:
            dict: 이슈 통계
        """
        # 심각도별 집계
        before_stats = self._count_issues_by_severity(before_issues)
        after_stats = self._count_issues_by_severity(after_issues)
        
        # 타입별 집계
        before_types = self._count_issues_by_type(before_issues)
        after_types = self._count_issues_by_type(after_issues)
        
        # 해결된 이슈 찾기
        fixed_issues = []
        for issue_type, count in before_types.items():
            after_count = after_types.get(issue_type, 0)
            if after_count < count:
                fixed_issues.append({
                    'type': issue_type,
                    'before_count': count,
                    'after_count': after_count,
                    'fixed_count': count - after_count
                })
        
        return {
            'before_errors': before_stats.get('error', 0),
            'after_errors': after_stats.get('error', 0),
            'fixed_count': before_stats.get('error', 0) - after_stats.get('error', 0),
            'details': {
                'severity_changes': {
                    'before': before_stats,
                    'after': after_stats
                },
                'fixed_issues': fixed_issues
            }
        }
    
    def _count_issues_by_severity(self, issues: List[Dict]) -> Dict[str, int]:
        """이슈를 심각도별로 집계"""
        counts = {}
        for issue in issues:
            severity = issue.get('severity', 'info')
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def _count_issues_by_type(self, issues: List[Dict]) -> Dict[str, int]:
        """이슈를 타입별로 집계"""
        counts = {}
        for issue in issues:
            issue_type = issue.get('type', 'unknown')
            counts[issue_type] = counts.get(issue_type, 0) + 1
        return counts
    
    def generate_comparison_summary(self, fix_comparison: Dict[str, Any]) -> str:
        """
        비교 요약 텍스트 생성
        
        Args:
            fix_comparison: 포맷된 비교 데이터
            
        Returns:
            str: 요약 텍스트
        """
        if not fix_comparison:
            return "비교 데이터 없음"
        
        summary_parts = []
        
        # 수정 개수
        fixed_count = fix_comparison.get('fixed_count', 0)
        if fixed_count > 0:
            summary_parts.append(f"{fixed_count}개 오류 해결")
        
        # 주요 변경사항
        for change in fix_comparison.get('changes', []):
            if change.get('improvement'):
                summary_parts.append(change['after'])
        
        return " • ".join(summary_parts) if summary_parts else "변경사항 없음"