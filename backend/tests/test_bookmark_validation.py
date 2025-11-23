"""Tests for bookmark model validation."""
import pytest
from pydantic import ValidationError

from app.models.bookmark import BookmarkCreate, BookmarkUpdate


class TestBookmarkCreateValidation:
    """Test validation for BookmarkCreate schema."""

    def test_valid_bookmark_creation(self):
        """Test creating a valid bookmark."""
        bookmark = BookmarkCreate(
            title="Test Bookmark",
            url="https://example.com",
            description="A test bookmark",
            category="Test",
            tags=["tag1", "tag2"],
            favicon="https://example.com/favicon.ico"
        )
        assert bookmark.title == "Test Bookmark"
        assert bookmark.url == "https://example.com"
        assert bookmark.tags == ["tag1", "tag2"]

    def test_minimal_valid_bookmark(self):
        """Test creating bookmark with only required fields."""
        bookmark = BookmarkCreate(
            title="Test",
            url="https://example.com"
        )
        assert bookmark.title == "Test"
        assert bookmark.url == "https://example.com"
        assert bookmark.favicon is None
        assert bookmark.tags is None

    def test_reject_javascript_scheme(self):
        """Test that javascript: URLs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BookmarkCreate(
                title="Malicious",
                url="javascript:alert('xss')"
            )

        errors = exc_info.value.errors()
        assert any("not allowed" in str(error['msg']).lower() for error in errors)

    def test_reject_data_scheme(self):
        """Test that data: URLs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BookmarkCreate(
                title="Malicious",
                url="data:text/html,<script>alert('xss')</script>"
            )

        errors = exc_info.value.errors()
        assert any("not allowed" in str(error['msg']).lower() for error in errors)

    def test_reject_vbscript_scheme(self):
        """Test that vbscript: URLs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BookmarkCreate(
                title="Malicious",
                url="vbscript:msgbox('xss')"
            )

        errors = exc_info.value.errors()
        assert any("not allowed" in str(error['msg']).lower() for error in errors)

    def test_reject_file_scheme(self):
        """Test that file: URLs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BookmarkCreate(
                title="Local File",
                url="file:///etc/passwd"
            )

        errors = exc_info.value.errors()
        assert any("not allowed" in str(error['msg']).lower() for error in errors)

    def test_require_valid_scheme(self):
        """Test that URLs must have http or https scheme."""
        with pytest.raises(ValidationError) as exc_info:
            BookmarkCreate(
                title="FTP Link",
                url="ftp://example.com"
            )

        errors = exc_info.value.errors()
        assert any("http or https" in str(error['msg']).lower() for error in errors)

    def test_require_domain(self):
        """Test that URLs must have a valid domain."""
        with pytest.raises(ValidationError) as exc_info:
            BookmarkCreate(
                title="Invalid",
                url="https://"
            )

        errors = exc_info.value.errors()
        assert any("domain" in str(error['msg']).lower() for error in errors)

    def test_reject_malicious_favicon_javascript(self):
        """Test that javascript: favicon URLs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BookmarkCreate(
                title="Test",
                url="https://example.com",
                favicon="javascript:void(0)"
            )

        errors = exc_info.value.errors()
        assert any("favicon" in str(error['ctx']).lower() or
                   "favicon" in str(error['loc']).lower()
                   for error in errors)

    def test_reject_malicious_favicon_data(self):
        """Test that data: favicon URLs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BookmarkCreate(
                title="Test",
                url="https://example.com",
                favicon="data:image/png;base64,malicious"
            )

        errors = exc_info.value.errors()
        assert any("favicon" in str(error['ctx']).lower() or
                   "favicon" in str(error['loc']).lower()
                   for error in errors)

    def test_accept_valid_favicon(self):
        """Test that valid favicon URLs are accepted."""
        bookmark = BookmarkCreate(
            title="Test",
            url="https://example.com",
            favicon="https://example.com/favicon.ico"
        )
        assert bookmark.favicon == "https://example.com/favicon.ico"

    def test_accept_null_favicon(self):
        """Test that null favicon is accepted."""
        bookmark = BookmarkCreate(
            title="Test",
            url="https://example.com",
            favicon=None
        )
        assert bookmark.favicon is None

    def test_tags_as_list(self):
        """Test that tags are properly stored as a list."""
        bookmark = BookmarkCreate(
            title="Test",
            url="https://example.com",
            tags=["tag1", "tag2", "tag3"]
        )
        assert bookmark.tags == ["tag1", "tag2", "tag3"]


