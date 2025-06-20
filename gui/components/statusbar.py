# gui/components/statusbar.py
"""
상태바 컴포넌트
프로그램 상태, 감시 상태, 파일 수, 시계 등을 표시합니다.
"""

import tkinter as tk
import customtkinter as ctk
from datetime import datetime


class Statusbar:
    """상태바 컴포넌트 클래스"""
    
    def __init__(self, main_window):
        """
        상태바 초기화
        
        Args:
            main_window: 메인 윈도우 인스턴스
        """
        self.main_window = main_window
        self._create_statusbar()
        self._update_time()
    
    def _create_statusbar(self):
        """상태바 생성"""
        statusbar = ctk.CTkFrame(
            self.main_window.root, 
            height=30, 
            corner_radius=0,
            fg_color=self.main_window.colors['bg_secondary']
        )
        statusbar.pack(side='bottom', fill='x')
        
        # 상태바 내용
        status_content = ctk.CTkFrame(statusbar, fg_color="transparent")
        status_content.pack(fill='x', expand=True)
        
        # 상태 텍스트
        self.status_var = tk.StringVar()
        self.status_var.set("준비됨")
        self.status_label = ctk.CTkLabel(
            status_content, 
            textvariable=self.status_var,
            font=self.main_window.fonts['small']
        )
        self.status_label.pack(side='left', padx=20)
        
        # 감시 상태
        self.watch_status_var = tk.StringVar()
        self.watch_status_var.set("감시: 중지")
        self.watch_label = ctk.CTkLabel(
            status_content, 
            textvariable=self.watch_status_var,
            font=self.main_window.fonts['small']
        )
        self.watch_label.pack(side='left', padx=20)
        
        # 파일 수
        self.file_count_var = tk.StringVar()
        self.file_count_var.set("처리: 0개")
        self.count_label = ctk.CTkLabel(
            status_content, 
            textvariable=self.file_count_var,
            font=self.main_window.fonts['small']
        )
        self.count_label.pack(side='right', padx=20)
        
        # 시계
        self.time_label = ctk.CTkLabel(
            status_content, 
            text="",
            font=self.main_window.fonts['small']
        )
        self.time_label.pack(side='right', padx=20)
    
    def _update_time(self):
        """시계 업데이트"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.time_label.configure(text=current_time)
        self.main_window.root.after(1000, self._update_time)
    
    def set_status(self, message):
        """상태 메시지 설정"""
        self.status_var.set(message)
    
    def update_watch_status(self, status):
        """감시 상태 업데이트"""
        self.watch_status_var.set(status)
    
    def update_file_count(self, count):
        """파일 수 업데이트"""
        self.file_count_var.set(f"처리: {count}개")