# print_quality_checker.py - 고급 인쇄 품질 검사 엔진
# 2025.06 수정: Ghostscript를 사용한 정확한 오버프린트 검사로 전환
"""
print_quality_checker.py - 인쇄 품질을 전문적으로 검사하는 클래스

주요 기능:
1. 투명도 검사 - 인쇄 시 문제가 될 수 있는 투명 효과 탐지
2. 오버프린트 검사 - Ghostscript를 사용한 고신뢰도 중복인쇄 설정 확인
3. 블리드 검사 - 재단선 여백 확인
4. 별색 검사 - PANTONE 등 특수 색상 사용 확인
5. 이미지 압축 검사 - 과도한 압축으로 인한 품질 저하 확인
6. 텍스트 크기 검사 - 인쇄 시 읽기 어려운 작은 텍스트 확인

외부 도구가 없으면 해당 검사를 수행하지 않음 (안전한 폴백 방식)
"""

# 필요한 라이브러리들을 가져옵니다
import fitz  # PyMuPDF - PDF 파일을 읽고 분석하는 라이브러리 (이미지 검사용으로만 사용)
import pikepdf  # PDF 파일의 내부 구조를 정밀하게 분석하는 라이브러리
from pathlib import Path  # 파일 경로를 다루는 라이브러리
from utils import points_to_mm, safe_float  # 유틸리티 함수들
from config import Config  # 설정 파일
import re  # 정규표현식 라이브러리

# 새로 추가된 외부 도구 모듈을 안전하게 가져오기 시도
try:
    # external_tools 모듈에서 필요한 함수들을 가져옵니다
    from external_tools import check_overprint_external, check_external_tools_status
    HAS_EXTERNAL_TOOLS = True  # 외부 도구를 사용할 수 있음을 표시
except ImportError:
    # 만약 external_tools 모듈이 없다면 기존 방식으로 동작
    HAS_EXTERNAL_TOOLS = False
    print("경고: external_tools 모듈을 찾을 수 없습니다. 기존 방식으로 폴백합니다.")


