# settings_window.py - 사용자 친화적인 설정 창 (외부 도구 통합 버전)
# 테마 설정 탭 추가, 라이트/다크 모드 지원
# 2025.06 추가: 외부 도구 설정 탭 및 상태 확인 기능
"""
최적화된 설정 창 - 외부 도구 통합 버전
- 화면 크기에 따른 동적 크기 조정
- 스크롤 가능한 프레임으로 모든 내용 표시
- 탭별 최적화된 레이아웃
- 잉크량 검사 ON/OFF 설정
- 테마 시스템 (다크/라이트 모드)
- 외부 도구 설정 및 상태 확인 추가
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import json
from pathlib import Path
from config import Config
from datetime import datetime
import customtkinter as ctk

# 알림 매니저 (선택적)
try:
    from notification_manager import get_notification_manager
    HAS_NOTIFICATION = True
except ImportError:
    HAS_NOTIFICATION = False

# 외부 도구 상태 확인 (새로 추가)
try:
    from external_tools import check_external_tools_status, HAS_EXTERNAL_TOOLS
    HAS_EXTERNAL_TOOLS_CHECK = True
except ImportError:
    HAS_EXTERNAL_TOOLS_CHECK = False

class SettingsWindow:
    """설정 창 클래스 - 외부 도구 통합 버전"""
    
    def __init__(self, parent=None, config=None):
        """
        설정 창 초기화
        
        Args:
            parent: 부모 윈도우 (None이면 독립 창)
            config: Config 인스턴스 (선택사항)
        """
        # 창 생성
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()
        
        self.window.title("PDF 검수 시스템 설정")
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        
        # 화면 크기 확인
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # 화면 크기에 따른 동적 크기 설정
        window_width = min(max(900, int(screen_width * 0.65)), int(screen_width * 0.85))
        window_height = min(max(750, int(screen_height * 0.8)), int(screen_height * 0.9))
        
        self.window.geometry(f"{window_width}x{window_height}")
        self.window.minsize(900, 750)
        
        # 아이콘 설정 (있으면)
        try:
            self.window.iconbitmap("icon.ico")
        except:
            pass
        
        # Config 인스턴스 저장
        self.config = config if config else Config()
        
        # 설정값 저장용 변수들
        self.settings_vars = {}
        self.original_settings = {}
        
        # 테마 관련 변수
        self.theme_colors = {}
        self.preview_frames = {}
        
        # 외부 도구 상태 (새로 추가)
        self.external_tools_status = {}
        if HAS_EXTERNAL_TOOLS_CHECK:
            self.external_tools_status = check_external_tools_status()
        
        # UI 생성
        self._create_ui()
        
        # 현재 설정 로드
        self._load_current_settings()
        
        # 창 중앙 배치
        self._center_window()
    
    def _center_window(self):
        """창을 화면 중앙에 배치"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_ui(self):
        """UI 구성 요소 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 윈도우 크기 조절 설정
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # 노트북 (탭) 위젯
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 각 탭 생성
        self._create_theme_tab()      # 새로 추가: 테마 설정
        self._create_quality_tab()
        self._create_processing_tab()
        self._create_folders_tab()
        self._create_external_tools_tab()  # 새로 추가: 외부 도구 설정
        self._create_notification_tab()
        self._create_advanced_tab()
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 버튼들
        ttk.Button(button_frame, text="💾 저장", command=self._save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="↩️ 기본값 복원", command=self._reset_to_default).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📤 설정 내보내기", command=self._export_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📥 설정 가져오기", command=self._import_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ 취소", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _create_theme_tab(self):
        """테마 설정 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🎨 테마")
        
        # 스크롤 가능한 프레임 생성
        scrollable_frame = self._create_scrollable_frame(tab)
        
        # 테마 모드 설정
        mode_frame = ttk.LabelFrame(scrollable_frame, text="🌓 테마 모드", padding="10")
        mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 테마 모드 선택
        self._create_radio_setting(
            mode_frame, "theme_mode", "테마 모드",
            "애플리케이션의 색상 테마를 선택합니다",
            [
                ("다크 모드", "dark"),
                ("라이트 모드", "light"),
                ("시스템 설정 따라가기", "system"),
                ("시간대별 자동 전환", "auto")
            ],
            "dark"
        )
        
        # 시간대별 자동 전환 설정
        auto_frame = ttk.LabelFrame(scrollable_frame, text="⏰ 자동 전환 설정", padding="10")
        auto_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 자동 전환 시간
        time_frame = ttk.Frame(auto_frame)
        time_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(time_frame, text="라이트 모드 시작 시간:").pack(side=tk.LEFT, padx=(0, 10))
        self.light_start_hour = tk.StringVar(value="6")
        light_start_combo = ttk.Combobox(
            time_frame,
            textvariable=self.light_start_hour,
            values=[str(i) for i in range(24)],
            state='readonly',
            width=5
        )
        light_start_combo.pack(side=tk.LEFT)
        ttk.Label(time_frame, text="시").pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(time_frame, text="다크 모드 시작 시간:").pack(side=tk.LEFT, padx=(0, 10))
        self.dark_start_hour = tk.StringVar(value="18")
        dark_start_combo = ttk.Combobox(
            time_frame,
            textvariable=self.dark_start_hour,
            values=[str(i) for i in range(24)],
            state='readonly',
            width=5
        )
        dark_start_combo.pack(side=tk.LEFT)
        ttk.Label(time_frame, text="시").pack(side=tk.LEFT, padx=(5, 0))
        
        # 설명
        ttk.Label(
            auto_frame,
            text="시간대별 자동 전환을 선택하면 지정한 시간에 따라 테마가 자동으로 변경됩니다.",
            foreground="gray"
        ).pack(anchor=tk.W, pady=(10, 0))
        
        # 색상 커스터마이징
        custom_frame = ttk.LabelFrame(scrollable_frame, text="🎨 색상 커스터마이징", padding="10")
        custom_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 커스텀 색상 활성화
        self._create_checkbox_setting(
            custom_frame, "enable_custom_colors", "커스텀 색상 사용",
            "기본 테마 색상 대신 사용자 정의 색상을 사용합니다", 
            False
        )
        
        # 색상 선택 버튼들
        color_buttons_frame = ttk.Frame(custom_frame)
        color_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        color_items = [
            ("primary_color", "주 색상", "#0078d4"),
            ("success_color", "성공 색상", "#107c10"),
            ("warning_color", "경고 색상", "#ff8c00"),
            ("error_color", "오류 색상", "#d83b01")
        ]
        
        for i, (key, label, default) in enumerate(color_items):
            if i % 2 == 0:
                row_frame = ttk.Frame(color_buttons_frame)
                row_frame.pack(fill=tk.X, pady=5)
            
            item_frame = ttk.Frame(row_frame)
            item_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            
            ttk.Label(item_frame, text=f"{label}:").pack(side=tk.LEFT, padx=(0, 10))
            
            # 색상 변수
            color_var = tk.StringVar(value=default)
            self.settings_vars[key] = color_var
            self.theme_colors[key] = color_var
            
            # 색상 미리보기
            preview = tk.Frame(item_frame, width=30, height=20, bg=default, relief=tk.SOLID, borderwidth=1)
            preview.pack(side=tk.LEFT, padx=(0, 5))
            self.preview_frames[key] = preview
            
            # 색상 선택 버튼
            def choose_color(k=key, p=preview):
                color = colorchooser.askcolor(initialcolor=self.theme_colors[k].get())
                if color[1]:
                    self.theme_colors[k].set(color[1])
                    p.configure(bg=color[1])
            
            ttk.Button(item_frame, text="선택", command=choose_color, width=8).pack(side=tk.LEFT)
        
        # 테마 미리보기
        preview_frame = ttk.LabelFrame(scrollable_frame, text="👁️ 테마 미리보기", padding="10")
        preview_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 미리보기 버튼
        preview_btn = ttk.Button(
            preview_frame,
            text="미리보기 적용",
            command=self._preview_theme
        )
        preview_btn.pack(pady=5)
        
        ttk.Label(
            preview_frame,
            text="미리보기는 일시적으로 적용됩니다. 저장하지 않으면 원래 설정으로 돌아갑니다.",
            foreground="gray"
        ).pack()
        
        # 사전 정의 테마
        preset_frame = ttk.LabelFrame(scrollable_frame, text="📋 사전 정의 테마", padding="10")
        preset_frame.pack(fill=tk.X, padx=10, pady=5)
        
        preset_buttons_frame = ttk.Frame(preset_frame)
        preset_buttons_frame.pack(fill=tk.X)
        
        presets = [
            ("기본 다크", self._apply_default_dark),
            ("기본 라이트", self._apply_default_light),
            ("고대비", self._apply_high_contrast),
            ("블루 테마", self._apply_blue_theme)
        ]
        
        for text, command in presets:
            ttk.Button(
                preset_buttons_frame,
                text=text,
                command=command,
                width=15
            ).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 여백 추가
        ttk.Frame(scrollable_frame, height=20).pack()
    
    def _create_scrollable_frame(self, parent):
        """스크롤 가능한 프레임 생성"""
        # 캔버스와 스크롤바 생성
        canvas = tk.Canvas(parent, highlightthickness=0, bg='white')
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # 캔버스 창에 프레임 배치
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # 프레임 크기가 변경될 때 스크롤 영역 업데이트
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # 캔버스 너비에 맞춰 프레임 너비 조정
            canvas_width = canvas.winfo_width()
            canvas.itemconfig(canvas_frame, width=canvas_width)
        
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        # 캔버스 크기 변경 시 프레임 너비 조정
        def configure_canvas(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_frame, width=canvas_width)
        
        canvas.bind("<Configure>", configure_canvas)
        
        # 마우스 휠 스크롤 지원
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 배치
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return scrollable_frame
    
    def _create_quality_tab(self):
        """품질 검사 기준 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="검사 기준")
        
        # 스크롤 가능한 프레임 생성
        scrollable_frame = self._create_scrollable_frame(tab)
        
        # 잉크량 설정
        ink_frame = ttk.LabelFrame(scrollable_frame, text="💧 잉크량 기준", padding="10")
        ink_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 최대 잉크량
        self._create_slider_setting(
            ink_frame, "max_ink_coverage", "최대 허용 잉크량",
            "총 잉크량(TAC)의 최대 허용치입니다",
            200, 400, Config.MAX_INK_COVERAGE, "%"
        )
        
        # 경고 잉크량
        self._create_slider_setting(
            ink_frame, "warning_ink_coverage", "경고 수준 잉크량",
            "이 값을 초과하면 경고를 표시합니다",
            200, 400, Config.WARNING_INK_COVERAGE, "%"
        )
        
        # 이미지 설정
        image_frame = ttk.LabelFrame(scrollable_frame, text="🖼️ 이미지 품질", padding="10")
        image_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 안내 메시지 추가
        info_label = ttk.Label(
            image_frame, 
            text="💡 해상도 기준이 완화되었습니다 (72 DPI 이상만 허용)",
            foreground="blue"
        )
        info_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 최소 해상도
        self._create_number_setting(
            image_frame, "min_image_dpi", "최소 이미지 해상도",
            "72 DPI 미만은 인쇄 품질이 심각하게 저하됩니다",
            Config.MIN_IMAGE_DPI, "DPI"
        )
        
        # 경고 해상도
        self._create_number_setting(
            image_frame, "warning_image_dpi", "경고 해상도",
            "일반 문서는 150 DPI 이상을 권장합니다",
            Config.WARNING_IMAGE_DPI, "DPI"
        )
        
        # 최적 해상도
        self._create_number_setting(
            image_frame, "optimal_image_dpi", "최적 해상도",
            "고품질 인쇄를 위한 권장 해상도입니다",
            Config.OPTIMAL_IMAGE_DPI, "DPI"
        )
        
        # 페이지 설정
        page_frame = ttk.LabelFrame(scrollable_frame, text="📐 페이지 및 재단선", padding="10")
        page_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 재단 여백
        self._create_number_setting(
            page_frame, "standard_bleed_size", "표준 재단 여백",
            "일반적인 인쇄물의 재단선 크기입니다",
            Config.STANDARD_BLEED_SIZE, "mm"
        )
        
        # 페이지 크기 허용 오차
        self._create_number_setting(
            page_frame, "page_size_tolerance", "페이지 크기 허용 오차",
            "동일 크기로 간주할 오차 범위입니다",
            Config.PAGE_SIZE_TOLERANCE, "mm"
        )
        
        # 텍스트 설정
        text_frame = ttk.LabelFrame(scrollable_frame, text="🔤 텍스트 기준", padding="10")
        text_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 최소 텍스트 크기
        self._create_number_setting(
            text_frame, "min_text_size", "최소 텍스트 크기",
            "가독성을 위한 최소 글자 크기입니다",
            Config.MIN_TEXT_SIZE, "pt"
        )
        
        # 여백 추가
        ttk.Frame(scrollable_frame, height=20).pack()
    
    def _create_processing_tab(self):
        """처리 옵션 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="처리 옵션")
        
        # 스크롤 가능한 프레임 생성
        scrollable_frame = self._create_scrollable_frame(tab)
        
        # 잉크량 분석 설정
        ink_analysis_frame = ttk.LabelFrame(scrollable_frame, text="🎨 잉크량 분석", padding="10")
        ink_analysis_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 잉크량 검사 활성화/비활성화
        self._create_checkbox_setting(
            ink_analysis_frame, "ink_coverage", "잉크량 분석 활성화",
            "PDF 파일의 잉크 커버리지를 분석합니다 (처리 시간이 크게 증가합니다)", 
            Config.CHECK_OPTIONS.get('ink_coverage', False)
        )
        
        # 경고 메시지
        warning_frame = ttk.Frame(ink_analysis_frame)
        warning_frame.pack(fill=tk.X, pady=(5, 0))
        
        warning_label = ttk.Label(
            warning_frame,
            text="⚠️ 잉크량 분석은 파일당 10-30초의 추가 시간이 소요됩니다.\n   대량 처리 시에는 비활성화를 권장합니다.",
            foreground="red",
            wraplength=500
        )
        warning_label.pack(anchor=tk.W)
        
        # 잉크량 계산 해상도 설정
        dpi_frame = ttk.Frame(ink_analysis_frame)
        dpi_frame.pack(fill=tk.X, pady=(10, 0))
        
        self._create_combo_setting(
            dpi_frame, "ink_calculation_dpi", "계산 해상도",
            "높을수록 정확하지만 시간이 더 오래 걸립니다",
            ["100", "150", "200", "300"],
            str(Config.INK_CALCULATION_DPI)
        )
        
        # 검사 옵션
        check_frame = ttk.LabelFrame(scrollable_frame, text="🔍 검사 항목", padding="10")
        check_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 체크박스 옵션들
        self._create_checkbox_setting(
            check_frame, "check_transparency", "투명도 검사",
            "투명 효과 사용을 감지합니다", 
            Config.CHECK_OPTIONS.get('transparency', False)
        )
        
        self._create_checkbox_setting(
            check_frame, "check_overprint", "중복인쇄 검사",
            "오버프린트 설정을 확인합니다", 
            Config.CHECK_OPTIONS.get('overprint', True)
        )
        
        self._create_checkbox_setting(
            check_frame, "check_bleed", "재단선 검사",
            "재단 여백을 확인합니다 (정보 제공용)", 
            Config.CHECK_OPTIONS.get('bleed', True)
        )
        
        self._create_checkbox_setting(
            check_frame, "check_spot_colors", "별색 상세 검사",
            "PANTONE 등 별색 사용을 분석합니다", 
            Config.CHECK_OPTIONS.get('spot_colors', True)
        )
        
        # 성능 옵션
        perf_frame = ttk.LabelFrame(scrollable_frame, text="⚡ 성능 설정", padding="10")
        perf_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 프로세스 지연
        self._create_number_setting(
            perf_frame, "process_delay", "파일 처리 지연",
            "파일 복사 완료 대기 시간입니다",
            Config.PROCESS_DELAY, "초"
        )
        
        # 동시 처리 파일 수
        self._create_number_setting(
            perf_frame, "max_concurrent_files", "최대 동시 처리 파일 수",
            "동시에 처리할 최대 파일 개수입니다",
            getattr(Config, 'MAX_CONCURRENT_FILES', 4), "개"
        )
        
        # 보고서 옵션
        report_frame = ttk.LabelFrame(scrollable_frame, text="📝 보고서 설정", padding="10")
        report_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 보고서 형식
        self._create_combo_setting(
            report_frame, "default_report_format", "기본 보고서 형식",
            "생성할 보고서 형식을 선택합니다",
            ["text", "html", "both"],
            Config.DEFAULT_REPORT_FORMAT
        )
        
        # HTML 스타일
        self._create_combo_setting(
            report_frame, "html_report_style", "HTML 보고서 스타일",
            "HTML 보고서의 디자인 스타일입니다",
            ["business", "dashboard", "practical"],
            Config.HTML_REPORT_STYLE
        )
        
        # 보고서 열 수
        self._create_number_setting(
            report_frame, "layout_columns", "문제 표시 열 수",
            "HTML 보고서의 문제 표시 열 개수입니다",
            3, "열"
        )
        
        # 여백 추가
        ttk.Frame(scrollable_frame, height=20).pack()
    
    def _create_folders_tab(self):
        """폴더 설정 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="폴더 설정")
        
        # 스크롤 가능한 프레임 생성
        scrollable_frame = self._create_scrollable_frame(tab)
        
        # 폴더 경로 설정
        folder_frame = ttk.LabelFrame(scrollable_frame, text="📁 작업 폴더", padding="10")
        folder_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 입력 폴더
        self._create_folder_setting(
            folder_frame, "input_folder", "입력 폴더",
            "PDF 파일을 넣을 폴더입니다",
            Config.INPUT_FOLDER
        )
        
        # 출력 폴더
        self._create_folder_setting(
            folder_frame, "output_folder", "출력 폴더",
            "처리된 파일이 저장될 폴더입니다",
            Config.OUTPUT_FOLDER
        )
        
        # 보고서 폴더
        self._create_folder_setting(
            folder_frame, "reports_folder", "보고서 폴더",
            "검수 보고서가 저장될 폴더입니다",
            Config.REPORTS_FOLDER
        )
        
        # 프리플라이트 설정
        profile_frame = ttk.LabelFrame(scrollable_frame, text="🎯 프리플라이트", padding="10")
        profile_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 기본 프로파일
        self._create_combo_setting(
            profile_frame, "default_preflight_profile", "기본 프리플라이트 프로파일",
            "PDF 검사에 사용할 기본 프로파일입니다",
            Config.AVAILABLE_PROFILES,
            Config.DEFAULT_PREFLIGHT_PROFILE
        )
        
        # 프로파일 설명
        profile_info = ttk.LabelFrame(scrollable_frame, text="프로파일 설명", padding="10")
        profile_info.pack(fill=tk.X, padx=10, pady=5)
        
        info_text = """• offset: 오프셋 인쇄용 (가장 엄격한 기준)
