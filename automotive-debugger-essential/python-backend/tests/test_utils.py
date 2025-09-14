"""
Tests for utility modules
"""

import pytest
import tempfile
import os
from typing import Dict, Any
from utils.csv_exporter import CSVExporter
from utils.html_exporter import HTMLExporter
from utils.pdf_exporter import PDFExporter

class TestExporters:
    """Test export utility classes"""

    @pytest.fixture
    def sample_analysis_data(self) -> Dict[str, Any]:
        """Sample analysis data for testing"""
        return {
            'analysis_id': 'test_analysis_123',
            'timestamp': '2025-01-14T10:00:00Z',
            'files': ['file1.asc', 'file2.blf'],
            'results': {
                'errors': [
                    {
                        'type': 'BusOff',
                        'description': 'CAN bus went offline',
                        'timestamp': '10.234',
                        'severity': 'Critical'
                    },
                    'Simple error string'
                ],
                'patterns': {
                    'bus_load': 0.75,
                    'dominant_id': '0x123',
                    'message_count': 50000
                },
                'timeline': {
                    'events': [
                        {'time': 0.0, 'event': 'start'},
                        {'time': 10.5, 'event': 'error'}
                    ]
                },
                'statistics': {
                    'total_messages': 50000,
                    'unique_ids': 150,
                    'duration': 60.0
                }
            }
        }

    @pytest.mark.asyncio
    async def test_csv_exporter(self, sample_analysis_data):
        """Test CSV exporter functionality"""
        exporter = CSVExporter()

        # Test exporting all sections
        csv_content = await exporter.export(
            sample_analysis_data,
            ['errors', 'patterns', 'timeline', 'statistics']
        )

        assert isinstance(csv_content, str)
        assert 'Section,Type,Description,Timestamp,Severity' in csv_content
        assert 'BusOff' in csv_content
        assert 'bus_load' in csv_content
        assert 'Timeline Data' in csv_content

    @pytest.mark.asyncio
    async def test_html_exporter(self, sample_analysis_data):
        """Test HTML exporter functionality"""
        exporter = HTMLExporter()

        # Test exporting all sections
        html_content = await exporter.export(
            sample_analysis_data,
            ['errors', 'patterns', 'timeline']
        )

        assert isinstance(html_content, str)
        assert '<!DOCTYPE html>' in html_content
        assert 'Automotive Debug Analysis Report' in html_content
        assert 'test_analysis_123' in html_content
        assert 'Errors Detected' in html_content

    @pytest.mark.asyncio
    async def test_pdf_exporter(self, sample_analysis_data):
        """Test PDF exporter functionality"""
        exporter = PDFExporter()

        # Test exporting (returns placeholder content for now)
        pdf_content = await exporter.export(
            sample_analysis_data,
            ['errors', 'patterns']
        )

        assert isinstance(pdf_content, bytes)
        assert pdf_content.startswith(b'%PDF-1.4')

    @pytest.mark.asyncio
    async def test_csv_exporter_empty_data(self):
        """Test CSV exporter with empty data"""
        exporter = CSVExporter()

        empty_data = {
            'analysis_id': 'empty_test',
            'results': {}
        }

        csv_content = await exporter.export(empty_data, ['errors'])
        assert 'Section,Type,Description,Timestamp,Severity' in csv_content

    @pytest.mark.asyncio
    async def test_html_exporter_single_section(self, sample_analysis_data):
        """Test HTML exporter with single section"""
        exporter = HTMLExporter()

        html_content = await exporter.export(sample_analysis_data, ['errors'])

        assert 'Errors Detected' in html_content
        assert 'Patterns Analysis' not in html_content