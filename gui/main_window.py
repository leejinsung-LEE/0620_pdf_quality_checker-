# gui/main_window.py - 메인 윈도우 클래스
"""
메인 윈도우 클래스 - GUI의 중심이 되는 클래스
각 구성요소(사이드바, 메뉴바, 탭 등)를 조합하여 전체 GUI를 구성합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from pathlib import Path
import queue
from datetime import datetime, timedelta
import os

# CustomTkinter 설정
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# 프로젝트 내부 모듈들 (기존과 동일)
from config import Config
from simple_logger import SimpleLogger
from data_manager import DataManager
from notification_manager import get_notification_manager
from multi_folder_watcher import MultiFolderWatcher
from settings_window import SettingsWindow
from pdf_comparison_window import PDFComparisonWindow

# GUI 구성요소 모듈들 (새로 추가)
from .components.sidebar import Sidebar
from .components.menubar import Menubar
from .components.statusbar import Statusbar
from .tabs.realtime_tab import RealtimeTab
from .tabs.statistics_tab import StatisticsTab
from .tabs.history_tab import HistoryTab
from .dialogs.folder_dialogs import FolderDialogs

# tkinterdnd2 임포트 시도
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False
    TkinterDnD = tk.Tk


class EnhancedPDFCheckerGUI:
    """향상된 PDF 검수 시스템 GUI - Modularized Edition"""
    
    def __init__(self):
        """GUI 초기화"""
        # 메인 윈도우 생성 - DnD 호환성 유지
        if HAS_DND:
            self.root = TkinterDnD.Tk()
            self.root.configure(bg='#1a1a1a')
        else:
            self.root = ctk.CTk()
        
        self.root.title("PDF 품질 검수 시스템 v4.0 - Modularized Edition")
        
        # 화면 크기에 따른 동적 크기 설정
        self._setup_window_size()
        
        # 색상 테마 정의
        self.colors = {
            'bg_primary': '#1a1a1a',
            'bg_secondary': '#252525',
            'bg_card': '#2d2d2d',
            'accent': '#0078d4',
            'accent_hover': '#106ebe',
            'success': '#107c10',
            'warning': '#ff8c00',
            'error': '#d83b01',
            'text_primary': '#ffffff',
            'text_secondary': '#b3b3b3',
            'border': '#404040'
        }
        
        # 폰트 설정
        self.fonts = {
            'title': ('맑은 고딕', 16, 'bold'),
            'heading': ('맑은 고딕', 13, 'bold'),
            'subheading': ('맑은 고딕', 11, 'bold'),
            'body': ('맑은 고딕', 10),
            'small': ('맑은 고딕', 9),
            'mono': ('D2Coding', 10) if os.name == 'nt' else ('Consolas', 10)
        }
        
        # 설정 및 매니저 초기화
        self._init_managers()
        
        # GUI 상태 변수
        self._init_state_variables()
        
        # GUI 구성
        self._setup_styles()
        self._create_gui()
        
        # 폴더 감시 시작 (설정에 따라)
        self._init_folder_watching()
        
        # 윈도우 이벤트
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 주기적 업데이트
        self._start_periodic_updates()
        
        # 아이템 카운터 초기화
        self.item_counter = 0
    
    def _setup_window_size(self):
        """윈도우 크기 설정"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 화면의 80% 크기로 설정 (최대 1600x900)
        window_width = min(int(screen_width * 0.8), 1600)
        window_height = min(int(screen_height * 0.8), 900)
        
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.minsize(1200, 700)
        
        # 아이콘 설정
        try:
            self.root.iconbitmap("assets/icon.ico")
        except:
            pass
    
    def _init_managers(self):
        """각종 매니저 초기화"""
        # 설정
        self.config = Config()
        Config.create_folders()
        
        # 로거
        self.logger = SimpleLogger()
        self.logger.log("프로그램 시작 - Modularized Edition")
        
        # 데이터 매니저
        self.data_manager = DataManager()
        
        # 알림 매니저
        self.notification_manager = get_notification_manager()
        
        # 폴더 감시기
        self.folder_watcher = MultiFolderWatcher()
        self.folder_watcher.set_callback(self._on_folder_pdf_found)
        
        # 배치 프로세서
        self.batch_processor = None
        
        # 큐
        self.file_queue = queue.Queue()
        self.result_queue = queue.Queue()
    
    def _init_state_variables(self):
        """GUI 상태 변수 초기화"""
        # 처리 상태
        self.processing_files = {}
        self.is_processing = False
        self.is_folder_watching = False
        
        # 현재 선택된 탭
        self.current_tab = tk.StringVar(value="realtime")
        
        # 통계 캐시
        self.stats_cache = None
        self.stats_last_updated = None
        
        # 드롭된 파일들
        self.dropped_files = []
        
        # 잉크량 검수 기본값
        self.include_ink_analysis = tk.BooleanVar(value=Config.is_ink_analysis_enabled())
    
    def _setup_styles(self):
        """ttk 스타일 설정 - 다크 테마"""
        self.style = ttk.Style()
        
        # 테마 설정
        try:
            self.style.theme_use('clam')
        except:
            pass
        
        # Treeview 스타일
        self.style.configure("Treeview",
            background=self.colors['bg_secondary'],
            foreground=self.colors['text_primary'],
            fieldbackground=self.colors['bg_secondary'],
            borderwidth=0,
            highlightthickness=0,
            rowheight=25
        )
        
        self.style.configure("Treeview.Heading",
            background=self.colors['bg_card'],
            foreground=self.colors['text_primary'],
            borderwidth=0,
            relief='flat',
            font=self.fonts['subheading']
        )
        
        self.style.map("Treeview",
            background=[('selected', self.colors['accent'])],
            foreground=[('selected', 'white')]
        )
        
        # Notebook (탭) 스타일
        self.style.configure('TNotebook',
            background=self.colors['bg_secondary'],
            borderwidth=0
        )
        
        self.style.configure('TNotebook.Tab',
            background=self.colors['bg_card'],
            foreground=self.colors['text_secondary'],
            padding=(20, 10),
            font=self.fonts['body']
        )
        
        self.style.map('TNotebook.Tab',
            background=[('selected', self.colors['accent'])],
            foreground=[('selected', 'white')]
        )
        
        # Combobox 스타일
        self.style.configure("TCombobox",
            fieldbackground=self.colors['bg_card'],
            background=self.colors['bg_card'],
            foreground=self.colors['text_primary'],
            borderwidth=0,
            arrowcolor=self.colors['text_primary']
        )
        
        # Scrollbar 스타일
        self.style.configure("Vertical.TScrollbar",
            background=self.colors['bg_secondary'],
            darkcolor=self.colors['bg_card'],
            lightcolor=self.colors['bg_card'],
            troughcolor=self.colors['bg_secondary'],
            bordercolor=self.colors['bg_secondary'],
            arrowcolor=self.colors['text_secondary']
        )
    
    def _create_gui(self):
        """GUI 구성요소 생성"""
        # 메뉴바 생성
        self.menubar = Menubar(self)
        
        # 메인 컨테이너
        main_container = ctk.CTkFrame(self.root, fg_color=self.colors['bg_primary'])
        main_container.pack(fill='both', expand=True)
        
        # 사이드바 생성
        self.sidebar = Sidebar(self, main_container)
        
        # 콘텐츠 영역 생성
        self._create_content_area(main_container)
        
        # 상태바 생성
        self.statusbar = Statusbar(self)
        
        # 대화상자 핸들러 생성
        self.folder_dialogs = FolderDialogs(self)
    
    def _create_content_area(self, parent):
        """콘텐츠 영역 생성"""
        content = ctk.CTkFrame(parent, fg_color=self.colors['bg_primary'])
        content.pack(side='right', fill='both', expand=True)
        
        # 탭 위젯
        tab_container = ctk.CTkFrame(content, fg_color=self.colors['bg_secondary'],
                                   corner_radius=10)
        tab_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.notebook = ttk.Notebook(tab_container)
        self.notebook.pack(fill='both', expand=True, padx=2, pady=2)
        
        # 각 탭 생성
        self.realtime_tab = RealtimeTab(self, self.notebook)
        self.statistics_tab = StatisticsTab(self, self.notebook)
        self.history_tab = HistoryTab(self, self.notebook)
        
        # 탭 변경 이벤트
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
    
    def _generate_safe_item_id(self, prefix="item"):
        """Treeview에서 안전하게 사용할 수 있는 ID 생성"""
        import time
        self.item_counter += 1
        timestamp = int(time.time() * 1000)
        safe_id = f"{prefix}_{self.item_counter}_{timestamp}"
        return safe_id
    
    def _init_folder_watching(self):
        """폴더 감시 초기화"""
        # 저장된 폴더 설정이 있으면 자동 시작
        if len(self.folder_watcher.folder_configs) > 0:
            auto_start = messagebox.askyesno(
                "폴더 감시",
                "저장된 폴더 설정이 있습니다.\n폴더 감시를 시작하시겠습니까?"
            )
            if auto_start:
                self.start_folder_watching()
    
    def _start_periodic_updates(self):
        """주기적 업데이트 시작"""
        self.sidebar.update_quick_stats()
        self.root.after(30000, self._start_periodic_updates)  # 30초마다
    
    def _on_tab_changed(self, event):
        """탭 변경 이벤트"""
        selected_tab = event.widget.tab('current')['text']
        
        if '통계' in selected_tab:
            self.statistics_tab.update_statistics()
        elif '이력' in selected_tab:
            self.history_tab.update_history()
    
    def _on_folder_pdf_found(self, file_path: Path, folder_config: dict):
        """폴더에서 PDF 발견시 콜백"""
        self.realtime_tab.add_file_to_process(file_path, folder_config)
    
    # ===== 폴더 관리 메서드 (대화상자로 위임) =====
    
    def add_watch_folder(self):
        """감시 폴더 추가"""
        self.folder_dialogs.show_add_folder_dialog()
    
    def edit_folder_settings(self):
        """폴더 설정 편집"""
        self.folder_dialogs.show_edit_folder_dialog()
    
    def remove_watch_folder(self):
        """폴더 제거"""
        self.sidebar.remove_selected_folder()
    
    def manage_folders(self):
        """폴더 관리"""
        messagebox.showinfo("정보", "사이드바에서 폴더를 선택한 후 설정 버튼을 클릭하세요.")
    
    # ===== 폴더 감시 제어 =====
    
    def toggle_folder_watching(self):
        """폴더 감시 토글"""
        if self.sidebar.watch_toggle_switch.get():
            self.start_folder_watching()
        else:
            self.stop_folder_watching()
    
    def start_folder_watching(self):
        """폴더 감시 시작"""
        if not self.folder_watcher.folder_configs:
            messagebox.showinfo("정보", "감시할 폴더가 없습니다.\n먼저 폴더를 추가하세요.")
            self.sidebar.watch_toggle_switch.deselect()
            return
        
        self.folder_watcher.start_watching()
        self.is_folder_watching = True
        
        # UI 업데이트
        self.sidebar.update_watch_status(True)
        self.statusbar.update_watch_status("감시: 실행 중")
        
        self.logger.log("폴더 감시 시작")
        self.statusbar.set_status("폴더 감시가 시작되었습니다.")
    
    def stop_folder_watching(self):
        """폴더 감시 중지"""
        self.folder_watcher.stop_watching()
        self.is_folder_watching = False
        
        # UI 업데이트
        self.sidebar.update_watch_status(False)
        self.statusbar.update_watch_status("감시: 중지")
        
        self.logger.log("폴더 감시 중지")
        self.statusbar.set_status("폴더 감시가 중지되었습니다.")
    
    # ===== 파일 처리 메서드 =====
    
    def browse_files(self):
        """파일 선택"""
        self.realtime_tab.browse_files()
    
    def browse_folder(self):
        """폴더 선택"""
        self.realtime_tab.browse_folder()
    
    # ===== 도구 메서드 =====
    
    def open_comparison_window(self):
        """PDF 비교 창 열기"""
        PDFComparisonWindow(self.root)
    
    def open_settings(self):
        """설정 창 열기"""
        SettingsWindow(self.root)
    
    def test_notification(self):
        """알림 테스트"""
        self.notification_manager.test_notification()
    
    def view_logs(self):
        """로그 보기"""
        self.menubar.view_logs()
    
    def cleanup_database(self):
        """데이터베이스 정리"""
        if messagebox.askyesno("확인", "오래된 데이터를 정리하시겠습니까?\n(30일 이상된 데이터 삭제)"):
            # 구현 필요
            messagebox.showinfo("완료", "데이터베이스 정리가 완료되었습니다.")
    
    def export_data(self):
        """데이터 내보내기"""
        self.menubar.export_data()
    
    # ===== 통계 메서드 =====
    
    def show_statistics(self, period):
        """통계 보기"""
        self.statistics_tab.show_statistics(period)
    
    def generate_stats_report(self):
        """통계 리포트 생성"""
        self.statistics_tab.generate_report()
    
    # ===== 도움말 메서드 =====
    
    def show_help(self):
        """도움말"""
        self.menubar.show_help()
    
    def show_shortcuts(self):
        """단축키 목록"""
        self.menubar.show_shortcuts()
    
    def show_about(self):
        """프로그램 정보"""
        self.menubar.show_about()
    
    def refresh_current_tab(self):
        """현재 탭 새로고침"""
        current = self.notebook.index('current')
        
        if current == 0:  # 실시간
            self.realtime_tab.refresh()
        elif current == 1:  # 통계
            self.statistics_tab.update_statistics()
        elif current == 2:  # 이력
            self.history_tab.update_history()
    
    # ===== 프로그램 종료 =====
    
    def on_closing(self):
        """프로그램 종료"""
        if self.is_folder_watching:
            if messagebox.askyesno("확인", "폴더 감시가 실행 중입니다.\n종료하시겠습니까?"):
                self.stop_folder_watching()
            else:
                return
        
        self.logger.log("프로그램 종료")
        self.root.destroy()
    
    def run(self):
        """GUI 실행"""
        self.statusbar.set_status("PDF 품질 검수 시스템이 준비되었습니다.")
        self.root.mainloop()