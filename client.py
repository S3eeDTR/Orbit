from __future__ import annotations

import time
from typing import Any

import requests

from .constants import CHAT_ENDPOINT, MODELS_ENDPOINT, USER_AGENT
from .ui import console


class OpenRouterError(RuntimeError):
    """User-friendly OpenRouter API error."""


class OpenRouterClient:
    def __init__(self, api_key: str, timeout: int = 120) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/S3eeDTR/Orbit",
                "X-Title": "ORBIT",
                "User-Agent": USER_AGENT,
            }
        )

    def fetch_models(self) -> list[dict[str, Any]]:
        response = self.session.get(MODELS_ENDPOINT, timeout=30)
        self._raise_for_status(response, "Failed to fetch models")
        return response.json().get("data", [])

    def verify_key(self) -> bool:
        try:
            response = self.session.get(MODELS_ENDPOINT, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def chat(self, model: str, messages: list[dict[str, str]]) -> dict[str, Any]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }

        response = self.session.post(
            CHAT_ENDPOINT,
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code == 429:
            retry_after, provider = self._rate_limit_details(response)
            console.print(
                f"[yellow]Rate limited by {provider}. "
                f"Retrying in {retry_after:.0f} seconds...[/yellow]"
            )

            time.sleep(max(1, retry_after))

            response = self.session.post(
                CHAT_ENDPOINT,
                json=payload,
                timeout=self.timeout,
            )

            if response.status_code == 429:
                retry_after, provider = self._rate_limit_details(response)
                raise OpenRouterError(
                    f"Rate limited by {provider}. Try again in about "
                    f"{retry_after:.0f} seconds, or switch models with /model. "
                    "Free models are often busy."
                )

        self._raise_for_status(response, "OpenRouter chat request failed")
        return response.json()

    @staticmethod
    def _rate_limit_details(response: requests.Response) -> tuple[float, str]:
        retry_after = 10.0
        provider = "the provider"

        try:
            error = response.json().get("error", {})
            metadata = error.get("metadata", {}) or {}

            retry_after = float(
                metadata.get("retry_after_seconds")
                or metadata.get("retry_after_seconds_raw")
                or response.headers.get("Retry-After")
                or 10
            )

            provider = str(metadata.get("provider_name") or provider)

        except Exception:
            pass

        return retry_after, provider

    @staticmethod
    def _raise_for_status(response: requests.Response, prefix: str) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            try:
                error = response.json().get("error", {})
                message = error.get("message") or response.text[:500]
            except Exception:
                message = response.text[:500]

            raise OpenRouterError(f"{prefix}: {message}") from exc
