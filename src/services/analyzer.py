"""Data analysis service."""

import logging
import uuid
from typing import Optional

import pandas as pd

from src.adapters.cache import CacheAdapter
from src.adapters.google_drive import GoogleDriveAdapter
from src.adapters.openai_client import OpenAIAdapter
from src.domain.exceptions import OpenAIError
from src.domain.models import Analysis

logger = logging.getLogger(__name__)


class AnalyzerService:
    """Service for analyzing data using GPT."""

    def __init__(
        self,
        openai_adapter: Optional[OpenAIAdapter] = None,
        cache_adapter: Optional[CacheAdapter] = None,
        drive_adapter: Optional[GoogleDriveAdapter] = None,
    ):
        """
        Initialize analyzer service.

        Args:
            openai_adapter: OpenAI adapter (defaults to new instance)
            cache_adapter: Cache adapter (defaults to new instance)
            drive_adapter: Google Drive adapter (for data loading)
        """
        self.openai_adapter = openai_adapter or OpenAIAdapter()
        self.cache_adapter = cache_adapter or CacheAdapter()
        self.drive_adapter = drive_adapter or GoogleDriveAdapter()

    def analyze_spreadsheet(
        self, file_id: str, file_name: str, prompt: str, use_cache: bool = True
    ) -> Analysis:
        """
        Analyze a spreadsheet with a custom prompt.

        Args:
            file_id: Google Sheet file ID
            file_name: File name for reference
            prompt: Analysis prompt
            use_cache: Whether to check cache first

        Returns:
            Analysis object

        Raises:
            OpenAIError: If analysis fails
        """
        try:
            logger.info(f"Analyzing spreadsheet: {file_name}")

            # Check cache
            cached_result = None
            if use_cache:
                cached_result = self.cache_adapter.get(file_id, prompt)
                if cached_result:
                    logger.info("Using cached analysis result")
                    return Analysis(
                        id=str(uuid.uuid4()),
                        dataset_id=file_id,
                        dataset_name=file_name,
                        prompt=prompt,
                        result=cached_result,
                        cached=True,
                    )

            # Load data
            df = self.drive_adapter.read_spreadsheet(file_id)

            # Analyze with GPT
            result = self.openai_adapter.process_data_with_gpt(df, prompt)

            # Cache result
            self.cache_adapter.set(file_id, prompt, result)

            # Create Analysis object
            analysis = Analysis(
                id=str(uuid.uuid4()),
                dataset_id=file_id,
                dataset_name=file_name,
                prompt=prompt,
                result=result,
                cached=False,
            )

            logger.info("Analysis completed successfully")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing spreadsheet: {str(e)}")
            raise OpenAIError(f"Failed to analyze spreadsheet: {str(e)}") from e

    def generate_insights(
        self, file_id: str, file_name: str, use_cache: bool = True
    ) -> Analysis:
        """
        Generate automatic insights from a spreadsheet.

        Args:
            file_id: Google Sheet file ID
            file_name: File name for reference
            use_cache: Whether to check cache first

        Returns:
            Analysis object with insights
        """
        prompt = """
Analise estes dados e forneça:
1. Principais insights e padrões identificados
2. Anomalias ou valores interessantes
3. Correlações importantes (se aplicável)
4. Recomendações de ações baseadas nos dados
5. Sugestões de análises adicionais que poderiam ser valiosas
"""
        return self.analyze_spreadsheet(file_id, file_name, prompt, use_cache)

    def clear_cache(self) -> int:
        """
        Clear the analysis cache.

        Returns:
            Number of cache entries deleted
        """
        count = self.cache_adapter.clear()
        logger.info(f"Cache cleared: {count} entries deleted")
        return count
