"""Tiny CLI to exercise the core against the live RSS feeds.

Usage:
    python -m nyaa_core.main "your query" [--site sukebei] [--cat anime]
"""

import argparse
from urllib.request import Request, urlopen

from .core import fetch_results, to_result_row

SITES = {
    "nyaa": "https://nyaa.si",
    "sukebei": "https://sukebei.nyaa.si",
}


def _fetch(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as resp:  # noqa: S310 (trusted, fixed hosts)
        return resp.read().decode("utf-8", "replace")


def main():
    parser = argparse.ArgumentParser(description="Query nyaa/sukebei RSS.")
    parser.add_argument("query")
    parser.add_argument("--site", choices=sorted(SITES), default="nyaa")
    parser.add_argument("--cat", default="0_0", help="nyaa category code, e.g. 1_0")
    parser.add_argument(
        "--filter",
        type=int,
        choices=(0, 1, 2),
        default=0,
        help="nyaa f= filter: 0 none, 1 no-remakes, 2 trusted-only",
    )
    args = parser.parse_args()

    base_url = SITES[args.site]
    items = fetch_results(_fetch, base_url, args.cat, args.query, filt=args.filter)
    print("%d results from %s" % (len(items), base_url))
    for item in items[:10]:
        row = to_result_row(item, base_url)
        print("%5s S  %s  (%s)" % (row["seeds"], row["name"], row["size"]))


if __name__ == "__main__":
    main()
