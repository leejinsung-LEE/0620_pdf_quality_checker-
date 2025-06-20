# reports/builders/html_builder.py
"""
HTML 형식 보고서 생성 모듈
시각적이고 인터랙티브한 HTML 보고서 생성
"""

from typing import Dict, Any, List
from pathlib import Path

from config import Config
from utils import format_datetime
from .base_builder import BaseReportBuilder
from ..core.issue_analyzer import IssueAnalyzer


class HTMLReportBuilder(BaseReportBuilder):
    """HTML 보고서 빌더"""
    
    def __init__(self, config: Config):
        """HTML 빌더 초기화"""
        super().__init__(config)
        self.issue_analyzer = IssueAnalyzer()
    
    def get_file_extension(self) -> str:
        """파일 확장자 반환"""
        return '.html'
    
    def build(self, analysis_result: Dict[str, Any], prepared_data: Dict[str, Any]) -> str:
        """
        HTML 형식의 보고서 생성
        
        Args:
            analysis_result: PDF 분석 결과
            prepared_data: 준비된 추가 데이터
            
        Returns:
            str: HTML 보고서 내용
        """
        # 오류가 있는 경우
        if 'error' in analysis_result:
            return self._create_error_report(analysis_result['error'])
        
        # 전체 상태 결정
        overall_status = self._determine_overall_status(analysis_result)
        
        # HTML 생성
        html = self._create_html_structure(
            analysis_result,
            prepared_data,
            overall_status
        )
        
        return html
    
    def _determine_overall_status(self, analysis_result: Dict[str, Any]) -> Dict[str, str]:
        """전체 상태 결정"""
        issues = analysis_result.get('issues', [])
        error_count = sum(1 for i in issues if i['severity'] == 'error')
        warning_count = sum(1 for i in issues if i['severity'] == 'warning')
        info_count = sum(1 for i in issues if i['severity'] == 'info')
        
        # 프리플라이트 결과 확인
        preflight = analysis_result.get('preflight_result', {})
        preflight_status = preflight.get('overall_status', 'unknown')
        
        if preflight_status == 'fail' or error_count > 0:
            status = {
                'level': 'error',
                'text': '수정 필요',
                'color': '#ef4444',
                'icon': '❌'
            }
        elif preflight_status == 'warning' or warning_count > 0:
            status = {
                'level': 'warning',
                'text': '확인 필요',
                'color': '#f59e0b',
                'icon': '⚠️'
            }
        else:
            status = {
                'level': 'success',
                'text': '인쇄 준비 완료',
                'color': '#10b981',
                'icon': '✅'
            }
        
        # 자동 수정이 적용된 경우
        if 'auto_fix_applied' in analysis_result:
            status['text'] = '자동 수정 완료'
            status['icon'] = '🔧'
        
        status['counts'] = {
            'error': error_count,
            'warning': warning_count,
            'info': info_count
        }
        
        return status
    
    def _create_error_report(self, error_message: str) -> str:
        """오류 보고서 생성"""
        return f"""
        <html>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1 style="color: #e74c3c;">PDF 분석 실패</h1>
            <p>오류: {error_message}</p>
        </body>
        </html>
        """
    
    def _create_html_structure(
        self, 
        analysis_result: Dict[str, Any],
        prepared_data: Dict[str, Any],
        overall_status: Dict[str, Any]
    ) -> str:
        """HTML 구조 생성"""
        # 기본 정보
        basic_info = analysis_result['basic_info']
        pages = analysis_result.get('pages', [])
        first_page = pages[0] if pages else None
        
        # 썸네일 데이터
        thumbnail_data = prepared_data.get('thumbnail', {
            'data_url': '',
            'page_shown': 0,
            'total_pages': 0
        })
        
        # HTML 템플릿
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF 품질 검수 보고서 - {analysis_result['filename']}</title>
    {self._create_styles()}
