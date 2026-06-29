"""Tests for the generated single-file plugins (fake qBittorrent modules)."""

import importlib.util
import os
import sys
import types

import build_plugin
import pytest
from sample_rss import SAMPLE_RSS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_DIR = os.path.join(ROOT, "engine")

PLUGINS = [
    ("nyaa", "https://nyaa.si", "Nyaa"),
    ("sukebei", "https://sukebei.nyaa.si", "Sukebei"),
]


def _load_engine(module_name, captured):
    """Import an engine/*.py file with fake helpers/novaprinter injected."""
    fake_helpers = types.ModuleType("helpers")
    fake_helpers.retrieve_url = lambda url: SAMPLE_RSS
    fake_helpers.download_file = lambda url: url + " /tmp/fake.torrent"
    fake_novaprinter = types.ModuleType("novaprinter")
    fake_novaprinter.prettyPrinter = lambda d: captured.append(d)

    saved = {k: sys.modules.get(k) for k in ("helpers", "novaprinter", module_name)}
    sys.modules["helpers"] = fake_helpers
    sys.modules["novaprinter"] = fake_novaprinter
    try:
        path = os.path.join(ENGINE_DIR, module_name + ".py")
        spec = importlib.util.spec_from_file_location("engine_" + module_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


@pytest.mark.parametrize("module_name,url,name", PLUGINS)
def test_engine_file_exists(module_name, url, name):
    assert os.path.exists(os.path.join(ENGINE_DIR, module_name + ".py"))


@pytest.mark.parametrize("module_name,url,name", PLUGINS)
def test_version_header_first_line(module_name, url, name):
    with open(os.path.join(ENGINE_DIR, module_name + ".py"), encoding="utf-8") as f:
        first = f.readline().strip()
    assert first.startswith("# VERSION:")


@pytest.mark.parametrize("module_name,url,name", PLUGINS)
def test_no_third_party_imports(module_name, url, name):
    with open(os.path.join(ENGINE_DIR, module_name + ".py"), encoding="utf-8") as f:
        src = f.read()
    for banned in ("import requests", "import nyaa_core", "from nyaa_core"):
        assert banned not in src


@pytest.mark.parametrize("module_name,url,name", PLUGINS)
def test_class_contract(module_name, url, name):
    mod = _load_engine(module_name, [])
    cls = getattr(mod, module_name)
    assert cls.url == url
    assert cls.name == name
    assert "all" in cls.supported_categories
    inst = cls()
    assert hasattr(inst, "search")
    assert hasattr(inst, "download_torrent")


@pytest.mark.parametrize("module_name,url,name", PLUGINS)
def test_search_maps_fields_and_sorts(module_name, url, name):
    captured = []
    mod = _load_engine(module_name, captured)
    cls = getattr(mod, module_name)
    cls().search("anything")
    assert len(captured) == 2
    # Sorted by seeders desc.
    assert captured[0]["seeds"] == 99
    row = captured[0]
    assert set(row) == {
        "link",
        "name",
        "size",
        "seeds",
        "leech",
        "engine_url",
        "desc_link",
        "pub_date",
    }
    assert row["link"].startswith("magnet:?xt=urn:btih:")
    assert row["engine_url"] == url


@pytest.mark.parametrize("module_name,url,name", PLUGINS)
def test_download_torrent_magnet_passthrough(module_name, url, name, capsys):
    mod = _load_engine(module_name, [])
    cls = getattr(mod, module_name)
    magnet = "magnet:?xt=urn:btih:DEADBEEF"
    cls().download_torrent(magnet)
    out = capsys.readouterr().out.strip()
    assert out == magnet + " " + magnet


@pytest.mark.parametrize("module_name,url,name", PLUGINS)
def test_download_torrent_file_fallback(module_name, url, name, capsys):
    mod = _load_engine(module_name, [])
    cls = getattr(mod, module_name)
    torrent_url = "https://nyaa.si/download/1.torrent"
    cls().download_torrent(torrent_url)
    out = capsys.readouterr().out.strip()
    assert out.startswith(torrent_url + " ")


def test_generator_is_deterministic_and_compiles():
    import py_compile
    import tempfile

    for site in build_plugin.SITES.values():
        first = build_plugin.generate(site)
        second = build_plugin.generate(site)
        assert first == second
        with tempfile.NamedTemporaryFile(
            "w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(first)
            tmp = f.name
        py_compile.compile(tmp, doraise=True)
        os.unlink(tmp)
