# reports/builders/text_builder.py
"""
텍스트 형식 보고서 생성 모듈
가독성 높은 텍스트 보고서 생성
"""

from typing import Dict, Any, List
from pathlib import Path

from config import Config
from utils import format_datetime
from .base_builder import BaseReportBuilder
from ..core.issue_analyzer import IssueAnalyzer


class TextReportBuilder(BaseReportBuilder):
    """텍스트 보고서 빌더"""
    
    def __init__(self, config: Config):
        """텍스트 빌더 초기화"""
        super().__init__(config)
        self.issue_analyzer = IssueAnalyzer()
    
    def build(self, analysis_result: Dict[str, Any], prepared_data: Dict[str, Any]) -> str:
        """
        텍스트 형식의 보고서 생성
        
        Args:
            analysis_result: PDF 분석 결과
            prepared_data: 준비된 추가 데이터
            
        Returns:
            str: 텍스트 보고서 내용
        """
        # 오류가 있는 경우
        if 'error' in analysis_result:
            return f"분석 실패: {analysis_result['error']}"
        
        report = []
        
        # 헤더
        report.extend(self._create_header(analysis_result, prepared_data))
        
        # 자동 수정 정보
        if 'auto_fix_applied' in analysis_result:
            report.extend(self._create_auto_fix_section(analysis_result))
        
        # 주요 오류 요약
        if prepared_data.get('error_summary'):
            report.extend(self._create_error_summary_section(prepared_data['error_summary']))
        
        # 프리플라이트 결과
        if analysis_result.get('preflight_result'):
            report.extend(self._create_preflight_section(analysis_result['preflight_result']))
        
        # 기본 정보
        report.extend(self._create_basic_info_section(analysis_result['basic_info']))
        
        # 수정 전후 비교
        if prepared_data.get('fix_comparison'):
            report.extend(self._create_comparison_section(prepared_data['fix_comparison']))
        
        # 문제점 상세
        if prepared_data.get('issue_groups'):
            report.extend(self._create_issues_section(prepared_data['issue_groups']))
        else:
            report.extend([
                "\n✅ 발견된 문제점이 없습니다!",
                ""
            ])
        
        # 통계 정보
        report.extend(self._create_statistics_section(analysis_result))
        
        # 푸터
        report.extend([
            "",
            "=" * 70,
            "보고서 끝"
        ])
        
        return "\n".join(report)
    
    def _create_header(self, analysis_result: Dict[str, Any], prepared_data: Dict[str, Any]) -> List[str]:
        """헤더 섹션 생성"""
        pages = analysis_result.get('pages', [])
        first_page = pages[0] if pages else None
        
        header = [
            "=" * 70,
            "PDF 품질 검수 보고서 (Phase 2.5)",
            "=" * 70,
            f"생성 일시: {prepared_data.get('datetime', format_datetime())}",
            f"파일명: {analysis_result['filename']}",
            f"파일 크기: {analysis_result.get('file_size_formatted', 'N/A')}",
            f"프리플라이트 프로파일: {analysis_result.get('preflight_profile', 'N/A')}",
            f"분석 소요시간: {analysis_result.get('analysis_time', 'N/A')}"
        ]
        
        # 첫 페이지 정보
        if first_page:
            header.append(f"첫 페이지 크기: {first_page['size_formatted']} ({first_page['paper_size']})")
            if first_page.get('rotation', 0) != 0:
                header.append(f"  - {first_page['rotation']}° 회전됨")
        
        return header
    
    def _create_auto_fix_section(self, analysis_result: Dict[str, Any]) -> List[str]:
        """자동 수정 섹션 생성"""
        section = [
            "",
            "🔧 자동 수정 적용됨",
            "-" * 50
        ]
        
        for mod in analysis_result['auto_fix_applied']:
            section.append(f"  • {mod}")
        
        return section
    
    def _create_error_summary_section(self, error_summary: List[str]) -> List[str]:
        """오류 요약 섹션 생성"""
        section = [
            "",
            "❗ 주요 오류 요약",
            "-" * 50
        ]
        
        for summary in error_summary:
            section.append(f"  • {summary}")
        
        section.append("")
        return section
    
    def _create_preflight_section(self, preflight: Dict[str, Any]) -> List[str]:
        """프리플라이트 섹션 생성"""
        section = [
            "🎯 프리플라이트 검사 결과",
            "-" * 50
        ]
        
        status = preflight.get('overall_status', 'unknown')
        if status == 'pass':
            section.append("  ✅ 상태: 통과 - 인쇄 준비 완료!")
        elif status == 'warning':
            section.append("  ⚠️  상태: 경고 - 확인 필요")
        else:
            section.append("  ❌ 상태: 실패 - 수정 필요")
        
        section.extend([
            f"  • 통과: {len(preflight.get('passed', []))}개 항목",
            f"  • 실패: {len(preflight.get('failed', []))}개 항목",
            f"  • 경고: {len(preflight.get('warnings', []))}개 항목",
            f"  • 정보: {len(preflight.get('info', []))}개 항목"
        ])
        
        if preflight.get('auto_fixable'):
            section.append(f"  • 자동 수정 가능: {len(preflight['auto_fixable'])}개 항목")
        
        section.append("")
        return section
    
    def _create_basic_info_section(self, basic_info: Dict[str, Any]) -> List[str]:
        """기본 정보 섹션 생성"""
        section = [
            "📋 기본 정보",
            "-" * 50,
            f"  • 총 페이지 수: {basic_info['page_count']}페이지",
            f"  • PDF 버전: {basic_info['pdf_version']}",
            f"  • 제목: {basic_info['title'] or '(없음)'}",
            f"  • 작성자: {basic_info['author'] or '(없음)'}",
            f"  • 생성 프로그램: {basic_info['creator'] or '(없음)'}",
            f"  • PDF 생성기: {basic_info['producer'] or '(없음)'}"
        ]
        
        if basic_info.get('is_linearized'):
            section.append("  • 웹 최적화: ✓")
        
        section.append("")
        return section
    
    def _create_comparison_section(self, comparison: Dict[str, Any]) -> List[str]:
        """수정 전후 비교 섹션 생성"""
        section = [
            "📊 자동 수정 결과",
            "=" * 70,
            f"수정 전 오류: {comparison['before_errors']}개 → 수정 후 오류: {comparison['after_errors']}개",
            f"해결된 문제: {comparison['fixed_count']}개",
            ""
        ]
        
        if comparison.get('changes'):
            section.append("변경 내역:")
            for change in comparison['changes']:
                section.append(f"  • {change['type'].upper()}: {change['before']} → {change['after']}")
        
        section.append("")
        return section
    
    def _create_issues_section(self, issue_groups: Dict[str, List]) -> List[str]:
        """문제점 상세 섹션 생성"""
        section = [
            "🚨 발견된 문제점 (유형별)",
            "=" * 70
        ]
        
        for issue_type, issues in issue_groups.items():
            if not issues:
                continue
            
            type_info = self.issue_analyzer.get_issue_type_info(issue_type)
            section.extend([
                f"\n{type_info['icon']} [{type_info['title']}]",
                "-" * 50
            ])
            
            # 첫 번째 이슈를 대표로 사용
            main_issue = issues[0]
            
            # 영향받는 모든 페이지 수집
            all_pages = []
            for issue in issues:
                if 'affected_pages' in issue:
                    all_pages.extend(issue['affected_pages'])
                elif 'pages' in issue:
                    all_pages.extend(issue['pages'])
                elif 'page' in issue and issue['page']:
                    all_pages.append(issue['page'])
            
            all_pages = sorted(set(all_pages))
            
            # 기본 메시지
            section.append(f"상태: {main_issue['message']}")
            
            # 영향받는 페이지
            if all_pages:
                page_str = self.issue_analyzer.format_page_list(all_pages)
                section.append(f"영향 페이지: {page_str}")
            
            # 유형별 추가 정보
            self._add_issue_details(section, issue_type, main_issue)
            
            # 해결 방법
            if 'suggestion' in main_issue:
                section.append(f"💡 해결방법: {main_issue['suggestion']}")
                
                # 자동 수정 가능 표시
                if issue_type == 'font_not_embedded':
                    section.append("   → 자동 수정 가능: 폰트 아웃라인 변환")
                elif issue_type == 'rgb_only':
                    section.append("   → 자동 수정 가능: RGB→CMYK 변환")
        
        section.append("")
        return section
    
    def _add_issue_details(self, section: List[str], issue_type: str, issue: Dict[str, Any]):
        """이슈 타입별 추가 정보"""
        if issue_type == 'font_not_embedded' and 'fonts' in issue:
            section.append(f"문제 폰트 ({len(issue['fonts'])}개):")
            for font in issue['fonts'][:5]:
                section.append(f"  - {font}")
            if len(issue['fonts']) > 5:
                section.append(f"  ... 그 외 {len(issue['fonts']) - 5}개")
        
        elif issue_type == 'low_resolution_image' and 'min_dpi' in issue:
            section.append(f"최저 해상도: {issue['min_dpi']:.0f} DPI")
        
        elif issue_type == 'page_size_inconsistent' and 'page_details' in issue:
            section.append(f"기준 크기: {issue['base_size']} ({issue['base_paper']})")
            section.append("다른 크기 페이지:")
            for detail in issue['page_details'][:5]:
                rotation_info = f" - {detail['rotation']}° 회전" if detail['rotation'] != 0 else ""
                section.append(f"  - {detail['page']}페이지: {detail['size']} ({detail['paper_size']}){rotation_info}")
            if len(issue['page_details']) > 5:
                section.append(f"  ... 그 외 {len(issue['page_details']) - 5}개")
        
        elif issue_type == 'insufficient_bleed':
            section.append(f"현재: 0mm / 필요: {Config.STANDARD_BLEED_SIZE}mm")
        
        elif issue_type == 'high_ink_coverage':
            section.append(f"권장: {Config.MAX_INK_COVERAGE}% 이하")
        
        elif issue_type == 'spot_colors' and 'spot_colors' in issue:
            section.append("별색 목록:")
            for color in issue['spot_colors'][:5]:
                section.append(f"  - {color}")
            if len(issue['spot_colors']) > 5:
                section.append(f"  ... 그 외 {len(issue['spot_colors']) - 5}개")
    
    def _create_statistics_section(self, analysis_result: Dict[str, Any]) -> List[str]:
        """통계 섹션 생성"""
        section = [
            "📊 전체 통계",
            "-" * 50
        ]
        
        # 페이지 크기 통계
        pages = analysis_result.get('pages', [])
        size_groups = {}
        for page in pages:
            size_key = f"{page['size_formatted']} ({page['paper_size']})"
            if page.get('rotation', 0) != 0:
                size_key += f" - {page['rotation']}° 회전"
            if size_key not in size_groups:
                size_groups[size_key] = []
            size_groups[size_key].append(page['page_number'])
        
        section.append(f"  • 페이지 크기: {len(size_groups)}종")
        for size_key, page_nums in size_groups.items():
            section.append(f"    - {size_key}: {len(page_nums)}페이지")
        
        # 폰트 통계
        fonts = analysis_result.get('fonts', {})
        not_embedded = sum(1 for f in fonts.values() if not f.get('embedded', False))
        section.append(f"\n  • 폰트: 총 {len(fonts)}개 (미임베딩 {not_embedded}개)")
        
        # 이미지 통계
        images = analysis_result.get('images', {})
        if images.get('total_count', 0) > 0:
            section.extend([
                f"  • 이미지: 총 {images['total_count']}개"
            ])
            
            # 해상도 분포
            res_cat = images.get('resolution_categories', {})
            if res_cat:
                section.extend([
                    f"    - 최적(300 DPI↑): {res_cat.get('optimal', 0)}개",
                    f"    - 양호(150-300): {res_cat.get('acceptable', 0)}개",
                    f"    - 주의(72-150): {res_cat.get('warning', 0)}개",
                    f"    - 위험(72 미만): {res_cat.get('critical', 0)}개"
                ])
        
        # 잉크량 통계
        ink = analysis_result.get('ink_coverage', {})
        if 'summary' in ink:
            section.append(f"  • 잉크량: 평균 {ink['summary']['avg_coverage']:.1f}%, 최대 {ink['summary']['max_coverage']:.1f}%")
        
        return section