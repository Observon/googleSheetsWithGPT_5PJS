"""OpenAI API adapter."""

import json
import logging
from typing import Optional

import pandas as pd
from openai import OpenAI

from src.config import settings
from src.domain.exceptions import OpenAIError

logger = logging.getLogger(__name__)


class OpenAIAdapter:
    """Adapter for OpenAI API operations."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client.

        Args:
            api_key: Optional API key (defaults to OPENAI_API_KEY from config)

        Raises:
            OpenAIError: If API key is not configured
        """
        try:
            key = api_key or settings.openai_api_key
            if not key:
                raise OpenAIError("OPENAI_API_KEY not configured")

            self.client = OpenAI(api_key=key)
            logger.info("OpenAI client initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing OpenAI: {str(e)}")
            raise OpenAIError(f"Failed to initialize OpenAI: {str(e)}") from e

    def analyze_data_structure(self, df: pd.DataFrame) -> str:
        """
        Analyze the structure of a DataFrame.

        Args:
            df: DataFrame to analyze

        Returns:
            JSON string with structure information
        """
        try:
            info = {
                "shape": df.shape,
                "columns": list(df.columns),
                "dtypes": df.dtypes.to_dict(),
                "null_counts": df.isnull().sum().to_dict(),
                "sample_data": df.head(3).to_dict(orient="records"),
            }
            return json.dumps(info, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error analyzing data structure: {str(e)}")
            raise OpenAIError(f"Failed to analyze data: {str(e)}") from e

    def prepare_data_summary(self, df: pd.DataFrame, max_rows: int = 20) -> str:
        """
        Prepare a concise data summary for GPT processing.

        Args:
            df: DataFrame to summarize
            max_rows: Maximum rows to include in sample

        Returns:
            Formatted data summary string
        """
        summary = "Dataset Info:\n"
        summary += f"- Shape: {df.shape[0]} rows, {df.shape[1]} columns\n"
        summary += f"- Columns: {', '.join(df.columns.astype(str))}\n\n"

        # Data types
        summary += "Data Types:\n"
        for col, dtype in df.dtypes.items():
            summary += f"- {col}: {dtype}\n"

        # Sample data
        summary += f"\nSample Data (first {min(max_rows, len(df))} rows):\n"
        summary += df.head(max_rows).to_string(index=False, max_cols=10)

        # Basic statistics for numeric columns
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            summary += "\n\nNumeric Statistics:\n"
            summary += df[numeric_cols].describe().to_string()

        return summary

    def process_data_with_gpt(
        self, df: pd.DataFrame, prompt: str, model: str = "gpt-4o-mini"
    ) -> str:
        """
        Process data using GPT with the given prompt.

        Args:
            df: DataFrame to analyze
            prompt: User prompt for analysis
            model: GPT model to use

        Returns:
            GPT response string

        Raises:
            OpenAIError: If the API call fails
        """
        try:
            # Prepare data summary
            data_summary = self.prepare_data_summary(df)

            # Create the full prompt
            full_prompt = f"""
Você é um especialista em análise de dados. Analise os seguintes dados e responda à pergunta do usuário.

DADOS:
{data_summary}

PERGUNTA DO USUÁRIO:
{prompt}

Por favor, forneça uma análise detalhada, insights relevantes e recomendações baseadas nos dados apresentados.
Se necessário, sugira visualizações ou análises adicionais que poderiam ser úteis.
"""

            logger.info(f"Sending request to {model}")

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um assistente especializado em análise de dados e insights de negócio. Forneça respostas claras, objetivas e acionáveis.",
                    },
                    {"role": "user", "content": full_prompt},
                ],
                max_tokens=2000,
                temperature=0.3,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error processing data with GPT: {str(e)}")
            raise OpenAIError(f"Failed to process with GPT: {str(e)}") from e

    def generate_insights(self, df: pd.DataFrame) -> str:
        """
        Generate automatic insights from data.

        Args:
            df: DataFrame to analyze

        Returns:
            Generated insights string
        """
        prompt = """
Analise estes dados e forneça:
1. Principais insights e padrões identificados
2. Anomalias ou valores interessantes
3. Correlações importantes (se aplicável)
4. Recomendações de ações baseadas nos dados
5. Sugestões de análises adicionais que poderiam ser valiosas
"""
        return self.process_data_with_gpt(df, prompt)
