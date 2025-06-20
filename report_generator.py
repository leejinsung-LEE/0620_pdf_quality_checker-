# report_generator.py - 호환성 브릿지 파일
"""
report_generator.py - ReportGenerator 호환성 브릿지
기존 import 경로를 유지하면서 새로운 모듈화된 구조를 사용합니다.

이 파일은 기존의 2000줄 report_generator.py를 대체합니다.
모든 실제 구현은 reports/ 폴더의 모듈들로 이동했습니다.

Phase 4.0: 모듈화된 구조로 전환 (2025.06.17)
"""

# 새로운 모듈화된 ReportGenerator를 import
from reports import ReportGenerator

# 기존 코드 호환성을 위해 동일한 이름으로 export
__all__ = ['ReportGenerator']

# 버전 정보 (기존 코드가 참조할 수 있음)
__version__ = '4.0.0'

# 기존 코드가 직접 접근할 수 있는 일부 유틸리티 함수들
# (필요한 경우에만 추가)
def get_report_version():
    """보고서 버전 정보 반환"""
    return __version__

# 추가 호환성 지원이 필요한 경우 여기에 추가
# 예: 기존 코드가 특정 상수나 함수를 직접 참조하는 경우

"""
전환 가이드:
1. 기존 report_generator.py를 report_generator_backup.py로 백업
2. 이 파일을 report_generator.py로 저장
3. reports/ 폴더가 있는지 확인
4. 테스트 실행

기존 import는 그대로 작동합니다:
    from report_generator import ReportGenerator
    
새로운 import도 사용 가능합니다:
    from reports import ReportGenerator
"""