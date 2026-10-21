import importlib
import io
import ssl
from unittest.mock import patch


def test_https_uses_only_certifi_roots():
    client = importlib.import_module('nyaa_core.main')
    context = ssl.create_default_context(cafile=client.certifi.where())
    with patch.object(client.ssl, "create_default_context", return_value=context) as factory:
        with patch.object(client, "urlopen") as opener:
            opener.return_value.__enter__.return_value = io.BytesIO(b"{}")
            client._fetch("https://example.invalid")
    factory.assert_called_once_with(cafile=client.certifi.where())
    assert opener.call_args.kwargs["context"] is context
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname
