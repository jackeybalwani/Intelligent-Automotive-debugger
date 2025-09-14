"""
HTML Export Utility for Analysis Results
Exports analysis results to HTML format
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class HTMLExporter:
    """Export analysis results to HTML format"""

    def __init__(self):
        """Initialize HTML exporter"""
        pass

    async def export(self, analysis_data: Dict[str, Any], include_sections: List[str]) -> str:
        """
        Export analysis data to HTML format

        Args:
            analysis_data: Analysis results dictionary
            include_sections: List of sections to include in export

        Returns:
            HTML content as string
        """
        try:
            logger.info(f"Exporting HTML with sections: {include_sections}")

            # Generate HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Automotive Analysis Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #f0f0f0; padding: 20px; }}
                    .section {{ margin: 20px 0; }}
                    .error {{ color: red; }}
                    .warning {{ color: orange; }}
                    .info {{ color: blue; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Automotive Debug Analysis Report</h1>
                    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>

                <div class="section">
                    <h2>Analysis Summary</h2>
                    <p>Analysis ID: {analysis_data.get('analysis_id', 'N/A')}</p>
                    <p>Files Processed: {len(analysis_data.get('files', []))}</p>
                </div>

                {''.join(self._render_section(section, analysis_data) for section in include_sections)}

            </body>
            </html>
            """

            return html_content.strip()

        except Exception as e:
            logger.error(f"Error exporting HTML: {e}")
            raise

    def _render_section(self, section: str, data: Dict[str, Any]) -> str:
        """Render individual section of the report"""
        results = data.get('results', {})

        if section == 'errors':
            errors = results.get('errors', [])
            return f"""
            <div class="section">
                <h2>Errors Detected</h2>
                {''.join(f'<div class="error">• {error}</div>' for error in errors)}
            </div>
            """
        elif section == 'patterns':
            patterns = results.get('patterns', {})
            return f"""
            <div class="section">
                <h2>Patterns Analysis</h2>
                <pre>{patterns}</pre>
            </div>
            """
        elif section == 'timeline':
            return f"""
            <div class="section">
                <h2>Timeline Data</h2>
                <p>Timeline visualization data available</p>
            </div>
            """
        else:
            return f"""
            <div class="section">
                <h2>{section.title()}</h2>
                <p>Section data available</p>
            </div>
            """