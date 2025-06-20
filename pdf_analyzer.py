# pdf_analyzer.py - PDF 분석 핵심 엔진 (외부 도구 통합 버전)
# 2025.06 수정: pdffonts를 사용한 정확한 폰트 임베딩 검사로 전환
"""
pdf_analyzer.py - PDF 분석 핵심 엔진 (외부 도구 통합 버전)

주요 기능:
1. PDF 기본 정보 분석 (페이지 수, 버전, 메타데이터 등)
2. 페이지 크기 및 방향 분석 (회전 고려)
3. 폰트 임베딩 검사 - pdffonts를 사용한 고신뢰도 검사
4. 색상 공간 분석 (RGB, CMYK, 별색 등)
5. 이미지 해상도 및 품질 분석
6. 종합적인 문제점 검출 및 보고

외부 도구가 없으면 해당 검사를 수행하지 않음 (부정확한 검사 제거)
스레드 안전성을 고려한 설계로 멀티스레드 환경에서도 안정적으로 동작
"""

# 필요한 라이브러리들을 가져옵니다
import pikepdf  # PDF 파일의 내부 구조를 정밀하게 분석하는 라이브러리
import fitz  # PyMuPDF - PDF 파일을 읽고 분석하는 라이브러리 (이미지 분석용으로만 사용)
from pathlib import Path  # 파일 경로를 다루는 라이브러리
from utils import (
    points_to_mm, format_size_mm, safe_str, format_file_size,
    safe_integer, safe_float
)  # 유틸리티 함수들
from config import Config  # 설정 파일
from ink_calculator import InkCalculator  # 잉크량 계산기
from print_quality_checker import PrintQualityChecker  # 인쇄 품질 검사기
from preflight_profiles import PreflightProfiles  # 프리플라이트 프로파일
import time  # 시간 측정용
import threading  # 스레드 관련 기능

# 새로 추가된 외부 도구 모듈을 안전하게 가져오기 시도
try:
    # external_tools 모듈에서 필요한 함수들을 가져옵니다
    from external_tools import check_fonts_external, check_external_tools_status
    HAS_EXTERNAL_TOOLS = True  # 외부 도구를 사용할 수 있음을 표시
except ImportError:
    # 만약 external_tools 모듈이 없다면 기존 방식으로 동작
    HAS_EXTERNAL_TOOLS = False
    print("경고: external_tools 모듈을 찾을 수 없습니다. 기존 방식으로 폴백합니다.")


