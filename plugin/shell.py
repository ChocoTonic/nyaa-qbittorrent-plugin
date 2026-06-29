# VERSION: __PLUGIN_VERSION__
# qBittorrent search engine plugin for __PLUGIN_NAME__ (__BASE_URL__)
#
# AUTO-GENERATED -- DO NOT EDIT engine/*.py BY HAND.
# Source of truth: src/nyaa_core/core.py + plugin/shell.py
# Regenerate with `make plugin`.
# Project: https://github.com/ChocoTonic/nyaa-qbittorrent-plugin

try:
    from helpers import download_file, retrieve_url
    from novaprinter import prettyPrinter
except ImportError:
    # Allows this file to be imported / unit-tested outside of qBittorrent.
    def retrieve_url(url):
        raise RuntimeError("retrieve_url is only available inside qBittorrent")

    def download_file(url):
        raise RuntimeError("download_file is only available inside qBittorrent")

    def prettyPrinter(dictionary):
        print(dictionary)


# __NYAA_CORE__


class __PLUGIN_CLASS__(object):
    url = "__BASE_URL__"
    name = "__PLUGIN_NAME__"
    supported_categories = __CATEGORY_MAP__

    def search(self, what, cat="all"):
        cat_code = self.supported_categories.get(cat, "0_0")
        for item in fetch_results(retrieve_url, self.url, cat_code, what):
            prettyPrinter(to_result_row(item, self.url))

    def download_torrent(self, info):
        # Results carry a magnet rebuilt from the RSS infoHash, so this is almost
        # always a passthrough; the rare magnet-less item is a .torrent URL that
        # qBittorrent downloads via download_file.
        if info.startswith("magnet:"):
            print(info + " " + info)
        else:
            print(download_file(info))
