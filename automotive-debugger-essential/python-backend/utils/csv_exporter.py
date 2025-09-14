"""
CSV Export Utility for Analysis Results
Exports analysis results to CSV format
"""

import logging
import csv
from typing import Dict, List, Any
from io import StringIO

logger = logging.getLogger(__name__)

class CSVExporter:
    """Export analysis results to CSV format"""

    def __init__(self):
        """Initialize CSV exporter"""
        pass

    async def export(self, analysis_data: Dict[str, Any], include_sections: List[str]) -> str:
        """
        Export analysis data to CSV format

        Args:
            analysis_data: Analysis results dictionary
            include_sections: List of sections to include in export

        Returns:
            CSV content as string
        """
        try:
            logger.info(f"Exporting CSV with sections: {include_sections}")

            output = StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(['Section', 'Type', 'Description', 'Timestamp', 'Severity'])

            results = analysis_data.get('results', {})

            # Export errors section
            if 'errors' in include_sections:
                errors = results.get('errors', [])
                for error in errors:
                    if isinstance(error, dict):
                        writer.writerow([
                            'Errors',
                            error.get('type', 'Unknown'),
                            error.get('description', 'N/A'),
                            error.get('timestamp', 'N/A'),
                            error.get('severity', 'N/A')
                        ])
                    else:
                        writer.writerow(['Errors', 'Error', str(error), 'N/A', 'N/A'])

            # Export patterns section
            if 'patterns' in include_sections:
                patterns = results.get('patterns', {})
                for pattern_name, pattern_data in patterns.items():
                    writer.writerow([
                        'Patterns',
                        pattern_name,
                        str(pattern_data),
                        'N/A',
                        'Info'
                    ])

            # Export timeline section
            if 'timeline' in include_sections:
                timeline = results.get('timeline', {})
                writer.writerow([
                    'Timeline',
                    'Timeline Data',
                    f"Events: {len(timeline.get('events', []))}",
                    'N/A',
                    'Info'
                ])

            # Export statistics section
            if 'statistics' in include_sections:
                stats = results.get('statistics', {})
                for stat_name, stat_value in stats.items():
                    writer.writerow([
                        'Statistics',
                        stat_name,
                        str(stat_value),
                        'N/A',
                        'Info'
                    ])

            csv_content = output.getvalue()
            output.close()

            return csv_content

        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            raise