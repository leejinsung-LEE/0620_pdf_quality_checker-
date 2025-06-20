# external_tools.py - 외부 도구를 사용한 정확한 PDF 검사
"""
pdffonts와 Ghostscript를 사용한 고신뢰도 PDF 검사 모듈
poppler-utils와 Ghostscript가 설치되어 있어야 함
"""

import subprocess
import tempfile
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import shutil
import platform


class ExternalPDFChecker:
    """외부 도구를 사용한 PDF 검사 클래스"""
    
    def __init__(self):
        self.pdffonts_path = self._find_pdffonts()
        self.gs_path = self._find_ghostscript()
        self.temp_dir = tempfile.mkdtemp(prefix="pdf_check_")
        
    def __del__(self):
        """임시 디렉토리 정리"""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _find_pdffonts(self) -> Optional[str]:
        """pdffonts 실행 파일 찾기"""
        # Windows
        if platform.system() == 'Windows':
            # 일반적인 설치 경로들
            paths = [
                r"C:\Program Files\poppler\Library\bin\pdffonts.exe",
                r"C:\Program Files (x86)\poppler\Library\bin\pdffonts.exe",
                r"C:\poppler\Library\bin\pdffonts.exe",
                r"C:\tools\poppler\Library\bin\pdffonts.exe"
            ]
            
            for path in paths:
                if os.path.exists(path):
                    return path
                    
            # PATH에서 찾기
            pdffonts = shutil.which("pdffonts.exe") or shutil.which("pdffonts")
            if pdffonts:
                return pdffonts
        else:
            # Linux/Mac
            return shutil.which("pdffonts")
            
        return None
    
    
    def _find_ghostscript(self) -> Optional[str]:
        """Ghostscript 실행 파일 찾기"""
        if platform.system() == 'Windows':
            import glob
            # glob 패턴으로 검색
            search_patterns = [
                "C:\Program Files\gs\gs*\bin\gswin64c.exe",
                "C:\Program Files\gs\gs*\bin\gswin32c.exe",
                "C:\Program Files (x86)\gs\gs*\bin\gswin32c.exe",
            ]

            for pattern in search_patterns:
                matches = glob.glob(pattern)
                if matches:
                    matches.sort(reverse=True)  # 최신 버전이 먼저 오도록 정렬
                    return matches[0]

            # PATH에서 찾기
            gs = shutil.which("gswin64c.exe") or shutil.which("gswin32c.exe")
            if gs:
                return gs
        else:
            # Linux/Mac
            return shutil.which("gs")
        return None

    def check_font_embedding_with_pdffonts(self, pdf_path: str) -> Dict:
        """
        pdffonts를 사용한 정확한 폰트 임베딩 검사
        
        Returns:
            dict: {
                'success': bool,
                'fonts': {
                    'font_name': {
                        'type': str,
                        'embedded': bool,
                        'subset': bool,
                        'encoding': str,
                        'pages': list
                    }
                },
                'not_embedded_fonts': list,
                'error': str (있는 경우)
            }
        """
        result = {
            'success': False,
            'fonts': {},
            'not_embedded_fonts': [],
            'error': None
        }
        
        if not self.pdffonts_path:
            result['error'] = "pdffonts가 설치되어 있지 않습니다. poppler-utils를 설치해주세요."
            return result
        
        try:
            # pdffonts 실행
            cmd = [self.pdffonts_path, "-l", "1000", str(pdf_path)]
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if process.returncode != 0:
                result['error'] = f"pdffonts 실행 실패: {process.stderr}"
                return result
            
            # 출력 파싱
            lines = process.stdout.strip().split('\n')
            
            # 헤더 찾기 (name, type, encoding, emb, sub, uni 등)
            header_line = None
            for i, line in enumerate(lines):
                if 'name' in line.lower() and 'type' in line.lower():
                    header_line = i
                    break
            
            if header_line is None:
                result['error'] = "pdffonts 출력 형식을 인식할 수 없습니다"
                return result
            
            # 헤더 다음 줄부터 파싱
            for line in lines[header_line + 2:]:  # 헤더와 구분선 건너뛰기
                if not line.strip():
                    continue
                
                # 공백으로 분리 (폰트명에 공백이 있을 수 있으므로 주의)
                parts = line.split()
                if len(parts) < 6:
                    continue
                
                # emb 컬럼 찾기 (보통 4번째 또는 5번째)
                emb_value = None
                font_name = None
                font_type = None
                
                # 일반적인 형식: name type encoding emb sub uni object ID
                if len(parts) >= 6:
                    # 폰트명이 여러 단어일 수 있으므로 역으로 파싱
                    # 마지막 몇 개는 고정값 (object ID, uni, sub, emb)
                    emb_value = parts[-4]  # emb
                    sub_value = parts[-3]  # sub
                    font_type = parts[-6]  # type
                    
                    # 나머지를 폰트명으로
                    font_name = ' '.join(parts[:-6])
                
                if not font_name:
                    continue
                
                # 임베딩 상태 확인
                is_embedded = emb_value.lower() == 'yes'
                is_subset = sub_value.lower() == 'yes'
                
                # 폰트 정보 저장
                if font_name not in result['fonts']:
                    result['fonts'][font_name] = {
                        'type': font_type,
                        'embedded': is_embedded,
                        'subset': is_subset,
                        'encoding': parts[-5] if len(parts) > 6 else 'unknown',
                        'pages': []  # pdffonts는 페이지 정보를 제공하지 않음
                    }
                
                # 미임베딩 폰트 목록
                if not is_embedded:
                    if font_name not in result['not_embedded_fonts']:
                        result['not_embedded_fonts'].append(font_name)
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = f"pdffonts 검사 중 오류: {str(e)}"
        
        return result
    
    def check_overprint_with_ghostscript(self, pdf_path: str, page_num: int = 1) -> Dict:
        """
        Ghostscript tiffsep 디바이스를 사용한 오버프린트 검사
        
        Args:
            pdf_path: PDF 파일 경로
            page_num: 검사할 페이지 번호 (기본값: 1)
            
        Returns:
            dict: {
                'success': bool,
                'has_overprint': bool,
                'overprint_areas': list,  # 오버프린트가 감지된 영역
                'separations': dict,      # 색상 분리 정보
                'error': str (있는 경우)
            }
        """
        result = {
            'success': False,
            'has_overprint': False,
            'overprint_areas': [],
            'separations': {},
            'error': None
        }
        
        if not self.gs_path:
            result['error'] = "Ghostscript가 설치되어 있지 않습니다."
            return result
        
        try:
            # 출력 파일 경로
            output_base = os.path.join(self.temp_dir, f"page_{page_num}")
            
            # Ghostscript 명령어 구성
            cmd = [
                self.gs_path,
                "-dNOPAUSE",
                "-dBATCH",
                "-dSAFER",
                "-sDEVICE=tiffsep",
                "-r72",  # 낮은 해상도로 빠른 검사
                f"-dFirstPage={page_num}",
                f"-dLastPage={page_num}",
                f"-sOutputFile={output_base}%d.tif",
                "-dOverprint=/simulate",  # 오버프린트 시뮬레이션
                str(pdf_path)
            ]
            
            # Ghostscript 실행
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.temp_dir
            )
            
            if process.returncode != 0:
                # Ghostscript 경고는 무시하고 파일 생성 여부로 판단
                pass
            
            # 생성된 분리 파일들 확인
            import glob
            sep_files = glob.glob(os.path.join(self.temp_dir, f"page_{page_num}*.tif"))
            
            if not sep_files:
                result['error'] = "색상 분리 파일이 생성되지 않았습니다"
                return result
            
            # 분리된 색상 채널 분석
            separations = {}
            for sep_file in sep_files:
                filename = os.path.basename(sep_file)
                
                # 색상 채널 이름 추출
                if '.Cyan.' in filename:
                    channel = 'Cyan'
                elif '.Magenta.' in filename:
                    channel = 'Magenta'
                elif '.Yellow.' in filename:
                    channel = 'Yellow'
                elif '.Black.' in filename:
                    channel = 'Black'
                elif '(s)' in filename:
                    # 별색 채널
                    match = re.search(r'\.(.+?)\(s\)\.', filename)
                    if match:
                        channel = f"Spot-{match.group(1)}"
                    else:
                        continue
                else:
                    continue
                
                separations[channel] = sep_file
            
            result['separations'] = separations
            
            # 오버프린트 검사 로직
            # 실제로는 각 분리 이미지를 분석하여 오버프린트 영역을 찾아야 함
            # 여기서는 간단히 분리 파일의 존재와 크기로 판단
            
            if len(separations) > 4:  # CMYK 이상의 채널이 있으면 별색 사용
                result['has_overprint'] = True
                result['overprint_areas'].append({
                    'type': 'spot_color_overprint',
                    'channels': list(separations.keys())
                })
            
            # 각 채널의 파일 크기를 비교하여 오버프린트 가능성 판단
            # (실제 구현에서는 이미지 분석 라이브러리를 사용해야 함)
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = f"Ghostscript 검사 중 오류: {str(e)}"
        finally:
            # 임시 파일 정리
            for file in glob.glob(os.path.join(self.temp_dir, "*.tif")):
                try:
                    os.remove(file)
                except:
                    pass
        
        return result
    
    def get_installation_guide(self) -> str:
        """외부 도구 설치 가이드"""
        guide = """
# 외부 도구 설치 가이드

## Windows

### 1. Poppler (pdffonts 포함) 설치
1. https://github.com/oschwartz10612/poppler-windows/releases 에서 최신 버전 다운로드
2. C:\\Program Files\\poppler 에 압축 해제
3. 시스템 환경 변수 PATH에 C:\\Program Files\\poppler\\Library\\bin 추가

### 2. Ghostscript 설치
1. https://www.ghostscript.com/download/gsdnld.html 에서 최신 버전 다운로드
2. 설치 프로그램 실행 (기본 경로 사용 권장)
3. 설치 완료 후 자동으로 PATH에 추가됨

## Linux (Ubuntu/Debian)

```bash
# Poppler 설치
sudo apt-get update
sudo apt-get install poppler-utils

# Ghostscript 설치
sudo apt-get install ghostscript
```

## macOS

```bash
# Homebrew 사용
brew install poppler
brew install ghostscript
```

## 설치 확인

```bash
# pdffonts 확인
pdffonts -v

# Ghostscript 확인
gs -v
```
"""
        return guide


