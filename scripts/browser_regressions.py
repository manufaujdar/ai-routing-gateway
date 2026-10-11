"""Synthetic Chromium regressions; all API traffic is intercepted and local."""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def fixture(browser, assets, blocked_storage=False):
    page = browser.new_page(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    if blocked_storage:
        page.add_init_script(
            "Object.defineProperty(window, 'localStorage', {get(){throw new DOMException('Synthetic denied storage', 'SecurityError')}})"
        )

    def route(request):
        from urllib.parse import urlparse

        url = urlparse(request.request.url)
        if url.hostname != "synthetic.test":
            request.abort()
        elif url.path in assets:
            kind = (
                "text/css"
                if url.path.endswith(".css")
                else "text/javascript"
                if url.path.endswith(".js")
                else "text/html"
            )
            body = assets[url.path] + (
                ";window.__syntheticAppReady=true;" if url.path.endswith(".js") else ""
            )
            request.fulfill(body=body, content_type=kind)
        elif url.path.startswith("/v1/"):
            request.fulfill(json={"execution_mode": "mock", "runtime_credentials_allowed": False})
        else:
            request.abort()

    page.route("**/*", route)
    page.goto("https://synthetic.test/")
    page.wait_for_function("window.__syntheticAppReady === true")
    return page, errors


def run(browser):
    base = ROOT / "src/ai_gateway/static"
    assets = {
        "/": (base / "index.html").read_text(),
        "/assets/app.js": (base / "app.js").read_text(),
        "/assets/styles.css": (base / "styles.css").read_text(),
    }
    page, errors = fixture(browser, assets)
    page.route(
        "**/v1/route",
        lambda route: route.fulfill(
            json={
                "decision": {
                    "route": "llm.fast",
                    "confidence": 1,
                    "model": "synthetic",
                    "task_type": "synthetic",
                    "complexity": "low",
                    "reasons": ["Synthetic"],
                    "risk_flags": [],
                    "model_candidates": [],
                    "council_plan": None,
                    "execution_plan": None,
                },
                "output": "SYNTHETIC OUTPUT",
                "metadata": {},
            }
        ),
    )
    page.locator("#saveHistory").uncheck()
    page.locator("#prompt").fill("SYNTHETIC OFF-PERIOD")
    page.evaluate("async()=>{await submitRoute({preventDefault(){}})}")
    assert page.evaluate("localStorage.getItem('ai-gateway-history')") is None
    page.locator("#saveHistory").check()
    page.locator("#prompt").fill("SYNTHETIC ON-PERIOD")
    page.evaluate("async()=>{await submitRoute({preventDefault(){}})}")
    saved = page.evaluate("localStorage.getItem('ai-gateway-history')")
    assert "ON-PERIOD" in saved and "OFF-PERIOD" not in saved
    assert page.locator(".results").evaluate("el=>getComputedStyle(el).overflowY") == "visible"
    assert page.locator("#strategyPlan").get_attribute("tabindex") == "0"
    assert not errors, errors
    page.close()
    page, errors = fixture(browser, assets, True)
    page.locator("#prompt").fill("SYNTHETIC STORAGE FAILURE")
    page.route(
        "**/v1/route",
        lambda route: route.fulfill(
            json={
                "decision": {
                    "route": "llm.fast",
                    "confidence": 1,
                    "model": "synthetic",
                    "task_type": "synthetic",
                    "complexity": "low",
                    "reasons": [],
                    "risk_flags": [],
                    "model_candidates": [],
                },
                "metadata": {},
            }
        ),
    )
    page.evaluate("async()=>{await submitRoute({preventDefault(){}})}")
    assert "cannot be saved" in page.locator("#historyNotice").inner_text()
    assert not errors, errors
    page.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        options = {"headless": True}
        if os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"):
            options["executable_path"] = os.environ["PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"]
        browser = playwright.chromium.launch(**options)
        try:
            run(browser)
            print("Synthetic browser regressions passed")
        finally:
            browser.close()
