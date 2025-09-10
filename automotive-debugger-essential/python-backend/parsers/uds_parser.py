"""
UDS Parser Module
Parses UDS (Unified Diagnostic Services) log files
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class UDSMessage:
    """Represents a single UDS message"""
    timestamp: float
    source: str
    target: str
    service_id: int
    data: bytes
    response_code: Optional[int] = None
    raw_line: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'source': self.source,
            'target': self.target,
            'service_id': self.service_id,
            'data': self.data.hex(),
            'response_code': self.response_code
        }

class UDSParser:
    """
    Parser for UDS log files
    """
    
    def __init__(self):
        self.patterns = {
            'uds': re.compile(r'UDS\s+(\d+\.\d+)\s+(\w+)\s+->\s+(\w+)\s+([0-9A-Fa-f]+)')
        }
    
    def validate_format(self, file_path: Path) -> bool:
        """Validate if file is a valid UDS log"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for _ in range(10):
                    line = f.readline()
                    if not line:
                        break
                    if self.patterns['uds'].match(line.strip()):
                        return True
            return False
        except Exception as e:
            logger.error(f"Error validating UDS format: {e}")
            return False
    
    def parse_file(self, file_path: str, chunk_size: int = 10000) -> Generator[List[UDSMessage], None, None]:
        """Parse UDS log file in chunks"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        messages_buffer = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    message = self.parse_line(line)
                    if message:
                        messages_buffer.append(message)
                        
                        if len(messages_buffer) >= chunk_size:
                            yield messages_buffer
                            messages_buffer = []
                
                if messages_buffer:
                    yield messages_buffer
                    
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise
    
    def parse_line(self, line: str) -> Optional[UDSMessage]:
        """Parse a single line of UDS log"""
        match = self.patterns['uds'].match(line)
        if match:
            timestamp = float(match.group(1))
            source = match.group(2)
            target = match.group(3)
            data_str = match.group(4)
            
            data_bytes = bytes.fromhex(data_str) if data_str else b''
            service_id = data_bytes[0] if data_bytes else 0
            
            return UDSMessage(
                timestamp=timestamp,
                source=source,
                target=target,
                service_id=service_id,
                data=data_bytes
            )
        
        return None
    
    def get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """Get statistics about the UDS log file"""
        stats = {
            'total_messages': 0,
            'unique_services': set(),
            'time_range': {'start': None, 'end': None},
            'file_size': Path(file_path).stat().st_size
        }
        
        first_timestamp = None
        last_timestamp = None
        
        for chunk in self.parse_file(file_path, chunk_size=10000):
            for msg in chunk:
                stats['total_messages'] += 1
                stats['unique_services'].add(msg.service_id)
                
                if first_timestamp is None:
                    first_timestamp = msg.timestamp
                last_timestamp = msg.timestamp
        
        stats['unique_services'] = len(stats['unique_services'])
        
        if first_timestamp and last_timestamp:
            stats['time_range']['start'] = first_timestamp
            stats['time_range']['end'] = last_timestamp
        
        return stats
