"""Opt-in, allowlisted HTTP source snapshot fetching with SSRF safeguards."""
import hashlib
import http.client
import ipaddress
import os
import re
import socket
import ssl
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from email.message import Message
from html.parser import HTMLParser
from urllib.parse import urlsplit, urlunsplit


_HOST_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_IGNORED_TAGS = {"script", "style", "noscript", "svg", "template"}


class EvidenceFetchRequestError(ValueError):
    """Raised when a requested URL violates the configured source policy."""


class EvidenceFetchingDisabled(RuntimeError):
    """Raised when source fetching has no explicit hostname allowlist."""


class EvidenceFetchUnavailable(RuntimeError):
    """Raised when an allowlisted source cannot be fetched safely."""


@dataclass(frozen=True)
class FetchedEvidence:
    evidence_id: str
    source_name: str
    url: str
    retrieved_at: str
    content_type: str
    content_sha256: str
    content: str


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in _IGNORED_TAGS:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in _IGNORED_TAGS and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


class EvidenceFetcher:
    """Fetch bounded text from explicitly allowlisted public hosts only.

    Redirects, non-default ports, IP literals, private/reserved DNS answers,
    non-text content, and oversized responses are rejected. DNS is resolved
    once and the socket connects to that checked IP while TLS still validates
    the original hostname. Fetching is disabled unless the host allowlist is set.
    """

    def __init__(
        self,
        allowed_hosts: Iterable[str] = (),
        *,
        timeout_seconds: float = 3.0,
        max_response_bytes: int = 262144,
        max_text_chars: int = 20000,
        resolver: Callable[..., list[tuple]] | None = None,
        connector: Callable[..., socket.socket] | None = None,
    ) -> None:
        if not 0 < timeout_seconds <= 10:
            raise ValueError("timeout_seconds must be between 0 and 10")
        if not 1 <= max_response_bytes <= 1048576:
            raise ValueError("max_response_bytes must be between 1 and 1048576")
        if not 1 <= max_text_chars <= 50000:
            raise ValueError("max_text_chars must be between 1 and 50000")
        self.allowed_hosts = frozenset(self._normalize_allowed_host(host) for host in allowed_hosts)
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        self.max_text_chars = max_text_chars
        self._resolver = resolver or socket.getaddrinfo
        self._connector = connector or socket.create_connection

    @classmethod
    def from_env(cls) -> "EvidenceFetcher":
        hosts = tuple(
            item.strip()
            for item in os.getenv("ORCHESTRA_EVIDENCE_ALLOWED_HOSTS", "").split(",")
            if item.strip()
        )
        return cls(hosts)

    @property
    def enabled(self) -> bool:
        return bool(self.allowed_hosts)

    @staticmethod
    def _normalize_allowed_host(value: str) -> str:
        host = value.strip().rstrip(".").lower()
        try:
            host = host.encode("idna").decode("ascii")
        except UnicodeError:
            raise ValueError("evidence allowlist contains an invalid hostname") from None
        if not host or len(host) > 253 or any(not _HOST_LABEL.fullmatch(label) for label in host.split(".")):
            raise ValueError("evidence allowlist entries must be DNS hostnames without ports or paths")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return host
        raise ValueError("evidence allowlist entries must be hostnames, not IP addresses")

    def _validate_url(self, url: str) -> tuple[str, str, int, str, str, str]:
        if not isinstance(url, str) or not url.strip() or any(ord(char) < 32 or ord(char) == 127 for char in url):
            raise EvidenceFetchRequestError("URL is invalid")
        parts = urlsplit(url.strip())
        scheme = parts.scheme.lower()
        if scheme not in {"http", "https"} or not parts.hostname or parts.username is not None or parts.password is not None:
            raise EvidenceFetchRequestError("Only absolute HTTP(S) URLs without user information are accepted")
        try:
            supplied_port = parts.port
        except ValueError:
            raise EvidenceFetchRequestError("URL port is invalid") from None
        port = 443 if scheme == "https" else 80
        if supplied_port not in {None, port}:
            raise EvidenceFetchRequestError("Non-default URL ports are not allowed")
        try:
            host = parts.hostname.rstrip(".").encode("idna").decode("ascii").lower()
        except UnicodeError:
            raise EvidenceFetchRequestError("URL hostname is invalid") from None
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise EvidenceFetchRequestError("IP-literal URLs are not allowed")
        if not any(host == allowed or host.endswith("." + allowed) for allowed in self.allowed_hosts):
            raise EvidenceFetchRequestError("URL hostname is not in ORCHESTRA_EVIDENCE_ALLOWED_HOSTS")
        path = parts.path or "/"
        query = parts.query
        if any(char.isspace() for char in path + query):
            raise EvidenceFetchRequestError("URL path contains invalid whitespace")
        canonical_url = urlunsplit((scheme, host, path, query, ""))
        return canonical_url, host, port, scheme, path, query

    def _resolve_public_ip(self, host: str, port: int) -> str:
        try:
            answers = self._resolver(host, port, type=socket.SOCK_STREAM)
        except OSError:
            raise EvidenceFetchUnavailable("Source host could not be resolved") from None
        addresses: list[str] = []
        for answer in answers:
            raw_ip = answer[4][0].split("%", 1)[0]
            try:
                address = ipaddress.ip_address(raw_ip)
            except ValueError:
                continue
            if not address.is_global:
                raise EvidenceFetchRequestError("Source hostname resolves to a non-public IP address")
            addresses.append(str(address))
        if not addresses:
            raise EvidenceFetchUnavailable("Source host has no usable public address")
        return addresses[0]

    def fetch_many(self, urls: Iterable[str]) -> tuple[FetchedEvidence, ...]:
        if not self.enabled:
            raise EvidenceFetchingDisabled("Set ORCHESTRA_EVIDENCE_ALLOWED_HOSTS to enable source fetching")
        requested = tuple(urls)
        if not 1 <= len(requested) <= 5:
            raise EvidenceFetchRequestError("Between 1 and 5 source URLs are required")
        validated = tuple(self._validate_url(url) for url in requested)
        canonical_urls = [item[0] for item in validated]
        if len(set(canonical_urls)) != len(canonical_urls):
            raise EvidenceFetchRequestError("Duplicate source URLs are not allowed")
        return tuple(self._fetch_one(item) for item in validated)

    def _fetch_one(self, item: tuple[str, str, int, str, str, str]) -> FetchedEvidence:
        canonical_url, host, port, scheme, path, query = item
        ip = self._resolve_public_ip(host, port)
        sock = None
        response = None
        try:
            sock = self._connector((ip, port), timeout=self.timeout_seconds)
            sock.settimeout(self.timeout_seconds)
            if scheme == "https":
                sock = ssl.create_default_context().wrap_socket(sock, server_hostname=host)
                sock.settimeout(self.timeout_seconds)
            target = path + (("?" + query) if query else "")
            request = (
                f"GET {target} HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                "User-Agent: AI-ORCHESTRA-EvidenceFetcher/0.1\r\n"
                "Accept: text/html, text/plain;q=0.9\r\n"
                "Accept-Encoding: identity\r\n"
                "Connection: close\r\n\r\n"
            )
            sock.sendall(request.encode("ascii"))
            response = http.client.HTTPResponse(sock)
            response.begin()
            if response.status != 200:
                raise EvidenceFetchUnavailable("Source server did not return HTTP 200")
            content_type = response.getheader("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type not in {"text/html", "text/plain"}:
                raise EvidenceFetchUnavailable("Source content type is not supported")
            content_length = response.getheader("Content-Length")
            if content_length:
                try:
                    if int(content_length) > self.max_response_bytes:
                        raise EvidenceFetchUnavailable("Source response exceeds the configured size limit")
                except ValueError:
                    raise EvidenceFetchUnavailable("Source response has invalid length metadata") from None
            body = response.read(self.max_response_bytes + 1)
            if len(body) > self.max_response_bytes:
                raise EvidenceFetchUnavailable("Source response exceeds the configured size limit")
            charset = response.headers.get_content_charset() or "utf-8"
            try:
                text = body.decode(charset, errors="replace")
            except LookupError:
                text = body.decode("utf-8", errors="replace")
            if content_type == "text/html":
                parser = _VisibleTextParser()
                parser.feed(text)
                text = " ".join(parser.parts)
            text = " ".join(text.split())[: self.max_text_chars]
            if not text:
                raise EvidenceFetchUnavailable("Source contains no readable text")
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            evidence_id = "ev_" + hashlib.sha256(
                (canonical_url + "\0" + digest).encode("utf-8")
            ).hexdigest()[:24]
            return FetchedEvidence(
                evidence_id=evidence_id,
                source_name=host,
                url=canonical_url,
                retrieved_at=datetime.now(UTC).isoformat(),
                content_type=content_type,
                content_sha256=digest,
                content=text,
            )
        except (OSError, ssl.SSLError, http.client.HTTPException):
            raise EvidenceFetchUnavailable("Source fetch failed") from None
        finally:
            if response is not None:
                response.close()
            if sock is not None:
                sock.close()
