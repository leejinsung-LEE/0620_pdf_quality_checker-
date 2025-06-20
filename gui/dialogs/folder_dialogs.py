# gui/dialogs/folder_dialogs.py
"""
폴더 대화상자 - 개선된 버전
폴더 추가, 편집 등의 대화상자를 관리합니다.
개선사항: 창 크기 증가, 중앙 배치, 최소 크기 설정
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from pathlib import Path
import os

from config import Config


class FolderDialogs:
    """폴더 관련 대화상자 클래스"""
    
    def __init__(self, main_window):
        """
        초기화
        
        Args:
            main_window: 메인 윈도우 인스턴스
        """
        self.main_window = main_window
    
    def _center_window(self, window, width=700, height=750):
        """창을 화면 중앙에 배치"""
        window.update_idletasks()
        
        # 화면 크기 가져오기
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # 중앙 위치 계산
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        # 위치와 크기 설정
        window.geometry(f'{width}x{height}+{x}+{y}')
        window.minsize(width - 100, height - 100)  # 최소 크기 설정
    
    def show_add_folder_dialog(self):
        """감시 폴더 추가 대화상자"""
        dialog = ctk.CTkToplevel(self.main_window.root)
        dialog.title("감시 폴더 추가")
        dialog.transient(self.main_window.root)
        dialog.grab_set()
        
        # 창 크기와 위치 설정
        self._center_window(dialog, 700, 750)
        
        # 메인 스크롤 프레임
        main_scroll_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        main_scroll_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 메인 프레임
        main_frame = ctk.CTkFrame(main_scroll_frame, fg_color="transparent")
        main_frame.pack(fill='both', expand=True)
        
        # 제목
        title_label = ctk.CTkLabel(
            main_frame,
            text="새 감시 폴더 추가",
            font=self.main_window.fonts['heading']
        )
        title_label.pack(pady=(0, 20))
        
        # 폴더 선택
        folder_var = self._create_folder_selector(main_frame, "📁 폴더 선택")
        
        # 프로파일 선택
        profile_var = self._create_profile_selector(main_frame, "🎯 프리플라이트 프로파일")
        
        # 처리 옵션
        fix_options = self._create_processing_options(main_frame, "⚙️ 처리 옵션")
        
        # 출력 폴더
        output_var = self._create_output_folder_selector(main_frame)
        
        # 버튼 프레임 (스크롤 영역 밖에 고정)
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self._create_dialog_buttons(
            button_frame, 
            dialog,
            lambda: self._add_folder(dialog, folder_var, profile_var, fix_options, output_var)
        )
    
    def show_edit_folder_dialog(self):
        """폴더 설정 편집 대화상자"""
        # 선택한 폴더 정보 가져오기
        folder_info = self.main_window.sidebar.get_selected_folder()
        if not folder_info:
            messagebox.showinfo("정보", "편집할 폴더를 선택하세요.")
            return
        
        folder_path = folder_info['path']
        
        # 편집 대화상자
        dialog = ctk.CTkToplevel(self.main_window.root)
        dialog.title("폴더 설정 편집")
        dialog.transient(self.main_window.root)
        dialog.grab_set()
        
        # 창 크기와 위치 설정
        self._center_window(dialog, 700, 800)
        
        # 메인 스크롤 프레임
        main_scroll_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        main_scroll_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 메인 프레임
        main_frame = ctk.CTkFrame(main_scroll_frame, fg_color="transparent")
        main_frame.pack(fill='both', expand=True)
        
        # 제목
        title_label = ctk.CTkLabel(
            main_frame,
            text="폴더 설정 편집",
            font=self.main_window.fonts['heading']
        )
        title_label.pack(pady=(0, 20))
        
        # 폴더 정보 표시
        self._create_folder_info(main_frame, folder_info)
        
        # 프로파일 선택
        profile_var = self._create_profile_selector(
            main_frame, 
            "🎯 프리플라이트 프로파일",
            current_value=folder_info['profile']
        )
        
        # 처리 옵션
        folder_config = self.main_window.folder_watcher.folder_configs.get(folder_path, {})
        current_settings = folder_config.auto_fix_settings if hasattr(folder_config, 'auto_fix_settings') else {}
        
        fix_options = self._create_processing_options(
            main_frame, 
            "⚙️ 처리 옵션",
            current_settings=current_settings
        )
        
        # 활성화 옵션
        enabled_var = tk.BooleanVar(value=folder_info['enabled'])
        enabled_check = ctk.CTkCheckBox(
            main_frame,
            text="이 폴더 감시 활성화",
            variable=enabled_var,
            font=self.main_window.fonts['body']
        )
        enabled_check.pack(anchor='w', pady=20)
        
        # 버튼 프레임 (스크롤 영역 밖에 고정)
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # 폴더 열기 버튼
        def open_folder():
            try:
                os.startfile(folder_path)
            except:
                pass
                
        ctk.CTkButton(
            button_frame, 
            text="📂 폴더 열기", 
            command=open_folder,
            width=120, 
            height=36,
            fg_color=self.main_window.colors['bg_secondary'],
            hover_color=self.main_window.colors['accent']
        ).pack(side='left')
        
        # 저장/취소 버튼
        def save_settings():
            self._save_folder_settings(
                dialog, 
                folder_path, 
                profile_var, 
                fix_options, 
                enabled_var
            )
        
        ctk.CTkButton(
            button_frame, 
            text="💾 저장", 
            command=save_settings,
            width=80, 
            height=36
        ).pack(side='right', padx=5)
        
        ctk.CTkButton(
            button_frame, 
            text="❌ 취소", 
            command=dialog.destroy,
            width=80, 
            height=36,
            fg_color=self.main_window.colors['bg_secondary'],
            hover_color=self.main_window.colors['error']
        ).pack(side='right')
    
    def _create_folder_selector(self, parent, title):
        """폴더 선택 섹션 생성"""
        folder_frame = ctk.CTkFrame(
            parent, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10
        )
        folder_frame.pack(fill='x', pady=(0, 15))
        
        folder_inner = ctk.CTkFrame(folder_frame, fg_color="transparent")
        folder_inner.pack(fill='x', padx=20, pady=20)
        
        ctk.CTkLabel(
            folder_inner, 
            text=title, 
            font=self.main_window.fonts['subheading']
        ).pack(anchor='w', pady=(0, 10))
        
        # 입력 프레임
        input_frame = ctk.CTkFrame(folder_inner, fg_color="transparent")
        input_frame.pack(fill='x')
        
        folder_var = tk.StringVar()
        folder_entry = ctk.CTkEntry(
            input_frame, 
            textvariable=folder_var, 
            height=36,
            placeholder_text="폴더 경로를 입력하거나 찾아보기를 클릭하세요"
        )
        folder_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        def browse():
            folder = filedialog.askdirectory()
            if folder:
                folder_var.set(folder)
        
        ctk.CTkButton(
            input_frame, 
            text="찾아보기", 
            command=browse,
            width=100, 
            height=36
        ).pack(side='right')
        
        # 설명
        ctk.CTkLabel(
            folder_inner,
            text="이 폴더에 추가되는 PDF 파일을 자동으로 검사합니다.",
            font=self.main_window.fonts['small'],
            text_color=self.main_window.colors['text_secondary']
        ).pack(anchor='w', pady=(5, 0))
        
        return folder_var
    
    def _create_profile_selector(self, parent, title, current_value='offset'):
        """프로파일 선택 섹션 생성"""
        profile_frame = ctk.CTkFrame(
            parent, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10
        )
        profile_frame.pack(fill='x', pady=(0, 15))
        
        profile_inner = ctk.CTkFrame(profile_frame, fg_color="transparent")
        profile_inner.pack(fill='x', padx=20, pady=20)
        
        ctk.CTkLabel(
            profile_inner, 
            text=title, 
            font=self.main_window.fonts['subheading']
        ).pack(anchor='w', pady=(0, 10))
        
        profile_var = tk.StringVar(value=current_value)
        
        # 프로파일 설명
        profile_descriptions = {
            'offset': '오프셋 인쇄용 - 가장 엄격한 기준',
            'digital': '디지털 인쇄용 - 중간 수준의 기준',
            'newspaper': '신문 인쇄용 - 완화된 기준',
            'large_format': '대형 인쇄용 - 배너, 현수막',
            'high_quality': '고품질 인쇄용 - 화보집, 아트북'
        }
        
        # 라디오 버튼을 담을 프레임
        radio_container = ctk.CTkFrame(profile_inner, fg_color="transparent")
        radio_container.pack(fill='x', pady=(5, 0))
        
        for i, profile in enumerate(Config.AVAILABLE_PROFILES):
            row_frame = ctk.CTkFrame(radio_container, fg_color="transparent")
            row_frame.pack(fill='x', pady=5)
            
            # 라디오 버튼
            radio = ctk.CTkRadioButton(
                row_frame,
                text=profile,
                variable=profile_var,
                value=profile,
                radiobutton_width=20,
                radiobutton_height=20
            )
            radio.pack(side='left', padx=(0, 10))
            
            # 설명
            desc_label = ctk.CTkLabel(
                row_frame,
                text=f"- {profile_descriptions.get(profile, '')}",
                font=self.main_window.fonts['small'],
                text_color=self.main_window.colors['text_secondary']
            )
            desc_label.pack(side='left')
        
        return profile_var
    
    def _create_processing_options(self, parent, title, current_settings=None):
        """처리 옵션 섹션 생성"""
        options_frame = ctk.CTkFrame(
            parent, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10
        )
        options_frame.pack(fill='x', pady=(0, 15))
        
        options_inner = ctk.CTkFrame(options_frame, fg_color="transparent")
        options_inner.pack(fill='x', padx=20, pady=20)
        
        ctk.CTkLabel(
            options_inner, 
            text=title, 
            font=self.main_window.fonts['subheading']
        ).pack(anchor='w', pady=(0, 10))
        
        if current_settings is None:
            current_settings = {}
        
        fix_options = {
            'auto_convert_rgb': tk.BooleanVar(
                value=current_settings.get('auto_convert_rgb', False)
            ),
            'auto_outline_fonts': tk.BooleanVar(
                value=current_settings.get('auto_outline_fonts', False)
            ),
            'include_ink_analysis': tk.BooleanVar(
                value=current_settings.get('include_ink_analysis', Config.is_ink_analysis_enabled())
            )
        }
        
        # 체크박스들
        check_items = [
            ('auto_convert_rgb', "RGB → CMYK 자동 변환", "RGB 색상을 인쇄용 CMYK로 변환합니다"),
            ('auto_outline_fonts', "폰트 아웃라인 변환", "미임베딩 폰트를 아웃라인으로 변환합니다"),
            ('include_ink_analysis', "잉크량 분석 포함", "잉크 커버리지를 분석합니다 (처리 시간 증가)")
        ]
        
        for key, label, desc in check_items:
            check_frame = ctk.CTkFrame(options_inner, fg_color="transparent")
            check_frame.pack(fill='x', pady=5)
            
            ctk.CTkCheckBox(
                check_frame,
                text=label,
                variable=fix_options[key],
                font=self.main_window.fonts['body']
            ).pack(anchor='w')
            
            ctk.CTkLabel(
                check_frame,
                text=desc,
                font=self.main_window.fonts['small'],
                text_color=self.main_window.colors['text_secondary']
            ).pack(anchor='w', padx=(25, 0))
        
        return fix_options
    
    def _create_output_folder_selector(self, parent):
        """출력 폴더 선택 섹션 생성"""
        output_frame = ctk.CTkFrame(
            parent, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10
        )
        output_frame.pack(fill='x', pady=(0, 15))
        
        output_inner = ctk.CTkFrame(output_frame, fg_color="transparent")
        output_inner.pack(fill='x', padx=20, pady=20)
        
        ctk.CTkLabel(
            output_inner, 
            text="📤 출력 폴더 (선택사항)", 
            font=self.main_window.fonts['subheading']
        ).pack(anchor='w', pady=(0, 10))
        
        output_var = tk.StringVar()
        ctk.CTkEntry(
            output_inner, 
            textvariable=output_var, 
            height=36,
            placeholder_text="비워두면 입력 폴더 내에 하위 폴더 자동 생성"
        ).pack(fill='x')
        
        # 자동 생성 폴더 설명
        auto_folders_frame = ctk.CTkFrame(output_inner, fg_color="transparent")
        auto_folders_frame.pack(fill='x', pady=(10, 0))
        
        ctk.CTkLabel(
            auto_folders_frame,
            text="자동 생성되는 하위 폴더:",
            font=self.main_window.fonts['small'],
            text_color=self.main_window.colors['text_secondary']
        ).pack(anchor='w')
        
        folders_list = "• reports (보고서)\n• completed (완료)\n• errors (오류)\n• backup (백업)"
        ctk.CTkLabel(
            auto_folders_frame,
            text=folders_list,
            font=self.main_window.fonts['small'],
            text_color=self.main_window.colors['text_secondary'],
            justify='left'
        ).pack(anchor='w', padx=(10, 0))
        
        return output_var
    
    def _create_folder_info(self, parent, folder_info):
        """폴더 정보 표시 섹션 생성"""
        info_frame = ctk.CTkFrame(
            parent, 
            fg_color=self.main_window.colors['bg_card'],
            corner_radius=10
        )
        info_frame.pack(fill='x', pady=(0, 15))
        
        info_inner = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_inner.pack(fill='x', padx=20, pady=20)
        
        ctk.CTkLabel(
            info_inner, 
            text="📊 폴더 정보", 
            font=self.main_window.fonts['subheading']
        ).pack(anchor='w', pady=(0, 10))
        
        # 정보 항목들
        info_items = [
            ("경로", folder_info['path']),
            ("처리된 파일", f"{folder_info['processed']}개"),
            ("현재 상태", "활성화" if folder_info['enabled'] else "비활성화"),
            ("프로파일", folder_info['profile'])
        ]
        
        for label, value in info_items:
            item_frame = ctk.CTkFrame(info_inner, fg_color="transparent")
            item_frame.pack(fill='x', pady=2)
            
            ctk.CTkLabel(
                item_frame,
                text=f"{label}:",
                font=self.main_window.fonts['body'],
                text_color=self.main_window.colors['text_secondary']
            ).pack(side='left', padx=(0, 10))
            
            ctk.CTkLabel(
                item_frame,
                text=str(value),
                font=self.main_window.fonts['body']
            ).pack(side='left')
    
    def _create_dialog_buttons(self, parent, dialog, add_command):
        """대화상자 버튼 생성"""
        # 왼쪽: 도움말
        help_btn = ctk.CTkButton(
            parent,
            text="❔ 도움말",
            command=lambda: messagebox.showinfo(
                "도움말",
                "감시 폴더 기능:\n\n"
                "1. 지정한 폴더를 실시간으로 감시합니다.\n"
                "2. 새로운 PDF 파일이 추가되면 자동으로 검사합니다.\n"
                "3. 검사 결과에 따라 파일을 자동 분류합니다.\n"
                "4. 보고서는 reports 폴더에 저장됩니다.\n\n"
                "프로파일에 따라 검사 기준이 달라집니다."
            ),
            width=80,
            height=36,
            fg_color=self.main_window.colors['bg_secondary']
        )
        help_btn.pack(side='left')
        
        # 오른쪽: 추가/취소
        right_frame = ctk.CTkFrame(parent, fg_color="transparent")
        right_frame.pack(side='right')
        
        ctk.CTkButton(
            right_frame, 
            text="➕ 추가", 
            command=add_command,
            width=80, 
            height=36
        ).pack(side='right', padx=(5, 0))
        
        ctk.CTkButton(
            right_frame, 
            text="❌ 취소", 
            command=dialog.destroy,
            width=80, 
            height=36,
            fg_color=self.main_window.colors['bg_secondary'],
            hover_color=self.main_window.colors['error']
        ).pack(side='right')
    
    def _add_folder(self, dialog, folder_var, profile_var, fix_options, output_var):
        """폴더 추가"""
        folder_path = folder_var.get()
        if not folder_path:
            messagebox.showwarning("경고", "폴더를 선택하세요.")
            return
        
        # 폴더 존재 확인
        if not Path(folder_path).exists():
            messagebox.showerror("오류", "선택한 폴더가 존재하지 않습니다.")
            return
        
        # 자동 수정 설정
        auto_fix_settings = {
            key: var.get() 
            for key, var in fix_options.items()
        }
        
        # 폴더 추가
        success = self.main_window.folder_watcher.add_folder(
            folder_path,
            profile=profile_var.get(),
            auto_fix_settings=auto_fix_settings,
            output_folder=output_var.get() or None
        )
        
        if success:
            # 하위 폴더 자동 생성
            self._create_folder_structure(folder_path)
            
            self.main_window.sidebar.update_folder_list()
            dialog.destroy()
            self.main_window.logger.log(f"감시 폴더 추가: {Path(folder_path).name}")
            messagebox.showinfo("성공", "폴더가 추가되었습니다.\n\n폴더 감시를 시작하려면 사이드바의 스위치를 켜세요.")
        else:
            messagebox.showerror("오류", "이미 추가된 폴더이거나 추가에 실패했습니다.")
    
    def _save_folder_settings(self, dialog, folder_path, profile_var, fix_options, enabled_var):
        """폴더 설정 저장"""
        # 자동 수정 설정
        auto_fix_settings = {
            key: var.get() 
            for key, var in fix_options.items()
        }
        
        # 설정 업데이트
        success = self.main_window.folder_watcher.update_folder_config(
            folder_path,
            profile=profile_var.get(),
            auto_fix_settings=auto_fix_settings,
            enabled=enabled_var.get()
        )
        
        if success:
            self.main_window.sidebar.update_folder_list()
            dialog.destroy()
            self.main_window.logger.log(f"폴더 설정 업데이트: {Path(folder_path).name}")
            messagebox.showinfo("성공", "설정이 저장되었습니다.")
        else:
            messagebox.showerror("오류", "설정 저장에 실패했습니다.")
    
    def _create_folder_structure(self, folder_path):
        """핫폴더 하위 구조 자동 생성"""
        folder_path = Path(folder_path)
        
        # 생성할 하위 폴더들
        subfolders = [
            'reports',      # 보고서
            'output',       # 출력
            'completed',    # 완료된 파일
            'errors',       # 오류 파일
            'backup'        # 백업
        ]
        
        created_folders = []
        for subfolder in subfolders:
            subfolder_path = folder_path / subfolder
            try:
                subfolder_path.mkdir(exist_ok=True)
                if not subfolder_path.exists():
                    created_folders.append(subfolder)
                self.main_window.logger.log(f"하위 폴더 생성: {subfolder_path}")
            except Exception as e:
                self.main_window.logger.error(f"하위 폴더 생성 실패 ({subfolder}): {e}")
        
        if created_folders:
            messagebox.showinfo(
                "폴더 생성 완료", 
                f"다음 하위 폴더가 생성되었습니다:\n\n" + 
                "\n".join(f"• {f}" for f in created_folders)
            )