"""In-memory download job registry and lifecycle.

Jobs live in a capped ``OrderedDict`` and are lost on restart (this is a
local-first single-process tool).
"""

from collections import OrderedDict
from typing import Any

from backend.config import settings
from backend.models.schemas import JobStatus

_jobs: OrderedDict[str, JobStatus] = OrderedDict()


def get_job(job_id: str) -> JobStatus | None:
    """Retrieve the current status of a download job by ID."""
    return _jobs.get(job_id)


def _set_job(job_id: str, **kwargs: Any) -> None:
    job = _jobs[job_id]
    updated = job.model_copy(update=kwargs)
    _jobs[job_id] = updated
    _jobs.move_to_end(job_id)


def _evict_finished_jobs() -> None:
    """Remove oldest completed/error jobs when the dict exceeds the cap."""
    while len(_jobs) > settings.max_retained_jobs:
        oldest_id, oldest = next(iter(_jobs.items()))
        if oldest.state in ("done", "error"):
            del _jobs[oldest_id]
        else:
            break
