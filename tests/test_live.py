"""Live integration tests -- hit the real RSS feeds. Skipped by default.

Run with: pytest -m live
"""

from urllib.request import Request, urlopen

import pytest

from nyaa_core import core


def _fetch(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as resp:  # noqa: S310 (trusted, fixed hosts)
        return resp.read().decode("utf-8", "replace")


@pytest.mark.live
@pytest.mark.parametrize(
    "base_url",
    ["https://nyaa.si", "https://sukebei.nyaa.si"],
)
def test_live_search_returns_results(base_url):
    items = core.fetch_results(_fetch, base_url, "0_0", "a", max_pages=1)
    assert items, "expected at least one result from %s" % base_url
    first = items[0]
    assert first["name"]
    assert first["infohash"]
    assert first["seeds"] >= 0
    # Sorted by seeders descending.
    assert items[0]["seeds"] >= items[-1]["seeds"]
