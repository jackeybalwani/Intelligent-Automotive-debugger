"""
DBC Parser Module
Parses DBC (Database CAN) files for signal decoding
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging
import cantools

logger = logging.getLogger(__name__)

@dataclass
class Signal:
    """Represents a CAN signal"""
    name: str
    start_bit: int
    size: int
    is_little_endian: bool
    is_signed: bool
    factor: float
    offset: float
    minimum: float
    maximum: float
    unit: str
    receivers: List[str] = field(default_factory=list)
    multiplexer_id: Optional[int] = None
    is_multiplexer: bool = False
    
    def decode(self, data: bytes) -> float:
        """Decode signal value from CAN data"""
        # Implementation depends on bit ordering and signal properties
        pass

@dataclass
class Message:
    """Represents a CAN message definition"""
    id: int
    name: str
    dlc: int
    sender: str
    signals: Dict[str, Signal] = field(default_factory=dict)
    cycle_time: Optional[int] = None
    comment: Optional[str] = None
    is_extended: bool = False

class DBCParser:
    """
    Parser for DBC (CAN Database) files
    """
    
    def __init__(self):
        self.messages: Dict[int, Message] = {}
        self.signals: Dict[str, Signal] = {}
        self.nodes: List[str] = []
        self.attributes: Dict[str, Any] = {}
        self.value_tables: Dict[str, Dict[int, str]] = {}
        self.db = None  # cantools database object
    
    def parse_file(self, dbc_path: str) -> Dict[str, Any]:
        """
        Parse DBC file and extract message/signal definitions
        """
        dbc_path = Path(dbc_path)
        
        if not dbc_path.exists():
            raise FileNotFoundError(f"DBC file not found: {dbc_path}")
        
        try:
            # Use cantools for robust DBC parsing
            self.db = cantools.database.load_file(str(dbc_path))
            
            # Extract information from cantools database
            self._extract_from_cantools()
            
            # Return parsed information
            return {
                'messages': self._messages_to_dict(),
                'signals': self._signals_to_dict(),
                'nodes': self.nodes,
                'attributes': self.attributes,
                'value_tables': self.value_tables,
                'statistics': self.get_statistics()
            }
            
        except Exception as e:
            logger.error(f"Error parsing DBC file: {e}")
            # Fallback to manual parsing
            return self._manual_parse(dbc_path)
    
    def _extract_from_cantools(self):
        """
        Extract information from cantools database
        """
        # Extract nodes
        self.nodes = list(self.db.nodes)
        
        # Extract messages and signals
        for msg in self.db.messages:
            message = Message(
                id=msg.frame_id,
                name=msg.name,
                dlc=msg.length,
                sender=msg.senders[0] if msg.senders else "",
                is_extended=msg.is_extended_frame
            )
            
            if hasattr(msg, 'cycle_time'):
                message.cycle_time = msg.cycle_time
            
            if hasattr(msg, 'comment'):
                message.comment = msg.comment
            
            # Extract signals
            for sig in msg.signals:
                signal = Signal(
                    name=sig.name,
                    start_bit=sig.start,
                    size=sig.length,
                    is_little_endian=(sig.byte_order == 'little_endian'),
                    is_signed=sig.is_signed,
                    factor=sig.scale,
                    offset=sig.offset,
                    minimum=sig.minimum if sig.minimum is not None else 0,
                    maximum=sig.maximum if sig.maximum is not None else 0,
                    unit=sig.unit if sig.unit else "",
                    receivers=list(sig.receivers) if sig.receivers else []
                )
                
                if hasattr(sig, 'is_multiplexer'):
                    signal.is_multiplexer = sig.is_multiplexer
                
                if hasattr(sig, 'multiplexer_ids'):
                    signal.multiplexer_id = sig.multiplexer_ids[0] if sig.multiplexer_ids else None
                
                message.signals[signal.name] = signal
                self.signals[f"{message.name}.{signal.name}"] = signal
            
            self.messages[message.id] = message
        
        # Extract value tables
        for msg in self.db.messages:
            for sig in msg.signals:
                if sig.choices:
                    self.value_tables[f"{msg.name}.{sig.name}"] = sig.choices
    
    def _manual_parse(self, dbc_path: Path) -> Dict[str, Any]:
        """
        Manual DBC parsing as fallback
        """
        with open(dbc_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Parse nodes
        self._parse_nodes(content)
        
        # Parse messages
        self._parse_messages(content)
        
        # Parse signals
        self._parse_signals(content)
        
        # Parse attributes
        self._parse_attributes(content)
        
        # Parse value tables
        self._parse_value_tables(content)
        
        return {
            'messages': self._messages_to_dict(),
            'signals': self._signals_to_dict(),
            'nodes': self.nodes,
            'attributes': self.attributes,
            'value_tables': self.value_tables,
            'statistics': self.get_statistics()
        }
    
    def _parse_nodes(self, content: str):
        """Parse network nodes from DBC"""
        pattern = re.compile(r'BU_\s+(.*)')
        match = pattern.search(content)
        if match:
            self.nodes = match.group(1).split()
    
    def _parse_messages(self, content: str):
        """Parse message definitions from DBC"""
        pattern = re.compile(
            r'BO_\s+(\d+)\s+(\w+):\s+(\d+)\s+(\w+)'
        )
        
        for match in pattern.finditer(content):
            msg_id = int(match.group(1))
            msg_name = match.group(2)
            dlc = int(match.group(3))
            sender = match.group(4)
            
            # Check if extended ID (> 0x7FF for 11-bit IDs)
            is_extended = msg_id > 0x7FF
            
            self.messages[msg_id] = Message(
                id=msg_id,
                name=msg_name,
                dlc=dlc,
                sender=sender,
                is_extended=is_extended
            )
    
    def _parse_signals(self, content: str):
        """Parse signal definitions from DBC"""
        pattern = re.compile(
            r'SG_\s+(\w+)\s*(?:(\w+)\s*)?:\s*(\d+)\|(\d+)@(\d+)([\+\-])\s*\(([^,]+),([^)]+)\)\s*\[([^|]+)\|([^\]]+)\]\s*"([^"]*)"\s*(.*)'
        )
        
        current_msg_id = None
        
        # Find which message each signal belongs to
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('BO_'):
                match = re.match(r'BO_\s+(\d+)', line)
                if match:
                    current_msg_id = int(match.group(1))
            
            elif line.strip().startswith('SG_'):
                match = pattern.match(line.strip())
                if match and current_msg_id and current_msg_id in self.messages:
                    signal_name = match.group(1)
                    start_bit = int(match.group(3))
                    size = int(match.group(4))
                    byte_order = int(match.group(5))  # 0=motorola, 1=intel
                    is_signed = match.group(6) == '-'
                    factor = float(match.group(7))
                    offset = float(match.group(8))
                    minimum = float(match.group(9))
                    maximum = float(match.group(10))
                    unit = match.group(11)
                    receivers = match.group(12).split() if match.group(12) else []
                    
                    signal = Signal(
                        name=signal_name,
                        start_bit=start_bit,
                        size=size,
                        is_little_endian=(byte_order == 1),
                        is_signed=is_signed,
                        factor=factor,
                        offset=offset,
                        minimum=minimum,
                        maximum=maximum,
                        unit=unit,
                        receivers=receivers
                    )
                    
                    self.messages[current_msg_id].signals[signal_name] = signal
                    self.signals[f"{self.messages[current_msg_id].name}.{signal_name}"] = signal
    
    def _parse_attributes(self, content: str):
        """Parse attributes from DBC"""
        # Parse attribute definitions
        attr_def_pattern = re.compile(r'BA_DEF_\s+(\w+)?\s*"([^"]+)"\s+(\w+)')
        
        for match in attr_def_pattern.finditer(content):
            scope = match.group(1) if match.group(1) else "GLOBAL"
            attr_name = match.group(2)
            attr_type = match.group(3)
            
            if attr_name not in self.attributes:
                self.attributes[attr_name] = {
                    'scope': scope,
                    'type': attr_type,
                    'values': {}
                }
        
        # Parse attribute values
        attr_val_pattern = re.compile(r'BA_\s+"([^"]+)"\s+(.*);')
        
        for match in attr_val_pattern.finditer(content):
            attr_name = match.group(1)
            attr_value = match.group(2)
            
            if attr_name in self.attributes:
                self.attributes[attr_name]['values']['default'] = attr_value
    
    def _parse_value_tables(self, content: str):
        """Parse value tables (enumerations) from DBC"""
        pattern = re.compile(r'VAL_\s+(\d+)\s+(\w+)\s+((?:\d+\s+"[^"]+"\s*)+);')
        
        for match in pattern.finditer(content):
            msg_id = int(match.group(1))
            signal_name = match.group(2)
            values_str = match.group(3)
            
            # Parse value pairs
            value_pattern = re.compile(r'(\d+)\s+"([^"]+)"')
            values = {}
            
            for value_match in value_pattern.finditer(values_str):
                value = int(value_match.group(1))
                description = value_match.group(2)
                values[value] = description
            
            if msg_id in self.messages:
                msg_name = self.messages[msg_id].name
                self.value_tables[f"{msg_name}.{signal_name}"] = values
    
    def decode_message(self, can_id: int, data: bytes) -> Dict[str, Any]:
        """
        Decode CAN message using DBC definitions
        """
        if self.db:
            # Use cantools for decoding
            try:
                message = self.db.get_message_by_frame_id(can_id)
                decoded = message.decode(data)
                return {
                    'message_name': message.name,
                    'signals': decoded
                }
            except Exception as e:
                logger.debug(f"Could not decode message {can_id:08X}: {e}")
                return None
        
        # Manual decoding fallback
        if can_id not in self.messages:
            return None
        
        message = self.messages[can_id]
        decoded_signals = {}
        
        for signal_name, signal in message.signals.items():
            try:
                value = self._decode_signal(signal, data)
                decoded_signals[signal_name] = {
                    'value': value,
                    'unit': signal.unit
                }
                
                # Add enumeration if available
                key = f"{message.name}.{signal_name}"
                if key in self.value_tables and int(value) in self.value_tables[key]:
                    decoded_signals[signal_name]['text'] = self.value_tables[key][int(value)]
                    
            except Exception as e:
                logger.debug(f"Error decoding signal {signal_name}: {e}")
        
        return {
            'message_name': message.name,
            'signals': decoded_signals
        }
    
    def _decode_signal(self, signal: Signal, data: bytes) -> float:
        """
        Decode a signal value from CAN data
        """
        if len(data) * 8 < signal.start_bit + signal.size:
            return 0  # Not enough data
        
        # Extract bits
        value = 0
        
        if signal.is_little_endian:
            # Intel byte order
            for i in range(signal.size):
                byte_index = (signal.start_bit + i) // 8
                bit_index = (signal.start_bit + i) % 8
                
                if byte_index < len(data):
                    bit_value = (data[byte_index] >> bit_index) & 1
                    value |= bit_value << i
        else:
            # Motorola byte order
            for i in range(signal.size):
                bit_position = signal.start_bit - i
                byte_index = bit_position // 8
                bit_index = 7 - (bit_position % 8)
                
                if 0 <= byte_index < len(data):
                    bit_value = (data[byte_index] >> bit_index) & 1
                    value |= bit_value << (signal.size - 1 - i)
        
        # Handle signed values
        if signal.is_signed and value & (1 << (signal.size - 1)):
            value -= (1 << signal.size)
        
        # Apply factor and offset
        physical_value = value * signal.factor + signal.offset
        
        # Clamp to min/max
        if signal.minimum != 0 or signal.maximum != 0:
            physical_value = max(signal.minimum, min(signal.maximum, physical_value))
        
        return physical_value
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get DBC statistics
        """
        total_signals = sum(len(msg.signals) for msg in self.messages.values())
        
        return {
            'total_messages': len(self.messages),
            'total_signals': total_signals,
            'total_nodes': len(self.nodes),
            'extended_ids': sum(1 for msg in self.messages.values() if msg.is_extended),
            'standard_ids': sum(1 for msg in self.messages.values() if not msg.is_extended),
            'messages_with_cycle_time': sum(1 for msg in self.messages.values() if msg.cycle_time),
            'total_value_tables': len(self.value_tables)
        }
    
    def _messages_to_dict(self) -> Dict[str, Any]:
        """Convert messages to dictionary format"""
        return {
            str(msg_id): {
                'id': msg.id,
                'name': msg.name,
                'dlc': msg.dlc,
                'sender': msg.sender,
                'is_extended': msg.is_extended,
                'cycle_time': msg.cycle_time,
                'comment': msg.comment,
                'signals': list(msg.signals.keys())
            }
            for msg_id, msg in self.messages.items()
        }
    
    def _signals_to_dict(self) -> Dict[str, Any]:
        """Convert signals to dictionary format"""
        return {
            name: {
                'name': sig.name,
                'start_bit': sig.start_bit,
                'size': sig.size,
                'is_little_endian': sig.is_little_endian,
                'is_signed': sig.is_signed,
                'factor': sig.factor,
                'offset': sig.offset,
                'minimum': sig.minimum,
                'maximum': sig.maximum,
                'unit': sig.unit,
                'receivers': sig.receivers
            }
            for name, sig in self.signals.items()
        }
    
    def validate_format(self, file_path: Path) -> bool:
        """
        Validate if file is a valid DBC file
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)  # Read first 1KB
                
                # Check for DBC keywords
                dbc_keywords = ['VERSION', 'NS_', 'BS_', 'BU_', 'BO_', 'SG_']
                return any(keyword in content for keyword in dbc_keywords)
                
        except Exception as e:
            logger.error(f"Error validating DBC format: {e}")
            return False
