"""
LIN Parser Module
Parses LIN (Local Interconnect Network) log files
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LINMessage:
    """Represents a single LIN message"""
    timestamp: float
    frame_id: int
    data: bytes
    checksum: int
    raw_line: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'frame_id': self.frame_id,
            'data': self.data.hex(),
            'checksum': self.checksum
        }

class LINParser:
    """
    Parser for LIN log files
    """
    
    def __init__(self):
        self.patterns = {
            'lin': re.compile(r'LIN\s+(\d+\.\d+)\s+(\d+)\s+([0-9A-Fa-f]+)')
        }
    
    def validate_format(self, file_path: Path) -> bool:
        """Validate if file is a valid LIN log"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for _ in range(10):
                    line = f.readline()
                    if not line:
                        break
                    if self.patterns['lin'].match(line.strip()):
                        return True
            return False
        except Exception as e:
            logger.error(f"Error validating LIN format: {e}")
            return False
    
    def parse_file(self, file_path: str, chunk_size: int = 10000) -> Generator[List[LINMessage], None, None]:
        """Parse LIN log file in chunks"""
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
    
    def parse_line(self, line: str) -> Optional[LINMessage]:
        """Parse a single line of LIN log"""
        match = self.patterns['lin'].match(line)
        if match:
            timestamp = float(match.group(1))
            frame_id = int(match.group(2))
            data_str = match.group(3)
            
            data_bytes = bytes.fromhex(data_str) if data_str else b''
            
            return LINMessage(
                timestamp=timestamp,
                frame_id=frame_id,
                data=data_bytes,
                checksum=0  # Placeholder
            )
        
        return None
    
    def get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """Get statistics about the LIN log file"""
        stats = {
            'total_messages': 0,
            'unique_frame_ids': set(),
            'time_range': {'start': None, 'end': None},
            'file_size': Path(file_path).stat().st_size
        }
        
        first_timestamp = None
        last_timestamp = None
        
        for chunk in self.parse_file(file_path, chunk_size=10000):
            for msg in chunk:
                stats['total_messages'] += 1
                stats['unique_frame_ids'].add(msg.frame_id)
                
                if first_timestamp is None:
                    first_timestamp = msg.timestamp
                last_timestamp = msg.timestamp
        
        stats['unique_frame_ids'] = len(stats['unique_frame_ids'])
        
        if first_timestamp and last_timestamp:
            stats['time_range']['start'] = first_timestamp
            stats['time_range']['end'] = last_timestamp
        
        return stats
