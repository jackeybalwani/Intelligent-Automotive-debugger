"""
Auto Detector Module
Automatically detects log file formats and selects appropriate parser
"""

import os
import re
import struct
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import logging
try:
    import magic
except ImportError:
    magic = None
import json
import xml.etree.ElementTree as ET

from .can_parser import CANParser
from .lin_parser import LINParser
from .uds_parser import UDSParser
from .dbc_parser import DBCParser
from .blf_parser import BLFParser
from .asc_parser import ASCParser
from .pcap_parser import PCAPParser
from .canalyzer_parser import CANalyzerParser
from .inca_parser import INCAParser

logger = logging.getLogger(__name__)

class AutoDetector:
    """
    Automatically detect file format and return appropriate parser
    """
    
    def __init__(self):
        self.parsers = {
            # Raw log formats
            'can_asc': ASCParser(),
            'can_blf': BLFParser(),
            'can_trc': CANParser(),
            'can_log': CANParser(),
            'lin': LINParser(),
            'uds': UDSParser(),
            'pcap': PCAPParser(),
            'dbc': DBCParser(),
            
            # Tool outputs
            'canalyzer_xml': CANalyzerParser(),
            'canalyzer_csv': CANalyzerParser(),
            'inca_dat': INCAParser(),
            'inca_mdf': INCAParser(),
        }
        
        # File signatures (magic bytes)
        self.signatures = {
            b'LOGG': 'can_blf',  # Vector BLF
            b'date': 'can_asc',  # Vector ASC
            b'\xd0\xcf\x11\xe0': 'excel',  # Excel file
            b'<?xml': 'xml',  # XML file
            b'%PDF': 'pdf',  # PDF file
            b'PK\x03\x04': 'zip',  # ZIP archive
        }
        
        # File extension mapping
        self.extension_map = {
            '.asc': 'can_asc',
            '.blf': 'can_blf',
            '.trc': 'can_trc',
            '.log': 'can_log',
            '.txt': 'can_log',  # Default to CAN for .txt
            '.lin': 'lin',
            '.ldf': 'lin',
            '.uds': 'uds',
            '.pcap': 'pcap',
            '.pcapng': 'pcap',
            '.dbc': 'dbc',
            '.csv': 'csv',
            '.xml': 'xml',
            '.dat': 'inca_dat',
            '.mdf': 'inca_mdf',
            '.xlsx': 'excel',
            '.json': 'json',
        }
        
        # Regex patterns for content detection
        self.content_patterns = {
            'can_timestamp': re.compile(r'\(\d+\.\d+\)\s+\w+\s+[0-9A-Fa-f]+#[0-9A-Fa-f]+'),
            'can_asc': re.compile(r'^\s*\d+\.\d+\s+\d+\s+[0-9A-Fa-fx]+\s+Rx\s+d\s+\d+'),
            'j1939': re.compile(r'18[0-9A-F]{6}#[0-9A-F]+'),
            'uds': re.compile(r'(7[0-9A-F]{2}|[0-9A-F]{2}7[0-9A-F])\s*#'),
            'lin': re.compile(r'LIN\s+\d+\.\d+'),
            'canalyzer_log': re.compile(r'(CANalyzer|CANoe|Vector)'),
            'inca': re.compile(r'INCA|ETAS'),
        }
    
    def detect_format(self, file_path: str) -> str:
        """
        Detect file format using multiple strategies
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Strategy 1: Check file extension
        ext = file_path.suffix.lower()
        if ext in self.extension_map:
            format_hint = self.extension_map[ext]
            
            # Verify with content for ambiguous extensions
            if ext in ['.csv', '.xml', '.txt', '.log']:
                content_format = self._detect_by_content(file_path)
                if content_format:
                    return content_format
            
            return format_hint
        
        # Strategy 2: Check magic bytes
        magic_format = self._detect_by_magic(file_path)
        if magic_format:
            return magic_format
        
        # Strategy 3: Check content patterns
        content_format = self._detect_by_content(file_path)
        if content_format:
            return content_format
        
        # Strategy 4: Try parsing with each parser
        parse_format = self._detect_by_parsing(file_path)
        if parse_format:
            return parse_format
        
        # Default fallback
        logger.warning(f"Could not detect format for {file_path}, defaulting to can_log")
        return 'can_log'
    
    def _detect_by_magic(self, file_path: Path) -> Optional[str]:
        """
        Detect format by file signature (magic bytes)
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)
                
                for signature, format_type in self.signatures.items():
                    if header.startswith(signature):
                        # Further validation for XML files
                        if format_type == 'xml':
                            return self._detect_xml_format(file_path)
                        return format_type
                
                # Check for BLF format (specific structure)
                if len(header) >= 144 and header[0:4] == b'LOGG':
                    return 'can_blf'
                    
        except Exception as e:
            logger.error(f"Error reading file header: {e}")
        
        return None
    
    def _detect_by_content(self, file_path: Path) -> Optional[str]:
        """
        Detect format by analyzing file content
        """
        try:
            # Read sample lines
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                sample = f.read(10000)  # Read first 10KB
                
                # Check for specific patterns
                if self.content_patterns['can_timestamp'].search(sample):
                    return 'can_log'
                
                if self.content_patterns['can_asc'].search(sample):
                    return 'can_asc'
                
                if self.content_patterns['j1939'].search(sample):
                    return 'can_log'  # J1939 is a CAN variant
                
                if self.content_patterns['uds'].search(sample):
                    return 'uds'
                
                if self.content_patterns['lin'].search(sample):
                    return 'lin'
                
                if self.content_patterns['canalyzer_log'].search(sample):
                    # Check if it's CSV or XML
                    if file_path.suffix.lower() == '.csv':
                        return 'canalyzer_csv'
                    elif file_path.suffix.lower() == '.xml':
                        return 'canalyzer_xml'
                    return 'canalyzer_xml'
                
                if self.content_patterns['inca'].search(sample):
                    if file_path.suffix.lower() == '.dat':
                        return 'inca_dat'
                    elif file_path.suffix.lower() == '.mdf':
                        return 'inca_mdf'
                    return 'inca_dat'
                
        except Exception as e:
            logger.error(f"Error analyzing file content: {e}")
        
        return None
    
    def _detect_xml_format(self, file_path: Path) -> str:
        """
        Detect specific XML format (CANalyzer, INCA, etc.)
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Check for CANalyzer XML
            if 'CANalyzer' in root.tag or root.find('.//CANalyzer') is not None:
                return 'canalyzer_xml'
            
            # Check for CANoe XML
            if 'CANoe' in root.tag or root.find('.//CANoe') is not None:
                return 'canalyzer_xml'  # Use same parser
            
            # Check for other tool-specific XML formats
            if root.find('.//INCA') is not None:
                return 'inca_xml'
            
            # Default XML
            return 'xml'
            
        except Exception as e:
            logger.error(f"Error parsing XML: {e}")
            return 'xml'
    
    def _detect_by_parsing(self, file_path: Path) -> Optional[str]:
        """
        Try parsing with different parsers to detect format
        """
        # Try parsers in order of likelihood
        parser_order = ['can_log', 'can_asc', 'can_blf', 'lin', 'uds']
        
        for format_type in parser_order:
            if format_type in self.parsers:
                parser = self.parsers[format_type]
                try:
                    # Try to parse first few lines
                    if parser.validate_format(file_path):
                        return format_type
                except:
                    continue
        
        return None
    
    def get_parser(self, format_type: str):
        """
        Get parser instance for detected format
        """
        if format_type in self.parsers:
            return self.parsers[format_type]
        
        # Try to find a compatible parser
        if 'can' in format_type.lower():
            return self.parsers.get('can_log', CANParser())
        
        # Default parser
        logger.warning(f"No specific parser for {format_type}, using default CAN parser")
        return CANParser()
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed file information
        """
        file_path = Path(file_path)
        
        info = {
            'path': str(file_path),
            'name': file_path.name,
            'size': file_path.stat().st_size,
            'extension': file_path.suffix,
            'format': self.detect_format(file_path),
            'created': file_path.stat().st_ctime,
            'modified': file_path.stat().st_mtime,
        }
        
        # Add format-specific info
        parser = self.get_parser(info['format'])
        if hasattr(parser, 'get_file_stats'):
            info['stats'] = parser.get_file_stats(file_path)
        
        return info
    
    def detect_multiple_formats(self, file_paths: list) -> Dict[str, str]:
        """
        Detect formats for multiple files
        """
        results = {}
        
        for file_path in file_paths:
            try:
                format_type = self.detect_format(file_path)
                results[file_path] = format_type
            except Exception as e:
                logger.error(f"Error detecting format for {file_path}: {e}")
                results[file_path] = 'unknown'
        
        return results
