# gui/tabs/history_tab.py
"""
이력 탭
처리된 파일들의 이력을 표시하고 검색할 수 있는 탭입니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.scrolledtext as scrolledtext
import customtkinter as ctk
from pathlib import Path
import webbrowser


class HistoryTab:
    """이력 탭 클래스"""
    
    def __init__(self, main_window, parent):
        """
        이력 탭 초기화
        
        Args:
            main_window: 메인 윈도우 인스턴스
            parent: 부모 위젯 (Notebook)
        """
        self.main_window = main_window
        self.parent = parent
        
        # 탭 생성
        self._create_tab()
        
        # 초기 데이터 로드
        self.update_history()
    
    def _create_tab(self):
        """탭 생성"""
        self.tab = ctk.CTkFrame(self.parent, fg_color=self.main_window.colors['bg_primary'])
        self.parent.add(self.tab, text="📋 처리 이력")
        
        # 검색 프레임
        self._create_search_frame()
        
        # 이력 목록
        self._create_history_list()
        
        # 우클릭 메뉴
        self._create_context_menu()
    
    def _create_search_frame(self):
        """검색 프레임 생성"""
        search_frame = ctk.CTkFrame(self.tab, fg_color="transparent")
        search_frame.pack(fill='x', padx=20, pady=20)
        
        ctk.CTkLabel(
            search_frame, 
            text="검색:", 
            font=self.main_window.fonts['body']
        ).pack(side='left', padx=(0, 10))
        
        self.history_search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            search_frame, 
            textvariable=self.history_search_var, 
            width=300, 
            height=32
        )
        search_entry.pack(side='left', padx=5)
        
        ctk.CTkButton(
            search_frame, 
            text="🔍 검색", 
            command=self._search_history,
            width=80, 
            height=32
        ).pack(side='left', padx=5)
        
        ctk.CTkButton(
            search_frame, 
            text="🔄 초기화", 
            command=self._reset_search,
            width=80, 
            height=32,
            fg_color=self.main_window.colors['bg_card'],
            hover_color=self.main_window.colors['accent']
        ).pack(side='left', padx=5)
        
        # 필터 옵션
        filter_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        filter_frame.pack(side='right')
        
        self.filter_errors_only = tk.BooleanVar()
        ctk.CTkCheckBox(
            filter_frame, 
            text="오류만 표시", 
            variable=self.filter_errors_only,
            command=self.update_history
        ).pack(side='left', padx=10)
    
    def _create_history_list(self):
        """이력 목록 생성"""
        list_frame = ctk.CTkFrame(
            self.tab, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10
        )
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 트리뷰
        tree_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.history_tree = ttk.Treeview(
            tree_frame,
            columns=('date', 'pages', 'errors', 'warnings', 'profile', 'status'),
            show='tree headings',
            height=15
        )
        
        # 컬럼 설정
        self.history_tree.heading('#0', text='파일명')
        self.history_tree.heading('date', text='처리일시')
        self.history_tree.heading('pages', text='페이지')
        self.history_tree.heading('errors', text='오류')
        self.history_tree.heading('warnings', text='경고')
        self.history_tree.heading('profile', text='프로파일')
        self.history_tree.heading('status', text='상태')
        
        # 컬럼 너비
        self.history_tree.column('#0', width=250)
        self.history_tree.column('date', width=150)
        self.history_tree.column('pages', width=80)
        self.history_tree.column('errors', width=80)
        self.history_tree.column('warnings', width=80)
        self.history_tree.column('profile', width=100)
        self.history_tree.column('status', width=100)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        # 배치
        self.history_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 더블클릭 이벤트
        self.history_tree.bind('<Double-Button-1>', self._on_double_click)
    
    def _create_context_menu(self):
        """우클릭 컨텍스트 메뉴 생성"""
        self.context_menu = tk.Menu(
            self.main_window.root, 
            tearoff=0,
            bg=self.main_window.colors['bg_secondary'],
            fg=self.main_window.colors['text_primary'],
            activebackground=self.main_window.colors['accent'],
            activeforeground='white',
            font=self.main_window.fonts['body']
        )
        self.context_menu.add_command(label="상세 정보", command=self._show_details)
        self.context_menu.add_command(label="보고서 보기", command=self._view_report)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="파일 비교", command=self._compare_files)
        
        self.history_tree.bind('<Button-3>', self._show_context_menu)
    
    def update_history(self):
        """처리 이력 업데이트"""
        # 기존 항목 제거
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # 검색 조건
        search_text = self.history_search_var.get()
        filter_errors = self.filter_errors_only.get()
        
        # 데이터 조회
        if search_text:
            history = self.main_window.data_manager.search_files(filename_pattern=search_text)
        else:
            history = self.main_window.data_manager.get_recent_files(limit=100)
        
        # 필터링
        if filter_errors:
            history = [h for h in history if h.get('error_count', 0) > 0]
        
        # 트리에 추가
        for record in history:
            status = '통과' if record.get('error_count', 0) == 0 else '실패'
            
            self.history_tree.insert(
                '',
                'end',
                text=record['filename'],
                values=(
                    record['processed_at'],
                    record.get('page_count', '-'),
                    record.get('error_count', 0),
                    record.get('warning_count', 0),
                    record.get('profile', '-'),
                    status
                )
            )
    
    def _search_history(self):
        """이력 검색"""
        self.update_history()
    
    def _reset_search(self):
        """검색 초기화"""
        self.history_search_var.set("")
        self.filter_errors_only.set(False)
        self.update_history()
    
    def _show_context_menu(self, event):
        """우클릭 메뉴 표시"""
        item = self.history_tree.identify_row(event.y)
        if item:
            self.history_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _on_double_click(self, event):
        """더블클릭 이벤트"""
        self._view_report()
    
    def _show_details(self):
        """상세 정보 표시"""
        selection = self.history_tree.selection()
        if not selection:
            return
            
        item = self.history_tree.item(selection[0])
        filename = item['text']
        
        # 상세 정보 대화상자
        dialog = ctk.CTkToplevel(self.main_window.root)
        dialog.title(f"상세 정보 - {filename}")
        dialog.geometry("600x400")
        dialog.transient(self.main_window.root)
        
        # 정보 표시
        info_frame = ctk.CTkFrame(dialog)
        info_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        info_text = scrolledtext.ScrolledText(
            info_frame,
            wrap=tk.WORD,
            font=self.main_window.fonts['body'],
            bg=self.main_window.colors['bg_secondary'],
            fg=self.main_window.colors['text_primary'],
            insertbackground=self.main_window.colors['text_primary'],
            selectbackground=self.main_window.colors['accent'],
            borderwidth=0,
            highlightthickness=0
        )
        info_text.pack(fill='both', expand=True)
        
        # 데이터베이스에서 상세 정보 조회
        history = self.main_window.data_manager.get_file_history(filename)
        if history:
            latest = history[0]
            info_text.insert('1.0', f"""파일명: {filename}