</head>
<body>
    {self._create_header(analysis_result, prepared_data)}
    
    <div class="container">
        {self._create_status_banner(analysis_result, overall_status, first_page, thumbnail_data)}
        
        {self._create_statistics_cards(analysis_result, pages)}
        
        {self._create_auto_fix_banner(analysis_result) if 'auto_fix_applied' in analysis_result else ''}
        
        {self._create_comparison_section(prepared_data.get('fix_comparison')) if prepared_data.get('fix_comparison') else ''}
        
        {self._create_issues_section(analysis_result, overall_status)}
        
        {self._create_details_grid(analysis_result)}
        
        {self._create_action_buttons()}
    </div>
    
    {self._create_scripts()}
</body>
</html>
"""
        return html
    
    def _create_styles(self) -> str:
        """CSS 스타일 생성"""
        return """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
            background: #f8f9fa;
            color: #212529;
            line-height: 1.6;
        }
        
        /* 라이트 테마 변수 */
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --bg-card: #ffffff;
            --text-primary: #212529;
            --text-secondary: #6c757d;
            --accent-green: #28a745;
            --accent-yellow: #ffc107;
            --accent-red: #dc3545;
            --accent-blue: #007bff;
            --border: #dee2e6;
        }
        
        /* 헤더 */
        .header {
            background: var(--bg-primary);
            border-bottom: 2px solid var(--border);
            padding: 1.5rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header-title {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .header-title h1 {
            font-size: 1.75rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .logo-icon {
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, #007bff 0%, #6610f2 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: white;
        }
        
        .header-meta {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 0.25rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        /* 메인 컨테이너 */
        .container {
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem;
        }
        
        /* 상태 배너 */
        .status-banner {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            display: flex;
            gap: 2rem;
        }
        
        .status-content {
            flex: 1;
        }
        
        .status-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .status-icon {
            font-size: 3rem;
        }
        
        .status-text h2 {
            font-size: 2rem;
            margin-bottom: 0.25rem;
        }
        
        .status-text p {
            color: var(--text-secondary);
        }
        
        /* 빠른 요약 섹션 */
        .quick-summary {
            background: var(--bg-secondary);
            border-radius: 6px;
            padding: 1rem;
            margin-top: 1rem;
        }
        
        .quick-summary h4 {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 0.5rem;
        }
        
        .summary-item {
            display: flex;
            align-items: flex-start;
            gap: 0.5rem;
            font-size: 0.875rem;
            line-height: 1.4;
        }
        
        .summary-item-icon {
            flex-shrink: 0;
            margin-top: 0.1rem;
        }
        
        /* PDF 썸네일 */
        .pdf-thumbnail {
            width: 200px;
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
            border: 1px solid var(--border);
        }
        
        .thumbnail-image {
            width: 100%;
            border-radius: 4px;
            margin-bottom: 0.5rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .thumbnail-placeholder {
            width: 100%;
            height: 260px;
            background: var(--bg-secondary);
            border: 2px dashed var(--border);
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }
        
        .page-indicator {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        /* 자동 수정 알림 */
        .auto-fix-banner {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 6px;
            padding: 1rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .auto-fix-banner .icon {
            font-size: 1.5rem;
        }
        
        .auto-fix-banner .content {
            flex: 1;
        }
        
        .auto-fix-banner .title {
            font-weight: 600;
            color: #155724;
            margin-bottom: 0.25rem;
        }
        
        .auto-fix-banner .modifications {
            color: #155724;
            font-size: 0.875rem;
        }
        
        /* 수정 전후 비교 섹션 */
        .comparison-section {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .comparison-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border);
        }
        
        .comparison-content {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 2rem;
            align-items: center;
        }
        
        .before-after {
            text-align: center;
        }
        
        .before-after h4 {
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }
        
        .metric {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .metric.error {
            color: var(--accent-red);
        }
        
        .metric.success {
            color: var(--accent-green);
        }
        
        .arrow {
            font-size: 2rem;
            color: var(--accent-green);
        }
        
        .change-list {
            margin-top: 1.5rem;
            padding: 1rem;
            background: var(--bg-secondary);
            border-radius: 4px;
        }
        
        .change-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--border);
        }
        
        .change-item:last-child {
            border-bottom: none;
        }
        
        .change-item .icon {
            color: var(--accent-green);
        }
        
        /* 통계 카드 그리드 */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .stat-card.success { border-left: 4px solid var(--accent-green); }
        .stat-card.warning { border-left: 4px solid var(--accent-yellow); }
        .stat-card.error { border-left: 4px solid var(--accent-red); }
        .stat-card.info { border-left: 4px solid var(--accent-blue); }
        
        .stat-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .stat-icon {
            font-size: 1.5rem;
            opacity: 0.8;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.25rem;
        }
        
        .stat-change {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        /* 문제 유형별 섹션 */
        .issues-by-type-section {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .section-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border);
        }
        
        .section-icon {
            font-size: 1.5rem;
            color: var(--accent-blue);
        }
        
        .section-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        /* 문제 유형 그리드 */
        .issues-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1rem;
        }
        
        /* 문제 유형 카드 */
        .issue-type-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 1.5rem;
            transition: all 0.2s;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        
        .issue-type-card:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .issue-type-card.ok {
            background: #f0f9ff;
            border-color: #28a745;
        }
        
        .issue-type-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .issue-type-icon {
            font-size: 2rem;
        }
        
        .issue-type-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
            flex: 1;
        }
        
        .issue-type-severity {
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .severity-critical {
            background: rgba(139, 0, 0, 0.1);
            color: #8b0000;
        }
        
        .severity-error {
            background: rgba(220, 53, 69, 0.1);
            color: var(--accent-red);
        }
        
        .severity-warning {
            background: rgba(255, 193, 7, 0.1);
            color: #856404;
        }
        
        .severity-info {
            background: rgba(0, 123, 255, 0.1);
            color: var(--accent-blue);
        }
        
        .severity-ok {
            background: rgba(40, 167, 69, 0.1);
            color: var(--accent-green);
        }
        
        .issue-type-content {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .issue-info {
            margin-bottom: 0.75rem;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }
        
        .issue-pages {
            background: white;
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 0.75rem;
            margin: 0.5rem 0;
            font-size: 0.875rem;
        }
        
        .issue-suggestion {
            background: rgba(0, 123, 255, 0.05);
            border-left: 3px solid var(--accent-blue);
            padding: 0.75rem;
            margin-top: auto;
            font-size: 0.875rem;
            color: var(--text-primary);
        }
        
        .auto-fixable {
            background: rgba(40, 167, 69, 0.05);
            border-left: 3px solid var(--accent-green);
            padding: 0.5rem;
            margin-top: 0.5rem;
            font-size: 0.875rem;
            color: #155724;
        }
        
        .font-list, .color-list, .page-detail-list {
            list-style: none;
            padding: 0;
            margin: 0.5rem 0;
        }
        
        .font-list li, .color-list li, .page-detail-list li {
            padding: 0.25rem 0;
            font-family: monospace;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        /* 상세 정보 섹션 */
        .details-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        
        .detail-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .detail-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .info-grid {
            display: grid;
            gap: 0.5rem;
        }
        
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--bg-secondary);
        }
        
        .info-label {
            color: var(--text-secondary);
            font-size: 0.875rem;
        }
        
        .info-value {
            color: var(--text-primary);
            font-weight: 500;
            text-align: right;
        }
        
        /* 액션 버튼 */
        .action-buttons {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 2px solid var(--border);
        }
        
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
        }
        
        .btn-primary {
            background: var(--accent-blue);
            color: white;
        }
        
        .btn-primary:hover {
            background: #0056b3;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 123, 255, 0.2);
        }
        
        .btn-secondary {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }
        
        .btn-secondary:hover {
            background: var(--border);
        }
        
        /* 프린트 스타일 */
        @media print {
            body {
                background: white;
                color: black;
            }
            
            .header {
                display: none;
            }
            
            .btn {
                display: none;
            }
            
            .issue-type-card {
                break-inside: avoid;
            }
            
            .issues-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* 반응형 */
        @media (max-width: 768px) {
            .header-content {
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }
            
            .status-banner {
                flex-direction: column;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .issues-grid {
                grid-template-columns: 1fr;
            }
            
            .comparison-content {
                grid-template-columns: 1fr;
                text-align: center;
            }
            
            .arrow {
                transform: rotate(90deg);
            }
        }
    </style>
        """
    
    def _create_header(self, analysis_result: Dict[str, Any], prepared_data: Dict[str, Any]) -> str:
        """헤더 생성"""
        return f"""
    <header class="header">
        <div class="header-content">
            <div class="header-title">
                <div class="logo-icon">📊</div>
                <h1>PDF 품질 검수 리포트</h1>
            </div>
            <div class="header-meta">
                <span>📅 {prepared_data.get('datetime', format_datetime())}</span>
                <span>🎯 프로파일: {analysis_result.get('preflight_profile', 'N/A')}</span>
            </div>
        </div>
    </header>
        """
    
    def _create_status_banner(
        self, 
        analysis_result: Dict[str, Any],
        overall_status: Dict[str, Any],
        first_page: Any,
        thumbnail_data: Dict[str, Any]
    ) -> str:
        """상태 배너 생성"""
        # 주요 통계
        basic_info = analysis_result['basic_info']
        
        # 확장된 오류 요약 가져오기
        error_summary = self.issue_analyzer.get_error_summary(analysis_result)
        
        status_html = f"""
        <div class="status-banner">
            <div class="status-content">
                <div class="status-header">
                    <div class="status-icon">{overall_status['icon']}</div>
                    <div class="status-text">
                        <h2 style="color: {overall_status['color']}">{overall_status['text']}</h2>
                        <p>{analysis_result['filename']} • {analysis_result.get('file_size_formatted', 'N/A')}</p>
                    </div>
                </div>
                
                <div style="display: flex; gap: 3rem; margin-top: 1.5rem;">
                    <div>
                        <div style="font-size: 2rem; font-weight: 700;">{basic_info['page_count']}</div>
                        <div style="color: var(--text-secondary); font-size: 0.875rem;">총 페이지</div>
                    </div>
                    <div>
                        <div style="font-size: 2rem; font-weight: 700; color: var(--accent-red);">{overall_status['counts']['error']}</div>
                        <div style="color: var(--text-secondary); font-size: 0.875rem;">오류</div>
                    </div>
                    <div>
                        <div style="font-size: 2rem; font-weight: 700; color: var(--accent-yellow);">{overall_status['counts']['warning']}</div>
                        <div style="color: var(--text-secondary); font-size: 0.875rem;">경고</div>
                    </div>
                    <div>
                        <div style="font-size: 2rem; font-weight: 700;">{analysis_result.get('analysis_time', 'N/A')}</div>
                        <div style="color: var(--text-secondary); font-size: 0.875rem;">분석 시간</div>
                    </div>
                </div>
        """
        
        # 빠른 요약 (확장됨)
        if error_summary or first_page:
            status_html += """
                <div class="quick-summary">
                    <h4>빠른 요약</h4>
                    <div class="summary-grid">
            """
            
            # 첫 페이지 크기 정보
            if first_page:
                rotation_info = f" ({first_page['rotation']}° 회전)" if first_page.get('rotation', 0) != 0 else ""
                status_html += f"""
                        <div class="summary-item">
                            <span class="summary-item-icon">📐</span>
                            <span>페이지 크기: {first_page['size_formatted']} ({first_page['paper_size']}){rotation_info}</span>
                        </div>
                """
            
            # 모든 주요 문제점 표시
            for summary in error_summary:
                status_html += f"""
                        <div class="summary-item">
                            <span class="summary-item-icon">{summary[:2]}</span>
                            <span>{summary[2:].strip()}</span>
                        </div>
                """
            
            status_html += """
                    </div>
                </div>
            """
        
        status_html += """
            </div>
            
            <div class="pdf-thumbnail">
        """
        
        # 썸네일 추가
        if thumbnail_data['data_url']:
            status_html += f"""
                <img src="{thumbnail_data['data_url']}" alt="PDF 미리보기" class="thumbnail-image">
                <div class="page-indicator">{thumbnail_data['page_shown']} / {thumbnail_data['total_pages']} 페이지</div>
            """
        else:
            status_html += """
                <div class="thumbnail-placeholder">📄</div>
                <div class="page-indicator">미리보기 없음</div>
            """
        
        status_html += """
            </div>
        </div>
        """
        
        return status_html
    
    def _create_auto_fix_banner(self, analysis_result: Dict[str, Any]) -> str:
        """자동 수정 배너 생성"""
        modifications = ', '.join(analysis_result['auto_fix_applied'])
        
        return f"""
        <div class="auto-fix-banner">
            <div class="icon">🔧</div>
            <div class="content">
                <div class="title">자동 수정이 적용되었습니다</div>
                <div class="modifications">{modifications}</div>
            </div>
        </div>
        """
    
    def _create_comparison_section(self, comparison: Dict[str, Any]) -> str:
        """수정 전후 비교 섹션 생성"""
        html = f"""
        <div class="comparison-section">
            <div class="comparison-header">
                <div class="section-icon">📊</div>
                <h2 class="section-title">자동 수정 결과</h2>
            </div>
            
            <div class="comparison-content">
                <div class="before-after">
                    <h4>수정 전</h4>
                    <div class="metric error">{comparison['before_errors']}</div>
                    <div>오류</div>
                </div>
                
                <div class="arrow">→</div>
                
                <div class="before-after">
                    <h4>수정 후</h4>
                    <div class="metric success">{comparison['after_errors']}</div>
                    <div>오류</div>
                </div>
            </div>
            
            <div class="change-list">
                <h4 style="margin-bottom: 1rem;">적용된 수정 사항</h4>
        """
        
        for change in comparison.get('changes', []):
            html += f"""
                <div class="change-item">
                    <span class="icon">✓</span>
                    <strong>{change['type'].upper()}:</strong>
                    <span>{change['before']} → {change['after']}</span>
                </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _create_issues_section(self, analysis_result: Dict[str, Any], overall_status: Dict[str, Any]) -> str:
        """세부 내역 섹션 생성 - 모든 검수 항목 표시"""
        # 모든 검수 항목 가져오기
        all_check_items = self.issue_analyzer.get_all_check_items(analysis_result)
        
        html = """
        <div class="issues-by-type-section">
            <div class="section-header">
                <div class="section-icon">📋</div>
                <h2 class="section-title">세부 내역</h2>
            </div>
            
            <div class="issues-grid">
        """
        
        for check_item in all_check_items:
            issue_data = check_item['data']
            issue_type = issue_data.get('type', 'unknown')
            
            # 중복인쇄는 HTML에서만 숨김 (요구사항 6번)
            if issue_type in ['overprint_detected', 'white_overprint_detected', 'k_overprint_detected']:
                continue
            
            # 프리플라이트 중복 제거 (요구사항 2번)
            if issue_type.startswith('preflight_'):
                continue
            
            html += self._create_issue_card(issue_type, [issue_data], check_item['status'])
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _create_issue_card(self, issue_type: str, issues: List[Dict[str, Any]], status: str = 'issue') -> str:
        """개별 이슈 카드 생성"""
        type_info = self.issue_analyzer.get_issue_type_info(issue_type)
        main_issue = issues[0]
        severity = main_issue['severity']
        severity_info = self.issue_analyzer.get_severity_info(severity)
        
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
        
        # 카드 클래스 결정
        card_class = 'issue-type-card'
        if status == 'ok':
            card_class += ' ok'
        
        html = f"""
            <div class="{card_class}">
                <div class="issue-type-header">
                    <div class="issue-type-icon">{type_info['icon']}</div>
                    <div class="issue-type-title">{type_info['title']}</div>
                    <div class="issue-type-severity severity-{severity}">{severity_info['name']}</div>
                </div>
                
                <div class="issue-type-content">
                    <div class="issue-info">{main_issue['message']}</div>
        """
        
        # 영향받는 페이지
        if all_pages:
            page_str = self.issue_analyzer.format_page_list(all_pages, max_display=20)
            html += f'<div class="issue-pages"><strong>영향 페이지:</strong> {page_str}</div>'
        
        # 유형별 추가 정보
        if status != 'ok':
            html += self._create_issue_details(issue_type, main_issue)
        
        # 해결 방법
        if 'suggestion' in main_issue:
            html += f'<div class="issue-suggestion">💡 <strong>해결방법:</strong> {main_issue["suggestion"]}</div>'
        
        # 자동 수정 가능 표시
        if issue_type == 'font_not_embedded':
            html += '<div class="auto-fixable">🔧 자동 수정 가능: 폰트 아웃라인 변환</div>'
        elif issue_type == 'rgb_only':
            html += '<div class="auto-fixable">🔧 자동 수정 가능: RGB→CMYK 변환</div>'
        
        html += """
                </div>
            </div>
        """
        
        return html
    
    def _create_issue_details(self, issue_type: str, issue: Dict[str, Any]) -> str:
        """이슈 타입별 추가 정보 HTML"""
        html = ""
        
        if issue_type == 'font_not_embedded' and 'fonts' in issue:
            html += '<div class="issue-info"><strong>문제 폰트:</strong></div>'
            html += '<ul class="font-list">'
            for font in issue['fonts'][:5]:
                html += f'<li>• {font}</li>'
            if len(issue['fonts']) > 5:
                html += f'<li>... 그 외 {len(issue["fonts"]) - 5}개</li>'
            html += '</ul>'
        
        elif issue_type == 'low_resolution_image' and 'min_dpi' in issue:
            html += f'<div class="issue-info"><strong>최저 해상도:</strong> {issue["min_dpi"]:.0f} DPI (권장: {Config.MIN_IMAGE_DPI} DPI 이상)</div>'
        
        elif issue_type == 'page_size_inconsistent' and 'page_details' in issue:
            html += f'<div class="issue-info"><strong>기준 크기:</strong> {issue["base_size"]} ({issue["base_paper"]})</div>'
            html += '<div class="issue-info"><strong>다른 크기 페이지:</strong></div>'
            html += '<ul class="page-detail-list">'
            for detail in issue['page_details'][:3]:
                rotation_info = f" - {detail['rotation']}° 회전" if detail['rotation'] != 0 else ""
                html += f'<li>• {detail["page"]}p: {detail["size"]} ({detail["paper_size"]}){rotation_info}</li>'
            if len(issue['page_details']) > 3:
                html += f'<li>... 그 외 {len(issue["page_details"]) - 3}개</li>'
            html += '</ul>'
        
        elif issue_type == 'insufficient_bleed':
            # 요구사항 7번: 재단여백 문구 수정
            html += f'<div class="issue-info"><strong>현재:</strong> 0mm / <strong>필요:</strong> {Config.STANDARD_BLEED_SIZE}mm</div>'
            # suggestion은 별도로 처리되므로 여기서는 추가 정보만
            issue['suggestion'] = f"모든 페이지에 최소 {Config.STANDARD_BLEED_SIZE}mm의 재단 여백이 필요합니다 (기본 크기가 재단여백까지 포함된 사이즈일 수 있습니다.)"
        
        elif issue_type == 'high_ink_coverage':
            html += f'<div class="issue-info"><strong>권장:</strong> {Config.MAX_INK_COVERAGE}% 이하</div>'
        
        elif issue_type == 'spot_colors' and 'spot_colors' in issue:
            html += '<div class="issue-info"><strong>별색 목록:</strong></div>'
            html += '<ul class="color-list">'
            for color in issue['spot_colors'][:5]:
                pantone_badge = ' <span style="color: #e74c3c;">[PANTONE]</span>' if 'PANTONE' in color else ''
                html += f'<li>• {color}{pantone_badge}</li>'
            if len(issue['spot_colors']) > 5:
                html += f'<li>... 그 외 {len(issue["spot_colors"]) - 5}개</li>'
            html += '</ul>'
        
        elif issue_type == 'rgb_only':
            html += '<div class="issue-info">인쇄용 PDF는 CMYK 색상 사용을 권장합니다</div>'
        
        return html
    
    def _create_statistics_cards(self, analysis_result: Dict[str, Any], pages: List) -> str:
        """통계 카드 생성"""
        # 페이지 일관성
        size_groups = {}
        for page in pages:
            size_key = f"{page['size_formatted']} ({page['paper_size']})"
            if size_key not in size_groups:
                size_groups[size_key] = []
            size_groups[size_key].append(page['page_number'])
        
        most_common_size = max(size_groups.items(), key=lambda x: len(x[1])) if size_groups else (None, [])
        page_consistency = (len(most_common_size[1]) / len(pages) * 100) if pages and most_common_size else 100
        
        # 폰트 임베딩 - 중복 제거 (요구사항 8번)
        fonts = analysis_result.get('fonts', {})
        # 폰트명 기준으로 유니크하게 처리
        unique_fonts = {}
        for font_key, font_info in fonts.items():
            font_name = font_info.get('base_font', font_info.get('name', ''))
            if font_name not in unique_fonts:
                unique_fonts[font_name] = font_info
            else:
                # 이미 있는 폰트면 임베딩 상태만 업데이트 (하나라도 임베딩 안되어있으면 false)
                if not font_info.get('embedded', False):
                    unique_fonts[font_name]['embedded'] = False
        
        embedded_fonts = sum(1 for f in unique_fonts.values() if f.get('embedded', False))
        total_unique_fonts = len(unique_fonts)
        font_percentage = (embedded_fonts / total_unique_fonts * 100) if total_unique_fonts else 100
        
        # 이미지 품질
        images = analysis_result.get('images', {})
        total_images = images.get('total_count', 0)
        low_res_images = images.get('low_resolution_count', 0)
        image_quality = ((total_images - low_res_images) / total_images * 100) if total_images else 100
        
        html = '<div class="stats-grid">'
        
        # 페이지 일관성 카드
        html += f"""
            <div class="stat-card {'error' if page_consistency < 100 else 'success'}">
                <div class="stat-header">
                    <div class="stat-label">페이지 일관성</div>
                    <div class="stat-icon">📄</div>
                </div>
                <div class="stat-value">{page_consistency:.0f}%</div>
                <div class="stat-change">{len(size_groups)}개 크기 유형</div>
            </div>
        """
        
        # 폰트 임베딩 카드
        html += f"""
            <div class="stat-card {'error' if font_percentage < 100 else 'success'}">
                <div class="stat-header">
                    <div class="stat-label">폰트 임베딩</div>
                    <div class="stat-icon">🔤</div>
                </div>
                <div class="stat-value">{font_percentage:.0f}%</div>
                <div class="stat-change">{embedded_fonts}/{total_unique_fonts}개 임베딩됨</div>
            </div>
        """
        
        # 이미지 품질 카드
        html += f"""
            <div class="stat-card {'error' if low_res_images > 0 else 'success'}">
                <div class="stat-header">
                    <div class="stat-label">이미지 품질</div>
                    <div class="stat-icon">🖼️</div>
                </div>
                <div class="stat-value">{image_quality:.0f}%</div>
                <div class="stat-change">{total_images}개 중 {low_res_images}개 저해상도</div>
            </div>
        """
        
        # 잉크량 카드 (있는 경우)
        ink = analysis_result.get('ink_coverage', {})
        if 'summary' in ink:
            max_ink = ink['summary']['max_coverage']
            ink_status = 'error' if max_ink > 300 else 'warning' if max_ink > 280 else 'success'
            
            html += f"""
            <div class="stat-card {ink_status}">
                <div class="stat-header">
                    <div class="stat-label">최대 잉크량</div>
                    <div class="stat-icon">💧</div>
                </div>
                <div class="stat-value">{max_ink:.0f}%</div>
                <div class="stat-change">평균 {ink['summary']['avg_coverage']:.0f}%</div>
            </div>
            """
        
        html += '</div>'
        return html
    
    def _create_details_grid(self, analysis_result: Dict[str, Any]) -> str:
        """상세 정보 그리드 생성"""
        basic = analysis_result['basic_info']
        colors = analysis_result.get('colors', {})
        
        # 색상 모드
        color_modes = []
        if colors.get('has_rgb'):
            color_modes.append("RGB")
        if colors.get('has_cmyk'):
            color_modes.append("CMYK")
        if colors.get('has_gray'):
            color_modes.append("Grayscale")
        
        html = """
        <div class="details-grid">
            <!-- 기본 정보 -->
            <div class="detail-card">
                <div class="detail-header">
                    <span>📋</span>
                    <span>기본 정보</span>
                </div>
                <div class="info-grid">
        """
        
        html += f"""
                    <div class="info-row">
                        <span class="info-label">PDF 버전</span>
                        <span class="info-value">{basic['pdf_version']}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">제목</span>
                        <span class="info-value">{basic['title'] or '(없음)'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">작성자</span>
                        <span class="info-value">{basic['author'] or '(없음)'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">생성 프로그램</span>
                        <span class="info-value">{basic['creator'] or '(없음)'}</span>
                    </div>
        """
        
        html += """
                </div>
            </div>
            
            <!-- 색상 정보 -->
            <div class="detail-card">
                <div class="detail-header">
                    <span>🎨</span>
                    <span>색상 정보</span>
                </div>
                <div class="info-grid">
        """
        
        html += f"""
                    <div class="info-row">
                        <span class="info-label">색상 모드</span>
                        <span class="info-value">{', '.join(color_modes) if color_modes else '기본'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">별색 사용</span>
                        <span class="info-value">{len(colors.get('spot_color_names', []))}개</span>
                    </div>
        """
        
        if colors.get('spot_color_names'):
            for spot_name in colors['spot_color_names'][:3]:
                html += f"""
                    <div class="info-row">
                        <span class="info-label" style="padding-left: 1rem;">• {spot_name}</span>
                        <span class="info-value">{'PANTONE' if 'PANTONE' in spot_name else '커스텀'}</span>
                    </div>
                """
        
        html += """
                </div>
            </div>
        </div>
        """
        
        return html
    
    def _create_action_buttons(self) -> str:
        """액션 버튼 생성"""
        return """
        <div class="action-buttons">
            <button class="btn btn-primary" onclick="window.print()">
                🖨️ 보고서 인쇄
            </button>
            <button class="btn btn-secondary" onclick="saveReport()">
                💾 저장하기
            </button>
        </div>
        """
    
    def _create_scripts(self) -> str:
        """JavaScript 코드 생성"""
        return """
    <script>
        // 보고서 저장 기능
        function saveReport() {
            const element = document.documentElement;
            const opt = {
                margin: 10,
                filename: 'pdf_report.pdf',
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2 },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
            };
            
            // html2pdf 라이브러리가 있으면 PDF로 저장
            if (typeof html2pdf !== 'undefined') {
                html2pdf().from(element).set(opt).save();
            } else {
                // 없으면 HTML로 저장
                const blob = new Blob([document.documentElement.outerHTML], {type: 'text/html'});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'pdf_report.html';
                a.click();
            }
        }
    </script>
        """