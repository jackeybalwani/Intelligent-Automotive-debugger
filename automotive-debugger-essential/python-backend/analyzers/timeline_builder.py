"""
Timeline Builder Module
Builds timeline visualization data
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TimelineBuilder:
    """
    Builds timeline visualization data
    """
    
    def __init__(self):
        pass
    
    async def build_timeline(self, log_data: List[Any]) -> Dict[str, Any]:
        """
        Build timeline data for visualization
        """
        timeline = {
            'events': self._extract_events(log_data),
            'time_range': self._calculate_time_range(log_data),
            'event_types': self._categorize_events(log_data),
            'statistics': self._calculate_statistics(log_data)
        }
        
        return timeline
    
    def _extract_events(self, log_data: List[Any]) -> List[Dict[str, Any]]:
        """Extract events from log data"""
        events = []
        
        for item in log_data:
            if hasattr(item, 'timestamp'):
                event = {
                    'timestamp': item.timestamp,
                    'type': 'message',
                    'data': item.to_dict() if hasattr(item, 'to_dict') else str(item)
                }
                events.append(event)
        
        return events
    
    def _calculate_time_range(self, log_data: List[Any]) -> Dict[str, float]:
        """Calculate time range of data"""
        if not log_data:
            return {'start': 0, 'end': 0}
        
        timestamps = []
        for item in log_data:
            if hasattr(item, 'timestamp'):
                timestamps.append(item.timestamp)
        
        if not timestamps:
            return {'start': 0, 'end': 0}
        
        return {
            'start': min(timestamps),
            'end': max(timestamps)
        }
    
    def _categorize_events(self, log_data: List[Any]) -> Dict[str, int]:
        """Categorize events by type"""
        categories = {}
        
        for item in log_data:
            if hasattr(item, 'is_error') and item.is_error:
                categories['error'] = categories.get('error', 0) + 1
            else:
                categories['normal'] = categories.get('normal', 0) + 1
        
        return categories
    
    def _calculate_statistics(self, log_data: List[Any]) -> Dict[str, Any]:
        """Calculate timeline statistics"""
        return {
            'total_events': len(log_data),
            'duration': self._calculate_duration(log_data),
            'event_rate': self._calculate_event_rate(log_data)
        }
    
    def _calculate_duration(self, log_data: List[Any]) -> float:
        """Calculate total duration"""
        time_range = self._calculate_time_range(log_data)
        return time_range['end'] - time_range['start']
    
    def _calculate_event_rate(self, log_data: List[Any]) -> float:
        """Calculate events per second"""
        duration = self._calculate_duration(log_data)
        if duration > 0:
            return len(log_data) / duration
        return 0
