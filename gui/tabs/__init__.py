# gui/tabs/__init__.py
# GUI 탭 패키지

"""
GUI 탭 패키지
실시간, 통계, 이력 탭을 포함합니다.
"""

from .realtime_tab import RealtimeTab
from .statistics_tab import StatisticsTab
from .history_tab import HistoryTab

__all__ = ['RealtimeTab', 'StatisticsTab', 'HistoryTab']