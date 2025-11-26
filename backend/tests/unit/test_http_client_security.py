"""Tests for HTTP client SSRF protection and DNS rebinding prevention."""

import ipaddress
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from app.services.http_client import (
    BlockedIPError,
    HttpClient,
    SafeTCPConnector,
    is_blocked_ip,
    is_safe_url,
)


class TestBlockedIPDetection:
    """Tests for is_blocked_ip function."""

    def test_blocks_localhost_ipv4(self):
        """Verify 127.0.0.1 is blocked."""
        ip = ipaddress.ip_address("127.0.0.1")
        assert is_blocked_ip(ip) is True

    def test_blocks_localhost_ipv6(self):
        """Verify ::1 is blocked."""
        ip = ipaddress.ip_address("::1")
        assert is_blocked_ip(ip) is True

    def test_blocks_private_10_network(self):
        """Verify 10.0.0.0/8 network is blocked."""
        ip = ipaddress.ip_address("10.0.0.1")
        assert is_blocked_ip(ip) is True
        ip = ipaddress.ip_address("10.255.255.255")
        assert is_blocked_ip(ip) is True

    def test_blocks_private_172_network(self):
        """Verify 172.16.0.0/12 network is blocked."""
        ip = ipaddress.ip_address("172.16.0.1")
        assert is_blocked_ip(ip) is True
        ip = ipaddress.ip_address("172.31.255.255")
        assert is_blocked_ip(ip) is True

    def test_blocks_private_192_network(self):
        """Verify 192.168.0.0/16 network is blocked."""
        ip = ipaddress.ip_address("192.168.0.1")
        assert is_blocked_ip(ip) is True
        ip = ipaddress.ip_address("192.168.255.255")
        assert is_blocked_ip(ip) is True

    def test_blocks_link_local(self):
        """Verify 169.254.0.0/16 (link-local) is blocked."""
        ip = ipaddress.ip_address("169.254.0.1")
        assert is_blocked_ip(ip) is True
        ip = ipaddress.ip_address("169.254.169.254")  # AWS metadata
        assert is_blocked_ip(ip) is True

    def test_blocks_ipv6_link_local(self):
        """Verify fe80::/10 (IPv6 link-local) is blocked."""
        ip = ipaddress.ip_address("fe80::1")
        assert is_blocked_ip(ip) is True

    def test_blocks_ipv6_private(self):
        """Verify fc00::/7 (IPv6 private) is blocked."""
        ip = ipaddress.ip_address("fc00::1")
        assert is_blocked_ip(ip) is True

    def test_allows_public_ipv4(self):
        """Verify public IPv4 addresses are allowed."""
        ip = ipaddress.ip_address("8.8.8.8")
        assert is_blocked_ip(ip) is False
        ip = ipaddress.ip_address("1.1.1.1")
        assert is_blocked_ip(ip) is False

    def test_allows_public_ipv6(self):
        """Verify public IPv6 addresses are allowed."""
        ip = ipaddress.ip_address("2001:4860:4860::8888")
        assert is_blocked_ip(ip) is False


class TestSafeURLValidation:
    """Tests for is_safe_url function."""

    def test_blocks_localhost_hostname(self):
        """Verify localhost hostname is blocked."""
        assert is_safe_url("http://localhost/test") is False
        assert is_safe_url("https://localhost/test") is False

    def test_blocks_0_0_0_0(self):
        """Verify 0.0.0.0 is blocked."""
        assert is_safe_url("http://0.0.0.0/test") is False

    def test_blocks_non_http_schemes(self):
        """Verify non-HTTP(S) schemes are blocked."""
        assert is_safe_url("file:///etc/passwd") is False
        assert is_safe_url("ftp://example.com/file") is False
        assert is_safe_url("javascript:alert(1)") is False

    @patch("app.services.http_client.socket.getaddrinfo")
    def test_blocks_urls_resolving_to_private_ips(self, mock_getaddrinfo):
        """Verify URLs that resolve to private IPs are blocked."""
        # Mock DNS resolution to return a private IP
        mock_getaddrinfo.return_value = [(None, None, None, None, ("192.168.1.1", 80))]
        assert is_safe_url("http://malicious.example.com") is False

    @patch("app.services.http_client.socket.getaddrinfo")
    def test_allows_urls_resolving_to_public_ips(self, mock_getaddrinfo):
        """Verify URLs that resolve to public IPs are allowed."""
        # Mock DNS resolution to return a public IP
        mock_getaddrinfo.return_value = [(None, None, None, None, ("8.8.8.8", 80))]
        assert is_safe_url("http://google.com") is True