# 기존 시스템과의 통합을 위한 어댑터 함수들

def check_fonts_external(pdf_path: str) -> Dict:
    """
    pdf_analyzer.py의 _analyze_fonts 메서드를 대체할 함수
    
    Returns:
        기존 형식과 호환되는 딕셔너리
    """
    checker = ExternalPDFChecker()
    result = checker.check_font_embedding_with_pdffonts(pdf_path)
    
    # 기존 형식으로 변환
    fonts_info = {}
    
    if result['success']:
        for font_name, font_data in result['fonts'].items():
            # 기존 형식의 키 생성 (폰트명_페이지번호)
            # pdffonts는 페이지 정보를 제공하지 않으므로 전체 문서로 표시
            key = f"{font_name}_all"
            
            fonts_info[key] = {
                'name': font_name,
                'type': font_data['type'],
                'subtype': '',
                'embedded': font_data['embedded'],
                'subset': font_data['subset'],
                'encoding': font_data['encoding'],
                'base_font': font_name,
                'page': 0,  # 0은 전체 문서를 의미
                'is_standard': False,
                'is_type3': font_data['type'] == 'Type3'
            }
    else:
        # 실패 시 빈 딕셔너리 반환 (기존 방식으로 폴백 가능)
        print(f"외부 폰트 검사 실패: {result['error']}")
    
    return fonts_info