class PDFAnalyzer:
    """
    PDF 파일을 분석하는 메인 클래스 - 외부 도구 통합 버전
    
    이 클래스는 PDF 파일의 모든 측면을 종합적으로 분석합니다:
    - 문서 구조 및 메타데이터
    - 페이지 레이아웃 및 크기
    - 폰트 사용 및 임베딩 상태
    - 색상 공간 및 별색 사용
    - 이미지 품질 및 해상도
    - 인쇄 적합성 검사
    
    각 분석 모듈은 독립적으로 동작하여 오류가 발생해도 
    다른 분석에 영향을 주지 않습니다.
    """
    
    def __init__(self):
        """
        PDF 분석기 초기화
        
        각 스레드별로 독립적인 인스턴스를 생성하여
        멀티스레드 환경에서의 안전성을 보장합니다.
        """
        # 스레드별 독립 인스턴스 생성
        self.ink_calculator = InkCalculator()  # 잉크량 계산을 위한 인스턴스
        self.print_quality_checker = PrintQualityChecker()  # 인쇄 품질 검사를 위한 인스턴스
        
        # 디버깅용 인스턴스 ID (문제 해결 시 유용)
        self.instance_id = id(self)  # 메모리 주소를 고유 ID로 사용
        self.thread_id = threading.current_thread().ident  # 현재 스레드 ID
        
        # 외부 도구 상태 확인
        if HAS_EXTERNAL_TOOLS:
            # 외부 도구들(pdffonts, Ghostscript 등)의 설치 상태를 확인
            self.external_tools_status = check_external_tools_status()
            
            # pdffonts가 설치되어 있지 않으면 경고 메시지 출력
            if not self.external_tools_status.get('pdffonts'):
                print("⚠️  pdffonts가 설치되어 있지 않습니다. 폰트 검사가 제한됩니다.")
        
    def analyze(self, pdf_path, include_ink_analysis=None, preflight_profile='offset'):
        """
        PDF 파일을 종합적으로 분석하는 메인 메서드
        
        외부 도구를 우선 사용하고, 실패 시 기존 방식으로 폴백하는 
        안전한 이중화 구조를 사용합니다.
        
        Args:
            pdf_path: 분석할 PDF 파일 경로 (문자열 또는 Path 객체)
            include_ink_analysis: 잉크량 분석 포함 여부 (None이면 설정값 사용)
            preflight_profile: 적용할 프리플라이트 프로파일 ('offset', 'digital' 등)
            
        Returns:
            dict: 분석 결과를 담은 딕셔너리
                - basic_info: PDF 기본 정보
                - pages: 페이지별 상세 정보
                - fonts: 폰트 사용 현황
                - colors: 색상 공간 정보
                - images: 이미지 품질 정보
                - print_quality: 고급 인쇄 품질 검사 결과
                - issues: 발견된 문제점들
                - preflight_result: 프리플라이트 검사 결과
        """
        # include_ink_analysis가 None이면 Config 설정 사용
        if include_ink_analysis is None:
            include_ink_analysis = Config.is_ink_analysis_enabled()
            
        # 스레드 정보 로깅 (디버깅 및 모니터링용)
        current_thread = threading.current_thread()
        print(f"\n📄 [Thread {current_thread.ident}] PDF 분석 시작: {Path(pdf_path).name}")
        print(f"   [Analyzer Instance: {self.instance_id}]")
        print(f"🎯 프리플라이트 프로파일: {preflight_profile}")
        print(f"🎨 잉크량 분석: {'포함' if include_ink_analysis else '제외'}")
        
        # 외부 도구 상태 표시
        if HAS_EXTERNAL_TOOLS and hasattr(self, 'external_tools_status'):
            print(f"🔧 외부 도구: pdffonts={'✓' if self.external_tools_status.get('pdffonts') else '✗'}")
        
        # 분석 시작 시간 기록
        start_time = time.time()
        
        # 지역 변수로 PDF와 결과 관리 (스레드 안전성)
        local_pdf = None
        local_analysis_result = {}
        
        try:
            # 프리플라이트 프로파일 로드
            current_profile = PreflightProfiles.get_profile_by_name(preflight_profile)
            if not current_profile:
                print(f"⚠️  '{preflight_profile}' 프로파일을 찾을 수 없습니다. 기본(offset) 사용")
                current_profile = PreflightProfiles.get_offset_printing()
            
            # PDF 파일 열기 - 지역 변수로 관리
            local_pdf = pikepdf.open(pdf_path)
            
            # 파일 크기 확인
            file_size = Path(pdf_path).stat().st_size
            
            # 분석 결과를 저장할 딕셔너리 초기화 - 지역 변수로 관리
            local_analysis_result = {
                'filename': Path(pdf_path).name,
                'file_path': str(pdf_path),
                'file_size': file_size,
                'file_size_formatted': format_file_size(file_size),
                'preflight_profile': current_profile.name,
                '_analyzer_instance': self.instance_id,  # 디버깅용
                '_thread_id': current_thread.ident,      # 디버깅용
                
                # Phase 1: 기본 분석
                'basic_info': self._analyze_basic_info(local_pdf),
                'pages': self._analyze_pages(local_pdf),
                'fonts': self._analyze_fonts(local_pdf, pdf_path),  # 외부 도구 통합
                'colors': self._analyze_colors(local_pdf),
                'images': self._analyze_images(local_pdf, pdf_path),
                'issues': []  # 발견된 문제점들을 저장할 리스트
            }
            
            # Phase 2: 고급 인쇄 품질 검사
            if any(Config.CHECK_OPTIONS.values()):
                print(Config.MESSAGES['print_quality_checking'])
                # 페이지 정보를 print_quality_checker에 전달
                print_quality_result = self.print_quality_checker.check_all(
                    pdf_path, 
                    pages_info=local_analysis_result['pages']
                )
                local_analysis_result['print_quality'] = print_quality_result
                
                # 고급 검사에서 발견된 문제들을 메인 이슈 목록에 추가
                for issue in print_quality_result.get('issues', []):
                    local_analysis_result['issues'].append(issue)
                for warning in print_quality_result.get('warnings', []):
                    local_analysis_result['issues'].append(warning)
            
            # Phase 3: 잉크량 분석 (선택적, 시간이 오래 걸릴 수 있음)
            if include_ink_analysis:
                print("\n🎨 잉크량 분석 중... (시간이 걸릴 수 있습니다)")
                ink_result = self.ink_calculator.calculate(pdf_path)
                local_analysis_result['ink_coverage'] = ink_result
            
            # Phase 4: 기본 문제점 검사
            self._check_issues(local_analysis_result)
            
            # Phase 5: 프리플라이트 검사 수행
            print(f"\n{Config.MESSAGES['preflight_checking']}")
            preflight_result = current_profile.check(local_analysis_result)
            local_analysis_result['preflight_result'] = preflight_result
            
            # 프리플라이트 결과를 이슈에 추가
            self._add_preflight_issues(local_analysis_result, preflight_result)
            
            # 분석 시간 기록
            analysis_time = time.time() - start_time
            local_analysis_result['analysis_time'] = f"{analysis_time:.1f}초"
            
            # 프리플라이트 결과 출력
            self._print_preflight_summary(preflight_result)
            
            print(f"\n✅ [Thread {current_thread.ident}] 분석 완료! (소요시간: {analysis_time:.1f}초)")
            
            return local_analysis_result
            
        except Exception as e:
            # 예외 발생 시 오류 정보 반환
            print(f"❌ [Thread {current_thread.ident}] PDF 분석 중 오류 발생: {e}")
            return {'error': str(e), '_thread_id': current_thread.ident}
        finally:
            # 메모리 누수 방지를 위해 PDF 파일 닫기
            if local_pdf:
                local_pdf.close()
    
    def _analyze_basic_info(self, pdf_obj):
        """
        PDF 기본 정보 추출
        
        PDF 파일의 메타데이터, 버전, 암호화 상태 등을 분석합니다.
        
        Args:
            pdf_obj: pikepdf로 열린 PDF 객체
            
        Returns:
            dict: PDF 기본 정보
        """
        print("  📋 기본 정보 분석 중...")
        
        # 기본 정보 딕셔너리 초기화
        info = {
            'page_count': len(pdf_obj.pages),  # 총 페이지 수
            'pdf_version': safe_str(pdf_obj.pdf_version),  # PDF 버전 (예: 1.4, 1.7)
            'is_encrypted': pdf_obj.is_encrypted,  # 암호화 여부
            'is_linearized': False,  # 웹 최적화(선형화) 여부
            # 메타데이터 필드들 (빈 문자열로 초기화)
            'title': '',
            'author': '',
            'subject': '',
            'keywords': '',
            'creator': '',      # 원본 문서를 만든 프로그램
            'producer': '',     # PDF를 생성한 프로그램
            'creation_date': '',
            'modification_date': ''
        }
        
        # 선형화(웹 최적화) 확인
        # 선형화된 PDF는 웹에서 빠르게 로딩됩니다
        try:
            if hasattr(pdf_obj, 'is_linearized'):
                info['is_linearized'] = pdf_obj.is_linearized
        except:
            # 확인할 수 없으면 False로 유지
            pass
        
        # 메타데이터 추출 (있는 경우)
        if pdf_obj.docinfo:
            # PDF 메타데이터에서 각 필드를 안전하게 추출
            info['title'] = safe_str(pdf_obj.docinfo.get('/Title', ''))
            info['author'] = safe_str(pdf_obj.docinfo.get('/Author', ''))
            info['subject'] = safe_str(pdf_obj.docinfo.get('/Subject', ''))
            info['keywords'] = safe_str(pdf_obj.docinfo.get('/Keywords', ''))
            info['creator'] = safe_str(pdf_obj.docinfo.get('/Creator', ''))
            info['producer'] = safe_str(pdf_obj.docinfo.get('/Producer', ''))
            
            # 날짜 정보 추출 (PDF 날짜 형식은 특수하므로 예외 처리)
            try:
                if '/CreationDate' in pdf_obj.docinfo:
                    info['creation_date'] = safe_str(pdf_obj.docinfo['/CreationDate'])
                if '/ModDate' in pdf_obj.docinfo:
                    info['modification_date'] = safe_str(pdf_obj.docinfo['/ModDate'])
            except:
                # 날짜 파싱 실패 시 빈 문자열 유지
                pass
        
        print(f"    ✓ 총 {info['page_count']}페이지, PDF {info['pdf_version']}")
        return info
    
    def _analyze_pages(self, pdf_obj):
        """
        각 페이지 정보 분석
        
        페이지 크기, 방향, 회전, 재단선 등을 상세히 분석합니다.
        
        Args:
            pdf_obj: pikepdf로 열린 PDF 객체
            
        Returns:
            list: 페이지별 정보 리스트
        """
        print("  📐 페이지 정보 분석 중...")
        
        pages_info = []
        
        # 각 페이지를 순회하면서 정보 수집
        for page_num, page in enumerate(pdf_obj.pages, 1):
            # PDF의 다양한 박스 정보 추출
            # MediaBox: 실제 페이지 크기 (필수)
            # CropBox: 표시될 영역 (옵션)
            # BleedBox: 재단 여백 포함 영역 (옵션)
            # TrimBox: 최종 재단 크기 (옵션)
            # ArtBox: 실제 콘텐츠 영역 (옵션)
            mediabox = page.MediaBox if '/MediaBox' in page else None
            cropbox = page.CropBox if '/CropBox' in page else mediabox
            bleedbox = page.BleedBox if '/BleedBox' in page else cropbox
            trimbox = page.TrimBox if '/TrimBox' in page else cropbox
            artbox = page.ArtBox if '/ArtBox' in page else cropbox
            
            # MediaBox 좌표값 추출 (PDF는 좌하단 기준 좌표계 사용)
            if mediabox:
                left = float(mediabox[0])    # 왼쪽 x 좌표
                bottom = float(mediabox[1])  # 아래쪽 y 좌표
                right = float(mediabox[2])   # 오른쪽 x 좌표
                top = float(mediabox[3])     # 위쪽 y 좌표
                
                # 페이지 크기 계산 (포인트 단위)
                width = right - left
                height = top - bottom
                
                # mm 단위로 변환 (인쇄업계 표준 단위)
                width_mm = points_to_mm(width)
                height_mm = points_to_mm(height)
                
                # 페이지 회전 정보 (0, 90, 180, 270도)
                rotation = int(page.get('/Rotate', 0))
                
                # 회전을 고려한 실제 표시 크기
                if rotation in [90, 270]:  # 90도 또는 270도 회전
                    display_width_mm = height_mm
                    display_height_mm = width_mm
                else:  # 0도 또는 180도 (회전 없음 또는 뒤집기)
                    display_width_mm = width_mm
                    display_height_mm = height_mm
                
                # 표준 용지 크기 감지 (A4, Letter 등)
                paper_size = Config.get_paper_size_name(display_width_mm, display_height_mm)
                
                # 회전 정보를 포함한 크기 표시
                size_formatted_with_rotation = format_size_mm(width, height)
                if rotation != 0:
                    size_formatted_with_rotation += f" ({rotation}° 회전)"
                
                # 페이지 정보 딕셔너리 구성
                page_info = {
                    'page_number': page_num,
                    # 원본 크기 (포인트)
                    'width_pt': width,
                    'height_pt': height,
                    # 원본 크기 (mm)
                    'width_mm': width_mm,
                    'height_mm': height_mm,
                    # 표시 크기 (회전 고려, mm)
                    'display_width_mm': display_width_mm,
                    'display_height_mm': display_height_mm,
                    # 크기 포맷팅
                    'size_formatted': format_size_mm(width, height),
                    'size_formatted_with_rotation': size_formatted_with_rotation,
                    # 용지 규격
                    'paper_size': paper_size,
                    # 회전 정보
                    'rotation': rotation,
                    'is_rotated': rotation != 0,
                    # 박스 좌표
                    'mediabox': [left, bottom, right, top],
                    # 재단선 정보 (초기값)
                    'has_bleed': False,
                    'bleed_info': {},
                    'min_bleed': 0
                }
                
                # Phase 2.5: 상세 재단선 정보 분석
                if trimbox and bleedbox and trimbox != bleedbox:
                    page_info['has_bleed'] = True
                    
                    # 각 방향별 재단 여백 계산
                    trim_coords = [float(x) for x in trimbox]
                    bleed_coords = [float(x) for x in bleedbox]
                    
                    # 재단선과 블리드의 차이를 계산하여 여백 크기 구함
                    page_info['bleed_info'] = {
                        'left': points_to_mm(trim_coords[0] - bleed_coords[0]),
                        'bottom': points_to_mm(trim_coords[1] - bleed_coords[1]),
                        'right': points_to_mm(bleed_coords[2] - trim_coords[2]),
                        'top': points_to_mm(bleed_coords[3] - trim_coords[3])
                    }
                    
                    # 최소 재단 여백 (가장 작은 쪽)
                    min_bleed = min(page_info['bleed_info'].values())
                    page_info['min_bleed'] = min_bleed
                
                pages_info.append(page_info)
                
                # 처음 3페이지만 상세 출력 (너무 많은 출력 방지)
                if page_num <= 3:
                    size_str = f"{page_info['size_formatted']}"
                    if paper_size != 'Custom':
                        size_str += f" ({paper_size})"
                    if rotation != 0:
                        size_str += f" - {rotation}° 회전"
                    print(f"    ✓ {page_num}페이지: {size_str}")
                    if page_info['has_bleed']:
                        print(f"      재단여백: {page_info['min_bleed']:.1f}mm")
        
        # 페이지가 많을 때는 요약 출력
        if len(pages_info) > 3:
            print(f"    ... 그 외 {len(pages_info) - 3}페이지")
        
        return pages_info
    
    def _analyze_fonts(self, pdf_obj, pdf_path):
        """
        폰트 정보 분석 - 외부 도구(pdffonts)만 사용하는 개선된 버전
        
        폰트 임베딩 상태는 인쇄 품질에 매우 중요한 요소입니다.
        임베딩되지 않은 폰트는 다른 시스템에서 다르게 표시될 수 있습니다.
        
        수정사항:
        - fonts_info의 타입과 내용을 더 엄격하게 검증
        - 실제 폰트 정보가 있는지 확인 (_not_checked 제외)
        - 메타데이터가 아닌 실제 폰트 데이터만 카운트
        
        Args:
            pdf_obj: pikepdf로 열린 PDF 객체 (사용하지 않지만 일관성을 위해 유지)
            pdf_path: PDF 파일 경로 (pdffonts 명령어에 전달)
            
        Returns:
            dict: 폰트 정보 또는 검사 실패 정보
        """
        print("  🔤 폰트 정보 분석 중...")
        
        # 외부 도구 사용 시도
        if HAS_EXTERNAL_TOOLS and hasattr(self, 'external_tools_status') and self.external_tools_status.get('pdffonts'):
            print("    📊 pdffonts를 사용한 정확한 분석 중...")
            
            try:
                # 외부 pdffonts 도구를 사용하여 폰트 정보 수집
                fonts_info = check_fonts_external(pdf_path)
                
                # === 수정된 부분: 더 엄격한 결과 검증 ===
                # fonts_info가 딕셔너리이고 비어있지 않은 경우
                if isinstance(fonts_info, dict) and fonts_info and not fonts_info.get('_not_checked'):
                    # 메타데이터가 아닌 실제 폰트 정보가 있는지 확인
                    # '_'로 시작하는 키는 메타데이터이므로 제외
                    actual_fonts = {k: v for k, v in fonts_info.items() if not k.startswith('_')}
                    
                    if actual_fonts:  # 실제 폰트 정보가 있는 경우
                        print(f"    ✓ 총 {len(actual_fonts)}개 폰트 발견 (pdffonts)")
                        
                        # 임베딩되지 않은 폰트 개수 계산
                        # .get('embedded', False)를 사용하여 키가 없을 때 안전하게 처리
                        not_embedded = sum(1 for f in actual_fonts.values() if not f.get('embedded', False))
                        if not_embedded > 0:
                            print(f"    ⚠️  {not_embedded}개 폰트가 임베딩되지 않음")
                        
                        # 서브셋 폰트 개수 계산 (파일 크기 최적화를 위해 사용되는 부분 폰트)
                        subset_count = sum(1 for f in actual_fonts.values() if f.get('subset', False))
                        if subset_count > 0:
                            print(f"    ✓ {subset_count}개 서브셋 폰트 발견 (최적화됨)")
                        
                        return fonts_info
                    else:
                        # fonts_info는 있지만 실제 폰트 정보가 없는 경우
                        print("    ❌ pdffonts 실행했지만 폰트 정보를 얻지 못함")
                else:
                    # fonts_info가 딕셔너리가 아니거나 비어있거나 _not_checked인 경우
                    print("    ❌ pdffonts 실행 실패 또는 잘못된 결과")
                    
            except Exception as e:
                # 예외 발생 시 안전하게 처리
                print(f"    ❌ 폰트 분석 중 오류: {str(e)}")
        else:
            # pdffonts가 설치되지 않은 경우
            print("    ❌ pdffonts가 설치되지 않음 - 폰트 검사 불가")
        
        # 외부 도구가 없거나 실패한 경우 - 검사하지 않음을 명시
        return {
            '_not_checked': True,
            '_message': 'pdffonts가 설치되지 않아 폰트 검사를 수행할 수 없습니다'
        }
    
    def _analyze_colors(self, pdf_obj):
        """
        색상 공간 정보 분석
        
        PDF에서 사용되는 색상 공간(RGB, CMYK, Gray, Spot Color 등)을 분석합니다.
        인쇄용 PDF는 일반적으로 CMYK를 사용해야 합니다.
        
        Args:
            pdf_obj: pikepdf로 열린 PDF 객체
            
        Returns:
            dict: 색상 공간 정보
        """
        print("  🎨 색상 정보 분석 중...")
        
        # 색상 정보를 저장할 딕셔너리 초기화
        color_info = {
            'color_spaces': set(),       # 사용된 색상 공간들 (중복 제거를 위해 set 사용)
            'has_rgb': False,            # RGB 색상 사용 여부
            'has_cmyk': False,           # CMYK 색상 사용 여부  
            'has_gray': False,           # 그레이스케일 사용 여부
            'has_spot_colors': False,    # 별색(Spot Color) 사용 여부
            'spot_color_names': [],      # 별색 이름 목록
            'spot_color_details': {},    # 별색 상세 정보
            'icc_profiles': []           # ICC 프로파일 목록
        }
        
        try:
            # 각 페이지를 순회하면서 색상 정보 수집
            for page_num, page in enumerate(pdf_obj.pages, 1):
                # 페이지에 리소스가 있는지 확인
                if '/Resources' in page:
                    resources = page.Resources
                    
                    # ColorSpace 리소스 확인
                    if '/ColorSpace' in resources:
                        # 각 색상 공간을 검사
                        for cs_name, cs_obj in resources.ColorSpace.items():
                            color_space = safe_str(cs_name)
                            color_info['color_spaces'].add(color_space)
                            
                            # RGB 색상 공간 확인
                            if 'RGB' in color_space.upper():
                                color_info['has_rgb'] = True
                            
                            # CMYK 색상 공간 확인
                            if 'CMYK' in color_space.upper():
                                color_info['has_cmyk'] = True
                            
                            # 그레이스케일 확인
                            if 'GRAY' in color_space.upper():
                                color_info['has_gray'] = True
                            
                            # 별색(Separation) 확인
                            if isinstance(cs_obj, list) and len(cs_obj) > 0:
                                if safe_str(cs_obj[0]) == '/Separation':
                                    color_info['has_spot_colors'] = True
                                    if len(cs_obj) > 1:
                                        spot_name = safe_str(cs_obj[1])
                                        
                                        # 새로운 별색이면 목록에 추가
                                        if spot_name not in color_info['spot_color_names']:
                                            color_info['spot_color_names'].append(spot_name)
                                            
                                            # 별색 상세 정보 저장
                                            color_info['spot_color_details'][spot_name] = {
                                                'name': spot_name,
                                                'pages': [page_num],
                                                'is_pantone': 'PANTONE' in spot_name.upper(),  # PANTONE 색상인지 확인
                                                'color_space': color_space
                                            }
                                        else:
                                            # 기존 별색이면 페이지만 추가
                                            color_info['spot_color_details'][spot_name]['pages'].append(page_num)
                            
                            # ICC 프로파일 확인 (색상 관리용)
                            if isinstance(cs_obj, list) and len(cs_obj) > 0:
                                if safe_str(cs_obj[0]) == '/ICCBased':
                                    color_info['icc_profiles'].append(color_space)
            
            # 결과 요약 출력
            print(f"    ✓ 색상 공간: {', '.join(color_info['color_spaces']) if color_info['color_spaces'] else '기본'}")
            if color_info['has_rgb']:
                print("    ✓ RGB 색상 사용")
            if color_info['has_cmyk']:
                print("    ✓ CMYK 색상 사용")
            if color_info['has_spot_colors']:
                # 별색이 많을 때는 처음 3개만 표시
                print(f"    ✓ 별색 {len(color_info['spot_color_names'])}개 사용: {', '.join(color_info['spot_color_names'][:3])}")
                if len(color_info['spot_color_names']) > 3:
                    print(f"       ... 그 외 {len(color_info['spot_color_names'])-3}개")
                
        except Exception as e:
            print(f"    ⚠️  색상 분석 중 일부 오류: {e}")
        
        # set을 list로 변환 (JSON 저장을 위해)
        color_info['color_spaces'] = list(color_info['color_spaces'])
        
        return color_info
    
    def _analyze_images(self, pdf_obj, pdf_path):
        """
        이미지 정보 분석
        
        PDF 내의 모든 이미지의 해상도, 색상 공간, 크기를 분석하여
        인쇄 품질을 평가합니다.
        
        Args:
            pdf_obj: pikepdf로 열린 PDF 객체 (사용하지 않지만 일관성을 위해 유지)
            pdf_path: PDF 파일 경로 (PyMuPDF에서 사용)
            
        Returns:
            dict: 이미지 분석 결과
        """
        print("  🖼️  이미지 정보 분석 중...")
        
        # 이미지 정보를 저장할 딕셔너리 초기화
        image_info = {
            'total_count': 0,               # 총 이미지 개수
            'low_resolution_count': 0,      # 저해상도 이미지 개수
            'images': [],                   # 이미지별 상세 정보
            'resolution_categories': {      # 해상도별 분류
                'critical': 0,              # 위험 (72 DPI 미만)
                'warning': 0,               # 주의 (72-150 DPI)
                'acceptable': 0,            # 양호 (150-300 DPI)
                'optimal': 0                # 최적 (300 DPI 이상)
            }
        }
        
        try:
            # PyMuPDF를 사용한 이미지 분석 - 별도의 문서 객체 사용
            doc = fitz.open(pdf_path)
            
            # 각 페이지의 이미지들을 검사
            for page_num, page in enumerate(doc, 1):
                # 페이지의 이미지 목록 가져오기
                image_list = page.get_images()
                
                # 각 이미지를 분석
                for img_index, img in enumerate(image_list):
                    image_info['total_count'] += 1
                    
                    # 이미지 정보 추출
                    xref = img[0]  # 이미지 참조 번호
                    pix = fitz.Pixmap(doc, xref)  # 픽스맵으로 변환
                    
                    # 이미지 데이터 구성
                    img_data = {
                        'page': page_num,
                        'width': pix.width,      # 이미지 폭 (픽셀)
                        'height': pix.height,    # 이미지 높이 (픽셀)
                        'dpi': 0,               # 해상도 (계산 필요)
                        'resolution_category': '',  # 해상도 카테고리
                        'colorspace': pix.colorspace.name if pix.colorspace else 'Unknown',  # 색상 공간
                        'size_bytes': len(pix.samples),  # 이미지 데이터 크기
                        'has_alpha': pix.alpha          # 투명도 채널 여부
                    }
                    
                    # DPI 계산 (Document에서의 표시 크기 기준)
                    if img[2] > 0 and img[3] > 0:  # 표시 크기가 있는 경우
                        img_width_pt = img[2]   # 문서에서의 표시 폭 (포인트)
                        img_height_pt = img[3]  # 문서에서의 표시 높이 (포인트)
                        
                        # DPI = 픽셀 수 / (포인트 크기 / 72)
                        dpi_x = pix.width / (img_width_pt / 72.0)
                        dpi_y = pix.height / (img_height_pt / 72.0)
                        img_data['dpi'] = min(dpi_x, dpi_y)  # 더 낮은 쪽을 기준으로
                        
                        # 해상도 카테고리 분류
                        if img_data['dpi'] < Config.MIN_IMAGE_DPI:  # 72 DPI 미만
                            img_data['resolution_category'] = 'critical'
                            image_info['resolution_categories']['critical'] += 1
                            image_info['low_resolution_count'] += 1
                        elif img_data['dpi'] < Config.WARNING_IMAGE_DPI:  # 72-150 DPI
                            img_data['resolution_category'] = 'warning'
                            image_info['resolution_categories']['warning'] += 1
                        elif img_data['dpi'] < Config.OPTIMAL_IMAGE_DPI:  # 150-300 DPI
                            img_data['resolution_category'] = 'acceptable'
                            image_info['resolution_categories']['acceptable'] += 1
                        else:  # 300 DPI 이상
                            img_data['resolution_category'] = 'optimal'
                            image_info['resolution_categories']['optimal'] += 1
                    
                    image_info['images'].append(img_data)
                    
                    # 메모리 정리 (중요: 픽스맵은 명시적으로 해제해야 함)
                    pix = None
            
            # 문서 닫기
            doc.close()
            
            # 결과 요약 출력
            print(f"    ✓ 총 {image_info['total_count']}개 이미지 발견")
            if image_info['low_resolution_count'] > 0:
                print(f"    ⚠️  {image_info['low_resolution_count']}개 이미지가 저해상도 ({Config.MIN_IMAGE_DPI} DPI 미만)")
            
            # 해상도 분포 출력 (이미지가 있는 경우에만)
            if image_info['total_count'] > 0:
                print(f"    • 최적(300 DPI↑): {image_info['resolution_categories']['optimal']}개")
                print(f"    • 양호(150-300): {image_info['resolution_categories']['acceptable']}개")
                print(f"    • 주의(72-150): {image_info['resolution_categories']['warning']}개")
                print(f"    • 위험(72 미만): {image_info['resolution_categories']['critical']}개")
                
        except Exception as e:
            print(f"    ⚠️  이미지 분석 중 일부 오류: {e}")
        
        return image_info
    
    def _check_issues(self, analysis_result):
        """
        발견된 문제점들을 종합하여 체크
        
        기본적인 PDF 품질 문제들을 검사하고 issues 리스트에 추가합니다.
        폰트 검사가 수행되지 않은 경우에는 적절한 메시지를 표시합니다.
        
        Args:
            analysis_result: 분석 결과 딕셔너리 (참조로 전달되어 수정됨)
        """
        print("\n🔍 문제점 검사 중...")
        
        issues = analysis_result['issues']
        
        # 1. 페이지 크기 일관성 검사 (회전 고려)
        pages = analysis_result['pages']
        if pages:
            # 회전을 고려한 표시 크기로 그룹화
            size_count = {}
            for page in pages:
                # 크기를 반올림하여 약간의 오차 허용
                size_key = (round(page['display_width_mm']), round(page['display_height_mm']))
                if size_key not in size_count:
                    size_count[size_key] = {
                        'pages': [],
                        'size_str': f"{page['display_width_mm']:.0f}×{page['display_height_mm']:.0f}mm",
                        'paper_size': page['paper_size'],
                        'rotation': page['rotation']
                    }
                size_count[size_key]['pages'].append(page)
            
            # 가장 일반적인 크기 찾기
            common_size_info = max(size_count.items(), key=lambda x: len(x[1]['pages']))
            common_size_key = common_size_info[0]
            common_size_data = common_size_info[1]
            
            # 크기가 다른 페이지들 수집
            inconsistent_pages_detail = []
            for size_key, size_data in size_count.items():
                if size_key != common_size_key:
                    for page in size_data['pages']:
                        inconsistent_pages_detail.append({
                            'page': page['page_number'],
                            'size': size_data['size_str'],
                            'paper_size': size_data['paper_size'],
                            'rotation': page['rotation']
                        })
            
            # 페이지 크기 불일치를 하나의 이슈로 통합
            if inconsistent_pages_detail:
                detail_msg = f"기준 크기: {common_size_data['size_str']} ({common_size_data['paper_size']})"
                
                issues.append({
                    'type': 'page_size_inconsistent',
                    'severity': 'warning',
                    'message': f"페이지 크기 불일치",
                    'base_size': common_size_data['size_str'],
                    'base_paper': common_size_data['paper_size'],
                    'affected_pages': [p['page'] for p in inconsistent_pages_detail],
                    'page_details': inconsistent_pages_detail,
                    'suggestion': f"모든 페이지를 동일한 크기로 통일하세요 ({detail_msg})"
                })
        
        # 2. 폰트 임베딩 검사 - 수정된 부분
        fonts = analysis_result['fonts']
        
        # 폰트 검사가 수행되지 않은 경우
        if fonts.get('_not_checked'):
            issues.append({
                'type': 'font_check_not_performed',
                'severity': 'warning',
                'message': "폰트 검사 미수행",
                'suggestion': fonts.get('_message', 'pdffonts를 설치하여 정확한 폰트 검사를 수행하세요')
            })
        else:
            # 정상적으로 검사된 경우만 폰트 임베딩 문제 확인
            font_issues = {}
            
            for font_key, font_info in fonts.items():
                if font_key.startswith('_'):  # 메타데이터는 건너뛰기
                    continue
                    
                # 임베딩되지 않았고 표준 폰트가 아닌 경우
                if not font_info['embedded'] and not font_info.get('is_standard', False):
                    font_name = font_info.get('base_font', font_info['name'])
                    if font_name not in font_issues:
                        font_issues[font_name] = []
                    # page가 0이면 전체 문서를 의미 (pdffonts 사용 시)
                    if font_info['page'] > 0:
                        font_issues[font_name].append(font_info['page'])
            
            # 폰트 임베딩 이슈를 하나로 통합
            if font_issues:
                all_pages = []
                all_fonts = list(font_issues.keys())
                for pages_list in font_issues.values():
                    all_pages.extend(pages_list)
                all_pages = sorted(list(set(all_pages)))  # 중복 제거 및 정렬
                
                # 페이지 정보가 없으면 전체 문서에 해당
                if not all_pages or 0 in all_pages:
                    message = f"폰트 미임베딩 - {len(all_fonts)}개 폰트 (전체 문서)"
                else:
                    message = f"폰트 미임베딩 - {len(all_fonts)}개 폰트"
                
                issues.append({
                    'type': 'font_not_embedded',
                    'severity': 'error',
                    'message': message,
                    'affected_pages': all_pages if all_pages else [],
                    'fonts': all_fonts,
                    'suggestion': "PDF 내보내기 시 '모든 폰트 포함' 옵션을 선택하세요"
                })
        
        # 3. RGB 색상 사용 검사
        colors = analysis_result['colors']
        if colors['has_rgb'] and not colors['has_cmyk']:
            issues.append({
                'type': 'rgb_only',
                'severity': 'warning',
                'message': "RGB 색상만 사용됨 (인쇄용은 CMYK 권장)",
                'suggestion': "인쇄 품질을 위해 CMYK로 변환하세요"
            })
        
        # 4. 별색 사용 검사
        if colors['has_spot_colors'] and colors['spot_color_names']:
            # PANTONE 색상 개수 확인
            pantone_colors = [name for name in colors['spot_color_names'] 
                            if 'PANTONE' in name.upper()]
            
            # 별색 개수에 따른 심각도 결정
            severity = 'info'
            suggestion = "별색 사용 시 추가 인쇄 비용이 발생할 수 있습니다"
            
            if len(colors['spot_color_names']) > 2:
                severity = 'warning'
                suggestion = "별색이 많습니다. 비용 절감을 위해 CMYK 변환을 고려하세요"
            
            # 별색이 사용된 페이지 수집
            spot_pages = []
            for spot_detail in colors['spot_color_details'].values():
                spot_pages.extend(spot_detail['pages'])
            spot_pages = sorted(list(set(spot_pages)))
            
            issues.append({
                'type': 'spot_colors',
                'severity': severity,
                'message': f"별색 {len(colors['spot_color_names'])}개 사용: {', '.join(colors['spot_color_names'][:3])}",
                'affected_pages': spot_pages,
                'spot_colors': colors['spot_color_names'],
                'pantone_count': len(pantone_colors),
                'suggestion': suggestion
            })
        
        # 5. 이미지 해상도 검사
        images = analysis_result.get('images', {})
        if images.get('low_resolution_count', 0) > 0:
            # 저해상도 이미지들 수집
            low_res_images = [img for img in images.get('images', []) 
                            if img['dpi'] > 0 and img['dpi'] < Config.MIN_IMAGE_DPI]
            
            low_res_pages = []
            min_dpi = float('inf')
            for img in low_res_images:
                low_res_pages.append(img['page'])
                if img['dpi'] < min_dpi:
                    min_dpi = img['dpi']
            low_res_pages = sorted(list(set(low_res_pages)))
            
            issues.append({
                'type': 'low_resolution_image',
                'severity': 'error',
                'message': f"저해상도 이미지 - {images['low_resolution_count']}개",
                'affected_pages': low_res_pages,
                'min_dpi': min_dpi,
                'suggestion': f"인쇄 품질을 위해 최소 {Config.MIN_IMAGE_DPI} DPI 이상으로 교체하세요"
            })
        
        # 주의가 필요한 이미지 (72-150 DPI)도 정보 제공
        if images.get('resolution_categories', {}).get('warning', 0) > 0:
            warning_images = [img for img in images.get('images', [])
                            if img.get('resolution_category') == 'warning']
            warning_pages = sorted(list(set([img['page'] for img in warning_images])))
            
            issues.append({
                'type': 'medium_resolution_image',
                'severity': 'info',
                'message': f"중간 해상도 이미지 - {len(warning_images)}개 (72-150 DPI)",
                'affected_pages': warning_pages,
                'suggestion': "일반 문서용으로는 사용 가능하나, 고품질 인쇄에는 부적합할 수 있습니다"
            })
        
        # 6. 잉크량 검사
        ink = analysis_result.get('ink_coverage', {})
        if 'summary' in ink and ink['summary']['problem_pages']:
            problem_pages = []
            max_coverage = 0
            for problem in ink['summary']['problem_pages']:
                problem_pages.append(problem['page'])
                if problem['max_coverage'] > max_coverage:
                    max_coverage = problem['max_coverage']
            
            issues.append({
                'type': 'high_ink_coverage',
                'severity': 'error',
                'message': f"잉크량 초과 - 최대 {max_coverage:.1f}%",
                'affected_pages': problem_pages,
                'suggestion': f"잉크량을 {Config.MAX_INK_COVERAGE}% 이하로 조정하세요"
            })
        
        # 결과 출력
        if issues:
            print(f"\n⚠️  발견된 문제: {len(issues)}개")
            
            # 심각도별 분류
            errors = [i for i in issues if i['severity'] == 'error']
            warnings = [i for i in issues if i['severity'] == 'warning']
            infos = [i for i in issues if i['severity'] == 'info']
            
            # 오류 출력 (최대 3개까지)
            if errors:
                print(f"\n❌ 오류 ({len(errors)}개):")
                for issue in errors[:3]:
                    print(f"  • {issue['message']}")
                if len(errors) > 3:
                    print(f"  ... 그 외 {len(errors) - 3}개")
            
            # 경고 출력 (최대 3개까지)
            if warnings:
                print(f"\n⚠️  경고 ({len(warnings)}개):")
                for issue in warnings[:3]:
                    print(f"  • {issue['message']}")
                if len(warnings) > 3:
                    print(f"  ... 그 외 {len(warnings) - 3}개")
            
            # 정보 출력 (최대 2개까지)
            if infos:
                print(f"\nℹ️  정보 ({len(infos)}개):")
                for issue in infos[:2]:
                    print(f"  • {issue['message']}")
        else:
            print("\n✅ 기본 검사에서 문제점이 발견되지 않았습니다!")
    
    def _add_preflight_issues(self, analysis_result, preflight_result):
        """
        프리플라이트 결과를 이슈에 추가 - 중복 제거
        
        프리플라이트 검사에서 발견된 문제들을 메인 이슈 목록에 추가합니다.
        블리드 관련 이슈는 print_quality_checker에서 이미 처리했으므로 제외합니다.
        
        Args:
            analysis_result: 분석 결과 딕셔너리
            preflight_result: 프리플라이트 검사 결과
        """
        issues = analysis_result['issues']
        
        # 프리플라이트 실패 항목을 이슈에 추가
        for failed in preflight_result['failed']:
            # 블리드 관련 이슈는 print_quality_checker에서 이미 처리했으므로 제외
            if 'bleed' not in failed['rule_name'].lower():
                issues.append({
                    'type': 'preflight_failed',
                    'severity': 'error',
                    'message': f"[프리플라이트] {failed['rule_name']}: {failed['message']}",
                    'rule': failed['rule_name'],
                    'expected': failed['expected'],
                    'found': failed['found']
                })
        
        # 프리플라이트 경고 항목을 이슈에 추가
        for warning in preflight_result['warnings']:
            issues.append({
                'type': 'preflight_warning',
                'severity': 'warning',
                'message': f"[프리플라이트] {warning['rule_name']}: {warning['message']}",
                'rule': warning['rule_name'],
                'expected': warning['expected'],
                'found': warning['found']
            })
        
        # 정보성 메시지도 추가 (블리드 관련은 제외)
        for info in preflight_result.get('info', []):
            # 블리드 관련 정보는 이미 print_quality_checker에서 처리됨
            if 'bleed' not in info['rule_name'].lower():
                issues.append({
                    'type': 'preflight_info',
                    'severity': 'info',
                    'message': f"[프리플라이트] {info['rule_name']}: {info['message']}",
                    'rule': info['rule_name'],
                    'expected': info['expected'],
                    'found': info['found']
                })
    
    def _print_preflight_summary(self, preflight_result):
        """
        프리플라이트 결과 요약 출력
        
        프리플라이트 검사의 전체 결과를 보기 좋게 정리하여 출력합니다.
        
        Args:
            preflight_result: 프리플라이트 검사 결과 딕셔너리
        """
        print(f"\n📋 프리플라이트 검사 결과 ({preflight_result['profile']})")
        print("=" * 50)
        
        # 전체 상태에 따른 아이콘과 메시지
        status = preflight_result['overall_status']
        if status == 'pass':
            print("✅ 상태: 통과 - 인쇄 준비 완료!")
        elif status == 'warning':
            print("⚠️  상태: 경고 - 확인 필요")
        else:
            print("❌ 상태: 실패 - 수정 필요")
        
        # 항목별 개수 출력
        print(f"\n• 통과: {len(preflight_result['passed'])}개 항목")
        print(f"• 실패: {len(preflight_result['failed'])}개 항목")
        print(f"• 경고: {len(preflight_result['warnings'])}개 항목")
        print(f"• 정보: {len(preflight_result.get('info', []))}개 항목")
        
        # 실패 항목 상세 출력 (최대 3개까지)
        if preflight_result['failed']:
            print("\n[실패 항목]")
            for failed in preflight_result['failed'][:3]:
                print(f"  ❌ {failed['rule_name']}: {failed['message']}")
            if len(preflight_result['failed']) > 3:
                print(f"  ... 그 외 {len(preflight_result['failed'])-3}개")
        
        # 자동 수정 가능한 항목이 있으면 안내
        if preflight_result['auto_fixable']:
            print(f"\n💡 {len(preflight_result['auto_fixable'])}개 항목은 자동 수정 가능합니다")