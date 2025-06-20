# reports/core/thumbnail_generator.py
"""
PDF 썸네일 및 미리보기 생성 모듈
PyMuPDF를 사용한 이미지 렌더링 담당
"""

from pathlib import Path
from typing import Dict, Optional, Union, Any
import base64
from io import BytesIO

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    print("경고: PyMuPDF가 설치되지 않았습니다. 썸네일 생성이 제한됩니다.")


class ThumbnailGenerator:
    """PDF 썸네일 생성 클래스"""
    
    def __init__(self):
        """썸네일 생성기 초기화"""
        self.has_pymupdf = HAS_PYMUPDF
    
    def create_thumbnail(
        self, 
        pdf_path: Union[str, Path], 
        max_width: int = 300, 
        page_num: int = 0
    ) -> Dict[str, Any]:
        """
        PDF 페이지의 썸네일 생성
        
        Args:
            pdf_path: PDF 파일 경로
            max_width: 썸네일 최대 너비 (픽셀)
            page_num: 썸네일로 만들 페이지 번호 (0부터 시작)
            
        Returns:
            dict: {
                'data_url': Base64 인코딩된 이미지 데이터 URL,
                'page_shown': 표시된 페이지 번호 (1부터 시작),
                'total_pages': 전체 페이지 수
            }
        """
        if not self.has_pymupdf:
            return self._empty_thumbnail()
        
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                return self._empty_thumbnail()
            
            # PDF 열기
            doc = fitz.open(str(pdf_path))
            
            # 페이지 번호 유효성 검사
            if page_num >= len(doc):
                page_num = 0
            
            # 페이지 가져오기
            page = doc[page_num]
            
            # 썸네일 크기 계산
            rect = page.rect
            zoom = max_width / rect.width
            mat = fitz.Matrix(zoom, zoom)
            
            # 페이지를 이미지로 렌더링
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # PNG 형식으로 변환
            img_data = pix.tobytes("png")
            
            # Base64로 인코딩
            img_base64 = base64.b64encode(img_data).decode()
            
            # 페이지 수 정보 저장
            total_pages = len(doc)
            
            doc.close()
            
            # 데이터 URL 형식으로 반환
            return {
                'data_url': f"data:image/png;base64,{img_base64}",
                'page_shown': page_num + 1,
                'total_pages': total_pages
            }
            
        except Exception as e:
            print(f"썸네일 생성 실패: {e}")
            return self._empty_thumbnail()
    
    def create_page_preview(
        self, 
        pdf_path: Union[str, Path], 
        page_num: int, 
        max_width: int = 200
    ) -> Optional[str]:
        """
        특정 페이지의 미리보기 생성
        
        Args:
            pdf_path: PDF 파일 경로
            page_num: 페이지 번호 (0부터 시작)
            max_width: 미리보기 최대 너비 (픽셀)
            
        Returns:
            str: Base64 인코딩된 이미지 데이터 URL
        """
        if not self.has_pymupdf:
            return None
        
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                return None
            
            doc = fitz.open(str(pdf_path))
            
            if page_num >= len(doc):
                doc.close()
                return None
                
            page = doc[page_num]
            
            # 미리보기 크기 계산
            rect = page.rect
            zoom = max_width / rect.width
            mat = fitz.Matrix(zoom, zoom)
            
            # 페이지를 이미지로 렌더링
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # PNG 형식으로 변환
            img_data = pix.tobytes("png")
            
            # Base64로 인코딩
            img_base64 = base64.b64encode(img_data).decode()
            
            doc.close()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            print(f"페이지 미리보기 생성 실패: {e}")
            return None
    
    def create_comparison_thumbnails(
        self,
        original_path: Union[str, Path],
        modified_path: Union[str, Path],
        page_num: int = 0,
        max_width: int = 200
    ) -> Dict[str, Optional[str]]:
        """
        수정 전후 비교를 위한 썸네일 쌍 생성
        
        Args:
            original_path: 원본 PDF 경로
            modified_path: 수정된 PDF 경로
            page_num: 페이지 번호
            max_width: 썸네일 너비
            
        Returns:
            dict: {'original': data_url, 'modified': data_url}
        """
        return {
            'original': self.create_page_preview(original_path, page_num, max_width),
            'modified': self.create_page_preview(modified_path, page_num, max_width)
        }
    
    def _empty_thumbnail(self) -> Dict[str, Any]:
        """빈 썸네일 데이터 반환"""
        return {
            'data_url': '',
            'page_shown': 0,
            'total_pages': 0
        }
    
    def get_page_dimensions(self, pdf_path: Union[str, Path], page_num: int = 0) -> Optional[Dict[str, float]]:
        """
        페이지 크기 정보 가져오기
        
        Args:
            pdf_path: PDF 파일 경로
            page_num: 페이지 번호
            
        Returns:
            dict: {'width': float, 'height': float} (포인트 단위)
        """
        if not self.has_pymupdf:
            return None
        
        try:
            doc = fitz.open(str(pdf_path))
            if page_num >= len(doc):
                doc.close()
                return None
            
            page = doc[page_num]
            rect = page.rect
            
            dimensions = {
                'width': rect.width,
                'height': rect.height
            }
            
            doc.close()
            return dimensions
            
        except Exception:
            return None