# gui/components/sidebar.py
"""
사이드바 컴포넌트
폴더 목록, 감시 상태, 빠른 통계를 표시합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from pathlib import Path
from datetime import datetime, timedelta


class Sidebar:
    """사이드바 컴포넌트 클래스"""
    
    def __init__(self, main_window, parent):
        """
        사이드바 초기화
        
        Args:
            main_window: 메인 윈도우 인스턴스 (EnhancedPDFCheckerGUI)
            parent: 부모 위젯
        """
        self.main_window = main_window
        self.parent = parent
        
        # 사이드바 생성
        self._create_sidebar()
    
    def _create_sidebar(self):
        """사이드바 생성"""
        # 사이드바 프레임
        self.sidebar = ctk.CTkFrame(
            self.parent, 
            width=300, 
            corner_radius=0, 
            fg_color=self.main_window.colors['bg_secondary']
        )
        self.sidebar.pack(side='left', fill='y', padx=(0, 1))
        self.sidebar.pack_propagate(False)
        
        # 로고/타이틀
        self._create_title_section()
        
        # 구분선
        self._create_separator()
        
        # 폴더 목록 섹션
        self._create_folder_section()
        
        # 감시 상태 카드
        self._create_watch_status_card()
        
        # 구분선
        self._create_separator()
        
        # 빠른 통계 카드
        self._create_quick_stats_card()
        
        # 초기 폴더 목록 업데이트
        self.update_folder_list()
    
    def _create_title_section(self):
        """타이틀 섹션 생성"""
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.pack(fill='x', padx=20, pady=(25, 20))
        
        logo_label = ctk.CTkLabel(title_frame, text="📊", font=('Arial', 36))
        logo_label.pack(side='left', padx=(0, 15))
        
        title_info = ctk.CTkFrame(title_frame, fg_color="transparent")
        title_info.pack(side='left', fill='both', expand=True)
        
        title_label = ctk.CTkLabel(
            title_info, 
            text="PDF 검수 시스템", 
            font=self.main_window.fonts['heading'],
            text_color=self.main_window.colors['text_primary']
        )
        title_label.pack(anchor='w')
        
        version_label = ctk.CTkLabel(
            title_info, 
            text="v4.0 Modularized", 
            font=self.main_window.fonts['small'],
            text_color=self.main_window.colors['text_secondary']
        )
        version_label.pack(anchor='w')
    
    def _create_separator(self):
        """구분선 생성"""
        ctk.CTkFrame(
            self.sidebar, 
            height=2, 
            fg_color=self.main_window.colors['border']
        ).pack(fill='x', padx=20, pady=10)
    
    def _create_folder_section(self):
        """폴더 목록 섹션 생성"""
        folder_section = ctk.CTkFrame(
            self.sidebar, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10
        )
        folder_section.pack(fill='both', expand=True, padx=15, pady=10)
        
        # 섹션 헤더
        header_frame = ctk.CTkFrame(folder_section, fg_color="transparent")
        header_frame.pack(fill='x', padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header_frame, 
            text="📁 감시 폴더", 
            font=self.main_window.fonts['subheading']
        ).pack(side='left')
        
        # 폴더 목록
        list_frame = ctk.CTkFrame(folder_section, fg_color="transparent")
        list_frame.pack(fill='both', expand=True, padx=15)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')
        
        self.folder_listbox = tk.Listbox(
            list_frame, 
            height=8, 
            selectmode='single',
            font=self.main_window.fonts['body'],
            bg=self.main_window.colors['bg_secondary'],
            fg=self.main_window.colors['text_primary'],
            selectbackground=self.main_window.colors['accent'],
            selectforeground='white',
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=scrollbar.set
        )
        self.folder_listbox.pack(fill='both', expand=True, side='left')
        scrollbar.config(command=self.folder_listbox.yview)
        
        # 폴더 버튼들
        self._create_folder_buttons(folder_section)
    
    def _create_folder_buttons(self, parent):
        """폴더 관리 버튼들 생성"""
        folder_buttons = ctk.CTkFrame(parent, fg_color="transparent")
        folder_buttons.pack(fill='x', padx=15, pady=(10, 15))
        
        btn_config = {'width': 70, 'height': 32, 'corner_radius': 6}
        
        ctk.CTkButton(
            folder_buttons, 
            text="➕ 추가", 
            command=self.main_window.add_watch_folder,
            **btn_config
        ).pack(side='left', padx=3)
        
        ctk.CTkButton(
            folder_buttons, 
            text="➖ 제거", 
            command=self.main_window.remove_watch_folder,
            fg_color=self.main_window.colors['bg_secondary'],
            hover_color=self.main_window.colors['error'],
            **btn_config
        ).pack(side='left', padx=3)
        
        ctk.CTkButton(
            folder_buttons, 
            text="⚙️ 설정", 
            command=self.main_window.edit_folder_settings,
            fg_color=self.main_window.colors['bg_secondary'],
            hover_color=self.main_window.colors['accent'],
            **btn_config
        ).pack(side='left', padx=3)
    
    def _create_watch_status_card(self):
        """감시 상태 카드 생성"""
        status_card = ctk.CTkFrame(
            self.sidebar, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10
        )
        status_card.pack(fill='x', padx=15, pady=10)
        
        status_inner = ctk.CTkFrame(status_card, fg_color="transparent")
        status_inner.pack(fill='x', padx=15, pady=15)
        
        status_header = ctk.CTkFrame(status_inner, fg_color="transparent")
        status_header.pack(fill='x')
        
        self.watch_status_label = ctk.CTkLabel(
            status_header,
            text="⏸️ 감시 중지됨",
            font=self.main_window.fonts['subheading']
        )
        self.watch_status_label.pack(side='left')
        
        self.watch_toggle_switch = ctk.CTkSwitch(
            status_header,
            text="",
            command=self.main_window.toggle_folder_watching,
            button_color=self.main_window.colors['accent'],
            progress_color=self.main_window.colors['success'],
            width=50,
            height=24
        )
        self.watch_toggle_switch.pack(side='right')
    
    def _create_quick_stats_card(self):
        """빠른 통계 카드 생성"""
        stats_card = ctk.CTkFrame(
            self.sidebar, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10
        )
        stats_card.pack(fill='x', padx=15, pady=(5, 20))
        
        stats_inner = ctk.CTkFrame(stats_card, fg_color="transparent")
        stats_inner.pack(fill='x', padx=15, pady=15)
        
        stats_title = ctk.CTkLabel(
            stats_inner, 
            text="📊 오늘의 통계", 
            font=self.main_window.fonts['subheading']
        )
        stats_title.pack(anchor='w', pady=(0, 15))
        
        self.quick_stats_labels = {}
        stats_items = [
            ('files', '처리 파일', '0개', self.main_window.colors['accent']),
            ('errors', '오류', '0개', self.main_window.colors['error']),
            ('fixed', '자동 수정', '0개', self.main_window.colors['success'])
        ]
        
        for key, label, default, color in stats_items:
            stat_frame = ctk.CTkFrame(stats_inner, fg_color="transparent")
            stat_frame.pack(fill='x', pady=4)
            
            label_widget = ctk.CTkLabel(
                stat_frame, 
                text=f"{label}:",
                font=self.main_window.fonts['body'],
                text_color=self.main_window.colors['text_secondary']
            )
            label_widget.pack(side='left')
            
            value_widget = ctk.CTkLabel(
                stat_frame, 
                text=default,
                font=self.main_window.fonts['subheading'],
                text_color=color
            )
            value_widget.pack(side='right')
            
            self.quick_stats_labels[key] = value_widget
    
    def update_folder_list(self):
        """폴더 목록 업데이트"""
        self.folder_listbox.delete(0, tk.END)
        
        for folder in self.main_window.folder_watcher.get_folder_list():
            status = "✓" if folder['enabled'] else "✗"
            ink = "🎨" if folder.get('auto_fix_settings', {}).get('include_ink_analysis', False) else ""
            text = f"{status} {folder['name']} ({folder['profile']}) {ink}"
            self.folder_listbox.insert(tk.END, text)
    
    def update_quick_stats(self):
        """빠른 통계 업데이트"""
        try:
            # 오늘의 통계
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            stats = self.main_window.data_manager.get_statistics(date_range=(today, tomorrow))
            
            self.quick_stats_labels['files'].configure(
                text=f"{stats['basic']['total_files']}개"
            )
            self.quick_stats_labels['errors'].configure(
                text=f"{stats['basic']['total_errors']}개"
            )
            self.quick_stats_labels['fixed'].configure(
                text=f"{stats['basic']['auto_fixed_count']}개"
            )
        except Exception as e:
            self.main_window.logger.error(f"통계 업데이트 오류: {e}")
    
    def update_watch_status(self, is_watching):
        """감시 상태 업데이트"""
        if is_watching:
            self.watch_status_label.configure(text="🟢 감시 중")
            self.watch_toggle_switch.select()
        else:
            self.watch_status_label.configure(text="⏸️ 감시 중지됨")
            self.watch_toggle_switch.deselect()
    
    def get_selected_folder(self):
        """선택된 폴더 정보 가져오기"""
        selection = self.folder_listbox.curselection()
        if selection:
            folder_list = self.main_window.folder_watcher.get_folder_list()
            return folder_list[selection[0]]
        return None
    
    def remove_selected_folder(self):
        """선택된 폴더 제거"""
        folder_info = self.get_selected_folder()
        if not folder_info:
            messagebox.showinfo("정보", "제거할 폴더를 선택하세요.")
            return
        
        # 확인
        if messagebox.askyesno("확인", f"'{folder_info['name']}' 폴더를 제거하시겠습니까?"):
            if self.main_window.folder_watcher.remove_folder(folder_info['path']):
                self.update_folder_list()
                self.main_window.logger.log(f"감시 폴더 제거: {folder_info['name']}")