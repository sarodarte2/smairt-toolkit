"""Bounded, injectable, read-only Zotero local and Web provider."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from smairt.credentials import resolve_credential
from smairt.local_setup import ConnectionProfile, resolve_profile
from smairt.models import SmairtConfig, ZoteroMode
from smairt.utils import validate_identifier

ZOTERO_API_VERSION = 3
MAX_QUERY_RESULTS = 50
MAX_COLLECTION_IMPORT = 1000
MAX_ATTACHMENT_BYTES = 100 * 1024 * 1024


class ZoteroProviderError(RuntimeError):
    """Represent a normalized, secret-free Zotero provider failure."""


class ZoteroAuthenticationError(ZoteroProviderError):
    """Indicate invalid or insufficient Zotero Web credentials."""


class ZoteroRateLimitError(ZoteroProviderError):
    """Indicate that Zotero asked the caller to back off."""


class ZoteroProvider:
    """Expose only bounded read operations from a configured Zotero library."""

    def __init__(
        self,
        root: Path,
        *,
        client_factory: Callable[[Any, float], Any] | None = None,
        timeout: float = 15.0,
    ) -> None:
        project = SmairtConfig.load(root / "smairt.yaml")
        shared = project.integrations.zotero
        enabled = shared.enabled or (
            project.schema_version < 5 and shared.mode is not ZoteroMode.DISABLED
        )
        if not enabled:
            raise ValueError("Zotero integration is disabled")
        try:
            _, config = resolve_profile(root, "zotero")
        except ValueError:
            if project.schema_version >= 5:
                raise
            config = ConnectionProfile(
                provider="zotero",
                credential_profile=shared.credential.profile,
                environment_variable=shared.credential.environment_variable,
                mode=shared.mode,
                library_id=shared.library_id,
                library_type=shared.library_type if shared.mode is ZoteroMode.WEB else None,
            )
        self.config = config
        self.timeout = timeout
        self.last_library_version: str | None = None
        self.client = (
            client_factory(config, timeout)
            if client_factory is not None
            else self._default_client(config, timeout)
        )

    @staticmethod
    def _default_client(config: Any, timeout: float) -> Any:
        """Build Pyzotero with a finite HTTP timeout and header-based credentials."""
        try:
            import httpx
            from pyzotero import zotero
        except ImportError as exc:
            raise RuntimeError("Pyzotero and HTTPX are required for Zotero access") from exc
        http_client = httpx.Client(timeout=timeout, follow_redirects=True)
        if config.mode is ZoteroMode.LOCAL:
            return zotero.Zotero(config.library_id or "0", "user", local=True, client=http_client)
        profile = config.credential
        key, _ = resolve_credential(
            "zotero", profile.profile, profile.environment_variable or "ZOTERO_API_KEY"
        )
        if not key:
            raise ValueError("Zotero Web API credential is missing")
        return zotero.Zotero(
            config.library_id,
            config.library_type.value,
            key,
            local=False,
            client=http_client,
        )

    def _call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """Invoke one read method and normalize provider-specific exceptions."""
        try:
            from pyzotero import zotero_errors

            value = getattr(self.client, method)(*args, v=ZOTERO_API_VERSION, **kwargs)
        except (AttributeError, TypeError) as exc:
            raise ZoteroProviderError("Zotero client returned an incompatible response") from exc
        except zotero_errors.UserNotAuthorisedError as exc:
            raise ZoteroAuthenticationError(
                "Zotero authentication or library access failed"
            ) from exc
        except (
            zotero_errors.TooManyRequestsError,
            zotero_errors.TooManyRetriesError,
        ) as exc:
            raise ZoteroRateLimitError("Zotero rate limit or backoff is active") from exc
        except (
            zotero_errors.CouldNotReachURLError,
            zotero_errors.HTTPError,
            zotero_errors.PyZoteroError,
        ) as exc:
            raise ZoteroProviderError(
                "Zotero is unavailable or returned an invalid response"
            ) from exc
        request = getattr(self.client, "request", None)
        headers = getattr(request, "headers", {})
        if hasattr(headers, "get"):
            version = headers.get("Last-Modified-Version") or headers.get("Zotero-Library-Version")
            self.last_library_version = str(version) if version is not None else None
        return value

    @staticmethod
    def _validate_limit(limit: int, maximum: int) -> int:
        """Reject unbounded or nonsensical result requests before any network call."""
        if limit < 1 or limit > maximum:
            raise ValueError(f"limit must be between 1 and {maximum}")
        return limit

    def _page(
        self,
        method: str,
        *args: Any,
        limit: int,
        maximum: int,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Follow API pagination only until the caller's validated bound is reached."""
        requested = self._validate_limit(limit, maximum)
        first_limit = min(requested, 100)
        page = self._call(method, *args, limit=first_limit, **kwargs)
        if not isinstance(page, list):
            raise ZoteroProviderError("Zotero returned an unexpected collection response")
        items: list[dict[str, Any]] = [item for item in page if isinstance(item, dict)]
        while len(items) < requested and getattr(self.client, "links", {}).get("next"):
            next_page = self._call("follow")
            if not isinstance(next_page, list):
                raise ZoteroProviderError("Zotero returned malformed pagination data")
            items.extend(item for item in next_page if isinstance(item, dict))
        return items[:requested]

    def item(self, key: str) -> dict[str, Any]:
        """Fetch one item by validated key."""
        validate_identifier(key, label="Zotero item key")
        item = self._call("item", key)
        if not isinstance(item, dict):
            raise ZoteroProviderError("Zotero returned an unexpected item")
        return item

    def children(self, key: str, limit: int = MAX_QUERY_RESULTS) -> list[dict[str, Any]]:
        """Fetch bounded child metadata for an item."""
        validate_identifier(key, label="Zotero item key")
        return self._page("children", key, limit=limit, maximum=MAX_QUERY_RESULTS)

    def collection_items(self, key: str, limit: int = 500) -> list[dict[str, Any]]:
        """Fetch paginated collection metadata within the import hard limit."""
        validate_identifier(key, label="Zotero collection key")
        return self._page("collection_items", key, limit=limit, maximum=MAX_COLLECTION_IMPORT)

    def collections(self, limit: int = MAX_QUERY_RESULTS) -> list[dict[str, Any]]:
        """List bounded collection metadata."""
        return self._page("collections", limit=limit, maximum=MAX_QUERY_RESULTS)

    def tags(self, limit: int = MAX_QUERY_RESULTS) -> list[dict[str, Any]]:
        """List bounded tag metadata."""
        return self._page("tags", limit=limit, maximum=MAX_QUERY_RESULTS)

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search bounded item metadata."""
        if not query.strip() or len(query) > 500:
            raise ValueError("Zotero search query must contain 1 to 500 characters")
        return self._page("items", q=query, limit=limit, maximum=MAX_QUERY_RESULTS)

    def recent(self, limit: int = 25) -> list[dict[str, Any]]:
        """Return recently modified top-level library items within the UI bound."""
        return self._page(
            "top", limit=limit, maximum=MAX_QUERY_RESULTS, sort="dateModified", direction="desc"
        )

    def local_attachment(self, key: str) -> tuple[dict[str, Any], bytes]:
        """Retrieve one explicit local PDF attachment through Zotero's loopback API."""
        if self.config.mode is not ZoteroMode.LOCAL:
            raise ValueError("Web attachment downloads are out of scope")
        item = self.item(key)
        data_value = item.get("data")
        data: dict[str, Any] = data_value if isinstance(data_value, dict) else {}
        filename = str(data.get("filename") or "")
        content_type = str(data.get("contentType") or "").lower()
        if data.get("itemType") != "attachment" or data.get("linkMode") == "linked_url":
            raise ValueError("selected Zotero child is not a local file attachment")
        if content_type != "application/pdf" and not filename.lower().endswith(".pdf"):
            raise ValueError("selected Zotero attachment is not a PDF")
        content = self._call("file", key)
        if not isinstance(content, bytes):
            raise ZoteroProviderError("Zotero returned invalid attachment content")
        if not content or len(content) > MAX_ATTACHMENT_BYTES:
            raise ValueError("Zotero attachment is empty or exceeds 100 MiB")
        if not content.startswith(b"%PDF-"):
            raise ValueError("Zotero attachment does not contain a PDF signature")
        return item, content


def public_item(item: dict[str, Any]) -> dict[str, Any]:
    """Remove paths, full text, notes, and attachment content from a Zotero response."""
    data_value = item.get("data")
    data: dict[str, Any] = data_value if isinstance(data_value, dict) else {}
    creators_value = data.get("creators")
    creators: list[Any] = creators_value if isinstance(creators_value, list) else []
    tags_value = data.get("tags")
    tags: list[Any] = tags_value if isinstance(tags_value, list) else []
    return {
        "key": item.get("key") or data.get("key"),
        "version": item.get("version") or data.get("version"),
        "itemType": data.get("itemType"),
        "title": data.get("title"),
        "creators": [
            {
                key: creator.get(key)
                for key in ("creatorType", "firstName", "lastName", "name")
                if creator.get(key)
            }
            for creator in creators
            if isinstance(creator, dict)
        ],
        "date": data.get("date"),
        "DOI": data.get("DOI"),
        "url": data.get("url"),
        "publicationTitle": data.get("publicationTitle"),
        "filename": data.get("filename"),
        "contentType": data.get("contentType"),
        "linkMode": data.get("linkMode"),
        "parentItem": data.get("parentItem"),
        "tags": [tag.get("tag") for tag in tags if isinstance(tag, dict)],
    }
