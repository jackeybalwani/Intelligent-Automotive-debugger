"""
ASC Parser Module
Parses Vector ASC (ASCII) log files
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ASCMessage:
    """Represents a single ASC message"""
    timestamp: float
    channel: int
    can_id: int
    direction: str
    dlc: int
    data: bytes
    raw_line: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'channel': self.channel,
            'can_id': self.can_id,
            'direction': self.direction,
            'dlc': self.dlc,
            'data': self.data.hex()
        }

class ASCParser:
    """
    Parser for Vector ASC files
    """
    
    def __init__(self):
        self.patterns = {
            'asc': re.compile(r'^(\d+\.\d+)\s+(\d+)\s+([0-9A-Fa-fx]+)\s+(Rx|Tx)\s+d\s+(\d+)\s+([0-9A-Fa-f\s]+)')
        }
    
    def validate_format(self, file_path: Path) -> bool:
        """Validate if file is a valid ASC file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for _ in range(10):
                    line = f.readline()
                    if not line:
                        break
                    if self.patterns['asc'].match(line.strip()):
                        return True
            return False
        except Exception as e:
            logger.error(f"Error validating ASC format: {e}")
            return False
    
    def parse_file(self, file_path: str, chunk_size: int = 10000) -> Generator[List[ASCMessage], None, None]:
        """Parse ASC file in chunks"""
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
    
    def parse_line(self, line: str) -> Optional[ASCMessage]:
        """Parse a single line of ASC log"""
        match = self.patterns['asc'].match(line)
        if match:
            timestamp = float(match.group(1))
            channel = int(match.group(2))
            can_id_str = match.group(3)
            direction = match.group(4)
            dlc = int(match.group(5))
            data_str = match.group(6).replace(' ', '')
            
            # Parse CAN ID
            can_id = int(can_id_str, 16) if 'x' not in can_id_str else int(can_id_str.replace('x', ''), 16)
            
            # Parse data
            data_bytes = bytes.fromhex(data_str)[:dlc]
            
            return ASCMessage(
                timestamp=timestamp,
                channel=channel,
                can_id=can_id,
                direction=direction,
                dlc=dlc,
                data=data_bytes,
                raw_line=line
            )
        
        return None
    
    def get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """Get statistics about the ASC file"""
        stats = {
            'total_messages': 0,
            'unique_ids': set(),
            'channels': set(),
            'time_range': {'start': None, 'end': None},
            'file_size': Path(file_path).stat().st_size
        }
        
        first_timestamp = None
        last_timestamp = None
        
        for chunk in self.parse_file(file_path, chunk_size=10000):
            for msg in chunk:
                stats['total_messages'] += 1
                stats['unique_ids'].add(msg.can_id)
                stats['channels'].add(msg.channel)
                
                if first_timestamp is None:
                    first_timestamp = msg.timestamp
                last_timestamp = msg.timestamp
        
        stats['unique_ids'] = len(stats['unique_ids'])
        stats['channels'] = list(stats['channels'])
        
        if first_timestamp and last_timestamp:
            stats['time_range']['start'] = first_timestamp
            stats['time_range']['end'] = last_timestamp
        
        return stats
