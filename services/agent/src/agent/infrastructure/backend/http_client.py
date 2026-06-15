from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx


class BackendApiError(RuntimeError):
    def __init__(
        self,
        *,
        method: str,
        url: str,
        status_code: int | None,
        detail: str,
    ) -> None:
        super().__init__(f"Backend API error {method} {url}: {status_code} {detail}")
        self.method = method
        self.url = url
        self.status_code = status_code
        self.detail = detail


class BackendHttpClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float = 10.0,
        access_token: str | None = None,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        self._base_url = base_url
        self._access_token = access_token
        self._timeout = httpx.Timeout(timeout_seconds)
        self._default_headers = dict(default_headers or {})
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_json(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self._request_json("GET", path, params=params, headers=headers)

    async def post_json(
        self,
        path: str,
        *,
        json: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self._request_json(
            "POST",
            path,
            json=json,
            params=params,
            headers=headers,
        )

    async def patch_json(
        self,
        path: str,
        *,
        json: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self._request_json(
            "PATCH",
            path,
            json=json,
            params=params,
            headers=headers,
        )

    # Short aliases used by newer adapters. Keep get_json/post_json/patch_json
    # for compatibility with older code.
    async def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self.get_json(path, params=params, headers=headers)

    async def post(
        self,
        path: str,
        *,
        json: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self.post_json(path, json=json, params=params, headers=headers)

    async def patch(
        self,
        path: str,
        *,
        json: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self.patch_json(path, json=json, params=params, headers=headers)

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        json: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        clean_params = _drop_none(params)
        clean_json = _drop_none(json)
        request_headers = self._headers(headers)

        try:
            response = await self._client.request(
                method,
                path,
                json=clean_json if json is not None else None,
                params=clean_params,
                headers=request_headers,
            )
        except httpx.HTTPError as exc:
            raise BackendApiError(
                method=method,
                url=f"{self._base_url}{path}",
                status_code=None,
                detail=str(exc),
            ) from exc

        if response.status_code >= 400:
            detail = _response_detail(response)
            raise BackendApiError(
                method=method,
                url=str(response.request.url),
                status_code=response.status_code,
                detail=detail,
            )

        if response.status_code == 204 or not response.content:
            return None

        return response.json()

    def _headers(self, extra: Mapping[str, str] | None) -> dict[str, str]:
        headers = dict(self._default_headers)

        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        if extra:
            headers.update(extra)

        return headers


def _drop_none(mapping: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if mapping is None:
        return None

    return {key: value for key, value in mapping.items() if value is not None}


def _response_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text

    if isinstance(payload, dict):
        detail = payload.get("detail") or payload.get("message") or payload.get("error")
        if detail is not None:
            return str(detail)

    return str(payload)