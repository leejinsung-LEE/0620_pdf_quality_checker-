# gui/tabs/statistics_tab.py
"""
통계 탭
처리 통계와 차트를 표시하는 탭입니다.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.scrolledtext as scrolledtext
import customtkinter as ctk
from datetime import datetime, timedelta
import webbrowser

# 차트 라이브러리 (선택적)
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class StatisticsTab:
    """통계 탭 클래스"""
    
    def __init__(self, main_window, parent):
        """
        통계 탭 초기화
        
        Args:
            main_window: 메인 윈도우 인스턴스
            parent: 부모 위젯 (Notebook)
        """
        self.main_window = main_window
        self.parent = parent
        
        # matplotlib 한글 폰트 설정
        if HAS_MATPLOTLIB:
            plt.rcParams['font.family'] = 'Malgun Gothic'
            plt.rcParams['axes.unicode_minus'] = False
        
        # 탭 생성
        self._create_tab()
    
    def _create_tab(self):
        """탭 생성"""
        self.tab = ctk.CTkFrame(self.parent, fg_color=self.main_window.colors['bg_primary'])
        self.parent.add(self.tab, text="📊 통계 대시보드")
        
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(self.tab, highlightthickness=0, bg=self.main_window.colors['bg_primary'])
        scrollbar = ttk.Scrollbar(self.tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas, fg_color=self.main_window.colors['bg_primary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 기간 선택
        self._create_period_selector(scrollable_frame)
        
        # 기본 통계 카드들
        self._create_stat_cards(scrollable_frame)
        
        # 차트 영역
        if HAS_MATPLOTLIB:
            self._create_charts(scrollable_frame)
        else:
            self._create_text_statistics(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_period_selector(self, parent):
        """기간 선택기 생성"""
        period_frame = ctk.CTkFrame(parent, fg_color="transparent")
        period_frame.pack(fill='x', padx=20, pady=20)
        
        ctk.CTkLabel(
            period_frame, 
            text="기간 선택:", 
            font=self.main_window.fonts['subheading']
        ).pack(side='left', padx=(0, 20))
        
        self.stats_period = tk.StringVar(value='today')
        periods = [
            ('오늘', 'today'),
            ('이번 주', 'week'),
            ('이번 달', 'month'),
            ('전체', 'all')
        ]
        
        for text, value in periods:
            ctk.CTkRadioButton(
                period_frame, 
                text=text, 
                variable=self.stats_period, 
                value=value,
                command=self.update_statistics,
                radiobutton_width=20,
                radiobutton_height=20
            ).pack(side='left', padx=10)
    
    def _create_stat_cards(self, parent):
        """통계 카드들 생성"""
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack(fill='x', padx=20, pady=20)
        
        self.stat_cards = {}
        card_info = [
            ('total_files', '📄', '총 파일', '0', self.main_window.colors['accent']),
            ('total_pages', '📃', '총 페이지', '0', '#00BCD4'),
            ('total_errors', '❌', '총 오류', '0', self.main_window.colors['error']),
            ('auto_fixed', '🔧', '자동 수정', '0', self.main_window.colors['success'])
        ]
        
        for key, icon, title, default, color in card_info:
            card = self._create_stat_card(cards_frame, icon, title, default, color)
            card.pack(side='left', fill='both', expand=True, padx=10)
            self.stat_cards[key] = card
    
    def _create_stat_card(self, parent, icon, title, value, color):
        """통계 카드 위젯 생성"""
        card = ctk.CTkFrame(
            parent, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10
        )
        card.configure(width=200, height=120)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 아이콘
        icon_label = ctk.CTkLabel(inner, text=icon, font=('Arial', 24))
        icon_label.pack()
        
        # 타이틀
        title_label = ctk.CTkLabel(
            inner, 
            text=title, 
            font=self.main_window.fonts['small'],
            text_color=self.main_window.colors['text_secondary']
        )
        title_label.pack(pady=(5, 0))
        
        # 값
        value_label = ctk.CTkLabel(
            inner, 
            text=value, 
            font=('맑은 고딕', 20, 'bold'),
            text_color=color
        )
        value_label.pack()
        
        # 레이블 참조 저장
        card.value_label = value_label
        
        return card
    
    def _create_charts(self, parent):
        """차트 생성 (matplotlib)"""
        charts_frame = ctk.CTkFrame(
            parent, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10
        )
        charts_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        charts_inner = ctk.CTkFrame(charts_frame, fg_color="transparent")
        charts_inner.pack(fill='both', expand=True, padx=15, pady=15)
        
        chart_title = ctk.CTkLabel(
            charts_inner, 
            text="📈 분석 차트", 
            font=self.main_window.fonts['heading']
        )
        chart_title.pack(anchor='w', pady=(0, 10))
        
        # 차트 캔버스들을 담을 프레임
        self.chart_frames = {}
        
        # 1. 일별 처리량 차트
        daily_frame = ctk.CTkFrame(charts_inner, fg_color="transparent")
        daily_frame.pack(fill='x', pady=10)
        
        fig1 = Figure(figsize=(10, 4), dpi=80, facecolor=self.main_window.colors['bg_card'])
        self.daily_chart = fig1.add_subplot(111)
        self.daily_chart.set_facecolor(self.main_window.colors['bg_card'])
        self.daily_chart.set_title('일별 처리량', fontsize=12, fontweight='bold', color='white')
        
        canvas1 = FigureCanvasTkAgg(fig1, master=daily_frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill='x')
        
        self.chart_frames['daily'] = (fig1, canvas1)
        
        # 2. 문제 유형별 분포 차트
        issue_frame = ctk.CTkFrame(charts_inner, fg_color="transparent")
        issue_frame.pack(fill='x', pady=10)
        
        fig2 = Figure(figsize=(10, 4), dpi=80, facecolor=self.main_window.colors['bg_card'])
        self.issue_chart = fig2.add_subplot(111)
        self.issue_chart.set_facecolor(self.main_window.colors['bg_card'])
        self.issue_chart.set_title('문제 유형별 분포', fontsize=12, fontweight='bold', color='white')
        
        canvas2 = FigureCanvasTkAgg(fig2, master=issue_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill='x')
        
        self.chart_frames['issues'] = (fig2, canvas2)
    
    def _create_text_statistics(self, parent):
        """텍스트 기반 통계 (matplotlib 없을 때)"""
        text_frame = ctk.CTkFrame(
            parent, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10
        )
        text_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        text_inner = ctk.CTkFrame(text_frame, fg_color="transparent")
        text_inner.pack(fill='both', expand=True, padx=15, pady=15)
        
        text_title = ctk.CTkLabel(
            text_inner, 
            text="📊 상세 통계", 
            font=self.main_window.fonts['heading']
        )
        text_title.pack(anchor='w', pady=(0, 10))
        
        self.stats_text = scrolledtext.ScrolledText(
            text_inner,
            wrap=tk.WORD,
            height=15,
            font=self.main_window.fonts['mono'],
            bg=self.main_window.colors['bg_secondary'],
            fg=self.main_window.colors['text_primary'],
            insertbackground=self.main_window.colors['text_primary'],
            selectbackground=self.main_window.colors['accent'],
            borderwidth=0,
            highlightthickness=0
        )
        self.stats_text.pack(fill='both', expand=True)
    
    def update_statistics(self):
        """통계 업데이트"""
        period = self.stats_period.get()
        
        # 기간 계산
        now = datetime.now()
        if period == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date = now - timedelta(days=7)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        else:  # all
            start_date = None
        
        # 통계 조회
        if start_date:
            stats = self.main_window.data_manager.get_statistics(date_range=(start_date, now))
        else:
            stats = self.main_window.data_manager.get_statistics()
        
        # 카드 업데이트
        self.stat_cards['total_files'].value_label.configure(
            text=str(stats['basic']['total_files'])
        )
        self.stat_cards['total_pages'].value_label.configure(
            text=str(stats['basic']['total_pages'])
        )
        self.stat_cards['total_errors'].value_label.configure(
            text=str(stats['basic']['total_errors'])
        )
        self.stat_cards['auto_fixed'].value_label.configure(
            text=str(stats['basic']['auto_fixed_count'])
        )
        
        # 차트 업데이트
        if HAS_MATPLOTLIB:
            self._update_charts(stats)
        else:
            self._update_text_stats(stats)
    
    def _update_charts(self, stats):
        """차트 업데이트"""
        # 일별 처리량 차트
        daily_data = stats['daily']
        if daily_data:
            dates = [d['date'] for d in daily_data]
            files = [d['files'] for d in daily_data]
            
            self.daily_chart.clear()
            bars = self.daily_chart.bar(dates, files, color=self.main_window.colors['accent'])
            self.daily_chart.set_xlabel('날짜', fontsize=10, color='white')
            self.daily_chart.set_ylabel('파일 수', fontsize=10, color='white')
            self.daily_chart.set_title('일별 처리량', fontsize=12, fontweight='bold', color='white')
            self.daily_chart.grid(True, alpha=0.3)
            self.daily_chart.tick_params(colors='white')
            
            # 값 표시
            for bar, value in zip(bars, files):
                height = bar.get_height()
                self.daily_chart.text(
                    bar.get_x() + bar.get_width()/2., 
                    height + 0.5,
                    f'{value}', 
                    ha='center', 
                    va='bottom', 
                    fontsize=9, 
                    color='white'
                )
            
            # X축 레이블 회전
            for tick in self.daily_chart.get_xticklabels():
                tick.set_rotation(45)
                tick.set_ha('right')
            
            self.daily_chart.figure.tight_layout()
            self.chart_frames['daily'][1].draw()
        
        # 문제 유형별 차트
        issue_data = stats['common_issues'][:5]
        if issue_data:
            types = [i['type'] for i in issue_data]
            counts = [i['count'] for i in issue_data]
            
            # 한글 레이블로 변환
            type_labels = {
                'font_not_embedded': '폰트 미임베딩',
                'low_resolution_image': '저해상도 이미지',
                'rgb_only': 'RGB 색상',
                'high_ink_coverage': '높은 잉크량',
                'page_size_inconsistent': '페이지 크기 불일치'
            }
            
            types_kr = [type_labels.get(t, t) for t in types]
            
            self.issue_chart.clear()
            bars = self.issue_chart.barh(types_kr, counts, color=self.main_window.colors['warning'])
            self.issue_chart.set_xlabel('발생 횟수', fontsize=10, color='white')
            self.issue_chart.set_title('주요 문제 유형', fontsize=12, fontweight='bold', color='white')
            self.issue_chart.grid(True, alpha=0.3, axis='x')
            self.issue_chart.tick_params(colors='white')
            
            # 값 표시
            for bar, value in zip(bars, counts):
                width = bar.get_width()
                self.issue_chart.text(
                    width + 0.5, 
                    bar.get_y() + bar.get_height()/2.,
                    f'{value}', 
                    ha='left', 
                    va='center', 
                    fontsize=9, 
                    color='white'
                )
            
            self.issue_chart.figure.tight_layout()
            self.chart_frames['issues'][1].draw()
    
    def _update_text_stats(self, stats):
        """텍스트 통계 업데이트"""
        self.stats_text.delete(1.0, tk.END)
        
        text = f"""=== 통계 요약 ===
