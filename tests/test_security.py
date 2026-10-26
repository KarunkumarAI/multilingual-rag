import pytest
from backend.app.browser.service import _safe_public_url

@pytest.mark.parametrize("url", [
    "http://localhost:8000", "http://127.0.0.1", "file:///etc/passwd",
    "ftp://example.com/file", "http://10.0.0.1", "http://192.168.1.10",
])
def test_blocks_unsafe_urls(url):
    with pytest.raises(ValueError):
        _safe_public_url(url)

def test_rejects_non_http_scheme_without_network():
    with pytest.raises(ValueError):
        _safe_public_url("javascript:alert(1)")
