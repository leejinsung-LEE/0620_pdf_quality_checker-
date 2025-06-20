# gui/components/menubar.py
"""
메뉴바 컴포넌트
프로그램의 모든 메뉴를 관리합니다.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.scrolledtext as scrolledtext
import customtkinter as ctk
import webbrowser


class Menubar:
    """메뉴바 컴포넌트 클래스"""
    
    def __init__(self, main_window):
        """
        메뉴바 초기화
        
        Args:
            main_window: 메인 윈도우 인스턴스
        """
        self.main_window = main_window
        self._create_menubar()
        self._bind_shortcuts()
    
    def _create_menubar(self):
        """메뉴바 생성"""
        menubar = tk.Menu(
            self.main_window.root, 
            bg=self.main_window.colors['bg_secondary'],
            fg=self.main_window.colors['text_primary'],
            activebackground=self.main_window.colors['accent'],
            activeforeground='white',
            font=self.main_window.fonts['body']
        )
        self.main_window.root.config(menu=menubar)
        
        # 파일 메뉴
        self._create_file_menu(menubar)
        
        # 폴더 메뉴
        self._create_folder_menu(menubar)
        
        # 도구 메뉴
        self._create_tools_menu(menubar)
        
        # 통계 메뉴
        self._create_stats_menu(menubar)
        
        # 도움말 메뉴
        self._create_help_menu(menubar)
    
    def _create_file_menu(self, menubar):
        """파일 메뉴 생성"""
        file_menu = tk.Menu(menubar, tearoff=0,
                           bg=self.main_window.colors['bg_secondary'],
                           fg=self.main_window.colors['text_primary'],
                           activebackground=self.main_window.colors['accent'],
                           activeforeground='white',
                           font=self.main_window.fonts['body'])
        menubar.add_cascade(label="파일", menu=file_menu)
        
        file_menu.add_command(
            label="PDF 파일 추가...", 
            command=self.main_window.browse_files, 
            accelerator="Ctrl+O"
        )
        file_menu.add_command(
            label="폴더 추가...", 
            command=self.main_window.browse_folder
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="데이터 내보내기...", 
            command=self.export_data
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="종료", 
            command=self.main_window.on_closing, 
            accelerator="Alt+F4"
        )
    
    def _create_folder_menu(self, menubar):
        """폴더 메뉴 생성"""
        folder_menu = tk.Menu(menubar, tearoff=0,
                             bg=self.main_window.colors['bg_secondary'],
                             fg=self.main_window.colors['text_primary'],
                             activebackground=self.main_window.colors['accent'],
                             activeforeground='white',
                             font=self.main_window.fonts['body'])
        menubar.add_cascade(label="폴더", menu=folder_menu)
        
        folder_menu.add_command(
            label="감시 폴더 추가...", 
            command=self.main_window.add_watch_folder
        )
        folder_menu.add_command(
            label="감시 시작/중지", 
            command=self.main_window.toggle_folder_watching
        )
        folder_menu.add_separator()
        folder_menu.add_command(
            label="폴더 설정 관리...", 
            command=self.main_window.manage_folders
        )
    
    def _create_tools_menu(self, menubar):
        """도구 메뉴 생성"""
        tools_menu = tk.Menu(menubar, tearoff=0,
                            bg=self.main_window.colors['bg_secondary'],
                            fg=self.main_window.colors['text_primary'],
                            activebackground=self.main_window.colors['accent'],
                            activeforeground='white',
                            font=self.main_window.fonts['body'])
        menubar.add_cascade(label="도구", menu=tools_menu)
        
        tools_menu.add_command(
            label="PDF 비교...", 
            command=self.main_window.open_comparison_window, 
            accelerator="Ctrl+D"
        )
        tools_menu.add_separator()
        tools_menu.add_command(
            label="설정...", 
            command=self.main_window.open_settings, 
            accelerator="Ctrl+,"
        )
        tools_menu.add_command(
            label="알림 테스트", 
            command=self.main_window.test_notification
        )
        tools_menu.add_separator()
        tools_menu.add_command(
            label="로그 보기", 
            command=self.view_logs
        )
        tools_menu.add_command(
            label="데이터베이스 정리", 
            command=self.main_window.cleanup_database
        )
    
    def _create_stats_menu(self, menubar):
        """통계 메뉴 생성"""
        stats_menu = tk.Menu(menubar, tearoff=0,
                            bg=self.main_window.colors['bg_secondary'],
                            fg=self.main_window.colors['text_primary'],
                            activebackground=self.main_window.colors['accent'],
                            activeforeground='white',
                            font=self.main_window.fonts['body'])
        menubar.add_cascade(label="통계", menu=stats_menu)
        
        stats_menu.add_command(
            label="오늘의 통계", 
            command=lambda: self.main_window.show_statistics('today')
        )
        stats_menu.add_command(
            label="이번 주 통계", 
            command=lambda: self.main_window.show_statistics('week')
        )
        stats_menu.add_command(
            label="이번 달 통계", 
            command=lambda: self.main_window.show_statistics('month')
        )
        stats_menu.add_separator()
        stats_menu.add_command(
            label="통계 리포트 생성...", 
            command=self.main_window.generate_stats_report
        )
    
    def _create_help_menu(self, menubar):
        """도움말 메뉴 생성"""
        help_menu = tk.Menu(menubar, tearoff=0,
                           bg=self.main_window.colors['bg_secondary'],
                           fg=self.main_window.colors['text_primary'],
                           activebackground=self.main_window.colors['accent'],
                           activeforeground='white',
                           font=self.main_window.fonts['body'])
        menubar.add_cascade(label="도움말", menu=help_menu)
        
        help_menu.add_command(label="사용 방법", command=self.show_help)
        help_menu.add_command(label="단축키 목록", command=self.show_shortcuts)
        help_menu.add_command(label="정보", command=self.show_about)
    
    def _bind_shortcuts(self):
        """단축키 바인딩"""
        self.main_window.root.bind('<Control-o>', lambda e: self.main_window.browse_files())
        self.main_window.root.bind('<Control-comma>', lambda e: self.main_window.open_settings())
        self.main_window.root.bind('<Control-d>', lambda e: self.main_window.open_comparison_window())
        self.main_window.root.bind('<F5>', lambda e: self.main_window.refresh_current_tab())
    
    def export_data(self):
        """데이터 내보내기"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML 파일", "*.html"), ("모든 파일", "*.*")]
        )
        
        if filename:
            self.main_window.data_manager.export_statistics_report(filename)
            messagebox.showinfo("완료", "데이터 내보내기가 완료되었습니다.")
    
    def view_logs(self):
        """로그 보기"""
        log_window = ctk.CTkToplevel(self.main_window.root)
        log_window.title("시스템 로그")
        log_window.geometry("800x600")
        
        # 프레임
        log_frame = ctk.CTkFrame(log_window)
        log_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 텍스트 위젯
        log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=self.main_window.fonts['mono'],
            bg=self.main_window.colors['bg_secondary'],
            fg=self.main_window.colors['text_primary'],
            insertbackground=self.main_window.colors['text_primary'],
            selectbackground=self.main_window.colors['accent'],
            borderwidth=0,
            highlightthickness=0
        )
        log_text.pack(fill='both', expand=True)
        
        # 로그 파일 읽기
        try:
            log_file = self.main_window.logger.get_log_file()
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_text.insert('1.0', f.read())
                log_text.config(state='disabled')
        except Exception as e:
            log_text.insert('1.0', f"로그 파일을 읽을 수 없습니다: {str(e)}")
    
    def show_help(self):
        """도움말"""
        help_text = """PDF 품질 검수 시스템 v4.0 - Modularized Edition

주요 기능:
1. 통합 실시간 처리 (드래그앤드롭 포함)
2. 다중 폴더 감시
3. 통계 대시보드
4. 처리 이력 관리
5. Windows 알림

사용법:
1. 사이드바에서 감시할 폴더 추가
2. 각 폴더별로 프로파일과 자동 수정 설정
3. 토글 스위치로 감시 시작
4. 실시간 탭에서 직접 파일 처리 가능

단축키:
- Ctrl+O: 파일 추가
- Ctrl+D: PDF 비교
- Ctrl+,: 설정
- F5: 새로고침"""
        
        messagebox.showinfo("도움말", help_text)
    
    def show_shortcuts(self):
        """단축키 목록"""
        shortcuts = """단축키 목록:

Ctrl+O - PDF 파일 추가
Ctrl+D - PDF 비교
Ctrl+, - 설정 열기
F5 - 현재 탭 새로고침
Alt+F4 - 프로그램 종료

마우스:
더블클릭 - 보고서 열기
우클릭 - 컨텍스트 메뉴"""
        
        messagebox.showinfo("단축키", shortcuts)
    
    def show_about(self):
        """프로그램 정보"""
        about_text = """PDF 품질 검수 시스템 v4.0
Modularized Edition

인쇄 품질을 위한 전문 PDF 검사 도구

주요 개선사항:
• 모듈화된 구조로 유지보수 용이
• 실시간 처리와 드래그앤드롭 통합
• 반응형 설정 창
• 향상된 사용자 경험

UI Framework: CustomTkinter
Theme: Dark Mode

© 2025 PDF Quality Checker
All rights reserved."""
        
        messagebox.showinfo("정보", about_text)