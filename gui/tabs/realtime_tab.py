# gui/tabs/realtime_tab.py
"""
실시간 처리 탭 - Enhanced Edition
파일 처리 현황과 드래그앤드롭 기능을 통합한 탭입니다.

개선사항:
1. 페이지 크기 일관성 표시
2. 처리 시간 실시간 업데이트
3. 필터링 및 검색 기능
4. 테마 시스템 지원
5. 크기 조절 가능한 대기목록
6. 단축키 지원
7. 상태 아이콘 표시
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from pathlib import Path
import threading
from datetime import datetime, timedelta
import shutil
import webbrowser
import os
import time
import json

# 프로젝트 모듈
from config import Config
from pdf_analyzer import PDFAnalyzer
from report_generator import ReportGenerator

# tkinterdnd2 임포트 시도
try:
    from tkinterdnd2 import DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False


class RealtimeTab:
    """실시간 처리 탭 클래스 - Enhanced Edition"""
    
    # 상태 아이콘 정의
    STATUS_ICONS = {
        'waiting': '⏳',
        'processing': '⚙️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌'
    }
    
    def __init__(self, main_window, parent):
        """
        실시간 탭 초기화
        
        Args:
            main_window: 메인 윈도우 인스턴스
            parent: 부모 위젯 (Notebook)
        """
        self.main_window = main_window
        self.parent = parent
        
        # PDF 분석 결과를 저장할 딕셔너리
        self.pdf_results = {}
        
        # 처리 시간 추적용
        self.processing_times = {}
        self.timer_threads = {}
        
        # 필터 상태
        self.filter_status = tk.StringVar(value="all")
        self.search_var = tk.StringVar()
        
        # 툴팁 관리
        self.tooltips = {}
        
        # 테마 설정 로드
        self._load_theme_settings()
        
        # 탭 생성
        self._create_tab()
        
        # 단축키 바인딩
        self._bind_shortcuts()
    
    def _load_theme_settings(self):
        """테마 설정 로드"""
        try:
            with open('user_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                self.current_theme = settings.get('theme', 'dark')
        except:
            self.current_theme = 'dark'
    
    def _create_tab(self):
        """탭 생성"""
        self.tab = ctk.CTkFrame(self.parent, fg_color=self.main_window.colors['bg_primary'])
        self.parent.add(self.tab, text="🔄 실시간 처리")
        
        # 메인 컨테이너 - PanedWindow로 변경하여 크기 조절 가능
        self.paned_window = tk.PanedWindow(
            self.tab, 
            orient=tk.HORIZONTAL,
            bg=self.main_window.colors['bg_primary'],
            sashwidth=5,
            sashrelief=tk.RAISED
        )
        self.paned_window.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 왼쪽: 실시간 처리 현황
        left_frame = self._create_left_section()
        self.paned_window.add(left_frame, minsize=600, width=800)
        
        # 오른쪽: 드래그앤드롭 영역
        right_frame = self._create_right_section()
        self.paned_window.add(right_frame, minsize=300, width=350)
    
    def _create_left_section(self):
        """왼쪽 섹션 생성 - 실시간 처리 현황"""
        left_frame = ctk.CTkFrame(self.paned_window, fg_color="transparent")
        
        # 헤더 (테마 토글 포함)
        header = ctk.CTkFrame(left_frame, fg_color="transparent")
        header.pack(fill='x', pady=(0, 10))
        
        ctk.CTkLabel(
            header, 
            text="실시간 처리 현황", 
            font=self.main_window.fonts['heading']
        ).pack(side='left')
        
        # 버튼 프레임
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side='right')
        
        # 테마 토글 버튼
        self.theme_btn = ctk.CTkButton(
            btn_frame, 
            text="🌙" if self.current_theme == 'dark' else "☀️",
            command=self.toggle_theme,
            width=40, 
            height=32,
            fg_color=self.main_window.colors['bg_card']
        )
        self.theme_btn.pack(side='left', padx=(0, 5))
        
        # 새로고침 버튼
        refresh_btn = ctk.CTkButton(
            btn_frame, 
            text="🔄 새로고침", 
            command=self.refresh,
            width=100, 
            height=32,
            fg_color=self.main_window.colors['bg_card'],
            hover_color=self.main_window.colors['accent']
        )
        refresh_btn.pack(side='left')
        
        # 필터 바 추가
        self._create_filter_bar(left_frame)
        
        # 처리 중인 파일 목록
        list_frame = ctk.CTkFrame(
            left_frame, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10
        )
        list_frame.pack(fill='both', expand=True)
        
        # 트리뷰
        tree_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 컬럼 구조: 아이콘 추가
        self.realtime_tree = ttk.Treeview(
            tree_frame,
            columns=('icon', 'folder', 'status_time', 'pages', 'size', 'issues'),
            show='tree headings',
            height=15
        )
        
        # 컬럼 설정
        self.realtime_tree.heading('#0', text='파일명')
        self.realtime_tree.heading('icon', text='')
        self.realtime_tree.heading('folder', text='폴더')
        self.realtime_tree.heading('status_time', text='상태')
        self.realtime_tree.heading('pages', text='페이지')
        self.realtime_tree.heading('size', text='크기')
        self.realtime_tree.heading('issues', text='문제')
        
        # 컬럼 너비
        self.realtime_tree.column('#0', width=250)
        self.realtime_tree.column('icon', width=30, stretch=False)
        self.realtime_tree.column('folder', width=120)
        self.realtime_tree.column('status_time', width=160)
        self.realtime_tree.column('pages', width=120)
        self.realtime_tree.column('size', width=80)
        self.realtime_tree.column('issues', width=100)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.realtime_tree.yview)
        self.realtime_tree.configure(yscrollcommand=scrollbar.set)
        
        # 배치
        self.realtime_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 우클릭 메뉴
        self._create_context_menu()
        
        # 태그 색상
        self.realtime_tree.tag_configure('processing', foreground=self.main_window.colors['accent'])
        self.realtime_tree.tag_configure('success', foreground=self.main_window.colors['success'])
        self.realtime_tree.tag_configure('error', foreground=self.main_window.colors['error'])
        self.realtime_tree.tag_configure('warning', foreground=self.main_window.colors['warning'])
        
        return left_frame
    
    def _create_filter_bar(self, parent):
        """필터 바 생성"""
        filter_frame = ctk.CTkFrame(
            parent, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10,
            height=50
        )
        filter_frame.pack(fill='x', pady=(0, 10))
        filter_frame.pack_propagate(False)
        
        inner_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        inner_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        # 상태 필터 버튼들
        filter_buttons_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        filter_buttons_frame.pack(side='left', fill='y')
        
        filters = [
            ("전체", "all", None),
            ("완료", "success", self.main_window.colors['success']),
            ("경고", "warning", self.main_window.colors['warning']),
            ("오류", "error", self.main_window.colors['error']),
            ("처리중", "processing", self.main_window.colors['accent'])
        ]
        
        for text, value, color in filters:
            btn = ctk.CTkButton(
                filter_buttons_frame,
                text=text,
                command=lambda v=value: self.apply_filter(v),
                width=60,
                height=28,
                fg_color=color if color else self.main_window.colors['bg_secondary'],
                hover_color=self.main_window.colors['accent'] if not color else color
            )
            btn.pack(side='left', padx=2)
        
        # 검색창
        search_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        search_frame.pack(side='right', fill='y')
        
        ctk.CTkLabel(
            search_frame, 
            text="🔍", 
            font=('Arial', 16)
        ).pack(side='left', padx=(10, 5))
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="파일명 검색...",
            textvariable=self.search_var,
            width=200,
            height=28
        )
        search_entry.pack(side='left')
        search_entry.bind('<KeyRelease>', lambda e: self.apply_search())
    
    def _create_right_section(self):
        """오른쪽 섹션 생성 - 드래그앤드롭 영역"""
        right_frame = ctk.CTkFrame(self.paned_window, fg_color="transparent")
        
        # 드롭존
        self.drop_frame = ctk.CTkFrame(
            right_frame, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=20,
            border_width=2,
            border_color=self.main_window.colors['border'],
            height=250
        )
        self.drop_frame.pack(fill='x', pady=(0, 15))
        self.drop_frame.pack_propagate(False)
        
        # 안내 텍스트
        drop_content = ctk.CTkFrame(self.drop_frame, fg_color="transparent")
        drop_content.place(relx=0.5, rely=0.5, anchor='center')
        
        # 아이콘
        ctk.CTkLabel(drop_content, text="📄", font=('Arial', 48)).pack(pady=(0, 10))
        
        self.drop_label = ctk.CTkLabel(
            drop_content,
            text="PDF 파일을 드래그하거나\n클릭하여 선택",
            font=self.main_window.fonts['body'],
            text_color=self.main_window.colors['text_secondary']
        )
        self.drop_label.pack()
        
        # 처리 옵션 카드
        self._create_options_card(right_frame)
        
        # 처리 대기 목록 (크기 조절 가능)
        self._create_queue_list(right_frame)
        
        # 클릭 이벤트
        self.drop_frame.bind("<Button-1>", lambda e: self.browse_files())
        
        # 드래그앤드롭 설정
        if HAS_DND:
            self._setup_drag_drop()
        
        return right_frame
    
    def _create_options_card(self, parent):
        """처리 옵션 카드 생성"""
        options_card = ctk.CTkFrame(
            parent, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10
        )
        options_card.pack(fill='x', pady=(0, 15))
        
        options_inner = ctk.CTkFrame(options_card, fg_color="transparent")
        options_inner.pack(padx=15, pady=15)
        
        options_title = ctk.CTkLabel(
            options_inner, 
            text="처리 옵션", 
            font=self.main_window.fonts['subheading']
        )
        options_title.pack(pady=(0, 10))
        
        # 프로파일 선택
        profile_frame = ctk.CTkFrame(options_inner, fg_color="transparent")
        profile_frame.pack(pady=5)
        
        ctk.CTkLabel(
            profile_frame, 
            text="프로파일:", 
            font=self.main_window.fonts['body']
        ).pack(side='left', padx=(0, 10))
        
        self.drop_profile_var = tk.StringVar(value='offset')
        profile_combo = ttk.Combobox(
            profile_frame, 
            textvariable=self.drop_profile_var,
            values=Config.AVAILABLE_PROFILES,
            state='readonly',
            width=12,
            font=self.main_window.fonts['body']
        )
        profile_combo.pack(side='left')
        
        # 체크박스들
        check_frame = ctk.CTkFrame(options_inner, fg_color="transparent")
        check_frame.pack(pady=10)
        
        self.drop_auto_fix_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            check_frame, 
            text="자동 수정 적용",
            variable=self.drop_auto_fix_var,
            height=24
        ).pack(pady=3)
        
        self.drop_ink_analysis_var = tk.BooleanVar(value=Config.is_ink_analysis_enabled())
        ctk.CTkCheckBox(
            check_frame,
            text="잉크량 분석 포함",
            variable=self.drop_ink_analysis_var,
            height=24
        ).pack(pady=3)
        
        # 처리 버튼
        process_btn = ctk.CTkButton(
            options_inner, 
            text="🚀 처리 시작", 
            command=self._process_dropped_files,
            width=200, 
            height=36,
            font=self.main_window.fonts['body']
        )
        process_btn.pack(pady=(10, 0))
    
    def _create_queue_list(self, parent):
        """처리 대기 목록 생성 (개선된 버전)"""
        queue_frame = ctk.CTkFrame(
            parent, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10
        )
        queue_frame.pack(fill='both', expand=True)
        
        queue_inner = ctk.CTkFrame(queue_frame, fg_color="transparent")
        queue_inner.pack(fill='both', expand=True, padx=15, pady=15)
        
        queue_header = ctk.CTkFrame(queue_inner, fg_color="transparent")
        queue_header.pack(fill='x', pady=(0, 10))
        
        ctk.CTkLabel(
            queue_header, 
            text="대기 목록", 
            font=self.main_window.fonts['subheading']
        ).pack(side='left')
        
        # 대기 파일 수 표시
        self.queue_count_label = ctk.CTkLabel(
            queue_header,
            text="(0개)",
            font=self.main_window.fonts['small'],
            text_color=self.main_window.colors['text_secondary']
        )
        self.queue_count_label.pack(side='left', padx=5)
        
        clear_btn = ctk.CTkButton(
            queue_header, 
            text="비우기", 
            command=self._clear_drop_list,
            width=60, 
            height=28,
            fg_color=self.main_window.colors['bg_secondary'],
            hover_color=self.main_window.colors['error']
        )
        clear_btn.pack(side='right')
        
        # 대기 목록
        list_frame = ctk.CTkFrame(queue_inner, fg_color="transparent")
        list_frame.pack(fill='both', expand=True)
        
        list_scroll = ttk.Scrollbar(list_frame, orient='vertical')
        list_scroll.pack(side='right', fill='y')
        
        self.drop_listbox = tk.Listbox(
            list_frame, 
            height=6,
            font=self.main_window.fonts['small'],
            bg=self.main_window.colors['bg_secondary'],
            fg=self.main_window.colors['text_primary'],
            selectbackground=self.main_window.colors['accent'],
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=list_scroll.set
        )
        self.drop_listbox.pack(fill='both', expand=True, side='left')
        list_scroll.config(command=self.drop_listbox.yview)
        
        # 리스트박스 이벤트
        self.drop_listbox.bind('<Motion>', self._on_listbox_motion)
        self.drop_listbox.bind('<Leave>', self._hide_tooltip)
        
        # 드래그로 순서 변경 (선택사항 - 복잡도가 높음)
        # self._setup_list_drag()
    
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
        self.context_menu.add_command(label="보고서 보기", command=self._view_report)
        self.context_menu.add_command(label="폴더에서 보기", command=self._show_in_folder)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="다시 처리", command=self._reprocess_file)
        
        self.realtime_tree.bind('<Button-3>', self._show_context_menu)
    
    def _bind_shortcuts(self):
        """단축키 바인딩"""
        # F5: 새로고침
        self.main_window.root.bind('<F5>', lambda e: self.refresh())
        
        # Ctrl+O: 파일 열기
        self.main_window.root.bind('<Control-o>', lambda e: self.browse_files())
        
        # Ctrl+D: 폴더 추가
        self.main_window.root.bind('<Control-d>', lambda e: self.main_window.add_watch_folder())
        
        # Ctrl+R: 선택 파일 재처리
        self.main_window.root.bind('<Control-r>', lambda e: self._reprocess_file())
        
        # Delete: 선택 항목 삭제
        self.realtime_tree.bind('<Delete>', self._delete_selected)
    
    def _setup_drag_drop(self):
        """드래그앤드롭 설정"""
        def drop_enter(event):
            """드래그 진입 시"""
            self.drop_frame.configure(border_color=self.main_window.colors['accent'])
            self.drop_label.configure(
                text="파일을 놓으세요!", 
                text_color=self.main_window.colors['accent']
            )
            return event.action
            
        def drop_leave(event):
            """드래그 떠날 시"""
            self.drop_frame.configure(border_color=self.main_window.colors['border'])
            self.drop_label.configure(
                text="PDF 파일을 드래그하거나\n클릭하여 선택",
                text_color=self.main_window.colors['text_secondary']
            )
            return event.action
            
        def drop_files(event):
            """파일 드롭 시"""
            files = self._parse_drop_files(event.data)
            pdf_files = [f for f in files if f.lower().endswith('.pdf')]
            
            if pdf_files:
                self.main_window.dropped_files = pdf_files
                for file in pdf_files:
                    self.drop_listbox.insert(tk.END, Path(file).name)
                self._update_queue_count()
                self.main_window.logger.log(f"드래그앤드롭으로 {len(pdf_files)}개 파일 추가")
            else:
                messagebox.showwarning("경고", "PDF 파일만 추가할 수 있습니다.")
                
            drop_leave(event)
            return event.action
        
        # 드래그앤드롭 이벤트 바인딩
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<DropEnter>>', drop_enter)
        self.drop_frame.dnd_bind('<<DropLeave>>', drop_leave)
        self.drop_frame.dnd_bind('<<Drop>>', drop_files)
    
    def _parse_drop_files(self, data):
        """드롭된 파일 경로 파싱"""
        files = []
        if data.startswith('{') and data.endswith('}'):
            data = data[1:-1]
            files = data.split('} {')
        else:
            files = data.split()
        
        cleaned_files = []
        for f in files:
            f = f.strip()
            if f:
                if (f.startswith('"') and f.endswith('"')) or (f.startswith("'") and f.endswith("'")):
                    f = f[1:-1]
                cleaned_files.append(f)
        
        return cleaned_files
    
    def add_file_to_process(self, file_path: Path, folder_config: dict):
        """폴더에서 발견된 파일 추가"""
        self.main_window.logger.log(f"PDF 발견: {file_path.name} (폴더: {file_path.parent.name})")
        
        # 안전한 item ID 생성
        item_id = self.main_window._generate_safe_item_id("folder")
        
        # 처리 시작 시간 기록
        self.processing_times[item_id] = {
            'start': time.time(),
            'status': 'waiting'
        }
        
        # 시간 포맷
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # 상태와 시간을 합쳐서 표시
        status_time = f"대기 중 ({current_time})"
        
        # 실시간 탭에 추가
        self.realtime_tree.insert(
            '',
            'end',
            iid=item_id,
            text=file_path.name,
            values=(
                self.STATUS_ICONS['waiting'],  # 아이콘
                file_path.parent.name,
                status_time,
                '-',  # 페이지수
                '-',  # 페이지 크기
                '-'   # 문제
            ),
            tags=('processing',)
        )
        
        # 처리 시작
        self._process_pdf_file(file_path, folder_config, item_id)
    
    def _format_file_size(self, size_bytes):
        """파일 크기를 읽기 쉬운 형식으로 변환"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _get_page_size_info(self, pages_info):
        """페이지 크기 정보 분석"""
        if not pages_info:
            return "알 수 없음"
        
        # 모든 페이지의 크기 수집
        size_map = {}
        for page in pages_info:
            size_key = page['paper_size']
            if size_key not in size_map:
                size_map[size_key] = {
                    'count': 0,
                    'size_str': page['size_formatted'],
                    'pages': []
                }
            size_map[size_key]['count'] += 1
            size_map[size_key]['pages'].append(page['page_number'])
        
        # 결과 포맷팅
        if len(size_map) == 1:
            # 모든 페이지가 같은 크기
            paper_size = list(size_map.keys())[0]
            size_info = list(size_map.values())[0]
            return f"{paper_size} ({size_info['size_str']})"
        else:
            # 여러 크기 혼합
            sizes = []
            for paper_size, info in size_map.items():
                sizes.append(f"{paper_size}({info['count']}p)")
            return f"혼합: {', '.join(sizes[:3])}"
    
    def _start_processing_timer(self, item_id):
        """처리 시간 타이머 시작"""
        def update_timer():
            while item_id in self.processing_times and self.processing_times[item_id]['status'] == 'processing':
                elapsed = time.time() - self.processing_times[item_id]['start']
                elapsed_str = f"{int(elapsed)}초"
                
                try:
                    self.realtime_tree.item(
                        item_id,
                        values=(
                            self.STATUS_ICONS['processing'],
                            self.realtime_tree.item(item_id)['values'][1],
                            f"처리 중... ({elapsed_str})",
                            self.realtime_tree.item(item_id)['values'][3],
                            self.realtime_tree.item(item_id)['values'][4],
                            self.realtime_tree.item(item_id)['values'][5]
                        )
                    )
                except:
                    break
                
                time.sleep(1)
        
        timer_thread = threading.Thread(target=update_timer, daemon=True)
        timer_thread.start()
        self.timer_threads[item_id] = timer_thread
    
    def _process_pdf_file(self, file_path: Path, folder_config: dict, tree_item_id: str):
        """PDF 파일 처리"""
        def process():
            try:
                # 처리 상태 업데이트
                self.processing_times[tree_item_id]['status'] = 'processing'
                self._start_processing_timer(tree_item_id)
                
                # 시간 포맷
                current_time = datetime.now().strftime('%H:%M:%S')
                
                # 상태 업데이트: 처리 중
                self.realtime_tree.item(
                    tree_item_id,
                    values=(
                        self.STATUS_ICONS['processing'],
                        file_path.parent.name,
                        f"처리 중... (0초)",
                        '-',
                        '-',
                        '-'
                    )
                )
                
                # 잉크량 분석 옵션 확인
                include_ink = folder_config.get('auto_fix_settings', {}).get(
                    'include_ink_analysis', 
                    Config.is_ink_analysis_enabled()
                )
                
                # PDF 분석
                analyzer = PDFAnalyzer()
                result = analyzer.analyze(
                    str(file_path),
                    include_ink_analysis=include_ink,
                    preflight_profile=folder_config.get('profile', 'offset')
                )
                
                # 분석 결과 저장
                self.pdf_results[tree_item_id] = result
                
                # 데이터베이스에 저장
                try:
                    self.main_window.data_manager.save_analysis_result(result)
                    self.main_window.logger.log(f"데이터베이스 저장 완료: {file_path.name}")
                except Exception as e:
                    self.main_window.logger.error(f"데이터베이스 저장 실패: {e}")
                
                # 드래그앤드롭과 폴더 감시 구분
                is_folder_watch = folder_config.get('path') is not None
                
                # 리포트 저장 경로 결정
                output_base = file_path.parent
                reports_folder = output_base / 'reports'
                reports_folder.mkdir(exist_ok=True)
                
                if not is_folder_watch:
                    self.main_window.logger.log(f"드래그앤드롭 리포트 폴더 생성: {reports_folder}")
                
                # 보고서 생성
                generator = ReportGenerator()
                report_filename = f"{file_path.stem}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # 텍스트 보고서 저장
                text_path = generator.save_text_report(
                    result, 
                    output_path=reports_folder / f"{report_filename}.txt"
                )
                
                # HTML 보고서 저장
                html_path = generator.save_html_report(
                    result,
                    output_path=reports_folder / f"{report_filename}.html"
                )
                
                self.main_window.logger.log(f"리포트 생성 완료: {reports_folder}")
                
                # 결과에 따라 파일 이동 (폴더 감시인 경우만)
                issues = result.get('issues', [])
                error_count = sum(1 for i in issues if i['severity'] == 'error')
                warning_count = sum(1 for i in issues if i['severity'] == 'warning')
                
                # 페이지수와 파일 크기 추출
                page_count = result.get('basic_info', {}).get('page_count', 0)
                file_size = result.get('file_size', 0)
                file_size_formatted = result.get('file_size_formatted', '-')
                
                # 페이지 크기 정보
                pages_info = result.get('pages', [])
                page_size_info = self._get_page_size_info(pages_info)
                
                # 처리 소요 시간 계산
                processing_time = time.time() - self.processing_times[tree_item_id]['start']
                processing_time_str = f"{processing_time:.1f}초"
                
                # 파일 이동 처리
                if is_folder_watch:
                    if error_count > 0:
                        dest_folder = output_base / 'errors'
                        status = 'error'
                        status_text = '오류'
                        icon = self.STATUS_ICONS['error']
                    elif warning_count > 0:
                        dest_folder = output_base / 'completed'
                        status = 'warning'
                        status_text = '경고'
                        icon = self.STATUS_ICONS['warning']
                    else:
                        dest_folder = output_base / 'completed'
                        status = 'success'
                        status_text = '완료'
                        icon = self.STATUS_ICONS['success']
                    
                    # 파일 이동
                    try:
                        dest_folder.mkdir(exist_ok=True)
                        dest_path = dest_folder / file_path.name
                        shutil.move(str(file_path), str(dest_path))
                        self.main_window.logger.log(f"파일 이동: {file_path.name} → {dest_folder.name}")
                    except Exception as e:
                        self.main_window.logger.error(f"파일 이동 실패: {e}")
                else:
                    # 드래그앤드롭의 경우
                    if error_count > 0:
                        status = 'error'
                        status_text = '오류'
                        icon = self.STATUS_ICONS['error']
                    elif warning_count > 0:
                        status = 'warning'
                        status_text = '경고'
                        icon = self.STATUS_ICONS['warning']
                    else:
                        status = 'success'
                        status_text = '완료'
                        icon = self.STATUS_ICONS['success']
                
                # 완료 시간
                complete_time = datetime.now().strftime('%H:%M:%S')
                
                # 처리 상태 업데이트
                self.processing_times[tree_item_id]['status'] = 'completed'
                
                # UI 업데이트
                self.realtime_tree.item(
                    tree_item_id,
                    values=(
                        icon,
                        file_path.parent.name,
                        f"{status_text} ({complete_time}, {processing_time_str})",
                        f"{page_count}p",
                        page_size_info,
                        f"오류:{error_count} 경고:{warning_count}"
                    ),
                    tags=(status,)
                )
                
                # 알림
                self.main_window.notification_manager.notify_success(
                    file_path.name,
                    len(issues),
                    page_count=page_count,
                    processing_time=processing_time
                )
                
                # 통계 업데이트
                self.main_window.sidebar.update_quick_stats()
                
            except Exception as e:
                self.main_window.logger.error(f"처리 오류: {e}")
                error_time = datetime.now().strftime('%H:%M:%S')
                
                # 처리 상태 업데이트
                if tree_item_id in self.processing_times:
                    self.processing_times[tree_item_id]['status'] = 'error'
                
                # 오류 시에도 상태와 시간 통합
                self.realtime_tree.item(
                    tree_item_id,
                    values=(
                        self.STATUS_ICONS['error'],
                        file_path.parent.name,
                        f"오류 ({error_time})",
                        '-',
                        '-',
                        str(e)[:50]
                    ),
                    tags=('error',)
                )
                
                # 오류 알림
                self.main_window.notification_manager.notify_error(file_path.name, str(e))
        
        # 별도 스레드에서 처리
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def browse_files(self):
        """파일 선택 (단축키: Ctrl+O)"""
        files = filedialog.askopenfilenames(
            title="PDF 파일 선택",
            filetypes=[("PDF 파일", "*.pdf"), ("모든 파일", "*.*")]
        )
        
        if files:
            # 파일 추가
            for file in files:
                self.drop_listbox.insert(tk.END, Path(file).name)
                
            self.main_window.dropped_files = list(files)
            self._update_queue_count()
    
    def browse_folder(self):
        """폴더 선택"""
        folder = filedialog.askdirectory(title="폴더 선택")
        
        if folder:
            pdf_files = list(Path(folder).glob("**/*.pdf"))
            if pdf_files:
                # 파일 추가
                for pdf in pdf_files:
                    self.drop_listbox.insert(tk.END, pdf.name)
                
                self.main_window.dropped_files = [str(f) for f in pdf_files]
                self._update_queue_count()
                
                self.main_window.statusbar.set_status(f"{len(pdf_files)}개 PDF 파일이 추가되었습니다.")
    
    def _process_dropped_files(self):
        """드롭된 파일들 처리"""
        if not self.main_window.dropped_files:
            messagebox.showinfo("정보", "처리할 파일이 없습니다.")
            return
        
        profile = self.drop_profile_var.get()
        auto_fix = self.drop_auto_fix_var.get()
        include_ink = self.drop_ink_analysis_var.get()
        
        # 처리 스레드 시작
        def process_all():
            for file_path in self.main_window.dropped_files:
                folder_config = {
                    'profile': profile,
                    'auto_fix_settings': {
                        'auto_convert_rgb': auto_fix,
                        'auto_outline_fonts': auto_fix,
                        'include_ink_analysis': include_ink
                    }
                }
                
                # 안전한 tree item ID 생성
                item_id = self.main_window._generate_safe_item_id("drop")
                
                # 처리 시작 시간 기록
                self.processing_times[item_id] = {
                    'start': time.time(),
                    'status': 'waiting'
                }
                
                # 시간 포맷
                current_time = datetime.now().strftime('%H:%M:%S')
                
                # 실시간 탭에 추가
                self.main_window.root.after(0, lambda fp=file_path, iid=item_id, ct=current_time: self.realtime_tree.insert(
                    '',
                    'end',
                    iid=iid,
                    text=Path(fp).name,
                    values=(
                        self.STATUS_ICONS['waiting'],
                        '드래그앤드롭',
                        f"대기 중 ({ct})",
                        '-',
                        '-',
                        '-'
                    ),
                    tags=('processing',)
                ))
                
                # 처리
                self._process_pdf_file(Path(file_path), folder_config, item_id)
            
            # 완료 후 목록 비우기
            self.main_window.root.after(0, self._clear_drop_list)
        
        thread = threading.Thread(target=process_all, daemon=True)
        thread.start()
        
        self.main_window.statusbar.set_status(f"{len(self.main_window.dropped_files)}개 파일 처리를 시작합니다.")
    
    def _clear_drop_list(self):
        """드롭 목록 비우기"""
        self.drop_listbox.delete(0, tk.END)
        self.main_window.dropped_files = []
        self._update_queue_count()
    
    def _update_queue_count(self):
        """대기 목록 개수 업데이트"""
        count = self.drop_listbox.size()
        self.queue_count_label.configure(text=f"({count}개)")
    
    def refresh(self):
        """탭 새로고침 (단축키: F5)"""
        # 필터 초기화
        self.filter_status.set("all")
        self.search_var.set("")
        self.apply_filter("all")
        
        self.main_window.statusbar.set_status("실시간 현황이 새로고침되었습니다.")
    
    def apply_filter(self, status):
        """상태별 필터 적용"""
        self.filter_status.set(status)
        self._update_tree_view()
    
    def apply_search(self):
        """검색 필터 적용"""
        self._update_tree_view()
    
    def _update_tree_view(self):
        """트리뷰 업데이트 (필터링 적용)"""
        # 모든 항목 가져오기
        all_items = self.realtime_tree.get_children()
        
        # 검색어
        search_text = self.search_var.get().lower()
        
        # 필터 상태
        filter_status = self.filter_status.get()
        
        for item_id in all_items:
            item = self.realtime_tree.item(item_id)
            filename = item['text'].lower()
            tags = item['tags']
            
            # 검색어 체크
            show = True
            if search_text and search_text not in filename:
                show = False
            
            # 상태 필터 체크
            if show and filter_status != "all":
                if filter_status not in tags:
                    show = False
            
            # 표시/숨김
            if show:
                self.realtime_tree.reattach(item_id, '', 'end')
            else:
                self.realtime_tree.detach(item_id)
    
    def toggle_theme(self):
        """테마 전환 (다크/라이트)"""
        if self.current_theme == 'dark':
            self.current_theme = 'light'
            ctk.set_appearance_mode("light")
            self.theme_btn.configure(text="☀️")
            
            # 라이트 모드 색상
            self.main_window.colors = {
                'bg_primary': '#f0f0f0',
                'bg_secondary': '#ffffff',
                'bg_card': '#ffffff',
                'accent': '#0078d4',
                'accent_hover': '#106ebe',
                'success': '#107c10',
                'warning': '#ff8c00',
                'error': '#d83b01',
                'text_primary': '#323130',
                'text_secondary': '#605e5c',
                'border': '#e1dfdd'
            }
        else:
            self.current_theme = 'dark'
            ctk.set_appearance_mode("dark")
            self.theme_btn.configure(text="🌙")
            
            # 다크 모드 색상
            self.main_window.colors = {
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
        
        # 설정 저장
        try:
            with open('user_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except:
            settings = {}
        
        settings['theme'] = self.current_theme
        
        with open('user_settings.json', 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        messagebox.showinfo("테마 변경", f"{self.current_theme.title()} 모드로 변경되었습니다.\n완전히 적용하려면 프로그램을 재시작하세요.")
    
    def _show_context_menu(self, event):
        """우클릭 메뉴 표시"""
        item = self.realtime_tree.identify_row(event.y)
        if item:
            self.realtime_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _view_report(self):
        """보고서 보기"""
        selection = self.realtime_tree.selection()
        if not selection:
            return
            
        item = self.realtime_tree.item(selection[0])
        filename = item['text']
        folder_name = item['values'][1]  # 인덱스 조정 (아이콘 때문에)
        
        # 파일이 원래 있던 폴더에서 reports 폴더 찾기
        for config in self.main_window.folder_watcher.folder_configs.values():
            if hasattr(config, 'path') and config.path.name == folder_name:
                reports_path = config.path / "reports"
                break
        else:
            # 드래그앤드롭의 경우
            possible_paths = []
            for dropped_file in self.main_window.dropped_files:
                parent_path = Path(dropped_file).parent / "reports"
                if parent_path not in possible_paths:
                    possible_paths.append(parent_path)
            
            # 가능한 경로들에서 보고서 찾기
            for path in possible_paths:
                if path.exists():
                    for report_file in path.glob(f"*{Path(filename).stem}*.html"):
                        webbrowser.open(str(report_file))
                        return
        
        # reports 폴더에서 보고서 찾기
        if 'reports_path' in locals() and reports_path.exists():
            for report_file in reports_path.glob(f"*{Path(filename).stem}*.html"):
                webbrowser.open(str(report_file))
                return
        
        messagebox.showinfo("정보", "보고서를 찾을 수 없습니다.")
    
    def _show_in_folder(self):
        """폴더에서 보기"""
        selection = self.realtime_tree.selection()
        if not selection:
            return
            
        item = self.realtime_tree.item(selection[0])
        folder_name = item['values'][1]  # 인덱스 조정
        
        # 폴더 열기
        if folder_name == '드래그앤드롭':
            messagebox.showinfo("정보", "드래그앤드롭으로 추가된 파일입니다.")
        else:
            for config in self.main_window.folder_watcher.folder_configs.values():
                if hasattr(config, 'path') and config.path.name == folder_name:
                    try:
                        os.startfile(str(config.path))
                    except:
                        pass
                    break
    
    def _reprocess_file(self):
        """파일 다시 처리 (단축키: Ctrl+R)"""
        selection = self.realtime_tree.selection()
        if not selection:
            messagebox.showinfo("정보", "재처리할 파일을 선택하세요.")
            return
        
        messagebox.showinfo("정보", "재처리 기능은 개발 중입니다.")
    
    def _delete_selected(self, event):
        """선택 항목 삭제 (Delete 키)"""
        selection = self.realtime_tree.selection()
        if selection:
            if messagebox.askyesno("확인", "선택한 항목을 목록에서 제거하시겠습니까?"):
                for item in selection:
                    # 타이머 정리
                    if item in self.processing_times:
                        del self.processing_times[item]
                    if item in self.timer_threads:
                        del self.timer_threads[item]
                    
                    self.realtime_tree.delete(item)
    
    def _on_listbox_motion(self, event):
        """리스트박스 마우스 이동 이벤트 (툴팁용)"""
        # 마우스 위치의 항목 찾기
        index = self.drop_listbox.nearest(event.y)
        
        if index >= 0:
            # 파일 경로 가져오기
            try:
                if index < len(self.main_window.dropped_files):
                    file_path = Path(self.main_window.dropped_files[index])
                    
                    # 파일 정보
                    file_size = file_path.stat().st_size
                    file_size_str = self._format_file_size(file_size)
                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                    
                    # 툴팁 표시
                    tooltip_text = f"크기: {file_size_str}\n수정일: {mod_time}\n경로: {file_path.parent}"
                    self._show_tooltip(event, tooltip_text)
            except:
                self._hide_tooltip()
    
    def _show_tooltip(self, event, text):
        """툴팁 표시"""
        # 기존 툴팁 제거
        self._hide_tooltip()
        
        # 새 툴팁 생성
        tooltip = tk.Toplevel()
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        
        label = tk.Label(
            tooltip, 
            text=text,
            background="lightyellow",
            relief="solid",
            borderwidth=1,
            font=self.main_window.fonts['small']
        )
        label.pack()
        
        self.tooltips['current'] = tooltip
    
    def _hide_tooltip(self, event=None):
        """툴팁 숨기기"""
        if 'current' in self.tooltips:
            try:
                self.tooltips['current'].destroy()
            except:
                pass
            del self.tooltips['current']