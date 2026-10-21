The vendored cacert.pem is the unmodified Mozilla CA bundle from certifi
2026.10.19, licensed under MPL-2.0 (CA-LICENSE).

Source: https://pypi.org/project/certifi/2026.10.19/
SHA-256: 50f79f98dac192b20dbf73f35c56f0b0c557ab267ff5199d1117cc1180b70785

The generator embeds this bundle into each single-file plugin. This preserves
the stdlib-only qBittorrent runtime while supplying explicit trust to both
retrieve_url and download_file. OS trust roots are not added. Refresh the
vendored bundle from an approved newer certifi release when updating trust,
update this fingerprint, then regenerate both plugins and run tests.