처리일시: {latest.get('processed_at', '-')}
프로파일: {latest.get('profile', '-')}
페이지 수: {latest.get('page_count', '-')}
PDF 버전: {latest.get('pdf_version', '-')}
파일 크기: {latest.get('file_size_formatted', '-')}

오류: {latest.get('error_count', 0)}개
경고: {latest.get('warning_count', 0)}개
총 문제: {latest.get('total_issues', 0)}개

처리 시간: {latest.get('processing_time', '-')}초
잉크량 분석: {'포함' if latest.get('ink_analysis_included', False) else '미포함'}
자동 수정: {'적용' if latest.get('auto_fix_applied', False) else '미적용'}
""")
        
        # 닫기 버튼
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=10)
        
        ctk.CTkButton(
            button_frame, 
            text="닫기", 
            command=dialog.destroy,
            width=80, 
            height=36
        ).pack()
    
    def _view_report(self):
        """보고서 보기"""
        selection = self.history_tree.selection()
        if not selection:
            return
            
        item = self.history_tree.item(selection[0])
        filename = item['text']
        
        # 보고서 찾기 및 열기
        # 먼저 기본 reports 폴더에서 찾기
        reports_path = Path("reports")
        for report_file in reports_path.glob(f"*{Path(filename).stem}*.html"):
            webbrowser.open(str(report_file))
            return
        
        # 못 찾으면 여러 경로에서 찾기
        possible_paths = []
        
        # 모든 감시 폴더의 reports 하위 폴더 확인
        for config in self.main_window.folder_watcher.folder_configs.values():
            if hasattr(config, 'path'):
                reports_folder = config.path / "reports"
                if reports_folder not in possible_paths:
                    possible_paths.append(reports_folder)
        
        # 가능한 경로들에서 보고서 찾기
        for path in possible_paths:
            if path.exists():
                for report_file in path.glob(f"*{Path(filename).stem}*.html"):
                    webbrowser.open(str(report_file))
                    return
        
        messagebox.showinfo("정보", "보고서를 찾을 수 없습니다.")
    
    def _compare_files(self):
        """파일 비교"""
        messagebox.showinfo("정보", "파일 비교 기능은 개발 중입니다.")