class PrintQualityChecker:
    """
    인쇄 품질을 전문적으로 검사하는 클래스
    
    이 클래스는 PDF 파일의 인쇄 품질에 영향을 줄 수 있는 다양한 요소들을 검사합니다.
    각 검사 항목은 독립적으로 동작하며, 문제가 발생하더라도 다른 검사에 영향을 주지 않습니다.
    """
    
    def __init__(self):
        """
        클래스 초기화 함수
        
        인스턴스가 생성될 때 자동으로 호출되며, 필요한 변수들을 초기화합니다.
        """
        self.issues = []      # 심각한 문제들을 저장하는 리스트
        self.warnings = []    # 경고사항들을 저장하는 리스트
        
        # 외부 도구 상태 확인
        if HAS_EXTERNAL_TOOLS:
            # 외부 도구들(Ghostscript, pdffonts 등)의 설치 상태를 확인
            self.external_tools_status = check_external_tools_status()
            
            # Ghostscript가 설치되어 있지 않으면 경고 메시지 출력
            if not self.external_tools_status.get('ghostscript'):
                print("⚠️  Ghostscript가 설치되어 있지 않습니다. 오버프린트 검사가 제한됩니다.")
        
    def check_all(self, pdf_path, pages_info=None):
        """
        모든 인쇄 품질 검사를 수행하는 메인 함수
        
        Args:
            pdf_path: 검사할 PDF 파일의 경로 (문자열)
            pages_info: pdf_analyzer에서 전달받은 페이지 정보 (블리드 포함)
        
        Returns:
            dict: 모든 검사 결과를 담은 딕셔너리
        """
        print("\n🔍 고급 인쇄 품질 검사 시작...")
        
        # 각 검사 항목별로 결과를 수집합니다
        # Config.CHECK_OPTIONS에서 각 검사의 활성화 여부를 확인
        results = {
            # 투명도 검사 - 설정에서 활성화된 경우에만 실행
            'transparency': self.check_transparency(pdf_path) if Config.CHECK_OPTIONS.get('transparency', False) else {'has_transparency': False},
            
            # 오버프린트 검사 - 기본적으로 활성화
            'overprint': self.check_overprint(pdf_path) if Config.CHECK_OPTIONS.get('overprint', True) else {'has_overprint': False},
            
            # 블리드 검사는 pdf_analyzer의 결과를 사용
            'bleed': self.process_bleed_info(pages_info) if Config.CHECK_OPTIONS.get('bleed', True) else {'has_proper_bleed': True},
            
            # 별색 검사 - 기본적으로 활성화
            'spot_colors': self.check_spot_color_usage(pdf_path) if Config.CHECK_OPTIONS.get('spot_colors', True) else {'has_spot_colors': False},
            
            # 이미지 압축 검사 - 기본적으로 활성화
            'image_compression': self.check_image_compression(pdf_path) if Config.CHECK_OPTIONS.get('image_compression', True) else {'total_images': 0},
            
            # 최소 텍스트 크기 검사 - 기본적으로 활성화
            'text_size': self.check_minimum_text_size(pdf_path) if Config.CHECK_OPTIONS.get('minimum_text', True) else {'has_small_text': False},
            
            # 발견된 문제들과 경고사항들
            'issues': self.issues,
            'warnings': self.warnings
        }
        
        return results
    
    def check_transparency(self, pdf_path):
        """
        투명도 사용 검사
        
        인쇄 시 투명도는 플래튼(평탄화) 처리가 필요할 수 있어서 미리 확인이 필요합니다.
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            dict: 투명도 검사 결과
        """
        print("  • 투명도 검사 중...")
        
        # 투명도 검사 결과를 저장할 딕셔너리 초기화
        transparency_info = {
            'has_transparency': False,          # 투명도 사용 여부
            'transparent_objects': [],          # 투명도를 사용하는 객체들의 목록
            'pages_with_transparency': [],      # 투명도가 있는 페이지 번호들
            'requires_flattening': False        # 평탄화 처리가 필요한지 여부
        }
        
        try:
            # PyMuPDF를 사용해 PDF 파일을 엽니다
            doc = fitz.open(pdf_path)
            
            # 각 페이지를 순회하면서 투명도를 검사
            for page_num, page in enumerate(doc, 1):  # enumerate(doc, 1)은 1부터 페이지 번호를 시작
                # 페이지 내용을 딕셔너리 형태로 추출
                page_dict = page.get_text("dict")
                
                # 투명도 관련 패턴 검사
                has_transparency = False
                
                # 1. 이미지의 알파 채널 검사
                for img in page.get_images():
                    xref = img[0]  # 이미지의 참조 번호
                    pix = fitz.Pixmap(doc, xref)  # 이미지 데이터를 픽스맵으로 변환
                    
                    if pix.alpha:  # 알파 채널이 있으면 투명도 사용
                        has_transparency = True
                        transparency_info['transparent_objects'].append({
                            'page': page_num,
                            'type': 'image_with_alpha',  # 알파 채널을 가진 이미지
                            'xref': xref
                        })
                
                # 2. PDF 명령어에서 투명도 관련 연산자 검사
                contents = page.read_contents()  # 페이지의 원시 PDF 명령어들을 읽음
                if contents:
                    # 투명도 관련 PDF 연산자들의 리스트
                    transparency_operators = [
                        b'/CA',     # 스트로크 알파 (선 그리기의 투명도)
                        b'/ca',     # 채우기 알파 (채우기의 투명도)
                        b'/BM',     # 블렌드 모드 (색상 혼합 방식)
                        b'/SMask',  # 소프트 마스크 (복잡한 투명도 효과)
                        b'gs'       # 그래픽 상태 (투명도 설정 포함 가능)
                    ]
                    
                    # 각 연산자가 페이지 내용에 있는지 확인
                    for op in transparency_operators:
                        if op in contents:
                            has_transparency = True
                            transparency_info['transparent_objects'].append({
                                'page': page_num,
                                'type': 'transparency_operator',
                                'operator': op.decode('utf-8', errors='ignore')  # 바이트를 문자열로 변환
                            })
                            break  # 하나라도 발견되면 루프 종료
                
                # 투명도가 발견된 페이지를 기록
                if has_transparency:
                    transparency_info['has_transparency'] = True
                    transparency_info['pages_with_transparency'].append(page_num)
            
            # 파일을 닫아 메모리를 해제
            doc.close()
            
            # 투명도가 있으면 플래튼 필요
            if transparency_info['has_transparency']:
                transparency_info['requires_flattening'] = True
                
                # 경고 메시지를 warnings 리스트에 추가
                self.warnings.append({
                    'type': 'transparency_detected',
                    'severity': 'warning',
                    'message': f"투명도가 {len(transparency_info['pages_with_transparency'])}개 페이지에서 발견됨",
                    'pages': transparency_info['pages_with_transparency'],
                    'suggestion': "인쇄 전 투명도 평탄화(Flatten Transparency)를 권장합니다"
                })
            
            print(f"    ✓ 투명도 검사 완료: {'발견' if transparency_info['has_transparency'] else '없음'}")
            
        except Exception as e:
            # 예외가 발생하면 에러 메시지를 출력하고 경고에 추가
            print(f"    ⚠️ 투명도 검사 중 오류: {e}")
            self.warnings.append({
                'type': 'transparency_check_error',
                'severity': 'info',
                'message': f"투명도 검사 중 일부 오류 발생: {str(e)}"
            })
        
        return transparency_info
    
    def check_overprint(self, pdf_path):
        """
        중복인쇄(Overprint) 설정 검사 - Ghostscript만 사용하는 개선된 버전
        
        오버프린트는 인쇄에서 색상이 겹치는 부분의 처리 방식을 결정하는 중요한 설정입니다.
        잘못된 오버프린트 설정은 예상과 다른 인쇄 결과를 만들 수 있습니다.
        
        수정사항:
        - external_result의 타입과 내용을 더 엄격하게 검증
        - success 키를 확인하여 실제로 성공한 경우만 처리
        - 예상치 못한 반환값에 대한 안전한 처리
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            dict: 오버프린트 검사 결과
        """
        print("  • 중복인쇄 설정 검사 중...")
        
        # 기본 결과 구조 - 모든 가능한 키를 미리 정의
        overprint_info = {
            'has_overprint': False,                 # 오버프린트 설정이 있는지
            'has_problematic_overprint': False,     # 문제가 있는 오버프린트인지
            'overprint_objects': [],                # 오버프린트 객체들의 목록
            'pages_with_overprint': [],             # 오버프린트가 있는 페이지들
            'white_overprint_pages': [],            # 흰색 오버프린트 페이지들 (문제가 될 수 있음)
            'k_only_overprint_pages': [],           # K(검정)만 있는 오버프린트 페이지들
            'light_color_overprint_pages': [],      # 연한 색상 오버프린트 페이지들
            'image_overprint_pages': [],            # 이미지 오버프린트 페이지들
            '_not_checked': False,                  # 검사를 수행하지 못했는지 여부
            '_message': ''                          # 검사 실패 이유
        }
        
        # 외부 도구 사용 시도
        if HAS_EXTERNAL_TOOLS and hasattr(self, 'external_tools_status') and self.external_tools_status.get('ghostscript'):
            print("    📊 Ghostscript를 사용한 정확한 분석 중...")
            
            try:
                # 전체 페이지 검사 여부 결정 (성능 고려)
                # check_all_pages=False로 설정하여 빠른 검사 수행
                external_result = check_overprint_external(pdf_path, check_all_pages=False)
                
                # === 수정된 부분: 더 엄격한 결과 검증 ===
                # external_result가 딕셔너리인지 확인
                if isinstance(external_result, dict):
                    # success 키가 있고 True인 경우만 처리
                    if external_result.get('success', False):
                        # 외부 도구 결과를 기존 형식에 맞춰 병합
                        # _not_checked와 _message, success, error는 제외하고 병합
                        for key, value in external_result.items():
                            if key not in ['_not_checked', '_message', 'success', 'error']:
                                overprint_info[key] = value
                        
                        # 오버프린트 관련 경고/정보 추가
                        if overprint_info['has_overprint']:
                            if overprint_info['has_problematic_overprint']:
                                # 문제가 있는 오버프린트는 심각한 이슈로 분류
                                self.issues.append({
                                    'type': 'problematic_overprint_detected',
                                    'severity': 'error',
                                    'message': f"문제가 있는 오버프린트 설정 발견",
                                    'pages': overprint_info['pages_with_overprint'],
                                    'suggestion': "오버프린트 설정을 확인하고 필요시 제거하세요"
                                })
                            else:
                                # 일반적인 오버프린트는 정보로만 제공
                                self.warnings.append({
                                    'type': 'overprint_detected',
                                    'severity': 'info',
                                    'message': f"중복인쇄 설정이 {len(overprint_info['pages_with_overprint'])}개 페이지에서 발견됨",
                                    'pages': overprint_info['pages_with_overprint'],
                                    'suggestion': "의도적인 설정인지 확인하세요"
                                })
                        
                        print(f"    ✓ 중복인쇄 검사 완료: {'발견' if overprint_info['has_overprint'] else '없음'} (Ghostscript)")
                        return overprint_info
                    else:
                        # success가 False이거나 error가 있는 경우
                        error_msg = external_result.get('error', 'Ghostscript 실행 실패')
                        print(f"    ❌ Ghostscript 실행 실패: {error_msg}")
                        overprint_info['_not_checked'] = True
                        overprint_info['_message'] = f'Ghostscript 실행 실패: {error_msg}'
                else:
                    # external_result가 딕셔너리가 아닌 경우
                    print(f"    ❌ 예상치 못한 반환값 타입: {type(external_result)}")
                    overprint_info['_not_checked'] = True
                    overprint_info['_message'] = 'Ghostscript 검사 결과를 처리할 수 없습니다'
                    
            except Exception as e:
                # 예외 발생 시 안전하게 처리
                print(f"    ❌ 오버프린트 검사 중 오류: {str(e)}")
                overprint_info['_not_checked'] = True
                overprint_info['_message'] = f'오버프린트 검사 중 오류 발생: {str(e)}'
        else:
            # Ghostscript가 없는 경우
            print("    ❌ Ghostscript가 설치되지 않음 - 오버프린트 검사 불가")
            overprint_info['_not_checked'] = True
            overprint_info['_message'] = 'Ghostscript가 설치되지 않아 오버프린트 검사를 수행할 수 없습니다'
        
        # 검사하지 못한 경우 경고 추가
        if overprint_info['_not_checked']:
            self.warnings.append({
                'type': 'overprint_not_checked',
                'severity': 'warning',
                'message': "오버프린트 검사 미수행",
                'suggestion': overprint_info['_message']
            })
        
        return overprint_info
    
    def process_bleed_info(self, pages_info):
        """
        pdf_analyzer에서 전달받은 페이지 정보를 기반으로 블리드 정보 처리
        
        블리드는 인쇄물의 재단선 밖으로 나가는 여백 부분으로,
        재단 시 흰 여백이 생기지 않도록 하는 중요한 요소입니다.
        
        Args:
            pages_info: pdf_analyzer에서 분석한 페이지 정보들
            
        Returns:
            dict: 블리드 검사 결과
        """
        print("  • 재단선 여백 정보 처리 중...")
        
        # 블리드 정보를 저장할 딕셔너리
        bleed_info = {
            'has_proper_bleed': True,               # 적절한 블리드가 있는지
            'pages_without_bleed': [],              # 블리드가 부족한 페이지들
            'bleed_sizes': {},                      # 각 페이지의 블리드 크기 정보
            'min_required_bleed': Config.STANDARD_BLEED_SIZE  # 최소 필요 블리드 크기
        }
        
        # pages_info가 없으면 기본값 반환
        if not pages_info:
            return bleed_info
        
        try:
            # pdf_analyzer에서 전달받은 페이지 정보 처리
            for page_info in pages_info:
                page_num = page_info['page_number']
                
                # 블리드가 있는 페이지 처리
                if page_info.get('has_bleed'):
                    min_bleed = page_info.get('min_bleed', 0)
                    bleed_info['bleed_sizes'][page_num] = {
                        'sizes': page_info.get('bleed_info', {}),
                        'minimum': min_bleed
                    }
                    
                    # 재단 여백이 부족한 경우
                    if min_bleed < Config.STANDARD_BLEED_SIZE:
                        bleed_info['has_proper_bleed'] = False
                        bleed_info['pages_without_bleed'].append({
                            'page': page_num,
                            'current_bleed': min_bleed,
                            'required_bleed': Config.STANDARD_BLEED_SIZE
                        })
                else:
                    # 블리드 박스가 없는 경우
                    bleed_info['has_proper_bleed'] = False
                    bleed_info['pages_without_bleed'].append({
                        'page': page_num,
                        'current_bleed': 0,
                        'required_bleed': Config.STANDARD_BLEED_SIZE
                    })
            
            # 재단 여백 문제를 정보로만 보고 (심각한 오류가 아니므로)
            if not bleed_info['has_proper_bleed']:
                self.warnings.append({
                    'type': 'insufficient_bleed',
                    'severity': 'info',
                    'message': f"{len(bleed_info['pages_without_bleed'])}개 페이지에 재단 여백 부족",
                    'pages': [p['page'] for p in bleed_info['pages_without_bleed']],
                    'suggestion': f"모든 페이지에 최소 {Config.STANDARD_BLEED_SIZE}mm의 재단 여백이 필요합니다"
                })
            
            print(f"    ✓ 재단선 정보 처리 완료: {'정상' if bleed_info['has_proper_bleed'] else '정보 제공됨'}")
            
        except Exception as e:
            print(f"    ⚠️ 재단선 정보 처리 중 오류: {e}")
        
        return bleed_info
    
    def check_spot_color_usage(self, pdf_path):
        """
        별색(Spot Color) 사용 상세 검사
        
        별색은 PANTONE 등의 특수 색상으로, 일반적인 CMYK 4색 인쇄와 달리
        추가 비용이 발생하므로 정확한 확인이 필요합니다.
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            dict: 별색 사용 검사 결과
        """
        print("  • 별색 사용 상세 검사 중...")
        
        # 별색 정보를 저장할 딕셔너리
        spot_color_info = {
            'has_spot_colors': False,       # 별색 사용 여부
            'spot_colors': {},              # 사용된 별색들의 상세 정보
            'total_spot_colors': 0,         # 총 별색 개수
            'pages_with_spots': []          # 별색이 사용된 페이지들
        }
        
        try:
            # pikepdf를 사용해 PDF 내부 구조를 정밀하게 분석
            with pikepdf.open(pdf_path) as pdf:
                # 각 페이지를 순회
                for page_num, page in enumerate(pdf.pages, 1):
                    # 페이지에 리소스가 있고, 그 중에 ColorSpace가 있는지 확인
                    if '/Resources' in page and '/ColorSpace' in page.Resources:
                        # 색상 공간들을 하나씩 검사
                        for cs_name, cs_obj in page.Resources.ColorSpace.items():
                            # Separation 색상 공간 확인 (별색의 PDF 내부 표현)
                            if isinstance(cs_obj, list) and len(cs_obj) > 0:
                                if str(cs_obj[0]) == '/Separation':
                                    spot_color_info['has_spot_colors'] = True
                                    
                                    # 별색 이름 추출
                                    spot_name = str(cs_obj[1]) if len(cs_obj) > 1 else 'Unknown'
                                    
                                    # 새로운 별색이면 정보 추가
                                    if spot_name not in spot_color_info['spot_colors']:
                                        spot_color_info['spot_colors'][spot_name] = {
                                            'name': spot_name,
                                            'pages': [],
                                            'is_pantone': 'PANTONE' in spot_name.upper()  # PANTONE 색상인지 확인
                                        }
                                    
                                    # 이 별색이 사용된 페이지 추가
                                    spot_color_info['spot_colors'][spot_name]['pages'].append(page_num)
                                    
                                    # 별색이 사용된 페이지 목록에 추가 (중복 제거)
                                    if page_num not in spot_color_info['pages_with_spots']:
                                        spot_color_info['pages_with_spots'].append(page_num)
            
            # 총 별색 개수 계산
            spot_color_info['total_spot_colors'] = len(spot_color_info['spot_colors'])
            
            # 별색 사용 보고
            if spot_color_info['has_spot_colors']:
                # PANTONE 색상들만 따로 추출
                pantone_colors = [name for name, info in spot_color_info['spot_colors'].items() 
                                if info['is_pantone']]
                
                # 메시지 구성
                message = f"별색 {spot_color_info['total_spot_colors']}개 사용 중"
                if pantone_colors:
                    message += f" (PANTONE {len(pantone_colors)}개 포함)"
                
                # 경고 추가 (별색은 추가 비용이 발생하므로)
                self.warnings.append({
                    'type': 'spot_colors_used',
                    'severity': 'info',
                    'message': message,
                    'spot_colors': list(spot_color_info['spot_colors'].keys()),
                    'suggestion': "별색 사용 시 추가 인쇄 비용이 발생합니다. 의도적인 사용인지 확인하세요"
                })
            
            print(f"    ✓ 별색 검사 완료: {spot_color_info['total_spot_colors']}개 발견")
            
        except Exception as e:
            print(f"    ⚠️ 별색 검사 중 오류: {e}")
        
        return spot_color_info
    
    def check_image_compression(self, pdf_path):
        """
        이미지 압축 품질 검사
        
        과도한 이미지 압축은 인쇄 품질 저하의 주요 원인입니다.
        특히 JPEG 압축률이 너무 높으면 인쇄물에서 품질 문제가 발생할 수 있습니다.
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            dict: 이미지 압축 검사 결과
        """
        print("  • 이미지 압축 품질 검사 중...")
        
        # 압축 정보를 저장할 딕셔너리
        compression_info = {
            'total_images': 0,              # 총 이미지 개수
            'jpeg_compressed': 0,           # JPEG 압축된 이미지 개수
            'low_quality_images': [],       # 품질이 낮은 이미지들
            'compression_types': {},        # 압축 형식별 개수
            'quality_details': []           # 상세한 품질 분석 결과
        }
        
        try:
            # PyMuPDF로 PDF 열기
            doc = fitz.open(pdf_path)
            
            # 각 페이지의 이미지들을 검사
            for page_num, page in enumerate(doc, 1):
                for img_index, img in enumerate(page.get_images()):
                    compression_info['total_images'] += 1
                    xref = img[0]  # 이미지의 참조 번호
                    
                    # 이미지 정보 추출
                    try:
                        # PDF 내부의 이미지 객체 정보 가져오기
                        img_dict = doc.xref_object(xref)
                        
                        # img_dict가 문자열인 경우가 있음 - 타입 체크 추가
                        if isinstance(img_dict, str):
                            # 문자열인 경우 간단히 파싱 시도
                            if 'DCTDecode' in img_dict:  # JPEG 압축 방식
                                compression_info['jpeg_compressed'] += 1
                                if 'DCTDecode' not in compression_info['compression_types']:
                                    compression_info['compression_types']['DCTDecode'] = 0
                                compression_info['compression_types']['DCTDecode'] += 1
                            continue  # 다음 이미지로 넘어감
                        
                        # 정상적인 딕셔너리인 경우
                        if '/Filter' in img_dict:
                            filter_type = img_dict['/Filter']
                            
                            # 필터가 리스트인 경우 첫 번째 요소 사용
                            if isinstance(filter_type, list):
                                filter_type = filter_type[0]
                            
                            # 슬래시(/) 제거하여 필터 이름 추출
                            filter_name = str(filter_type).replace('/', '')
                            
                            # 압축 타입별 개수 카운트
                            if filter_name not in compression_info['compression_types']:
                                compression_info['compression_types'][filter_name] = 0
                            compression_info['compression_types'][filter_name] += 1
                            
                            # JPEG 압축 확인
                            if 'DCTDecode' in filter_name:
                                compression_info['jpeg_compressed'] += 1
                                
                                # 더 정밀한 이미지 품질 분석 시도
                                try:
                                    quality_detail = self._analyze_image_quality_detailed(
                                        xref, doc, page_num, img_index
                                    )
                                    compression_info['quality_details'].append(quality_detail)
                                    
                                    # 기존 로직과 호환성 유지
                                    if quality_detail['print_suitability'] == '인쇄 부적합':
                                        compression_info['low_quality_images'].append({
                                            'page': page_num,
                                            'image_index': img_index,
                                            'compression_ratio': quality_detail['compression_ratio'],
                                            'size': quality_detail['size'],
                                            'quality_level': quality_detail['estimated_jpeg_quality']
                                        })
                                except:
                                    # 상세 분석 실패 시 기존 방식 사용
                                    pix = fitz.Pixmap(doc, xref)
                                    pixel_count = pix.width * pix.height
                                    stream = doc.xref_stream(xref)
                                    compressed_size = len(stream)
                                    
                                    # 압축률 계산 (압축된 크기 / 픽셀 수)
                                    compression_ratio = compressed_size / pixel_count if pixel_count > 0 else 1
                                    
                                    # 압축률이 너무 높으면 (0.5 미만) 품질 문제로 판단
                                    if compression_ratio < 0.5:
                                        compression_info['low_quality_images'].append({
                                            'page': page_num,
                                            'image_index': img_index,
                                            'compression_ratio': compression_ratio,
                                            'size': f"{pix.width}x{pix.height}"
                                        })
                                    pix = None  # 메모리 해제
                                    
                    except Exception as e:
                        # 개별 이미지 처리 실패는 무시하고 계속 진행
                        print(f"      이미지 {xref} 처리 중 오류: {str(e)[:50]}")
                        continue
            
            # 파일 닫기
            doc.close()
            
            # 압축 품질 문제 보고
            if compression_info['low_quality_images']:
                self.warnings.append({
                    'type': 'high_compression_detected',
                    'severity': 'warning',
                    'message': f"{len(compression_info['low_quality_images'])}개 이미지가 과도하게 압축됨",
                    'count': len(compression_info['low_quality_images']),
                    'suggestion': "인쇄 품질을 위해 이미지 압축률을 낮추는 것을 권장합니다"
                })
            
            print(f"    ✓ 이미지 압축 검사 완료: {compression_info['total_images']}개 이미지 중 {compression_info['jpeg_compressed']}개 JPEG 압축")
            
        except Exception as e:
            print(f"    ⚠️ 이미지 압축 검사 중 오류: {e}")
            self.warnings.append({
                'type': 'image_compression_check_error',
                'severity': 'info',
                'message': f"이미지 압축 검사 중 일부 오류 발생: {str(e)[:100]}"
            })
        
        return compression_info
    
    def _analyze_image_quality_detailed(self, xref, doc, page_num, img_index):
        """
        더 정밀한 이미지 품질 분석
        
        이 함수는 이미지의 압축률, JPEG 품질, 인쇄 적합성을 종합적으로 분석합니다.
        
        Args:
            xref: 이미지 참조 번호
            doc: PDF 문서 객체
            page_num: 페이지 번호
            img_index: 페이지 내 이미지 인덱스
            
        Returns:
            dict: 상세한 품질 분석 결과
        """
        # 품질 정보를 저장할 딕셔너리 초기화
        quality_info = {
            'page': page_num,
            'image_index': img_index,
            'compression_ratio': 0,
            'estimated_jpeg_quality': 'Unknown',
            'visual_impact': '',
            'print_suitability': '',
            'size': ''
        }
        
        try:
            # 이미지 데이터 추출
            pix = fitz.Pixmap(doc, xref)
            pixel_count = pix.width * pix.height * pix.n  # 색상 채널 고려
            stream = doc.xref_stream(xref)  # 압축된 이미지 데이터
            compressed_size = len(stream)
            
            # 기본 정보 설정
            quality_info['size'] = f"{pix.width}x{pix.height}"
            quality_info['compression_ratio'] = compressed_size / pixel_count if pixel_count > 0 else 1
            
            # JPEG 품질 추정
            if b'\xff\xdb' in stream[:500]:  # 양자화 테이블 마커가 있으면
                # 간단한 품질 추정 (양자화 테이블 분석은 복잡하므로 간략화)
                bytes_per_pixel = compressed_size / (pix.width * pix.height)
                
                # 픽셀당 바이트 수로 품질 추정
                if bytes_per_pixel < 0.3:
                    quality_info['estimated_jpeg_quality'] = '매우 낮음 (50 이하)'
                elif bytes_per_pixel < 0.5:
                    quality_info['estimated_jpeg_quality'] = '낮음 (50-70)'
                elif bytes_per_pixel < 0.8:
                    quality_info['estimated_jpeg_quality'] = '보통 (70-85)'
                else:
                    quality_info['estimated_jpeg_quality'] = '높음 (85 이상)'
            
            # 이미지 용도별 적합성 판단
            if pix.width < 300 or pix.height < 300:
                # 작은 이미지는 품질이 덜 중요
                quality_info['visual_impact'] = '작은 아이콘/로고'
                quality_info['print_suitability'] = '품질 무관'
            else:
                # 큰 이미지는 품질이 중요
                bytes_per_pixel = compressed_size / (pix.width * pix.height)
                if bytes_per_pixel < 0.3:
                    quality_info['visual_impact'] = '눈에 띄는 품질 저하'
                    quality_info['print_suitability'] = '인쇄 부적합'
                elif bytes_per_pixel < 0.5:
                    quality_info['visual_impact'] = '약간의 품질 저하'
                    quality_info['print_suitability'] = '일반 문서 가능'
                else:
                    quality_info['visual_impact'] = '양호'
                    quality_info['print_suitability'] = '고품질 인쇄 가능'
            
            pix = None  # 메모리 해제
            
        except Exception as e:
            print(f"      상세 품질 분석 오류: {str(e)[:50]}")
        
        return quality_info
    
    def check_minimum_text_size(self, pdf_path):
        """
        최소 텍스트 크기 검사
        
        너무 작은 텍스트는 인쇄 시 읽기 어렵거나 번짐 현상이 발생할 수 있습니다.
        일반적으로 4pt 미만의 텍스트는 인쇄 품질에 문제가 생길 수 있습니다.
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            dict: 텍스트 크기 검사 결과
        """
        print("  • 최소 텍스트 크기 검사 중...")
        
        # 텍스트 크기 정보를 저장할 딕셔너리
        text_size_info = {
            'min_size_found': 999,          # 발견된 최소 텍스트 크기
            'small_text_pages': [],         # 작은 텍스트가 있는 페이지들
            'text_sizes': {},               # 페이지별 최소 텍스트 크기
            'has_small_text': False         # 작은 텍스트 존재 여부
        }
        
        MIN_TEXT_SIZE = 4.0  # 최소 권장 크기 (포인트)
        
        try:
            # PyMuPDF로 PDF 열기
            doc = fitz.open(pdf_path)
            
            # 각 페이지의 텍스트를 검사
            for page_num, page in enumerate(doc, 1):
                # 텍스트 블록을 딕셔너리 형태로 추출
                blocks = page.get_text("dict")
                page_min_size = 999  # 페이지별 최소 크기 초기화
                
                # 각 블록을 순회
                for block in blocks.get("blocks", []):
                    if block.get("type") == 0:  # 텍스트 블록인 경우 (type 0)
                        # 라인들을 순회
                        for line in block.get("lines", []):
                            # 스팬(같은 스타일의 텍스트 구간)들을 순회
                            for span in line.get("spans", []):
                                font_size = span.get("size", 0)  # 폰트 크기 추출
                                
                                if font_size > 0:
                                    # 페이지별 최소 크기 업데이트
                                    if font_size < page_min_size:
                                        page_min_size = font_size
                                    
                                    # 전체 최소 크기 업데이트
                                    if font_size < text_size_info['min_size_found']:
                                        text_size_info['min_size_found'] = font_size
                                    
                                    # 너무 작은 텍스트 확인
                                    if font_size < MIN_TEXT_SIZE:
                                        text_size_info['has_small_text'] = True
                                        
                                        # 중복 방지: 이미 추가된 페이지인지 확인
                                        existing_pages = [p['page'] for p in text_size_info['small_text_pages']]
                                        if page_num not in existing_pages:
                                            text_size_info['small_text_pages'].append({
                                                'page': page_num,
                                                'min_size': font_size
                                            })
                
                # 페이지에서 텍스트를 찾았으면 기록
                if page_min_size < 999:
                    text_size_info['text_sizes'][page_num] = page_min_size
            
            # 파일 닫기
            doc.close()
            
            # 작은 텍스트 경고
            if text_size_info['has_small_text']:
                self.warnings.append({
                    'type': 'small_text_detected',
                    'severity': 'warning',
                    'message': f"{len(text_size_info['small_text_pages'])}개 페이지에 {MIN_TEXT_SIZE}pt 미만의 작은 텍스트 발견",
                    'pages': [p['page'] for p in text_size_info['small_text_pages']],
                    'min_found': f"{text_size_info['min_size_found']:.1f}pt",
                    'suggestion': f"인쇄 가독성을 위해 최소 {MIN_TEXT_SIZE}pt 이상의 텍스트 크기를 권장합니다"
                })
            
            print(f"    ✓ 텍스트 크기 검사 완료: 최소 {text_size_info['min_size_found']:.1f}pt")
            
        except Exception as e:
            print(f"    ⚠️ 텍스트 크기 검사 중 오류: {e}")
        
        return text_size_info