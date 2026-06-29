"""Transport-agnostic core for the nyaa qBittorrent search plugins.

This is the single source of truth shared by both generated plugins
(``engine/nyaa.py`` and ``engine/sukebei.py``). nyaa.si and sukebei.nyaa.si run
the same software, so they differ only in base URL, display name, and category
taxonomy -- everything below is identical for both.

stdlib-only by design: everything after the ``=== BEGIN PLUGIN INLINE ===``
marker is copied verbatim into each single-file plugin by
``tools/build_plugin.py``. HTTP is injected as a ``fetch(url) -> str`` callable
so the same code works with ``urllib`` (tests), ``requests``, or qBittorrent's
``helpers.retrieve_url``.
"""

# === BEGIN PLUGIN INLINE ===
from email.utils import parsedate_to_datetime
from urllib.parse import quote, urlencode
from xml.etree import ElementTree

# nyaa serves up to this many items per RSS page; fewer means the last page.
RESULTS_PER_PAGE = 75

# Cap pages fetched per search so a generic query can't fan out forever.
DEFAULT_MAX_PAGES = 4

# nyaa "f=" filter values. The qBittorrent search UI has no place to set this,
# so the generated plugins always use FILTER_NONE. It's plumbed through the API
# anyway so this core can double as a standalone search library where a caller
# may want trusted-only or no-remakes results.
FILTER_NONE = 0
FILTER_NO_REMAKES = 1
FILTER_TRUSTED_ONLY = 2
DEFAULT_FILTER = FILTER_NONE

# Public trackers nyaa.si bakes into the magnet links it generates. We rebuild
# magnets locally from <nyaa:infoHash> to avoid a per-result .torrent fetch.
NYAA_TRACKERS = (
    "http://nyaa.tracker.wf:7777/announce",
    "udp://open.stealth.si:80/announce",
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://exodus.desync.com:6969/announce",
    "udp://tracker.torrent.eu.org:451/announce",
)


def build_rss_url(base_url, cat_code, query, page=1, filt=DEFAULT_FILTER):
    """Build a nyaa/sukebei RSS search URL.

    ``filt`` is the nyaa ``f=`` value: ``FILTER_NONE`` (0), ``FILTER_NO_REMAKES``
    (1), or ``FILTER_TRUSTED_ONLY`` (2).
    """
    params = [
        ("page", "rss"),
        ("q", query),
        ("c", cat_code),
        ("f", filt),
        ("p", page),
    ]
    return base_url.rstrip("/") + "/?" + urlencode(params)


def build_magnet(infohash, name):
    """Construct a magnet URI from an infohash and display name."""
    parts = ["magnet:?xt=urn:btih:" + infohash]
    if name:
        parts.append("dn=" + quote(name))
    for tracker in NYAA_TRACKERS:
        parts.append("tr=" + quote(tracker, safe=""))
    return "&".join(parts)


def _to_int(text, default=-1):
    try:
        return int(text)
    except (TypeError, ValueError):
        return default


def _pub_date(text):
    """Convert an RFC-822 RSS pubDate to a Unix timestamp (-1 on failure)."""
    if not text:
        return -1
    try:
        return int(parsedate_to_datetime(text).timestamp())
    except (TypeError, ValueError, OverflowError):
        return -1


def _nyaa_text(item, tag):
    # Match the <nyaa:*> element by local name regardless of namespace URI:
    # nyaa.si declares ".../nyaa.si/xmlns/nyaa" while sukebei.nyaa.si declares
    # ".../sukebei.nyaa.si/xmlns/nyaa". The "{*}" wildcard (Python 3.8+) matches
    # either, so one parser serves both sites.
    el = item.find("{*}" + tag)
    if el is not None and el.text:
        return el.text
    return ""


def parse_rss(xml_text):
    """Parse a nyaa RSS document into a list of normalized result dicts."""
    root = ElementTree.fromstring(xml_text)
    results = []
    for item in root.iter("item"):
        results.append(
            {
                "name": item.findtext("title", "") or "",
                "infohash": _nyaa_text(item, "infoHash"),
                # Standard <link> is the .torrent file; <guid> is the view page.
                "torrent_url": item.findtext("link", "") or "",
                "desc_link": item.findtext("guid", "")
                or item.findtext("link", "")
                or "",
                "size": _nyaa_text(item, "size") or "-1",
                "seeds": _to_int(_nyaa_text(item, "seeders")),
                "leech": _to_int(_nyaa_text(item, "leechers")),
                "pub_date": _pub_date(item.findtext("pubDate", "")),
            }
        )
    return results


def fetch_results(
    fetch, base_url, cat_code, query, max_pages=DEFAULT_MAX_PAGES, filt=DEFAULT_FILTER
):
    """Fetch and merge all RSS pages for a query, sorted by seeders desc.

    RSS has no server-side sort, so we paginate until a short page and sort
    client-side -- qBittorrent expects the most-seeded results first.

    ``filt`` maps to nyaa's ``f=`` (see the ``FILTER_*`` constants). The plugins
    leave it at ``DEFAULT_FILTER``; standalone library callers can override it.
    """
    items = []
    for page in range(1, max_pages + 1):
        xml_text = fetch(build_rss_url(base_url, cat_code, query, page, filt))
        page_items = parse_rss(xml_text)
        items.extend(page_items)
        if len(page_items) < RESULTS_PER_PAGE:
            break
    items.sort(key=lambda it: it["seeds"], reverse=True)
    return items


def to_result_row(item, engine_url):
    """Map a parsed item to a qBittorrent prettyPrinter row dict."""
    if item.get("infohash"):
        link = build_magnet(item["infohash"], item.get("name", ""))
    else:
        link = item.get("torrent_url", "")
    return {
        "link": link,
        "name": item.get("name", ""),
        "size": item.get("size", "-1"),
        "seeds": item.get("seeds", -1),
        "leech": item.get("leech", -1),
        "engine_url": engine_url,
        "desc_link": item.get("desc_link", ""),
        "pub_date": item.get("pub_date", -1),
    }
