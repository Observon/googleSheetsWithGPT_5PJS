"""Export service for various formats."""

import csv
import logging
import uuid
from pathlib import Path
from typing import Optional

from src.config import settings
from src.domain.exceptions import ApplicationError
from src.domain.models import ExportResult, Analysis

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting analysis results."""

    SUPPORTED_FORMATS = ["csv", "pdf", "md"]

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize export service.

        Args:
            output_dir: Directory for exported files (defaults to settings.output_dir)
        """
        self.output_dir = Path(output_dir or settings.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Export service initialized with output dir: {self.output_dir}")

    def export_analysis(self, analysis: Analysis, format: str) -> ExportResult:
        """
        Export analysis result to specified format.

        Args:
            analysis: Analysis object to export
            format: Export format (csv, pdf, md)

        Returns:
            ExportResult object

        Raises:
            ApplicationError: If format is not supported or export fails
        """
        format = format.lower()

        if format not in self.SUPPORTED_FORMATS:
            raise ApplicationError(f"Unsupported export format: {format}")

        logger.info(f"Exporting analysis to {format}")

        if format == "csv":
            return self._export_csv(analysis)
        elif format == "pdf":
            return self._export_pdf(analysis)
        elif format == "md":
            return self._export_markdown(analysis)

    def _export_csv(self, analysis: Analysis) -> ExportResult:
        """
        Export analysis as CSV.

        Args:
            analysis: Analysis object

        Returns:
            ExportResult object
        """
        try:
            filename = f"analysis_{analysis.id[:8]}.csv"
            filepath = self.output_dir / filename

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Analysis Report"])
                writer.writerow([])
                writer.writerow(["Dataset ID", analysis.dataset_id])
                writer.writerow(["Dataset Name", analysis.dataset_name])
                writer.writerow(["Analysis Date", analysis.created_at.isoformat()])
                writer.writerow([])
                writer.writerow(["Prompt", analysis.prompt])
                writer.writerow([])
                writer.writerow(["Result"])
                writer.writerow([analysis.result])

            size = filepath.stat().st_size
            logger.info(f"CSV export successful: {filepath} ({size} bytes)")

            return ExportResult(
                analysis_id=analysis.id,
                format="csv",
                filepath=str(filepath),
                size_bytes=size,
            )

        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise ApplicationError(f"Failed to export to CSV: {str(e)}") from e

    def _export_pdf(self, analysis: Analysis) -> ExportResult:
        """
        Export analysis as PDF.

        Args:
            analysis: Analysis object

        Returns:
            ExportResult object
        """
        try:
            # Try to import reportlab
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.enums import TA_LEFT, TA_CENTER
            except ImportError:
                raise ApplicationError(
                    "reportlab not installed. Install with: pip install reportlab"
                )

            filename = f"analysis_{analysis.id[:8]}.pdf"
            filepath = self.output_dir / filename

            doc = SimpleDocTemplate(str(filepath), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=16,
                textColor="navy",
                spaceAfter=30,
                alignment=TA_CENTER,
            )
            story.append(Paragraph("Analysis Report", title_style))
            story.append(Spacer(1, 12))

            # Metadata
            meta_style = styles["Normal"]
            story.append(Paragraph(f"<b>Dataset ID:</b> {analysis.dataset_id}", meta_style))
            story.append(Paragraph(f"<b>Dataset Name:</b> {analysis.dataset_name}", meta_style))
            story.append(
                Paragraph(f"<b>Date:</b> {analysis.created_at.isoformat()}", meta_style)
            )
            story.append(Spacer(1, 20))

            # Prompt
            story.append(Paragraph("<b>Analysis Prompt:</b>", styles["Heading2"]))
            story.append(Paragraph(analysis.prompt.replace("\n", "<br/>"), meta_style))
            story.append(Spacer(1, 20))

            # Result
            story.append(Paragraph("<b>Analysis Result:</b>", styles["Heading2"]))
            story.append(Paragraph(analysis.result.replace("\n", "<br/>"), meta_style))

            doc.build(story)

            size = filepath.stat().st_size
            logger.info(f"PDF export successful: {filepath} ({size} bytes)")

            return ExportResult(
                analysis_id=analysis.id,
                format="pdf",
                filepath=str(filepath),
                size_bytes=size,
            )

        except ApplicationError:
            raise
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            raise ApplicationError(f"Failed to export to PDF: {str(e)}") from e

    def _export_markdown(self, analysis: Analysis) -> ExportResult:
        """
        Export analysis as Markdown.

        Args:
            analysis: Analysis object

        Returns:
            ExportResult object
        """
        try:
            filename = f"analysis_{analysis.id[:8]}.md"
            filepath = self.output_dir / filename

            content = f"""# Analysis Report

## Metadata

- **Analysis ID:** {analysis.id}
- **Dataset ID:** {analysis.dataset_id}
- **Dataset Name:** {analysis.dataset_name}
- **Analysis Date:** {analysis.created_at.isoformat()}
- **Cached:** {analysis.cached}

## Analysis Prompt

{analysis.prompt}

## Result

{analysis.result}

---
*Generated by Google Drive + GPT Data Analyzer*
"""

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            size = filepath.stat().st_size
            logger.info(f"Markdown export successful: {filepath} ({size} bytes)")

            return ExportResult(
                analysis_id=analysis.id,
                format="md",
                filepath=str(filepath),
                size_bytes=size,
            )

        except Exception as e:
            logger.error(f"Error exporting to Markdown: {str(e)}")
            raise ApplicationError(f"Failed to export to Markdown: {str(e)}") from e