class TestSafeTCPConnector:
    """Tests for SafeTCPConnector DNS rebinding protection."""

    @pytest.mark.asyncio
    async def test_blocks_connection_to_private_ip(self):
        """Verify SafeTCPConnector blocks connections to private IPs at connection time."""
        connector = SafeTCPConnector()

        # Mock the parent class _resolve_host to return a private IP
        with patch.object(
            aiohttp.TCPConnector, "_resolve_host", new_callable=AsyncMock
        ) as mock_resolve:
            mock_resolve.return_value = [
                {"host": "192.168.1.1", "port": 80, "family": 2, "proto": 6, "flags": 0}
            ]

            # Should raise BlockedIPError
            with pytest.raises(BlockedIPError) as exc_info:
                await connector._resolve_host("evil.example.com", 80)

            assert "private/internal IP blocked" in str(exc_info.value)

        await connector.close()

    @pytest.mark.asyncio
    async def test_blocks_connection_to_localhost(self):
        """Verify SafeTCPConnector blocks connections to localhost IPs."""
        connector = SafeTCPConnector()

        with patch.object(
            aiohttp.TCPConnector, "_resolve_host", new_callable=AsyncMock
        ) as mock_resolve:
            mock_resolve.return_value = [
                {"host": "127.0.0.1", "port": 80, "family": 2, "proto": 6, "flags": 0}
            ]

            with pytest.raises(BlockedIPError):
                await connector._resolve_host("localhost", 80)

        await connector.close()

    @pytest.mark.asyncio
    async def test_allows_connection_to_public_ip(self):
        """Verify SafeTCPConnector allows connections to public IPs."""
        connector = SafeTCPConnector()

        with patch.object(
            aiohttp.TCPConnector, "_resolve_host", new_callable=AsyncMock
        ) as mock_resolve:
            # Mock resolution to a public IP
            expected_result = [{"host": "8.8.8.8", "port": 80, "family": 2, "proto": 6, "flags": 0}]
            mock_resolve.return_value = expected_result

            # Should not raise an exception
            result = await connector._resolve_host("google.com", 80)
            assert result == expected_result

        await connector.close()

    @pytest.mark.asyncio
    async def test_blocks_invalid_ip_address(self):
        """Verify SafeTCPConnector blocks invalid IP addresses."""
        connector = SafeTCPConnector()

        with patch.object(
            aiohttp.TCPConnector, "_resolve_host", new_callable=AsyncMock
        ) as mock_resolve:
            mock_resolve.return_value = [
                {"host": "invalid-ip", "port": 80, "family": 2, "proto": 6, "flags": 0}
            ]

            with pytest.raises(BlockedIPError) as exc_info:
                await connector._resolve_host("evil.example.com", 80)

            assert "Invalid IP address" in str(exc_info.value)

        await connector.close()


class TestHttpClientSSRFProtection:
    """Tests for HttpClient SSRF protection."""

    @pytest.mark.asyncio
    async def test_get_json_blocks_unsafe_url(self):
        """Verify get_json blocks unsafe URLs."""
        client = HttpClient()

        with pytest.raises(ValueError) as exc_info:
            await client.get_json("http://localhost/admin")

        assert "Unsafe URL blocked" in str(exc_info.value)

        await client.close()

    @pytest.mark.asyncio
    async def test_get_text_blocks_unsafe_url(self):
        """Verify get_text blocks unsafe URLs."""
        client = HttpClient()

        with pytest.raises(ValueError) as exc_info:
            await client.get_text("http://127.0.0.1/secret")

        assert "Unsafe URL blocked" in str(exc_info.value)

        await client.close()

    @pytest.mark.asyncio
    async def test_get_blocks_unsafe_url(self):
        """Verify get blocks unsafe URLs."""
        client = HttpClient()

        with pytest.raises(ValueError) as exc_info:
            await client.get("http://0.0.0.0/test")

        assert "Unsafe URL blocked" in str(exc_info.value)

        await client.close()

    @pytest.mark.asyncio
    async def test_head_blocks_unsafe_url(self):
        """Verify head blocks unsafe URLs."""
        client = HttpClient()

        with pytest.raises(ValueError) as exc_info:
            await client.head("http://localhost/")

        assert "Unsafe URL blocked" in str(exc_info.value)

        await client.close()

    @pytest.mark.asyncio
    async def test_can_bypass_validation_when_needed(self):
        """Verify SSRF validation can be bypassed with validate_url=False."""
        client = HttpClient()

        # This should not raise an error even though localhost is blocked
        # We're not actually making the request, just checking the validation is bypassed
        with patch.object(aiohttp.ClientSession, "get", new_callable=AsyncMock) as mock_get:
            mock_response = AsyncMock()
            mock_response.raise_for_status = Mock()
            mock_response.json = AsyncMock(return_value={"test": "data"})
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await client.get_json("http://localhost/api", validate_url=False)
            assert result == {"test": "data"}

        await client.close()

    @pytest.mark.asyncio
    async def test_reuses_connector_across_requests(self):
        """Verify HttpClient reuses the same connector for multiple requests."""
        client = HttpClient()

        # Store reference to the connector
        connector = client.connector

        # Mock the session to avoid actual network requests
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.raise_for_status = Mock()
            mock_response.json = AsyncMock(return_value={})
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Make multiple requests
            with patch("app.services.http_client.is_safe_url", return_value=True):
                await client.get_json("http://example.com/1")
                await client.get_json("http://example.com/2")

            # Verify the same connector is used
            assert client.connector is connector

            # Verify session was created with the connector
            calls = mock_session_class.call_args_list
            for call in calls:
                assert call[1]["connector"] is connector

        await client.close()
