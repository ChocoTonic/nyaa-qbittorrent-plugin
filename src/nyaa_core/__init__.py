"""Shared core for the nyaa / sukebei qBittorrent search plugins."""

from .core import (
    FILTER_NO_REMAKES,
    FILTER_NONE,
    FILTER_TRUSTED_ONLY,
    build_magnet,
    build_rss_url,
    fetch_results,
    parse_rss,
    to_result_row,
)

__all__ = [
    "FILTER_NONE",
    "FILTER_NO_REMAKES",
    "FILTER_TRUSTED_ONLY",
    "build_magnet",
    "build_rss_url",
    "fetch_results",
    "parse_rss",
    "to_result_row",
]
