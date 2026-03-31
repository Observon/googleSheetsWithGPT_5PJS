"""Cache adapter for storing analysis results."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Any

from src.config import settings
from src.domain.exceptions import ApplicationError

logger = logging.getLogger(__name__)


class CacheAdapter:
    """File-based cache for analysis results."""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize cache adapter.

        Args:
            cache_dir: Directory to store cache files (defaults to settings.cache_dir)
        """
        self.cache_dir = Path(cache_dir or settings.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cache initialized at {self.cache_dir}")

    @staticmethod
    def _generate_key(spreadsheet_id: str, prompt: str) -> str:
        """
        Generate a cache key from spreadsheet ID and prompt.

        Args:
            spreadsheet_id: Google Sheet ID
            prompt: Analysis prompt

        Returns:
            MD5 hash string
        """
        combined = f"{spreadsheet_id}:{prompt}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get(self, spreadsheet_id: str, prompt: str) -> Optional[str]:
        """
        Retrieve cached analysis result.

        Args:
            spreadsheet_id: Google Sheet ID
            prompt: Analysis prompt

        Returns:
            Cached result or None if not found
        """
        try:
            key = self._generate_key(spreadsheet_id, prompt)
            cache_file = self.cache_dir / f"{key}.json"

            if cache_file.exists():
                with open(cache_file) as f:
                    data = json.load(f)
                    logger.info(f"Cache hit for key: {key}")
                    return data.get("result")

            return None

        except Exception as e:
            logger.warning(f"Error retrieving from cache: {str(e)}")
            return None

    def set(self, spreadsheet_id: str, prompt: str, result: str) -> bool:
        """
        Store analysis result in cache.

        Args:
            spreadsheet_id: Google Sheet ID
            prompt: Analysis prompt
            result: Analysis result to cache

        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._generate_key(spreadsheet_id, prompt)
            cache_file = self.cache_dir / f"{key}.json"

            data = {"key": key, "spreadsheet_id": spreadsheet_id, "prompt": prompt, "result": result}

            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Cached result for key: {key}")
            return True

        except Exception as e:
            logger.error(f"Error writing to cache: {str(e)}")
            return False

    def exists(self, spreadsheet_id: str, prompt: str) -> bool:
        """
        Check if analysis result exists in cache.

        Args:
            spreadsheet_id: Google Sheet ID
            prompt: Analysis prompt

        Returns:
            True if exists, False otherwise
        """
        key = self._generate_key(spreadsheet_id, prompt)
        cache_file = self.cache_dir / f"{key}.json"
        return cache_file.exists()

    def clear(self) -> int:
        """
        Clear all cache files.

        Returns:
            Number of files deleted
        """
        try:
            count = 0
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                count += 1

            logger.info(f"Cleared {count} cache files")
            return count

        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return 0

    def delete_key(self, spreadsheet_id: str, prompt: str) -> bool:
        """
        Delete a specific cache entry.

        Args:
            spreadsheet_id: Google Sheet ID
            prompt: Analysis prompt

        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._generate_key(spreadsheet_id, prompt)
            cache_file = self.cache_dir / f"{key}.json"

            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"Deleted cache entry for key: {key}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting cache entry: {str(e)}")
            return False
