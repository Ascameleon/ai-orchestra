"""Regression tests for fail-closed DNS validation in evidence fetching."""
import socket

import pytest

from orchestra.evidence_fetcher import EvidenceFetcher, EvidenceFetchRequestError


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
