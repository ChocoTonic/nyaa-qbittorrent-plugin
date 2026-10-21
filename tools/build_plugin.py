#!/usr/bin/env python3
"""Generate the single-file qBittorrent search plugins from the shared core.

Both nyaa.si and sukebei.nyaa.si run the same software, so a single
``plugin/shell.py`` template + ``src/nyaa_core/core.py`` produce two plugins
that differ only in base URL, display name, and category map:

    engine/nyaa.py     (class ``nyaa``    -> https://nyaa.si)
    engine/sukebei.py  (class ``sukebei`` -> https://sukebei.nyaa.si)

qBittorrent requires the filename to equal the class name and matches a result's
``engine_url`` back to the plugin's ``url`` to route downloads -- so the two
sites must be two files, not one.

Deterministic: same inputs -> byte-identical output, so CI can regenerate and
`git diff --exit-code` to detect a stale artifact. DO NOT edit engine/*.py by
hand. Run via `make plugin`.
"""

import os
import py_compile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "src", "nyaa_core", "core.py")
SHELL = os.path.join(ROOT, "plugin", "shell.py")
OUT_DIR = os.path.join(ROOT, "engine")

CORE_MARKER = "# === BEGIN PLUGIN INLINE ==="
CORE_PLACEHOLDER = "# __NYAA_CORE__"
VERSION_PLACEHOLDER = "__PLUGIN_VERSION__"

# The only per-site divergence. Keys must match qBittorrent's standard category
# names; values are nyaa "<main>_<sub>" codes (0_0 == everything).
SITES = {
    "nyaa": {
        "class": "nyaa",
        "name": "Nyaa",
        "base_url": "https://nyaa.si",
        "categories": {
            "all": "0_0",
            "anime": "1_0",
            "music": "2_0",
            "books": "3_0",  # Literature
            "tv": "4_0",  # Live Action
            "movies": "4_0",  # Live Action
            "pictures": "5_0",
            "software": "6_0",
        },
    },
    "sukebei": {
        "class": "sukebei",
        "name": "Sukebei",
        "base_url": "https://sukebei.nyaa.si",
        "categories": {
            "all": "0_0",
            "pictures": "1_0",  # Art
            "movies": "2_0",  # Real Life
        },
    },
}


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _core_body(core_src):
    idx = core_src.find(CORE_MARKER)
    if idx == -1:
        raise SystemExit("core.py is missing the marker: " + CORE_MARKER)
    return core_src[idx + len(CORE_MARKER) :].strip("\n")


def _plugin_version():
    """Version stamped into the ``# VERSION:`` header.

    Read from the ``PLUGIN_VERSION`` env var so the release workflow can stamp a
    real, monotonic version at publish time. Defaults to ``0.0`` for local/test
    builds (the committed tree carries no version -- releases own it).
    """
    return os.environ.get("PLUGIN_VERSION", "0.0").strip()


def _fmt_categories(categories):
    items = ", ".join('"%s": "%s"' % (k, v) for k, v in categories.items())
    return "{" + items + "}"


def generate(site):
    """Return generated plugin source for one site config (no side effects)."""
    shell_src = _read(SHELL)
    if CORE_PLACEHOLDER not in shell_src:
        raise SystemExit("plugin/shell.py is missing placeholder: " + CORE_PLACEHOLDER)
    out = shell_src.replace(VERSION_PLACEHOLDER, _plugin_version())
    out = out.replace("__CA_BUNDLE__", repr(_read(os.path.join(ROOT, "plugin", "cacert.pem"))))
    out = out.replace(CORE_PLACEHOLDER, _core_body(_read(CORE)))
    out = out.replace("__PLUGIN_CLASS__", site["class"])
    out = out.replace("__PLUGIN_NAME__", site["name"])
    out = out.replace("__BASE_URL__", site["base_url"])
    out = out.replace("__CATEGORY_MAP__", _fmt_categories(site["categories"]))
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for key, site in SITES.items():
        out_path = os.path.join(OUT_DIR, key + ".py")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(generate(site))
        py_compile.compile(out_path, doraise=True)
        print("Wrote {0} (VERSION {1})".format(out_path, _plugin_version()))


if __name__ == "__main__":
    main()