총 파일: {stats['basic']['total_files']}개
총 페이지: {stats['basic']['total_pages']}페이지
평균 처리 시간: {stats['basic']['avg_processing_time']:.1f}초
총 오류: {stats['basic']['total_errors']}개
총 경고: {stats['basic']['total_warnings']}개
자동 수정: {stats['basic']['auto_fixed_count']}개

=== 일별 처리량 ===
"""
        
        for daily in stats['daily']:
            text += f"{daily['date']}: {daily['files']}개 파일, {daily['pages']}페이지\n"
        
        text += "\n=== 주요 문제 유형 ===\n"
        for issue in stats['common_issues'][:10]:
            text += f"{issue['type']}: {issue['count']}회 (파일 {issue['affected_files']}개)\n"
        
        self.stats_text.insert(1.0, text)
    
    def show_statistics(self, period):
        """특정 기간의 통계 보기"""
        self.stats_period.set(period)
        self.parent.select(1)  # 통계 탭으로 이동
        self.update_statistics()
    
    def generate_report(self):
        """통계 리포트 생성"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML 파일", "*.html"), ("모든 파일", "*.*")]
        )
        
        if filename:
            self.main_window.data_manager.export_statistics_report(filename)
            
            # 생성된 파일 열기
            webbrowser.open(filename)