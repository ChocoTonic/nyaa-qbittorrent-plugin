"""Unit tests for the transport-agnostic core (mocked fetch, no network)."""

from sample_rss import SAMPLE_RSS, make_item, make_rss

from nyaa_core import core


def test_build_rss_url_has_required_params():
    url = core.build_rss_url("https://nyaa.si", "1_0", "cowboy bebop", page=2)
    assert url.startswith("https://nyaa.si/?")
    assert "page=rss" in url
    assert "c=1_0" in url
    assert "p=2" in url
    assert "q=cowboy+bebop" in url  # urlencode quotes the space


def test_build_rss_url_defaults_to_no_filter():
    url = core.build_rss_url("https://nyaa.si", "0_0", "x")
    assert "f=0" in url


def test_fetch_results_passes_filter_through():
    seen = []
    core.fetch_results(
        lambda url: seen.append(url) or make_rss([]),
        "https://nyaa.si",
        "0_0",
        "x",
        filt=core.FILTER_TRUSTED_ONLY,
    )
    assert "f=2" in seen[0]


def test_build_magnet_includes_hash_name_and_trackers():
    magnet = core.build_magnet("DEADBEEF", "My Release")
    assert magnet.startswith("magnet:?xt=urn:btih:DEADBEEF")
    assert "dn=My%20Release" in magnet
    assert magnet.count("&tr=") == len(core.NYAA_TRACKERS)


def test_parse_rss_extracts_fields():
    items = core.parse_rss(make_rss([make_item()]))
    assert len(items) == 1
    it = items[0]
    assert it["name"] == "Example Release 1080p"
    assert it["infohash"] == "0123456789abcdef0123456789abcdef01234567"
    assert it["torrent_url"] == "https://nyaa.si/download/2126378.torrent"
    assert it["desc_link"] == "https://nyaa.si/view/2126378"
    assert it["size"] == "1.4 GiB"
    assert it["seeds"] == 42
    assert it["leech"] == 3
    assert it["pub_date"] > 0


def test_parse_rss_handles_sukebei_namespace():
    # sukebei declares a different xmlns:nyaa URI than nyaa.si; the parser must
    # match namespaced elements by local name regardless of URI.
    rss = make_rss([make_item()]).replace(
        "https://nyaa.si/xmlns/nyaa", "https://sukebei.nyaa.si/xmlns/nyaa"
    )
    it = core.parse_rss(rss)[0]
    assert it["seeds"] == 42
    assert it["leech"] == 3
    assert it["size"] == "1.4 GiB"
    assert it["infohash"] == "0123456789abcdef0123456789abcdef01234567"


def test_parse_rss_handles_missing_numbers():
    item = make_item(seeders="", leechers="oops")
    it = core.parse_rss(make_rss([item]))[0]
    assert it["seeds"] == -1
    assert it["leech"] == -1


def test_fetch_results_sorts_by_seeders_desc():
    items = core.fetch_results(lambda url: SAMPLE_RSS, "https://nyaa.si", "0_0", "x")
    assert [it["seeds"] for it in items] == [99, 5]
    assert items[0]["name"] == "High Seeded Release"


def test_fetch_results_paginates_until_short_page():
    calls = []
    full_page = make_rss([make_item(tid=str(i)) for i in range(core.RESULTS_PER_PAGE)])
    short_page = make_rss([make_item(tid="last")])

    def fake_fetch(url):
        calls.append(url)
        # First page full -> keep going; second page short -> stop.
        return full_page if len(calls) == 1 else short_page

    items = core.fetch_results(fake_fetch, "https://nyaa.si", "0_0", "x", max_pages=5)
    assert len(calls) == 2
    assert len(items) == core.RESULTS_PER_PAGE + 1


def test_fetch_results_respects_max_pages():
    full_page = make_rss([make_item(tid=str(i)) for i in range(core.RESULTS_PER_PAGE)])
    calls = []

    def fake_fetch(url):
        calls.append(url)
        return full_page

    core.fetch_results(fake_fetch, "https://nyaa.si", "0_0", "x", max_pages=2)
    assert len(calls) == 2


def test_to_result_row_prefers_magnet():
    item = core.parse_rss(make_rss([make_item()]))[0]
    row = core.to_result_row(item, "https://nyaa.si")
    assert row["link"].startswith("magnet:?xt=urn:btih:")
    assert row["engine_url"] == "https://nyaa.si"
    assert row["desc_link"] == item["desc_link"]


def test_to_result_row_falls_back_to_torrent_url():
    item = core.parse_rss(make_rss([make_item()]))[0]
    item["infohash"] = ""
    row = core.to_result_row(item, "https://nyaa.si")
    assert row["link"] == item["torrent_url"]
