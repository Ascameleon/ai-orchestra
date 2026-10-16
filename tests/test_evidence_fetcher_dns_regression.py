"""Regression tests for fail-closed DNS validation in evidence fetching."""
import socket

import pytest

from orchestra.evidence_fetcher import (
    EvidenceFetcher,
    EvidenceFetchRequestError,
    EvidenceFetchUnavailable,
)


def test_mixed_public_and_private_dns_answers_fail_closed_before_connect():
    """A private answer invalidates the hostname even when a public IP is also returned."""
    connected = []

    def mixed_resolver(host, port, type):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", port)),
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("10.0.0.7", port)),
        ]

    fetcher = EvidenceFetcher(
        ["example.com"],
        resolver=mixed_resolver,
        connector=lambda *args, **kwargs: connected.append((args, kwargs)),
    )

    with pytest.raises(EvidenceFetchRequestError, match="non-public"):
        fetcher.fetch_many(["http://example.com/article"])

    assert connected == []


def test_ipv4_mapped_private_ipv6_dns_answer_fails_closed():
    """IPv4-mapped private addresses must not bypass the public-address check."""
    connected = []

    def mapped_resolver(host, port, type):
        return [
            (
                socket.AF_INET6,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("::ffff:10.0.0.7", port, 0, 0),
            )
        ]

    fetcher = EvidenceFetcher(
        ["example.com"],
        resolver=mapped_resolver,
        connector=lambda *args, **kwargs: connected.append((args, kwargs)),
    )

    with pytest.raises(EvidenceFetchRequestError, match="non-public"):
        fetcher.fetch_many(["http://example.com/article"])

    assert connected == []


def test_dns_answers_without_parseable_ips_fail_closed_without_connecting():
    """A resolver response with no usable IP must never reach the connector."""
    connected = []

    def unusable_resolver(host, port, type):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("not-an-ip", port))
        ]

    fetcher = EvidenceFetcher(
        ["example.com"],
        resolver=unusable_resolver,
        connector=lambda *args, **kwargs: connected.append((args, kwargs)),
    )

    with pytest.raises(EvidenceFetchUnavailable, match="no usable public address"):
        fetcher.fetch_many(["http://example.com/article"])

    assert connected == []



def test_malformed_bracketed_host_is_rejected_as_invalid_url():
    """Malformed URL authority must produce a request error, not leak ValueError."""
    connected = []
    fetcher = EvidenceFetcher(
        ["example.com"],
        resolver=lambda *args, **kwargs: [],
        connector=lambda *args, **kwargs: connected.append((args, kwargs)),
    )

    with pytest.raises(EvidenceFetchRequestError, match="URL is invalid"):
        fetcher.fetch_many(["http://[broken/"])

    assert connected == []


def test_dns_resolution_failure_is_normalized_and_never_connects():
    """DNS infrastructure errors are surfaced safely without attempting a connection."""
    connected = []

    def failing_resolver(host, port, type):
        raise socket.gaierror("private resolver details should not leak")

    fetcher = EvidenceFetcher(
        ["example.com"],
        resolver=failing_resolver,
        connector=lambda *args, **kwargs: connected.append((args, kwargs)),
    )

    with pytest.raises(EvidenceFetchUnavailable, match="could not be resolved") as error:
        fetcher.fetch_many(["http://example.com/article"])

    assert "private resolver details" not in str(error.value)
    assert connected == []



@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.20.30.40",
        "169.254.10.20",
        "192.0.2.10",
        "224.0.0.1",
        "::1",
        "fc00::1",
        "fe80::1",
        "2001:db8::1",
        "ff02::1",
        "0.0.0.0",
        "::",
    ],
)
def test_loopback_private_link_local_documentation_and_reserved_ips_are_blocked(address):
    """Every non-global DNS answer is rejected before the network connector is called."""
    connected = []

    def reserved_resolver(host, port, type):
        family = socket.AF_INET6 if ":" in address else socket.AF_INET
        sockaddr = (address, port, 0, 0) if family == socket.AF_INET6 else (address, port)
        return [(family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr)]

    fetcher = EvidenceFetcher(
        ["example.com"],
        resolver=reserved_resolver,
        connector=lambda *args, **kwargs: connected.append((args, kwargs)),
    )

    with pytest.raises(EvidenceFetchRequestError, match="non-public"):
        fetcher.fetch_many(["http://example.com/article"])

    assert connected == []
