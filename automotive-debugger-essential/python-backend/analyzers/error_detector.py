"""
Error Detector Module
Detects and categorizes errors in automotive logs
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class Error:
    """Represents a detected error"""
    timestamp: float
    error_type: str
    severity: str  # Critical, High, Medium, Low
    code: str
    description: str
    source: str
    can_id: Optional[int] = None
    data: Optional[bytes] = None
    fix_suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'error_type': self.error_type,
            'severity': self.severity,
            'code': self.code,
            'description': self.description,
            'source': self.source,
            'can_id': f"{self.can_id:08X}" if self.can_id else None,
            'data': self.data.hex() if self.data else None,
            'fix_suggestion': self.fix_suggestion
        }

class ErrorDetector:
    """
    Comprehensive error detection for automotive logs
    """
    
    def __init__(self):
        # J1939 SPN fault codes
        self.j1939_spn_codes = {
            91: "Accelerator Pedal Position",
            94: "Fuel Delivery Pressure",
            100: "Engine Oil Pressure",
            102: "Intake Manifold Pressure",
            105: "Intake Manifold Temperature",
            110: "Engine Coolant Temperature",
            190: "Engine Speed",
            520: "SPN Suspect Parameter Number",
            629: "Controller #1",
            639: "J1939 Network #1",
            1569: "Engine Protection Torque Derate",
        }
        
        # UDS negative response codes
        self.uds_negative_responses = {
            0x10: "General Reject",
            0x11: "Service Not Supported",
            0x12: "Sub Function Not Supported",
            0x13: "Incorrect Message Length Or Invalid Format",
            0x14: "Response Too Long",
            0x21: "Busy Repeat Request",
            0x22: "Conditions Not Correct",
            0x24: "Request Sequence Error",
            0x25: "No Response From Subnet Component",
            0x26: "Failure Prevents Execution Of Requested Action",
            0x31: "Request Out Of Range",
            0x33: "Security Access Denied",
            0x35: "Invalid Key",
            0x36: "Exceeded Number Of Attempts",
            0x37: "Required Time Delay Not Expired",
            0x70: "Upload Download Not Accepted",
            0x71: "Transfer Data Suspended",
            0x72: "General Programming Failure",
            0x73: "Wrong Block Sequence Counter",
            0x78: "Request Correctly Received Response Pending",
            0x7E: "Sub Function Not Supported In Active Session",
            0x7F: "Service Not Supported In Active Session",
        }
        
        # Common DTC patterns
        self.dtc_patterns = {
            'P0': 'Powertrain - Generic',
            'P1': 'Powertrain - Manufacturer Specific',
            'P2': 'Powertrain - Generic',
            'P3': 'Powertrain - Generic & Manufacturer Specific',
            'C0': 'Chassis - Generic',
            'C1': 'Chassis - Manufacturer Specific',
            'C2': 'Chassis - Manufacturer Specific',
            'C3': 'Chassis - Generic & Manufacturer Specific',
            'B0': 'Body - Generic',
            'B1': 'Body - Manufacturer Specific',
            'B2': 'Body - Manufacturer Specific',
            'B3': 'Body - Generic & Manufacturer Specific',
            'U0': 'Network - Generic',
            'U1': 'Network - Manufacturer Specific',
            'U2': 'Network - Manufacturer Specific',
            'U3': 'Network - Generic & Manufacturer Specific',
        }
        
        # Error patterns to detect
        self.error_patterns = {
            'bus_off': re.compile(r'bus[- _]?off|busoff', re.IGNORECASE),
            'error_frame': re.compile(r'error[- _]?frame|err[- _]?frame', re.IGNORECASE),
            'timeout': re.compile(r'timeout|timed?[- _]?out', re.IGNORECASE),
            'checksum': re.compile(r'checksum|crc[- _]?error|crc[- _]?fail', re.IGNORECASE),
            'dlc_error': re.compile(r'dlc[- _]?error|wrong[- _]?dlc|invalid[- _]?dlc', re.IGNORECASE),
            'stuff_error': re.compile(r'stuff[- _]?error|bit[- _]?stuff', re.IGNORECASE),
            'form_error': re.compile(r'form[- _]?error|format[- _]?error', re.IGNORECASE),
            'ack_error': re.compile(r'ack[- _]?error|no[- _]?ack|acknowledge[- _]?error', re.IGNORECASE),
            'bit_error': re.compile(r'bit[- _]?error|bit[- _]?fail', re.IGNORECASE),
            'arbitration_lost': re.compile(r'arbitration[- _]?lost|arb[- _]?lost', re.IGNORECASE),
            'overrun': re.compile(r'overrun|overflow', re.IGNORECASE),
            'fault': re.compile(r'fault|fail|error|err', re.IGNORECASE),
            'dtc': re.compile(r'[PCBU][0-9A-F]{4}', re.IGNORECASE),
        }
    
    async def detect_errors(self, log_data: List[Any], dbc_data: Optional[Dict] = None) -> List[Error]:
        """
        Detect errors in log data
        """
        errors = []
        
        for data_chunk in log_data:
            if isinstance(data_chunk, list):
                # Process CAN messages
                chunk_errors = self._detect_can_errors(data_chunk, dbc_data)
                errors.extend(chunk_errors)
            elif isinstance(data_chunk, dict):
                # Process structured data
                chunk_errors = self._detect_structured_errors(data_chunk)
                errors.extend(chunk_errors)
            elif isinstance(data_chunk, str):
                # Process text logs
                chunk_errors = self._detect_text_errors(data_chunk)
                errors.extend(chunk_errors)
        
        # Sort errors by timestamp
        errors.sort(key=lambda e: e.timestamp)
        
        # Add fix suggestions
        for error in errors:
            error.fix_suggestion = self._suggest_fix(error)
        
        return errors
    
    def _detect_can_errors(self, messages: List[Any], dbc_data: Optional[Dict] = None) -> List[Error]:
        """
        Detect errors in CAN messages
        """
        errors = []
        
        # Check for bus-off conditions
        bus_off_errors = self._detect_bus_off(messages)
        errors.extend(bus_off_errors)
        
        # Check for error frames
        error_frame_errors = self._detect_error_frames(messages)
        errors.extend(error_frame_errors)
        
        # Check for J1939 DTCs
        j1939_errors = self._detect_j1939_dtc(messages)
        errors.extend(j1939_errors)
        
        # Check for UDS errors
        uds_errors = self._detect_uds_errors(messages)
        errors.extend(uds_errors)
        
        # Check for DLC errors
        dlc_errors = self._detect_dlc_errors(messages, dbc_data)
        errors.extend(dlc_errors)
        
        # Check for missing periodic messages
        timeout_errors = self._detect_timeouts(messages, dbc_data)
        errors.extend(timeout_errors)
        
        return errors
    
    def _detect_bus_off(self, messages: List[Any], gap_threshold_ms: float = 100) -> List[Error]:
        """
        Detect bus-off conditions based on message gaps
        """
        errors = []
        
        if len(messages) < 2:
            return errors
        
        # Sort messages by timestamp
        sorted_msgs = sorted(messages, key=lambda m: m.timestamp if hasattr(m, 'timestamp') else 0)
        
        for i in range(1, len(sorted_msgs)):
            gap_ms = (sorted_msgs[i].timestamp - sorted_msgs[i-1].timestamp) * 1000
            
            if gap_ms > gap_threshold_ms:
                error = Error(
                    timestamp=sorted_msgs[i-1].timestamp,
                    error_type='BUS_OFF',
                    severity='Critical',
                    code='E_BUS_OFF',
                    description=f'Potential bus-off detected. Gap of {gap_ms:.1f}ms between messages',
                    source=sorted_msgs[i-1].channel if hasattr(sorted_msgs[i-1], 'channel') else 'CAN',
                    can_id=sorted_msgs[i-1].can_id if hasattr(sorted_msgs[i-1], 'can_id') else None
                )
                errors.append(error)
        
        return errors
    
    def _detect_error_frames(self, messages: List[Any]) -> List[Error]:
        """
        Detect error frames in CAN messages
        """
        errors = []
        
        for msg in messages:
            if hasattr(msg, 'is_error') and msg.is_error:
                error = Error(
                    timestamp=msg.timestamp,
                    error_type='ERROR_FRAME',
                    severity='High',
                    code='E_CAN_ERROR_FRAME',
                    description='CAN error frame detected',
                    source=msg.channel if hasattr(msg, 'channel') else 'CAN',
                    can_id=msg.can_id if hasattr(msg, 'can_id') else None,
                    data=msg.data if hasattr(msg, 'data') else None
                )
                errors.append(error)
        
        return errors
    
    def _detect_j1939_dtc(self, messages: List[Any]) -> List[Error]:
        """
        Detect J1939 diagnostic trouble codes
        """
        errors = []
        
        # J1939 DM1 (Active DTCs) - PGN 65226 (0xFECA)
        # J1939 DM2 (Previously Active DTCs) - PGN 65227 (0xFECB)
        dm1_pgn = 0xFECA
        dm2_pgn = 0xFECB
        
        for msg in messages:
            if not hasattr(msg, 'can_id'):
                continue
            
            # Extract PGN from CAN ID (for extended frame)
            if msg.can_id > 0x7FF:  # Extended frame
                pgn = (msg.can_id >> 8) & 0xFFFF
                
                if pgn == dm1_pgn or pgn == dm2_pgn:
                    # Parse DTC from data
                    if hasattr(msg, 'data') and len(msg.data) >= 8:
                        dtc_errors = self._parse_j1939_dm(msg, pgn)
                        errors.extend(dtc_errors)
        
        return errors
    
    def _parse_j1939_dm(self, msg: Any, pgn: int) -> List[Error]:
        """
        Parse J1939 DM1/DM2 messages for DTCs
        """
        errors = []
        
        # DM message format:
        # Byte 0-1: Lamp status
        # Byte 2-5: DTC 1 (SPN + FMI)
        # Byte 6-7: Occurrence count
        
        if len(msg.data) < 6:
            return errors
        
        # Extract lamp status
        lamp_status = (msg.data[0] << 8) | msg.data[1]
        
        # Extract DTCs (can have multiple)
        for i in range(2, len(msg.data) - 3, 4):
            if i + 3 < len(msg.data):
                # Extract SPN (Suspect Parameter Number)
                spn = (msg.data[i] | (msg.data[i+1] << 8) | ((msg.data[i+2] & 0xE0) << 11))
                # Extract FMI (Failure Mode Identifier)
                fmi = msg.data[i+2] & 0x1F
                
                if spn != 0:
                    spn_name = self.j1939_spn_codes.get(spn, f"SPN {spn}")
                    severity = 'Critical' if pgn == 0xFECA else 'Medium'
                    
                    error = Error(
                        timestamp=msg.timestamp,
                        error_type='J1939_DTC',
                        severity=severity,
                        code=f'SPN{spn}_FMI{fmi}',
                        description=f'J1939 DTC: {spn_name} - FMI {fmi}',
                        source='J1939',
                        can_id=msg.can_id,
                        data=msg.data
                    )
                    errors.append(error)
        
        return errors
    
    def _detect_uds_errors(self, messages: List[Any]) -> List[Error]:
        """
        Detect UDS (Unified Diagnostic Services) errors
        """
        errors = []
        
        for msg in messages:
            if not hasattr(msg, 'data') or len(msg.data) < 2:
                continue
            
            # Check for negative response (0x7F)
            if msg.data[0] == 0x7F:
                service_id = msg.data[1] if len(msg.data) > 1 else 0
                nrc = msg.data[2] if len(msg.data) > 2 else 0
                
                nrc_description = self.uds_negative_responses.get(nrc, f"Unknown NRC: {nrc:02X}")
                
                error = Error(
                    timestamp=msg.timestamp,
                    error_type='UDS_ERROR',
                    severity='Medium',
                    code=f'UDS_NRC_{nrc:02X}',
                    description=f'UDS Negative Response: Service {service_id:02X} - {nrc_description}',
                    source='UDS',
                    can_id=msg.can_id if hasattr(msg, 'can_id') else None,
                    data=msg.data
                )
                errors.append(error)
            
            # Check for DTCs in response to service 0x19 (Read DTC Information)
            elif msg.data[0] == 0x59:  # Positive response to service 0x19
                dtc_errors = self._parse_uds_dtc(msg)
                errors.extend(dtc_errors)
        
        return errors
    
    def _parse_uds_dtc(self, msg: Any) -> List[Error]:
        """
        Parse UDS DTC responses
        """
        errors = []
        
        if len(msg.data) < 4:
            return errors
        
        # Parse DTCs (3 bytes each: 2 bytes DTC + 1 byte status)
        for i in range(2, len(msg.data) - 2, 3):
            if i + 2 < len(msg.data):
                dtc_high = msg.data[i]
                dtc_low = msg.data[i + 1]
                status = msg.data[i + 2]
                
                # Convert to standard DTC format
                dtc_code = self._convert_to_dtc_format(dtc_high, dtc_low)
                
                if dtc_code:
                    error = Error(
                        timestamp=msg.timestamp,
                        error_type='UDS_DTC',
                        severity='High' if status & 0x01 else 'Medium',
                        code=dtc_code,
                        description=f'UDS DTC: {dtc_code} - Status: {status:02X}',
                        source='UDS',
                        can_id=msg.can_id if hasattr(msg, 'can_id') else None,
                        data=msg.data
                    )
                    errors.append(error)
        
        return errors
    
    def _convert_to_dtc_format(self, high_byte: int, low_byte: int) -> str:
        """
        Convert UDS DTC bytes to standard format (P/C/B/U + 4 hex digits)
        """
        # Extract DTC components
        dtc_class = (high_byte >> 6) & 0x03
        dtc_digit = (high_byte >> 4) & 0x03
        dtc_rest = ((high_byte & 0x0F) << 8) | low_byte
        
        # Map to letter prefix
        prefix_map = {0: 'P', 1: 'C', 2: 'B', 3: 'U'}
        prefix = prefix_map.get(dtc_class, 'P')
        
        return f"{prefix}{dtc_digit:01X}{dtc_rest:03X}"
    
    def _detect_dlc_errors(self, messages: List[Any], dbc_data: Optional[Dict] = None) -> List[Error]:
        """
        Detect DLC (Data Length Code) errors
        """
        errors = []
        
        if not dbc_data or 'messages' not in dbc_data:
            return errors
        
        dbc_messages = dbc_data['messages']
        
        for msg in messages:
            if not hasattr(msg, 'can_id') or not hasattr(msg, 'dlc'):
                continue
            
            # Check if message is defined in DBC
            msg_id_str = str(msg.can_id)
            if msg_id_str in dbc_messages:
                expected_dlc = dbc_messages[msg_id_str].get('dlc', 8)
                
                if msg.dlc != expected_dlc:
                    error = Error(
                        timestamp=msg.timestamp,
                        error_type='DLC_ERROR',
                        severity='Medium',
                        code='E_DLC_MISMATCH',
                        description=f'DLC mismatch for {dbc_messages[msg_id_str]["name"]}: '
                                  f'Expected {expected_dlc}, got {msg.dlc}',
                        source='CAN',
                        can_id=msg.can_id,
                        data=msg.data if hasattr(msg, 'data') else None
                    )
                    errors.append(error)
        
        return errors
    
    def _detect_timeouts(self, messages: List[Any], dbc_data: Optional[Dict] = None) -> List[Error]:
        """
        Detect missing periodic messages (timeouts)
        """
        errors = []
        
        if not dbc_data or 'messages' not in dbc_data:
            return errors
        
        # Group messages by ID
        msg_by_id = {}
        for msg in messages:
            if hasattr(msg, 'can_id'):
                if msg.can_id not in msg_by_id:
                    msg_by_id[msg.can_id] = []
                msg_by_id[msg.can_id].append(msg)
        
        # Check cycle times
        dbc_messages = dbc_data['messages']
        for msg_id_str, msg_def in dbc_messages.items():
            if 'cycle_time' in msg_def and msg_def['cycle_time']:
                msg_id = int(msg_id_str)
                cycle_time_ms = msg_def['cycle_time']
                
                if msg_id in msg_by_id:
                    msg_list = sorted(msg_by_id[msg_id], key=lambda m: m.timestamp)
                    
                    for i in range(1, len(msg_list)):
                        gap_ms = (msg_list[i].timestamp - msg_list[i-1].timestamp) * 1000
                        
                        # Check if gap exceeds 2x cycle time (allowing some tolerance)
                        if gap_ms > cycle_time_ms * 2:
                            error = Error(
                                timestamp=msg_list[i-1].timestamp,
                                error_type='TIMEOUT',
                                severity='High',
                                code='E_MSG_TIMEOUT',
                                description=f'Timeout detected for {msg_def["name"]}: '
                                          f'Expected {cycle_time_ms}ms, gap was {gap_ms:.1f}ms',
                                source='CAN',
                                can_id=msg_id
                            )
                            errors.append(error)
        
        return errors
    
    def _detect_structured_errors(self, data: Dict[str, Any]) -> List[Error]:
        """
        Detect errors in structured data (JSON, XML, etc.)
        """
        errors = []
        
        # Implementation depends on specific structure
        # This is a placeholder for structured data processing
        
        return errors
    
    def _detect_text_errors(self, text: str) -> List[Error]:
        """
        Detect errors in text logs using pattern matching
        """
        errors = []
        
        lines = text.split('\n')
        for line_num, line in enumerate(lines):
            # Try to extract timestamp
            timestamp = self._extract_timestamp(line)
            if timestamp is None:
                timestamp = float(line_num)  # Use line number as fallback
            
            # Check for error patterns
            for error_type, pattern in self.error_patterns.items():
                if pattern.search(line):
                    # Determine severity based on error type
                    severity = self._get_severity(error_type)
                    
                    error = Error(
                        timestamp=timestamp,
                        error_type=error_type.upper(),
                        severity=severity,
                        code=f'E_{error_type.upper()}',
                        description=line.strip()[:200],  # Limit description length
                        source='LOG'
                    )
                    
                    # Check for DTC codes
                    dtc_match = self.error_patterns['dtc'].search(line)
                    if dtc_match:
                        error.code = dtc_match.group(0).upper()
                        error.error_type = 'DTC'
                    
                    errors.append(error)
                    break  # Only report first matching error per line
        
        return errors
    
    def _extract_timestamp(self, line: str) -> Optional[float]:
        """
        Extract timestamp from log line
        """
        # Try various timestamp formats
        patterns = [
            r'\((\d+\.\d+)\)',  # (1234567890.123456)
            r'^(\d+\.\d+)',     # 1234567890.123456 at start
            r'(\d{2}:\d{2}:\d{2}\.\d+)',  # HH:MM:SS.mmm
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    return float(match.group(1).replace(':', ''))
                except:
                    pass
        
        return None
    
    def _get_severity(self, error_type: str) -> str:
        """
        Determine error severity based on type
        """
        critical_errors = ['bus_off', 'error_frame', 'fault']
        high_errors = ['timeout', 'checksum', 'dtc']
        medium_errors = ['dlc_error', 'ack_error', 'overrun']
        
        if error_type in critical_errors:
            return 'Critical'
        elif error_type in high_errors:
            return 'High'
        elif error_type in medium_errors:
            return 'Medium'
        else:
            return 'Low'
    
    def _suggest_fix(self, error: Error) -> str:
        """
        Suggest fix for detected error
        """
        fixes = {
            'BUS_OFF': 'Check bus termination resistors (120Ω). Verify cable connections. '
                      'Check for short circuits. Review bus load and timing.',
            
            'ERROR_FRAME': 'Check physical layer (cables, connectors). '
                          'Verify bit timing configuration. Check for EMI interference.',
            
            'TIMEOUT': 'Verify ECU is powered and connected. '
                      'Check message cycle time configuration. '
                      'Review network load and priorities.',
            
            'DLC_ERROR': 'Update message definition in DBC file. '
                        'Check sender ECU configuration. Verify protocol version.',
            
            'UDS_ERROR': 'Check diagnostic session state. '
                        'Verify security access if required. '
                        'Review service request parameters.',
            
            'J1939_DTC': 'Consult J1939-73 for DTC details. '
                        'Check related sensor/actuator. '
                        'Clear DTC after fixing root cause.',
            
            'CHECKSUM': 'Check for data corruption. '
                       'Verify message integrity. '
                       'Review sender checksum calculation.',
        }
        
        return fixes.get(error.error_type, 
                        'Review log context and consult documentation for this error type.')
    
    def get_error_summary(self, errors: List[Error]) -> Dict[str, Any]:
        """
        Generate error summary statistics
        """
        summary = {
            'total_errors': len(errors),
            'by_severity': {
                'Critical': sum(1 for e in errors if e.severity == 'Critical'),
                'High': sum(1 for e in errors if e.severity == 'High'),
                'Medium': sum(1 for e in errors if e.severity == 'Medium'),
                'Low': sum(1 for e in errors if e.severity == 'Low'),
            },
            'by_type': {},
            'by_source': {},
            'unique_codes': set(),
            'time_range': None
        }
        
        for error in errors:
            # Count by type
            if error.error_type not in summary['by_type']:
                summary['by_type'][error.error_type] = 0
            summary['by_type'][error.error_type] += 1
            
            # Count by source
            if error.source not in summary['by_source']:
                summary['by_source'][error.source] = 0
            summary['by_source'][error.source] += 1
            
            # Collect unique codes
            summary['unique_codes'].add(error.code)
        
        # Convert set to list for JSON serialization
        summary['unique_codes'] = list(summary['unique_codes'])
        
        # Calculate time range
        if errors:
            summary['time_range'] = {
                'start': min(e.timestamp for e in errors),
                'end': max(e.timestamp for e in errors)
            }
        
        return summary
