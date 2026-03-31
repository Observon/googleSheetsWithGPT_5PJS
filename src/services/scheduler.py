"""Task scheduling service."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import settings
from src.services.batch import BatchService
from src.domain.exceptions import ApplicationError

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling periodic analysis tasks."""

    JOBS_FILE = Path(settings.output_dir) / "scheduled_jobs.json"

    def __init__(self, batch_service: Optional[BatchService] = None):
        """
        Initialize scheduler service.

        Args:
            batch_service: Batch service (defaults to new instance)
        """
        self.batch_service = batch_service or BatchService()
        self.scheduler = BackgroundScheduler()
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self._load_jobs()

    def schedule_analysis(
        self,
        job_id: str,
        folder_id: str,
        prompt: str,
        cron_expression: str,
        export_format: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Schedule a periodic analysis task.

        Args:
            job_id: Unique job identifier
            folder_id: Google Drive folder ID
            prompt: Analysis prompt
            cron_expression: Cron expression for schedule (e.g., '0 9 * * MON')
            export_format: Optional export format

        Returns:
            Job configuration dictionary

        Raises:
            ApplicationError: If scheduling fails
        """
        try:
            logger.info(f"Scheduling analysis job: {job_id}")

            # Create job definition
            job_config = {
                "job_id": job_id,
                "folder_id": folder_id,
                "prompt": prompt,
                "cron": cron_expression,
                "export_format": export_format,
                "created_at": datetime.utcnow().isoformat(),
                "active": True,
            }

            # Schedule with APScheduler
            try:
                trigger = CronTrigger.from_crontab(cron_expression)
            except Exception as e:
                raise ApplicationError(f"Invalid cron expression: {str(e)}")

            self.scheduler.add_job(
                self._run_analysis,
                trigger=trigger,
                id=job_id,
                args=[folder_id, prompt, export_format],
                replace_existing=True,
            )

            # Store job configuration
            self.jobs[job_id] = job_config
            self._save_jobs()

            logger.info(f"Job scheduled: {job_id} with trigger: {cron_expression}")

            return job_config

        except ApplicationError:
            raise
        except Exception as e:
            logger.error(f"Error scheduling analysis: {str(e)}")
            raise ApplicationError(f"Failed to schedule analysis: {str(e)}") from e

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    def list_jobs(self) -> List[Dict[str, Any]]:
        """
        List all scheduled jobs.

        Returns:
            List of job configuration dictionaries
        """
        return list(self.jobs.values())

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a scheduled job.

        Args:
            job_id: Job identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
                self._save_jobs()
                logger.info(f"Job cancelled: {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling job: {str(e)}")
            return False

    def _run_analysis(self, folder_id: str, prompt: str, export_format: Optional[str]):
        """
        Execute analysis task.

        Args:
            folder_id: Google Drive folder ID
            prompt: Analysis prompt
            export_format: Optional export format
        """
        try:
            logger.info(f"Running scheduled analysis for folder: {folder_id}")
            results = self.batch_service.process_folder(
                folder_id, prompt, export_format
            )
            logger.info(f"Scheduled analysis completed: {len(results)} sheets processed")
        except Exception as e:
            logger.error(f"Error in scheduled analysis: {str(e)}")

    def _load_jobs(self):
        """Load previously scheduled jobs from file."""
        try:
            if self.JOBS_FILE.exists():
                with open(self.JOBS_FILE) as f:
                    self.jobs = json.load(f)
                logger.info(f"Loaded {len(self.jobs)} previous jobs")
        except Exception as e:
            logger.warning(f"Could not load previous jobs: {str(e)}")

    def _save_jobs(self):
        """Save scheduled jobs to file."""
        try:
            self.JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.JOBS_FILE, "w") as f:
                json.dump(self.jobs, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving jobs: {str(e)}")