class TestBookmarkUpdateValidation:
    """Test validation for BookmarkUpdate schema."""

    def test_partial_update_url_only(self):
        """Test updating only the URL."""
        update = BookmarkUpdate(url="https://updated.com")
        assert update.url == "https://updated.com"
        assert update.title is None

    def test_reject_malicious_url_in_update(self):
        """Test that malicious URLs are rejected in updates."""
        with pytest.raises(ValidationError) as exc_info:
            BookmarkUpdate(url="javascript:alert('xss')")

        errors = exc_info.value.errors()
        assert any("not allowed" in str(error['msg']).lower() for error in errors)

    def test_reject_malicious_favicon_in_update(self):
        """Test that malicious favicon URLs are rejected in updates."""
        with pytest.raises(ValidationError) as exc_info:
            BookmarkUpdate(favicon="javascript:void(0)")

        errors = exc_info.value.errors()
        assert any("favicon" in str(error['ctx']).lower() or
                   "favicon" in str(error['loc']).lower()
                   for error in errors)

    def test_accept_valid_update(self):
        """Test that valid updates are accepted."""
        update = BookmarkUpdate(
            title="Updated Title",
            url="https://updated.com",
            tags=["new", "tags"]
        )
        assert update.title == "Updated Title"
        assert update.url == "https://updated.com"
        assert update.tags == ["new", "tags"]

    def test_null_values_allowed(self):
        """Test that None values are allowed for optional fields."""
        update = BookmarkUpdate(
            title="Updated",
            url=None,
            favicon=None,
            tags=None
        )
        assert update.title == "Updated"
        assert update.url is None
        assert update.favicon is None
        assert update.tags is None


class TestURLValidationEdgeCases:
    """Test edge cases for URL validation."""

    def test_case_insensitive_scheme_detection(self):
        """Test that scheme detection is case-insensitive."""
        with pytest.raises(ValidationError):
            BookmarkCreate(title="Test", url="JavaScript:alert('xss')")

        with pytest.raises(ValidationError):
            BookmarkCreate(title="Test", url="JAVASCRIPT:alert('xss')")

        with pytest.raises(ValidationError):
            BookmarkCreate(title="Test", url="JaVaScRiPt:alert('xss')")

    def test_accept_http(self):
        """Test that HTTP URLs are accepted."""
        bookmark = BookmarkCreate(
            title="HTTP Site",
            url="http://example.com"
        )
        assert bookmark.url == "http://example.com"

    def test_accept_https(self):
        """Test that HTTPS URLs are accepted."""
        bookmark = BookmarkCreate(
            title="HTTPS Site",
            url="https://example.com"
        )
        assert bookmark.url == "https://example.com"

    def test_url_with_path(self):
        """Test URLs with paths are accepted."""
        bookmark = BookmarkCreate(
            title="Page",
            url="https://example.com/path/to/page"
        )
        assert bookmark.url == "https://example.com/path/to/page"

    def test_url_with_query_params(self):
        """Test URLs with query parameters are accepted."""
        bookmark = BookmarkCreate(
            title="Search",
            url="https://example.com/search?q=test&lang=en"
        )
        assert bookmark.url == "https://example.com/search?q=test&lang=en"

    def test_url_with_fragment(self):
        """Test URLs with fragments are accepted."""
        bookmark = BookmarkCreate(
            title="Section",
            url="https://example.com/page#section"
        )
        assert bookmark.url == "https://example.com/page#section"

    def test_url_with_port(self):
        """Test URLs with ports are accepted."""
        bookmark = BookmarkCreate(
            title="Custom Port",
            url="https://example.com:8443/path"
        )
        assert bookmark.url == "https://example.com:8443/path"

    def test_url_with_auth(self):
        """Test URLs with authentication are accepted."""
        bookmark = BookmarkCreate(
            title="Auth",
            url="https://user:pass@example.com"
        )
        assert bookmark.url == "https://user:pass@example.com"
