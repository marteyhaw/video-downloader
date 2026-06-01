import pytest

from backend.models.schemas import DownloadRequest
from backend.services.download.strategies import _reject_segment_download
from backend.services.security import SecurityError


def test_reject_m4s_download():
    req = DownloadRequest(
        item_id="x",
        title="frag",
        url="https://cdn.example.com/seg.m4s",
        ext="m4s",
        source="playwright",
    )
    with pytest.raises(SecurityError, match="fragment"):
        _reject_segment_download(req)