• digital: 디지털 인쇄용 (중간 수준)
• newspaper: 신문 인쇄용 (완화된 기준)
• large_format: 대형 인쇄용 (배너, 현수막)
• high_quality: 고품질 인쇄용 (화보집, 아트북)"""
        
        ttk.Label(profile_info, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)
        
        # 여백 추가
        ttk.Frame(scrollable_frame, height=20).pack()
    
    def _create_external_tools_tab(self):
        """외부 도구 설정 탭 - 새로 추가"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🛠️ 외부 도구")
        
        # 스크롤 가능한 프레임 생성
        scrollable_frame = self._create_scrollable_frame(tab)
        
        # 외부 도구 상태
        status_frame = ttk.LabelFrame(scrollable_frame, text="📊 외부 도구 상태", padding="10")
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 상태 확인 버튼
        status_btn_frame = ttk.Frame(status_frame)
        status_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            status_btn_frame,
            text="🔄 상태 새로고침",
            command=self._refresh_external_tools_status
        ).pack(side=tk.LEFT)
        
        # 상태 표시 영역
        self.tools_status_frame = ttk.Frame(status_frame)
        self.tools_status_frame.pack(fill=tk.X, pady=5)
        
        # 초기 상태 표시
        self._update_tools_status_display()
        
        # 설치 안내
        install_frame = ttk.LabelFrame(scrollable_frame, text="💿 설치 안내", padding="10")
        install_frame.pack(fill=tk.X, padx=10, pady=5)
        
        install_text = """외부 도구를 설치하면 더 정확한 분석이 가능합니다:

🔤 pdffonts (poppler-utils):
   • 정확한 폰트 임베딩 상태 확인
   • Windows: poppler 설치 후 PATH 추가
   • Ubuntu/Debian: sudo apt install poppler-utils
   • macOS: brew install poppler

👻 Ghostscript:
   • 정확한 오버프린트 검사
   • 색상 변환 및 최적화
   • Windows: https://www.ghostscript.com/download/gsdnld.html
   • Ubuntu/Debian: sudo apt install ghostscript
   • macOS: brew install ghostscript

⚠️ 외부 도구가 없어도 기본 기능은 정상 작동합니다."""
        
        install_label = ttk.Label(install_frame, text=install_text, justify=tk.LEFT)
        install_label.pack(anchor=tk.W)
        
        # 설정 옵션
        options_frame = ttk.LabelFrame(scrollable_frame, text="⚙️ 도구 설정", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 외부 도구 우선 사용
        self._create_checkbox_setting(
            options_frame, "prefer_external_tools", "외부 도구 우선 사용",
            "가능하면 항상 외부 도구를 먼저 시도합니다", 
            True
        )
        
        # 실패 시 기본 분석 사용
        self._create_checkbox_setting(
            options_frame, "fallback_to_basic", "실패 시 기본 분석 사용",
            "외부 도구 실패 시 기본 분석으로 대체합니다", 
            True
        )
        
        # 도구별 타임아웃 설정
        timeout_frame = ttk.Frame(options_frame)
        timeout_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(timeout_frame, text="도구 실행 타임아웃:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.tools_timeout = tk.StringVar(value="30")
        timeout_combo = ttk.Combobox(
            timeout_frame,
            textvariable=self.tools_timeout,
            values=["10", "30", "60", "120"],
            state='readonly',
            width=10
        )
        timeout_combo.pack(side=tk.LEFT)
        ttk.Label(timeout_frame, text="초").pack(side=tk.LEFT, padx=(5, 0))
        
        # 여백 추가
        ttk.Frame(scrollable_frame, height=20).pack()
    
    def _refresh_external_tools_status(self):
        """외부 도구 상태 새로고침"""
        if HAS_EXTERNAL_TOOLS_CHECK:
            self.external_tools_status = check_external_tools_status()
            self._update_tools_status_display()
            messagebox.showinfo("완료", "외부 도구 상태를 새로고침했습니다.")
        else:
            messagebox.showwarning("경고", "external_tools 모듈을 찾을 수 없습니다.")
    
    def _update_tools_status_display(self):
        """외부 도구 상태 표시 업데이트"""
        # 기존 위젯 제거
        for widget in self.tools_status_frame.winfo_children():
            widget.destroy()
        
        if not HAS_EXTERNAL_TOOLS_CHECK:
            ttk.Label(
                self.tools_status_frame,
                text="❌ external_tools 모듈을 찾을 수 없습니다.",
                foreground="red"
            ).pack(anchor=tk.W)
            return
        
        # 도구별 상태 표시
        tools_info = [
            ("pdffonts", "폰트 분석 도구"),
            ("ghostscript", "PostScript 처리 도구"),
            ("pdftk", "PDF 조작 도구 (선택사항)"),
            ("qpdf", "PDF 검증 도구 (선택사항)")
        ]
        
        for tool_name, description in tools_info:
            status = self.external_tools_status.get(tool_name, False)
            
            tool_frame = ttk.Frame(self.tools_status_frame)
            tool_frame.pack(fill=tk.X, pady=2)
            
            # 상태 아이콘
            status_icon = "✅" if status else "❌"
            status_text = "사용 가능" if status else "설치되지 않음"
            status_color = "green" if status else "red"
            
            ttk.Label(
                tool_frame,
                text=f"{status_icon} {tool_name}: {description}",
                foreground=status_color
            ).pack(side=tk.LEFT)
            
            ttk.Label(
                tool_frame,
                text=f"({status_text})",
                foreground=status_color
            ).pack(side=tk.RIGHT)
    
    def _create_notification_tab(self):
        """알림 설정 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="알림")
        
        # 스크롤 가능한 프레임 생성
        scrollable_frame = self._create_scrollable_frame(tab)
        
        # 알림 활성화
        notify_frame = ttk.LabelFrame(scrollable_frame, text="🔔 Windows 알림 설정", padding="10")
        notify_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 메인 활성화 스위치
        self._create_checkbox_setting(
            notify_frame, "enable_notifications", "Windows 알림 사용",
            "처리 완료/오류 시 Windows 토스트 알림을 표시합니다", 
            False
        )
        
        # 알림 사용 가능 여부 확인
        if HAS_NOTIFICATION:
            # 알림 매니저 상태 확인
            notifier = get_notification_manager()
            status = notifier.get_status()
            
            status_text = f"알림 시스템: {status['method'] or '사용 불가'}"
            if status['method']:
                status_color = "green"
            else:
                status_color = "red"
                status_text += "\n알림 라이브러리를 설치하세요: pip install win10toast"
            
            status_label = ttk.Label(notify_frame, text=status_text, foreground=status_color)
            status_label.pack(anchor='w', pady=(10, 0))
            
            # 테스트 버튼
            def test_notification():
                notifier.test_notification()
                messagebox.showinfo("테스트", "알림 테스트를 발송했습니다.\n화면에 알림이 표시되는지 확인하세요.")
            
            ttk.Button(notify_frame, text="🔔 알림 테스트", command=test_notification).pack(pady=(10, 0))
        else:
            ttk.Label(
                notify_frame, 
                text="알림 모듈이 설치되지 않았습니다.\nnotification_manager.py 파일이 필요합니다.",
                foreground="red"
            ).pack(pady=10)
        
        # 세부 알림 옵션
        detail_frame = ttk.LabelFrame(scrollable_frame, text="📢 알림 상세 설정", padding="10")
        detail_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self._create_checkbox_setting(
            detail_frame, "notify_on_success", "처리 성공 알림",
            "PDF 처리가 성공적으로 완료되면 알림", 
            True
        )
        
        self._create_checkbox_setting(
            detail_frame, "notify_on_error", "오류 발생 알림",
            "PDF 처리 중 오류가 발생하면 알림", 
            True
        )
        
        self._create_checkbox_setting(
            detail_frame, "notify_on_batch_complete", "일괄 처리 완료 알림",
            "여러 파일 처리가 모두 완료되면 알림", 
            True
        )
        
        self._create_checkbox_setting(
            detail_frame, "notification_sound", "알림 소리",
            "알림 표시 시 소리도 함께 재생", 
            True
        )
        
        # 알림 표시 시간
        time_frame = ttk.Frame(detail_frame)
        time_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(time_frame, text="알림 표시 시간:").pack(side='left', padx=(0, 10))
        
        self.notification_duration = tk.StringVar(value="5")
        duration_combo = ttk.Combobox(
            time_frame,
            textvariable=self.notification_duration,
            values=["3", "5", "10", "15", "30"],
            state='readonly',
            width=10
        )
        duration_combo.pack(side='left')
        ttk.Label(time_frame, text="초").pack(side='left', padx=(5, 0))
        
        # 여백 추가
        ttk.Frame(scrollable_frame, height=20).pack()
    
    def _create_advanced_tab(self):
        """고급 설정 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="고급")
        
        # 스크롤 가능한 프레임 생성
        scrollable_frame = self._create_scrollable_frame(tab)
        
        # 자동 수정 옵션
        autofix_frame = ttk.LabelFrame(scrollable_frame, text="🔧 자동 수정 옵션", padding="10")
        autofix_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(autofix_frame, text="⚠️ 자동 수정 기능은 오류발견시 작동됩니다.(원본보존)", 
                 foreground="red").pack(pady=5)
        
        # 색상 변환 옵션
        color_frame = ttk.LabelFrame(autofix_frame, text="색상 변환", padding="5")
        color_frame.pack(fill=tk.X, pady=5)
        
        self._create_checkbox_setting(
            color_frame, "auto_convert_rgb", "RGB→CMYK 자동 변환",
            "RGB 색상을 CMYK로 자동 변환합니다", 
            False
        )
        
        # 폰트 처리 옵션
        font_frame = ttk.LabelFrame(autofix_frame, text="폰트 처리", padding="5")
        font_frame.pack(fill=tk.X, pady=5)
        
        self._create_checkbox_setting(
            font_frame, "auto_outline_fonts", "폰트 아웃라인 변환",
            "미임베딩 폰트가 있을경우 모든폰트를 아웃라인으로 변환합니다", 
            False
        )
        
        self._create_checkbox_setting(
            font_frame, "warn_small_text", "작은 텍스트 경고",
            "4pt 미만 텍스트에 대해 경고합니다", 
            True
        )
        
        # 백업 옵션
        backup_frame = ttk.LabelFrame(autofix_frame, text="백업 설정", padding="5")
        backup_frame.pack(fill=tk.X, pady=5)
        
        self._create_checkbox_setting(
            backup_frame, "always_backup", "항상 원본 백업",
            "수정 전 항상 원본을 백업합니다", 
            True
        )
        
        self._create_checkbox_setting(
            backup_frame, "create_comparison_report", "수정 전후 비교 리포트 생성",
            "자동 수정 후 변경사항 리포트를 생성합니다", 
            True
        )
        
        # 로그 설정
        log_frame = ttk.LabelFrame(scrollable_frame, text="📋 로그 설정", padding="10")
        log_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self._create_checkbox_setting(
            log_frame, "enable_logging", "로그 기록 활성화",
            "작업 내역을 파일로 기록합니다", 
            True
        )
        
        self._create_combo_setting(
            log_frame, "log_level", "로그 상세 수준",
            "기록할 로그의 상세 정도입니다",
            ["간단", "보통", "상세"],
            "보통"
        )
        
        # 여백 추가
        ttk.Frame(scrollable_frame, height=20).pack()
    
    def _create_radio_setting(self, parent, key, label, description, options, current):
        """라디오 버튼 설정 항목 생성"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        # 레이블
        ttk.Label(frame, text=label, font=('', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(frame, text=description, foreground="gray").pack(anchor=tk.W)
        
        # 변수
        var = tk.StringVar(value=current)
        self.settings_vars[key] = var
        
        # 라디오 버튼들
        radio_frame = ttk.Frame(frame)
        radio_frame.pack(fill=tk.X, pady=5)
        
        for text, value in options:
            ttk.Radiobutton(
                radio_frame,
                text=text,
                variable=var,
                value=value
            ).pack(anchor=tk.W, padx=(20, 0), pady=2)
    
    def _create_slider_setting(self, parent, key, label, description, min_val, max_val, current, unit):
        """슬라이더 설정 항목 생성"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        # 레이블
        ttk.Label(frame, text=label, font=('', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(frame, text=description, foreground="gray").pack(anchor=tk.W)
        
        # 슬라이더 프레임
        slider_frame = ttk.Frame(frame)
        slider_frame.pack(fill=tk.X, pady=5)
        
        # 현재값 표시
        value_var = tk.IntVar(value=current)
        self.settings_vars[key] = value_var
        
        value_label = ttk.Label(slider_frame, text=f"{current}{unit}", width=10)
        value_label.pack(side=tk.RIGHT, padx=5)
        
        # 슬라이더
        slider = ttk.Scale(
            slider_frame, from_=min_val, to=max_val,
            variable=value_var, orient=tk.HORIZONTAL
        )
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 값 변경 시 레이블 업데이트
        def update_label(val):
            value_label.config(text=f"{int(float(val))}{unit}")
        
        slider.config(command=update_label)
    
    def _create_number_setting(self, parent, key, label, description, current, unit):
        """숫자 입력 설정 항목 생성"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        # 레이블
        ttk.Label(frame, text=label, font=('', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(frame, text=description, foreground="gray").pack(anchor=tk.W)
        
        # 입력 프레임
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        # 변수
        if isinstance(current, float):
            var = tk.DoubleVar(value=current)
        else:
            var = tk.IntVar(value=current)
        self.settings_vars[key] = var
        
        # 입력창
        entry = ttk.Entry(input_frame, textvariable=var, width=10)
        entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # 단위
        ttk.Label(input_frame, text=unit).pack(side=tk.LEFT)
    
    def _create_checkbox_setting(self, parent, key, label, description, current):
        """체크박스 설정 항목 생성"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        # 변수
        var = tk.BooleanVar(value=current)
        self.settings_vars[key] = var
        
        # 체크박스
        check = ttk.Checkbutton(frame, text=label, variable=var)
        check.pack(anchor=tk.W)
        
        # 설명
        ttk.Label(frame, text=description, foreground="gray").pack(anchor=tk.W, padx=(20, 0))
        
        return check
    
    def _create_combo_setting(self, parent, key, label, description, options, current):
        """콤보박스 설정 항목 생성"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        # 레이블
        ttk.Label(frame, text=label, font=('', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(frame, text=description, foreground="gray").pack(anchor=tk.W)
        
        # 변수
        var = tk.StringVar(value=current)
        self.settings_vars[key] = var
        
        # 콤보박스
        combo = ttk.Combobox(frame, textvariable=var, values=options, state="readonly", width=30)
        combo.pack(anchor=tk.W, pady=5)
    
    def _create_folder_setting(self, parent, key, label, description, current):
        """폴더 선택 설정 항목 생성"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        # 레이블
        ttk.Label(frame, text=label, font=('', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(frame, text=description, foreground="gray").pack(anchor=tk.W)
        
        # 입력 프레임
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        # 변수
        var = tk.StringVar(value=current)
        self.settings_vars[key] = var
        
        # 입력창
        entry = ttk.Entry(input_frame, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # 찾아보기 버튼
        def browse():
            folder = filedialog.askdirectory(initialdir=current)
            if folder:
                var.set(Path(folder).name)
        
        ttk.Button(input_frame, text="찾아보기", command=browse).pack(side=tk.LEFT)
    
    def _preview_theme(self):
        """테마 미리보기 적용"""
        theme_mode = self.settings_vars.get('theme_mode', tk.StringVar(value='dark')).get()
        
        if theme_mode == 'light':
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")
        
        messagebox.showinfo("미리보기", f"{theme_mode} 모드가 일시적으로 적용되었습니다.\n저장하지 않으면 원래 설정으로 돌아갑니다.")
    
    def _apply_default_dark(self):
        """기본 다크 테마 적용"""
        self.theme_colors['primary_color'].set("#0078d4")
        self.theme_colors['success_color'].set("#107c10")
        self.theme_colors['warning_color'].set("#ff8c00")
        self.theme_colors['error_color'].set("#d83b01")
        self._update_color_previews()
    
    def _apply_default_light(self):
        """기본 라이트 테마 적용"""
        self.theme_colors['primary_color'].set("#0078d4")
        self.theme_colors['success_color'].set("#107c10")
        self.theme_colors['warning_color'].set("#ff8c00")
        self.theme_colors['error_color'].set("#d83b01")
        self._update_color_previews()
    
    def _apply_high_contrast(self):
        """고대비 테마 적용"""
        self.theme_colors['primary_color'].set("#00ffff")
        self.theme_colors['success_color'].set("#00ff00")
        self.theme_colors['warning_color'].set("#ffff00")
        self.theme_colors['error_color'].set("#ff0000")
        self._update_color_previews()
    
    def _apply_blue_theme(self):
        """블루 테마 적용"""
        self.theme_colors['primary_color'].set("#0066cc")
        self.theme_colors['success_color'].set("#006600")
        self.theme_colors['warning_color'].set("#ff9900")
        self.theme_colors['error_color'].set("#cc0000")
        self._update_color_previews()
    
    def _update_color_previews(self):
        """색상 미리보기 업데이트"""
        for key, preview in self.preview_frames.items():
            color = self.theme_colors[key].get()
            preview.configure(bg=color)
    
    def _load_current_settings(self):
        """현재 설정값 로드"""
        # 기존 설정 파일이 있으면 로드
        settings_file = Path("user_settings.json")
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    
                # 저장된 설정을 변수에 적용
                for key, value in saved_settings.items():
                    if key in self.settings_vars:
                        self.settings_vars[key].set(value)
                    elif key == 'notification_duration':
                        if hasattr(self, 'notification_duration'):
                            self.notification_duration.set(str(value))
                    elif key == 'light_start_hour':
                        if hasattr(self, 'light_start_hour'):
                            self.light_start_hour.set(str(value))
                    elif key == 'dark_start_hour':
                        if hasattr(self, 'dark_start_hour'):
                            self.dark_start_hour.set(str(value))
                    elif key == 'tools_timeout':
                        if hasattr(self, 'tools_timeout'):
                            self.tools_timeout.set(str(value))
            except Exception as e:
                print(f"설정 로드 오류: {e}")
        
        # 원본 설정 저장 (취소 시 복원용)
        for key, var in self.settings_vars.items():
            self.original_settings[key] = var.get()
    
    def _save_settings(self):
        """설정 저장 - 외부 도구 설정 포함"""
        try:
            # 설정 파일 경로
            settings_file = Path("user_settings.json")
            
            # 설정값 수집
            settings = {}
            
            # 기본 설정값들
            for key, var in self.settings_vars.items():
                settings[key] = var.get()
            
            # 추가 설정값들
            if hasattr(self, 'notification_duration'):
                settings['notification_duration'] = int(self.notification_duration.get())
            if hasattr(self, 'light_start_hour'):
                settings['light_start_hour'] = int(self.light_start_hour.get())
            if hasattr(self, 'dark_start_hour'):
                settings['dark_start_hour'] = int(self.dark_start_hour.get())
            if hasattr(self, 'tools_timeout'):
                settings['tools_timeout'] = int(self.tools_timeout.get())
            
            # Config 업데이트
            if 'ink_coverage' in settings:
                Config.set_ink_analysis(settings['ink_coverage'])
            
            # CHECK_OPTIONS 업데이트
            check_options = {}
            for key in ['check_transparency', 'check_overprint', 'check_bleed', 
                       'check_spot_colors', 'ink_coverage']:
                if key in settings:
                    check_options[key.replace('check_', '')] = settings[key]
            
            # 설정 구조화 (외부 도구 설정 추가)
            structured_settings = {
                # 테마 설정
                'theme': settings.get('theme_mode', 'dark'),
                'theme_mode': settings.get('theme_mode', 'dark'),
                'light_start_hour': settings.get('light_start_hour', 6),
                'dark_start_hour': settings.get('dark_start_hour', 18),
                'enable_custom_colors': settings.get('enable_custom_colors', False),
                'custom_colors': {
                    'primary': settings.get('primary_color', '#0078d4'),
                    'success': settings.get('success_color', '#107c10'),
                    'warning': settings.get('warning_color', '#ff8c00'),
                    'error': settings.get('error_color', '#d83b01')
                },
                
                # 품질 기준
                'max_ink_coverage': settings.get('max_ink_coverage', Config.MAX_INK_COVERAGE),
                'warning_ink_coverage': settings.get('warning_ink_coverage', Config.WARNING_INK_COVERAGE),
                'min_image_dpi': settings.get('min_image_dpi', Config.MIN_IMAGE_DPI),
                'warning_image_dpi': settings.get('warning_image_dpi', Config.WARNING_IMAGE_DPI),
                'optimal_image_dpi': settings.get('optimal_image_dpi', Config.OPTIMAL_IMAGE_DPI),
                'standard_bleed_size': settings.get('standard_bleed_size', Config.STANDARD_BLEED_SIZE),
                'page_size_tolerance': settings.get('page_size_tolerance', Config.PAGE_SIZE_TOLERANCE),
                'min_text_size': settings.get('min_text_size', Config.MIN_TEXT_SIZE),
                
                # 처리 옵션
                'check_options': check_options,
                'ink_calculation_dpi': settings.get('ink_calculation_dpi', str(Config.INK_CALCULATION_DPI)),
                'process_delay': settings.get('process_delay', Config.PROCESS_DELAY),
                'max_concurrent_files': settings.get('max_concurrent_files', 4),
                
                # 보고서
                'default_report_format': settings.get('default_report_format', Config.DEFAULT_REPORT_FORMAT),
                'html_report_style': settings.get('html_report_style', Config.HTML_REPORT_STYLE),
                'layout_columns': settings.get('layout_columns', 3),
                
                # 폴더
                'input_folder': settings.get('input_folder', Config.INPUT_FOLDER),
                'output_folder': settings.get('output_folder', Config.OUTPUT_FOLDER),
                'reports_folder': settings.get('reports_folder', Config.REPORTS_FOLDER),
                'default_preflight_profile': settings.get('default_preflight_profile', Config.DEFAULT_PREFLIGHT_PROFILE),
                
                # 외부 도구 설정 (새로 추가)
                'external_tools': {
                    'prefer_external_tools': settings.get('prefer_external_tools', True),
                    'fallback_to_basic': settings.get('fallback_to_basic', True),
                    'tools_timeout': settings.get('tools_timeout', 30)
                },
                
                # 자동 수정
                'auto_fix_options': {
                    'convert_rgb_to_cmyk': settings.get('auto_convert_rgb', False),
                    'outline_fonts': settings.get('auto_outline_fonts', False),
                    'always_backup': settings.get('always_backup', True),
                    'create_comparison_report': settings.get('create_comparison_report', True)
                },
                
                # 알림
                'enable_notifications': settings.get('enable_notifications', False),
                'notify_on_success': settings.get('notify_on_success', True),
                'notify_on_error': settings.get('notify_on_error', True),
                'notify_on_batch_complete': settings.get('notify_on_batch_complete', True),
                'notification_sound': settings.get('notification_sound', True),
                'notification_duration': settings.get('notification_duration', 5),
                
                # 로그
                'enable_logging': settings.get('enable_logging', True),
                'log_level': settings.get('log_level', '보통')
            }
            
            # JSON으로 저장
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(structured_settings, f, ensure_ascii=False, indent=2)
            
            # 알림 매니저 업데이트 (있는 경우)
            if HAS_NOTIFICATION and structured_settings.get('enable_notifications'):
                notifier = get_notification_manager()
                notifier.set_enabled(True)
            
            messagebox.showinfo("성공", "설정이 저장되었습니다.\n\n테마 변경은 프로그램 재시작 후 완전히 적용됩니다.\n외부 도구 설정이 업데이트되었습니다.")
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 중 오류가 발생했습니다:\n{str(e)}")
    
    def _reset_to_default(self):
        """기본값으로 재설정 - 외부 도구 설정 포함"""
        if messagebox.askyesno("확인", "모든 설정을 기본값으로 되돌리시겠습니까?"):
            # 기본값 설정 (외부 도구 설정 추가)
            defaults = {
                'theme_mode': 'dark',
                'enable_custom_colors': False,
                'primary_color': '#0078d4',
                'success_color': '#107c10',
                'warning_color': '#ff8c00',
                'error_color': '#d83b01',
                'max_ink_coverage': 300,
                'warning_ink_coverage': 280,
                'min_image_dpi': 72,
                'warning_image_dpi': 150,
                'optimal_image_dpi': 300,
                'standard_bleed_size': 3.0,
                'page_size_tolerance': 2.0,
                'min_text_size': 4.0,
                'ink_calculation_dpi': '150',
                'process_delay': 1,
                'max_concurrent_files': 4,
                'default_report_format': 'both',
                'html_report_style': 'dashboard',
                'layout_columns': 3,
                'input_folder': 'input',
                'output_folder': 'output', 
                'reports_folder': 'reports',
                'default_preflight_profile': 'offset',
                'check_transparency': False,
                'check_overprint': True,
                'check_bleed': True,
                'check_spot_colors': True,
                'ink_coverage': False,
                'prefer_external_tools': True,  # 새로 추가
                'fallback_to_basic': True,      # 새로 추가
                'auto_convert_rgb': False,
                'auto_outline_fonts': False,
                'warn_small_text': True,
                'always_backup': True,
                'create_comparison_report': True,
                'enable_logging': True,
                'log_level': '보통',
                'enable_notifications': False,
                'notify_on_success': True,
                'notify_on_error': True,
                'notify_on_batch_complete': True,
                'notification_sound': True
            }
            
            # 값 설정
            for key, value in defaults.items():
                if key in self.settings_vars:
                    self.settings_vars[key].set(value)
            
            # 추가 설정값
            if hasattr(self, 'notification_duration'):
                self.notification_duration.set("5")
            if hasattr(self, 'light_start_hour'):
                self.light_start_hour.set("6")
            if hasattr(self, 'dark_start_hour'):
                self.dark_start_hour.set("18")
            if hasattr(self, 'tools_timeout'):
                self.tools_timeout.set("30")
            
            # 색상 미리보기 업데이트
            self._update_color_previews()
    
    def _export_settings(self):
        """설정 내보내기"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON 파일", "*.json"), ("모든 파일", "*.*")]
        )
        
        if filename:
            try:
                settings = {}
                for key, var in self.settings_vars.items():
                    settings[key] = var.get()
                
                # 추가 설정값들
                if hasattr(self, 'notification_duration'):
                    settings['notification_duration'] = int(self.notification_duration.get())
                if hasattr(self, 'light_start_hour'):
                    settings['light_start_hour'] = int(self.light_start_hour.get())
                if hasattr(self, 'dark_start_hour'):
                    settings['dark_start_hour'] = int(self.dark_start_hour.get())
                if hasattr(self, 'tools_timeout'):
                    settings['tools_timeout'] = int(self.tools_timeout.get())
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("성공", "설정을 내보냈습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"설정 내보내기 중 오류가 발생했습니다:\n{str(e)}")
    
    def _import_settings(self):
        """설정 가져오기"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON 파일", "*.json"), ("모든 파일", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 설정 적용
                for key, value in settings.items():
                    if key in self.settings_vars:
                        self.settings_vars[key].set(value)
                    elif key == 'notification_duration' and hasattr(self, 'notification_duration'):
                        self.notification_duration.set(str(value))
                    elif key == 'light_start_hour' and hasattr(self, 'light_start_hour'):
                        self.light_start_hour.set(str(value))
                    elif key == 'dark_start_hour' and hasattr(self, 'dark_start_hour'):
                        self.dark_start_hour.set(str(value))
                    elif key == 'tools_timeout' and hasattr(self, 'tools_timeout'):
                        self.tools_timeout.set(str(value))
                    elif key == 'check_options' and isinstance(value, dict):
                        # check_options 처리
                        for opt_key, opt_value in value.items():
                            if f'check_{opt_key}' in self.settings_vars:
                                self.settings_vars[f'check_{opt_key}'].set(opt_value)
                            elif opt_key == 'ink_coverage' and 'ink_coverage' in self.settings_vars:
                                self.settings_vars['ink_coverage'].set(opt_value)
                    elif key == 'external_tools' and isinstance(value, dict):
                        # 외부 도구 설정 처리 (새로 추가)
                        for tool_key, tool_value in value.items():
                            if tool_key in self.settings_vars:
                                self.settings_vars[tool_key].set(tool_value)
                
                # 색상 미리보기 업데이트
                self._update_color_previews()
                
                # 외부 도구 상태 새로고침
                self._update_tools_status_display()
                
                messagebox.showinfo("성공", "설정을 가져왔습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"설정 가져오기 중 오류가 발생했습니다:\n{str(e)}")
    
    def on_mousewheel(self, event):
        """마우스휠 이벤트 처리 - 안전성 개선"""
        try:
            if hasattr(event.widget, 'winfo_exists') and event.widget.winfo_exists():
                current_tab = self.notebook.index('current')
                canvas = None
                
                # 현재 탭에 따라 적절한 캔버스 선택
                # 각 탭의 스크롤 가능한 캔버스를 찾아서 스크롤
                for child in self.notebook.winfo_children():
                    if isinstance(child, ttk.Frame):
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Canvas):
                                # 현재 보이는 캔버스인지 확인
                                if subchild.winfo_viewable():
                                    canvas = subchild
                                    break
                
                if canvas and hasattr(canvas, 'winfo_exists') and canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except Exception:
            pass
    
    def close(self):
        """설정 창 닫기 - 이벤트 바인딩 해제"""
        try:
            self.window.unbind_all("<MouseWheel>")
            self.window.unbind_all("<Button-4>")
            self.window.unbind_all("<Button-5>")
        except:
            pass
        
        # 변경사항 확인
        changes_made = False
        for key, var in self.settings_vars.items():
            if key in self.original_settings:
                if var.get() != self.original_settings[key]:
                    changes_made = True
                    break
        
        if changes_made:
            response = messagebox.askyesnocancel(
                "저장 확인",
                "변경사항이 있습니다. 저장하시겠습니까?"
            )
            if response is True:  # 예
                self._save_settings()
            elif response is None:  # 취소
                return
        
        self.window.destroy()

# 테스트용 메인 함수
if __name__ == "__main__":
    # 설정 창 테스트
    window = SettingsWindow()
    window.window.mainloop()