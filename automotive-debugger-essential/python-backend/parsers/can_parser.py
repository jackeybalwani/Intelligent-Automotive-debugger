"""
CAN Parser Module
Parses various CAN log formats including Linux SocketCAN format
"""

import re
import struct
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Generator
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class CANMessage:
    """Represents a single CAN message"""
    timestamp: float
    channel: str
    can_id: int
    is_extended: bool
    is_error: bool
    is_remote: bool
    dlc: int
    data: bytes
    raw_line: str = ""
    
    def __str__(self):
        data_hex = ' '.join(f'{b:02X}' for b in self.data)
        return f"{self.timestamp:.6f} {self.channel} {self.can_id:08X}#{data_hex}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'channel': self.channel,
            'can_id': self.can_id,
            'can_id_hex': f"{self.can_id:08X}",
            'is_extended': self.is_extended,
            'is_error': self.is_error,
            'is_remote': self.is_remote,
            'dlc': self.dlc,
            'data': self.data.hex(),
            'data_list': list(self.data)
        }

class CANParser:
    """
    Parser for CAN log files in various formats
    """
    
    def __init__(self):
        # Regex patterns for different CAN log formats
        self.patterns = {
            # Linux SocketCAN format: (timestamp) interface id#data
            'socketcan': re.compile(
                r'\((\d+\.\d+)\)\s+(\w+)\s+([0-9A-Fa-f]+)#([0-9A-Fa-f]*)'
            ),
            
            # CANalyzer ASC format
            'asc': re.compile(
                r'^(\d+\.\d+)\s+(\d+)\s+([0-9A-Fa-fx]+)\s+(Rx|Tx)\s+d\s+(\d+)\s+([0-9A-Fa-f\s]+)'
            ),
            
            # PCAN format
            'pcan': re.compile(
                r'(\d+)\s+(\d+\.\d+)\s+(Rx|Tx)\s+([0-9A-Fa-f]+)\s+(\d+)\s+([0-9A-Fa-f\s]+)'
            ),
            
            # Simple format: timestamp,id,dlc,data
            'simple': re.compile(
                r'(\d+\.?\d*),([0-9A-Fa-f]+),(\d+),([0-9A-Fa-f,\s]+)'
            ),
            
            # J1939 format (extended CAN)
            'j1939': re.compile(
                r'\((\d+\.\d+)\)\s+(\w+)\s+(1[0-9A-Fa-f]{7})#([0-9A-Fa-f]*)'
            )
        }
        
        self.current_format = None
        self.statistics = {}
    
    def validate_format(self, file_path: Path) -> bool:
        """
        Validate if file is a valid CAN log
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first few lines
                for _ in range(10):
                    line = f.readline()
                    if not line:
                        break
                    
                    # Try to parse the line
                    for format_name, pattern in self.patterns.items():
                        if pattern.match(line.strip()):
                            self.current_format = format_name
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating CAN format: {e}")
            return False
    
    def parse_file(self, file_path: str, chunk_size: int = 10000) -> Generator[List[CANMessage], None, None]:
        """
        Parse CAN log file in chunks for memory efficiency
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Auto-detect format if not already detected
        if not self.current_format:
            self.validate_format(file_path)
        
        messages_buffer = []
        line_count = 0
        error_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line_count += 1
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue
                    
                    # Skip header lines
                    if any(header in line.lower() for header in ['time', 'id', 'dlc', 'data', 'channel']):
                        continue
                    
                    try:
                        message = self.parse_line(line)
                        if message:
                            messages_buffer.append(message)
                            
                            # Yield chunk when buffer is full
                            if len(messages_buffer) >= chunk_size:
                                yield messages_buffer
                                messages_buffer = []
                                
                    except Exception as e:
                        error_count += 1
                        if error_count < 10:  # Log first 10 errors
                            logger.debug(f"Error parsing line {line_count}: {e}")
                
                # Yield remaining messages
                if messages_buffer:
                    yield messages_buffer
                    
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise
        
        logger.info(f"Parsed {line_count} lines with {error_count} errors")
    
    def parse_line(self, line: str) -> Optional[CANMessage]:
        """
        Parse a single line of CAN log
        """
        # Try SocketCAN format first (most common in sample)
        match = self.patterns['socketcan'].match(line)
        if match:
            timestamp = float(match.group(1))
            channel = match.group(2)
            can_id_str = match.group(3)
            data_str = match.group(4)
            
            # Parse CAN ID
            can_id = int(can_id_str, 16)
            is_extended = len(can_id_str) > 3  # Extended if more than 11 bits
            
            # Parse data
            data_bytes = bytes.fromhex(data_str) if data_str else b''
            
            return CANMessage(
                timestamp=timestamp,
                channel=channel,
                can_id=can_id,
                is_extended=is_extended,
                is_error=False,
                is_remote=False,
                dlc=len(data_bytes),
                data=data_bytes,
                raw_line=line
            )
        
        # Try J1939 format
        match = self.patterns['j1939'].match(line)
        if match:
            timestamp = float(match.group(1))
            channel = match.group(2)
            can_id = int(match.group(3), 16)
            data_str = match.group(4)
            
            data_bytes = bytes.fromhex(data_str) if data_str else b''
            
            return CANMessage(
                timestamp=timestamp,
                channel=channel,
                can_id=can_id,
                is_extended=True,  # J1939 always uses extended IDs
                is_error=False,
                is_remote=False,
                dlc=len(data_bytes),
                data=data_bytes,
                raw_line=line
            )
        
        # Try other formats
        for format_name, pattern in self.patterns.items():
            if format_name in ['socketcan', 'j1939']:
                continue
                
            match = pattern.match(line)
            if match:
                return self._parse_format_specific(format_name, match, line)
        
        return None
    
    def _parse_format_specific(self, format_name: str, match, line: str) -> Optional[CANMessage]:
        """
        Parse format-specific CAN message
        """
        try:
            if format_name == 'asc':
                timestamp = float(match.group(1))
                channel = f"can{match.group(2)}"
                can_id = int(match.group(3), 16) if 'x' not in match.group(3) else int(match.group(3).replace('x', ''), 16)
                direction = match.group(4)
                dlc = int(match.group(5))
                data_str = match.group(6).replace(' ', '')
                data_bytes = bytes.fromhex(data_str)[:dlc]
                
                return CANMessage(
                    timestamp=timestamp,
                    channel=channel,
                    can_id=can_id,
                    is_extended=can_id > 0x7FF,
                    is_error=False,
                    is_remote=False,
                    dlc=dlc,
                    data=data_bytes,
                    raw_line=line
                )
            
            elif format_name == 'simple':
                timestamp = float(match.group(1))
                can_id = int(match.group(2), 16)
                dlc = int(match.group(3))
                data_str = match.group(4).replace(',', '').replace(' ', '')
                data_bytes = bytes.fromhex(data_str)[:dlc]
                
                return CANMessage(
                    timestamp=timestamp,
                    channel='can0',
                    can_id=can_id,
                    is_extended=can_id > 0x7FF,
                    is_error=False,
                    is_remote=False,
                    dlc=dlc,
                    data=data_bytes,
                    raw_line=line
                )
                
        except Exception as e:
            logger.debug(f"Error parsing {format_name} format: {e}")
        
        return None
    
    def get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """
        Get statistics about the CAN log file
        """
        file_path = Path(file_path)
        stats = {
            'total_messages': 0,
            'unique_ids': set(),
            'channels': set(),
            'time_range': {'start': None, 'end': None},
            'message_rate': 0,
            'error_frames': 0,
            'extended_ids': 0,
            'standard_ids': 0,
            'id_frequency': {},
            'dlc_distribution': {},
            'file_size': file_path.stat().st_size
        }
        
        first_timestamp = None
        last_timestamp = None
        
        for chunk in self.parse_file(file_path, chunk_size=10000):
            for msg in chunk:
                stats['total_messages'] += 1
                stats['unique_ids'].add(msg.can_id)
                stats['channels'].add(msg.channel)
                
                # Track timestamps
                if first_timestamp is None:
                    first_timestamp = msg.timestamp
                last_timestamp = msg.timestamp
                
                # Track ID types
                if msg.is_extended:
                    stats['extended_ids'] += 1
                else:
                    stats['standard_ids'] += 1
                
                # Track errors
                if msg.is_error:
                    stats['error_frames'] += 1
                
                # ID frequency
                id_hex = f"{msg.can_id:08X}"
                stats['id_frequency'][id_hex] = stats['id_frequency'].get(id_hex, 0) + 1
                
                # DLC distribution
                stats['dlc_distribution'][msg.dlc] = stats['dlc_distribution'].get(msg.dlc, 0) + 1
        
        # Convert sets to lists for JSON serialization
        stats['unique_ids'] = len(stats['unique_ids'])
        stats['channels'] = list(stats['channels'])
        
        # Calculate time range and message rate
        if first_timestamp and last_timestamp:
            stats['time_range']['start'] = first_timestamp
            stats['time_range']['end'] = last_timestamp
            duration = last_timestamp - first_timestamp
            if duration > 0:
                stats['message_rate'] = stats['total_messages'] / duration
        
        # Get top IDs
        stats['top_ids'] = sorted(
            stats['id_frequency'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return stats
    
    def filter_messages(self, messages: List[CANMessage], 
                       can_ids: Optional[List[int]] = None,
                       time_range: Optional[Tuple[float, float]] = None,
                       channels: Optional[List[str]] = None) -> List[CANMessage]:
        """
        Filter CAN messages based on criteria
        """
        filtered = messages
        
        if can_ids:
            filtered = [m for m in filtered if m.can_id in can_ids]
        
        if time_range:
            start, end = time_range
            filtered = [m for m in filtered if start <= m.timestamp <= end]
        
        if channels:
            filtered = [m for m in filtered if m.channel in channels]
        
        return filtered
    
    def detect_bus_off(self, messages: List[CANMessage], threshold_ms: int = 100) -> List[Dict[str, Any]]:
        """
        Detect potential bus-off conditions
        """
        bus_offs = []
        
        # Group messages by channel
        channel_messages = {}
        for msg in messages:
            if msg.channel not in channel_messages:
                channel_messages[msg.channel] = []
            channel_messages[msg.channel].append(msg)
        
        # Check for gaps in each channel
        for channel, channel_msgs in channel_messages.items():
            if len(channel_msgs) < 2:
                continue
            
            sorted_msgs = sorted(channel_msgs, key=lambda m: m.timestamp)
            
            for i in range(1, len(sorted_msgs)):
                gap = (sorted_msgs[i].timestamp - sorted_msgs[i-1].timestamp) * 1000  # Convert to ms
                
                if gap > threshold_ms:
                    bus_offs.append({
                        'channel': channel,
                        'start_time': sorted_msgs[i-1].timestamp,
                        'end_time': sorted_msgs[i].timestamp,
                        'gap_ms': gap,
                        'last_msg_before': sorted_msgs[i-1].to_dict(),
                        'first_msg_after': sorted_msgs[i].to_dict()
                    })
        
        return bus_offs
