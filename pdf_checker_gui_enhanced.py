# pdf_checker_gui_enhanced.py - 메인 진입점
# 이 파일은 기존과 같은 이름으로 유지되어 기존 코드와의 호환성을 보장합니다

"""
PDF 품질 검수 시스템 v4.0 - Modularized Edition
메인 진입점 파일 - GUI 모듈을 임포트하여 실행
"""

from gui.main_window import EnhancedPDFCheckerGUI

def main():
    """메인 함수"""
    # GUI 인스턴스 생성
    app = EnhancedPDFCheckerGUI()
    
    # GUI 실행
    app.run()

# 프로그램 진입점
if __name__ == "__main__":
    main()