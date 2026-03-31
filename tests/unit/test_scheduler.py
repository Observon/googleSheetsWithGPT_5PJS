"""Tests for scheduler service."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.domain.exceptions import ApplicationError
from src.services.scheduler import SchedulerService


def test_schedule_analysis_success(tmp_path: Path):
    """Should schedule valid cron and persist job config."""
    SchedulerService.JOBS_FILE = tmp_path / "jobs.json"

    service = SchedulerService(batch_service=MagicMock())
    service.scheduler = MagicMock()

    result = service.schedule_analysis(
        job_id="job-1",
        folder_id="folder-1",
        prompt="Analyze",
        cron_expression="0 9 * * MON",
        export_format="pdf",
    )

    assert result["job_id"] == "job-1"
    assert service.jobs["job-1"]["active"] is True
    service.scheduler.add_job.assert_called_once()
    assert SchedulerService.JOBS_FILE.exists()


def test_schedule_analysis_invalid_cron_raises_error(tmp_path: Path):
    """Should reject invalid cron expressions."""
    SchedulerService.JOBS_FILE = tmp_path / "jobs.json"

    service = SchedulerService(batch_service=MagicMock())

    with pytest.raises(ApplicationError, match="Invalid cron expression"):
        service.schedule_analysis(
            job_id="job-1",
            folder_id="folder-1",
            prompt="Analyze",
            cron_expression="invalid cron",
        )


def test_start_and_stop_delegate_to_scheduler(tmp_path: Path):
    """Should start/stop scheduler according to running state."""
    SchedulerService.JOBS_FILE = tmp_path / "jobs.json"

    service = SchedulerService(batch_service=MagicMock())

    scheduler = MagicMock()
    scheduler.running = False
    service.scheduler = scheduler
    service.start()
    scheduler.start.assert_called_once_with()

    scheduler.running = True
    service.stop()
    scheduler.shutdown.assert_called_once_with()


def test_cancel_job_removes_existing_job(tmp_path: Path):
    """Should remove existing job and persist updated config."""
    SchedulerService.JOBS_FILE = tmp_path / "jobs.json"

    service = SchedulerService(batch_service=MagicMock())
    service.scheduler = MagicMock()
    service.jobs = {"job-1": {"job_id": "job-1"}}

    success = service.cancel_job("job-1")

    assert success is True
    assert "job-1" not in service.jobs
    service.scheduler.remove_job.assert_called_once_with("job-1")


def test_cancel_job_returns_false_for_unknown_job(tmp_path: Path):
    """Should return false when job id is unknown."""
    SchedulerService.JOBS_FILE = tmp_path / "jobs.json"

    service = SchedulerService(batch_service=MagicMock())
    service.scheduler = MagicMock()

    assert service.cancel_job("missing") is False


def test_run_analysis_swallows_batch_errors(tmp_path: Path):
    """_run_analysis should not raise when batch processing fails."""
    SchedulerService.JOBS_FILE = tmp_path / "jobs.json"

    batch = MagicMock()
    batch.process_folder.side_effect = RuntimeError("boom")

    service = SchedulerService(batch_service=batch)

    service._run_analysis("folder-1", "Analyze", "csv")

    batch.process_folder.assert_called_once_with("folder-1", "Analyze", "csv")
