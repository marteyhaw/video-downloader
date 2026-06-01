"""Tests for downloader job lifecycle and eviction."""

from backend.config import settings
from backend.models.schemas import JobStatus
from backend.services.download.jobs import _evict_finished_jobs, _jobs, get_job


def _reset_jobs():
    _jobs.clear()


def test_get_job_returns_none_for_missing():
    _reset_jobs()
    assert get_job("nonexistent") is None


def test_get_job_returns_existing():
    _reset_jobs()
    _jobs["test-id"] = JobStatus(id="test-id", state="pending", stage="Queued")
    job = get_job("test-id")
    assert job is not None
    assert job.id == "test-id"
    assert job.state == "pending"
    _reset_jobs()


def test_evict_finished_jobs_removes_oldest_done():
    _reset_jobs()
    cap = settings.max_retained_jobs
    for i in range(cap + 5):
        job_id = f"job-{i}"
        state = "done" if i < cap else "pending"
        _jobs[job_id] = JobStatus(id=job_id, state=state, stage="test")

    _evict_finished_jobs()
    # After eviction, finished jobs should be pruned down to the cap
    assert len(_jobs) <= cap + 5
    # Verify that at least some done jobs were removed
    done_count = sum(1 for j in _jobs.values() if j.state == "done")
    assert done_count < cap
    _reset_jobs()


def test_evict_finished_jobs_keeps_running():
    _reset_jobs()
    cap = settings.max_retained_jobs
    for i in range(cap + 5):
        job_id = f"job-{i}"
        _jobs[job_id] = JobStatus(id=job_id, state="running", stage="test")

    before = len(_jobs)
    _evict_finished_jobs()
    assert len(_jobs) == before
    _reset_jobs()
