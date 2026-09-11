from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Self

Notice = Callable[[str, str], None]
CHALLENGE_MARKERS = (
    "access to this page has been denied",
    "press & hold",
    "verify you are a human",
)


class BrowserTransportError(RuntimeError):
    pass


def _desktop_notice(title: str, message: str) -> None:
    """Best-effort local notification; failures never break the request."""
    if sys.platform != "win32":
        print(f"\a{title}: {message}", flush=True)
        return
    safe_title = title.replace("'", "''")
    safe_message = message.replace("'", "''")
    script = rf"""
try {{
  [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] > $null
  [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType=WindowsRuntime] > $null
  [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime] > $null
  $t=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
  $x=$t.GetElementsByTagName('text')
  $x.Item(0).AppendChild($t.CreateTextNode('{safe_title}')) > $null
  $x.Item(1).AppendChild($t.CreateTextNode('{safe_message}')) > $null
  $toast=[Windows.UI.Notifications.ToastNotification]::new($t)
  [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('streeteasy-unofficial').Show($toast)
}} catch {{}}
[console]::beep(880,180)
"""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            timeout=15,
            capture_output=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        print("\a", end="", flush=True)


class HeadfulBrowserTransport:
    """Visible-Chrome transport with human verification notifications.

    The class never solves or clicks a challenge. It brings Chrome forward,
    notifies the user, waits for the user to finish, and continues afterward.
    """

    def __init__(
        self,
        *,
        start_url: str,
        profile_dir: str | Path = ".streeteasy-browser",
        verification_timeout: float = 600,
        notify: Notice | None = None,
    ) -> None:
        self.start_url = start_url
        self.profile_dir = Path(profile_dir)
        self.verification_timeout = verification_timeout
        self.notify = notify or _desktop_notice
        self._playwright = None
        self._context = None
        self._page = None

    async def __aenter__(self) -> Self:
        try:
            from patchright.async_api import async_playwright
        except ImportError as exc:
            raise BrowserTransportError(
                'Install browser support with: pip install "streeteasy-unofficial[browser]"'
            ) from exc
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self._playwright = await async_playwright().start()
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.profile_dir),
            channel="chrome",
            headless=False,
            viewport={"width": 1440, "height": 900},
        )
        self._page = (
            self._context.pages[0]
            if self._context.pages
            else await self._context.new_page()
        )
        await self._page.goto(
            self.start_url, wait_until="domcontentloaded", timeout=60_000
        )
        await self._wait_for_human_if_needed()
        return self

    async def __aexit__(self, *_: object) -> None:
        try:
            if self._context:
                await self._context.close()
        finally:
            if self._playwright:
                await self._playwright.stop()

    async def _is_challenged(self) -> bool:
        if not self._page:
            return False
        try:
            if await self._page.locator("#px-captcha").count():
                return True
            body = (await self._page.locator("body").inner_text()).lower()
        except (AttributeError, RuntimeError, TypeError):
            return False
        return any(marker in body for marker in CHALLENGE_MARKERS)

    async def _wait_for_human_if_needed(self) -> None:
        if not await self._is_challenged():
            return
        assert self._page is not None
        await self._page.bring_to_front()
        await asyncio.to_thread(
            self.notify,
            "StreetEasy needs your attention",
            "Complete verification in the open Chrome window. The request will continue automatically.",
        )
        deadline = time.monotonic() + self.verification_timeout
        while time.monotonic() < deadline:
            await asyncio.sleep(1)
            if not await self._is_challenged():
                await asyncio.to_thread(
                    self.notify,
                    "StreetEasy verification complete",
                    "Continuing the request.",
                )
                return
        raise BrowserTransportError("Human verification timed out")

    async def __call__(self, endpoint: str, body: dict[str, Any]) -> dict[str, Any]:
        if not self._page:
            raise BrowserTransportError("Use the transport as an async context manager")

        async def send() -> dict[str, Any]:
            result = await self._page.evaluate(
                """async ({endpoint, body}) => {
                  const response = await fetch(endpoint, {
                    method: 'POST', credentials: 'include',
                    headers: {'content-type': 'application/json'},
                    body: JSON.stringify(body)
                  });
                  return {status: response.status, text: await response.text()};
                }""",
                {"endpoint": endpoint, "body": body},
            )
            if result["status"] != 200:
                raise BrowserTransportError(
                    f"StreetEasy returned HTTP {result['status']}"
                )
            try:
                return json.loads(result["text"])
            except json.JSONDecodeError as exc:
                raise BrowserTransportError(
                    "StreetEasy returned non-JSON data"
                ) from exc

        try:
            return await send()
        except BrowserTransportError:
            await self._page.goto(
                self.start_url, wait_until="domcontentloaded", timeout=60_000
            )
            if not await self._is_challenged():
                raise
            await self._wait_for_human_if_needed()
            return await send()
