# nyaa-qbittorrent-plugin

qBittorrent search engine plugins for **[nyaa.si](https://nyaa.si)** and
**[sukebei.nyaa.si](https://sukebei.nyaa.si)**, generated from a single shared,
stdlib-only core.

Both sites run the same software and expose an RSS feed, so one parser serves
both — the two plugins differ only in base URL, display name, and category map.

## Install (qBittorrent users)

In qBittorrent: **Search** tab → **Search plugins…** → **Install a new one** →
**Web link**, then paste the URL for the site(s) you want:

| Site | Install URL |
| --- | --- |
| Nyaa | `https://github.com/ChocoTonic/nyaa-qbittorrent-plugin/releases/latest/download/nyaa.py` |
| Sukebei | `https://github.com/ChocoTonic/nyaa-qbittorrent-plugin/releases/latest/download/sukebei.py` |

They install as two independent search engines. To update, reinstall with the
same URL (qBittorrent's "Check for updates" won't track these).

## How it works

```
src/nyaa_core/core.py      stdlib-only, transport-agnostic source of truth
        │                  (RSS fetch + parse, magnet build, sort, result mapping)
        ▼
plugin/shell.py            one parameterized qBittorrent plugin template
        │
        ▼  tools/build_plugin.py  (inlines core, fills per-site placeholders)
        ▼
engine/nyaa.py             class nyaa     → https://nyaa.si
engine/sukebei.py          class sukebei  → https://sukebei.nyaa.si
```

- **Data source:** each site's RSS feed (`?page=rss&q=…&c=…`), parsed with
  `xml.etree`. RSS has no server-side sort, so results are paginated and sorted
  by seeders client-side.
- **Download links:** magnet URIs rebuilt locally from `<nyaa:infoHash>` plus
  nyaa's standard trackers (no extra `.torrent` fetch); magnet-less items fall
  back to the `.torrent` URL.
- **Two files, one core:** qBittorrent requires `filename == class name` and
  routes downloads by matching a result's `engine_url` to a plugin's `url`, so
  the two sites must be two files. They're both generated from the same core —
  edit the core once, both plugins update.
- **No dependencies:** the generated plugins import only the Python standard
  library (and qBittorrent's own `helpers`/`novaprinter`).

## Development

```bash
make install     # uv sync --extra dev
make plugin      # regenerate engine/nyaa.py + engine/sukebei.py
make test        # unit + plugin tests (mocked, no network)
make test-live   # hits the real feeds (slow; retried)
make lint        # ruff
```

Never edit `engine/*.py` by hand — they're generated and gitignored. Change
`src/nyaa_core/core.py` (shared logic), `plugin/shell.py` (the plugin shape), or
the `SITES` table in `tools/build_plugin.py` (URLs / names / category codes),
then run `make plugin`. CI regenerates and runs `git diff --exit-code` to catch
a stale build.

Quick manual check against the live feeds:

```bash
PYTHONPATH=src python -m nyaa_core.main "cowboy bebop" --cat 1_0
PYTHONPATH=src python -m nyaa_core.main "a" --site sukebei
```

## Releases

Merging to `master` runs `.github/workflows/plugin-release.yml`, which
regenerates both plugins, skips publishing if neither body changed, and
otherwise publishes them to a GitHub Release (and a moving `latest` tag).
