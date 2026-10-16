import http.client
import socket
from email.message import Message

import pytest

from orchestra.evidence_fetcher import (
    EvidenceFetcher,
    EvidenceFetchingDisabled,
    EvidenceFetchRequestError,
    EvidenceFetchUnavailable,
    _VisibleTextParser,
)


class FakeSocket:
    def __init__(self):
        self.request = b""
        self.closed = False

    def settimeout(self, timeout):
        self.timeout = timeout

    def sendall(self, data):
        self.request += data

    def close(self):
        self.closed = True


class FakeResponse:
    def __init__(self, body=b"<html><body>Visible <script>hidden</script> source text</body></html>", status=200, content_type="text/html; charset=utf-8", content_length=None):
        self.status = status
        self.body = body
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        if content_length is not None:
            self.headers["Content-Length"] = str(content_length)
        self.closed = False
        self.read_called = False

    def begin(self):
        pass

    def getheader(self, name, default=None):
        return self.headers.get(name, default)

    def read(self, size=-1):
        self.read_called = True
        return self.body[:size]

    def close(self):
        self.closed = True


def public_resolver(host, port, type):
    return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", port))]


def test_visible_text_parser_does_not_unhide_content_on_mismatched_closing_tag():
    parser = _VisibleTextParser()
    parser.feed("<template>hidden</script>still hidden</template> visible")

    assert " ".join(parser.parts).strip() == "visible"


def test_fetch_pins_checked_public_ip_and_extracts_visible_text(monkeypatch):
    sock = FakeSocket()
    response = FakeResponse()
    addresses = []

    def connector(address, timeout):
        addresses.append(address)
        return sock

    monkeypatch.setattr(http.client, "HTTPResponse", lambda unused: response)
    fetcher = EvidenceFetcher(["example.com"], resolver=public_resolver, connector=connector)
    result = fetcher.fetch_many(["http://example.com/article#section"])[0]

    assert addresses == [("93.184.216.34", 80)]
    assert b"GET /article HTTP/1.1" in sock.request
    assert result.url == "http://example.com/article"
    assert result.source_name == "example.com"
    assert result.content == "Visible source text"
    assert len(result.content_sha256) == 64
    assert result.evidence_id.startswith("ev_")
    assert response.closed and sock.closed


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://127.0.0.1/",
        "http://evil.example/",
        "http://example.com:8080/",
        "http://user@example.com/",
    ],
)
def test_fetch_rejects_unsafe_or_unallowlisted_urls(url):
    fetcher = EvidenceFetcher(["example.com"], resolver=public_resolver)
    with pytest.raises(EvidenceFetchRequestError):
        fetcher.fetch_many([url])


def test_fetch_rejects_duplicate_canonical_urls_before_network():
    fetcher = EvidenceFetcher(["example.com"], resolver=public_resolver)
    with pytest.raises(EvidenceFetchRequestError, match="Duplicate"):
        fetcher.fetch_many(["http://example.com/a#one", "http://example.com/a#two"])


def test_fetch_blocks_private_dns_answers_before_connecting():
    called = []

    def private_resolver(host, port, type):
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", port))]

    fetcher = EvidenceFetcher(
        ["example.com"],
        resolver=private_resolver,
        connector=lambda *args, **kwargs: called.append(args),
    )
    with pytest.raises(EvidenceFetchRequestError, match="non-public"):
        fetcher.fetch_many(["http://example.com/"])
    assert called == []


@pytest.mark.parametrize("malformed_answers", [[()], [(None,)], [(0, 0, 0, "", ())], [(0, 0, 0, "", (None, 80))]])
def test_malformed_dns_resolver_records_fail_closed(malformed_answers):
    called = []

    def malformed_resolver(host, port, type):
        return malformed_answers

    fetcher = EvidenceFetcher(
        ["example.com"],
        resolver=malformed_resolver,
        connector=lambda *args, **kwargs: called.append(args),
    )

    with pytest.raises(EvidenceFetchUnavailable, match="no usable public address"):
        fetcher.fetch_many(["http://example.com/"])
    assert called == []


def test_redirects_are_rejected_and_never_followed(monkeypatch):
    sock = FakeSocket()
    response = FakeResponse(status=302)
    calls = []

    def connector(address, timeout):
        calls.append(address)
        return sock

    monkeypatch.setattr(http.client, "HTTPResponse", lambda unused: response)
    fetcher = EvidenceFetcher(["example.com"], resolver=public_resolver, connector=connector)
    with pytest.raises(EvidenceFetchUnavailable, match="HTTP 200"):
        fetcher.fetch_many(["http://example.com/"])
    assert len(calls) == 1
    assert response.closed


def test_oversized_content_length_is_rejected(monkeypatch):
    sock = FakeSocket()
    response = FakeResponse(content_length=100)
    monkeypatch.setattr(http.client, "HTTPResponse", lambda unused: response)
    fetcher = EvidenceFetcher(
        ["example.com"],
        max_response_bytes=10,
        resolver=public_resolver,
        connector=lambda address, timeout: sock,
    )
    with pytest.raises(EvidenceFetchUnavailable, match="size limit"):
        fetcher.fetch_many(["http://example.com/"])
    assert not response.read_called