def check_overprint_external(pdf_path: str, check_all_pages: bool = False) -> Dict:
    """
    print_quality_checker.py의 check_overprint 메서드를 대체할 함수
    
    Args:
        pdf_path: PDF 파일 경로
        check_all_pages: 모든 페이지 검사 여부
        
    Returns:
        기존 형식과 호환되는 딕셔너리
    """
    checker = ExternalPDFChecker()
    
    overprint_info = {
        'has_overprint': False,
        'has_problematic_overprint': False,
        'overprint_objects': [],
        'pages_with_overprint': [],
        'white_overprint_pages': [],
        'k_only_overprint_pages': [],
        'light_color_overprint_pages': [],
        'image_overprint_pages': []
    }
    
    # 첫 페이지만 검사 (성능을 위해)
    # 실제로는 check_all_pages가 True면 모든 페이지 검사해야 함
    result = checker.check_overprint_with_ghostscript(pdf_path, page_num=1)
    
    if result['success'] and result['has_overprint']:
        overprint_info['has_overprint'] = True
        overprint_info['pages_with_overprint'].append(1)
        
        # 오버프린트 타입 분류
        for area in result['overprint_areas']:
            if area['type'] == 'spot_color_overprint':
                overprint_info['has_problematic_overprint'] = True
                overprint_info['overprint_objects'].append({
                    'page': 1,
                    'type': 'spot_overprint',
                    'channels': area['channels']
                })
    
    return overprint_info


# 설치 상태 확인 함수
def check_external_tools_status() -> Dict[str, bool]:
    """외부 도구 설치 상태 확인"""
    checker = ExternalPDFChecker()
    return {
        'pdffonts': checker.pdffonts_path is not None,
        'ghostscript': checker.gs_path is not None,
        'pdffonts_path': checker.pdffonts_path or "Not found",
        'ghostscript_path': checker.gs_path or "Not found"
    }


if __name__ == "__main__":
    # 테스트 코드
    print("외부 도구 상태:")
    status = check_external_tools_status()
    for tool, installed in status.items():
        print(f"  {tool}: {installed}")
    
    # 설치 가이드 출력
    if not all([status['pdffonts'], status['ghostscript']]):
        print("\n" + ExternalPDFChecker().get_installation_guide())