def test_non_text_content_is_rejected(monkeypatch):
    sock = FakeSocket()
    response = FakeResponse(content_type="application/octet-stream")
    monkeypatch.setattr(http.client, "HTTPResponse", lambda unused: response)
    fetcher = EvidenceFetcher(
        ["example.com"],
        resolver=public_resolver,
        connector=lambda address, timeout: sock,
    )
    with pytest.raises(EvidenceFetchUnavailable, match="content type"):
        fetcher.fetch_many(["http://example.com/"])


def test_fetching_is_disabled_without_explicit_allowlist():
    with pytest.raises(EvidenceFetchingDisabled):
        EvidenceFetcher().fetch_many(["http://example.com/"])


@pytest.mark.parametrize("host", ["127.0.0.1", "example.com/path", "bad_host"])
def test_allowlist_rejects_non_host_values(host):
    with pytest.raises(ValueError):
        EvidenceFetcher([host])


def test_non_ascii_path_and_query_are_percent_encoded(monkeypatch):
    sock = FakeSocket()
    response = FakeResponse()
    monkeypatch.setattr(http.client, "HTTPResponse", lambda unused: response)
    fetcher = EvidenceFetcher(
        ["example.com"],
        resolver=public_resolver,
        connector=lambda address, timeout: sock,
    )

    result = fetcher.fetch_many(["http://example.com/café?q=é"])[0]

    assert b"GET /caf%C3%A9?q=%C3%A9 HTTP/1.1" in sock.request
    assert result.url == "http://example.com/caf%C3%A9?q=%C3%A9"



def test_fetch_rejects_mixed_public_and_private_dns_answers_before_connecting():
    called = []

    def mixed_resolver(host, port, type):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", port)),
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("10.0.0.7", port)),
        ]

    fetcher = EvidenceFetcher(
        ["example.com"],
        resolver=mixed_resolver,
        connector=lambda *args, **kwargs: called.append(args),
    )
    with pytest.raises(EvidenceFetchRequestError, match="non-public"):
        fetcher.fetch_many(["http://example.com/"])
    assert called == []


def test_fetch_bounds_body_when_content_length_is_missing(monkeypatch):
    sock = FakeSocket()
    response = FakeResponse(
        body=b"x" * 64,
        content_type="text/plain",
    )
    monkeypatch.setattr(http.client, "HTTPResponse", lambda unused: response)
    fetcher = EvidenceFetcher(
        ["example.com"],
        max_response_bytes=16,
        resolver=public_resolver,
        connector=lambda address, timeout: sock,
    )

    with pytest.raises(EvidenceFetchUnavailable, match="size limit"):
        fetcher.fetch_many(["http://example.com/"])

    assert response.read_called
    assert response.closed
    assert sock.closed


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/path with spaces",
        "http://example.com/?q=hello\r\nX-Injected: yes",
    ],
)
def test_fetch_rejects_whitespace_or_header_injection_in_url(url):
    fetcher = EvidenceFetcher(["example.com"], resolver=public_resolver)
    with pytest.raises(EvidenceFetchRequestError):
        fetcher.fetch_many([url])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_response_bytes": 1.5},
        {"max_response_bytes": True},
        {"max_text_chars": 1.5},
        {"max_text_chars": True},
        {"timeout_seconds": True},
        {"timeout_seconds": "3"},
    ],
)
def test_fetcher_rejects_invalid_resource_bounds(kwargs):
    with pytest.raises(ValueError):
        EvidenceFetcher(**kwargs)


def test_fetch_preserves_existing_percent_escapes_and_query_semantics(monkeypatch):
    sock = FakeSocket()
    response = FakeResponse(content_type="text/plain", body=b"ok")
    monkeypatch.setattr(http.client, "HTTPResponse", lambda unused: response)
    fetcher = EvidenceFetcher(
        ["example.com"],
        resolver=public_resolver,
        connector=lambda address, timeout: sock,
    )

    result = fetcher.fetch_many(["http://example.com/a%2Fb?q=a+b&next=%2F"])[0]

    assert b"GET /a%2Fb?q=a+b&next=%2F HTTP/1.1" in sock.request
    assert result.url == "http://example.com/a%2Fb?q=a+b&next=%2F"



def test_fetch_rejects_unbounded_url_iterable_after_six_items():
    consumed = []

    def urls():
        index = 0
        while True:
            consumed.append(index)
            yield "http://example.com/"
            index += 1

    fetcher = EvidenceFetcher(["example.com"], resolver=public_resolver)

    with pytest.raises(EvidenceFetchRequestError, match="Between 1 and 5"):
        fetcher.fetch_many(urls())

    assert consumed == list(range(6))


def test_fetch_rejects_non_iterable_url_input():
    fetcher = EvidenceFetcher(["example.com"], resolver=public_resolver)

    with pytest.raises(EvidenceFetchRequestError, match="iterable"):
        fetcher.fetch_many(None)


@pytest.mark.parametrize("url", ["http://[::1/", "https://[not-an-ip]/"])
def test_malformed_url_authority_is_a_request_error(url):
    fetcher = EvidenceFetcher(["example.com"], resolver=public_resolver)
    with pytest.raises(EvidenceFetchRequestError, match="URL is invalid"):
        fetcher.fetch_many([url])

