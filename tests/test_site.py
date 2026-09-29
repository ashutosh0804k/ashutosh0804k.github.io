"""End-to-end checks for the portfolio site, run with Playwright on every push."""

from urllib.parse import urlparse

import pytest
from axe_playwright_python.sync_playwright import Axe

from conftest import LIVE_URL, SITE_ROOT

# LinkedIn answers automated requests with status 999, so it can't be checked by a bot.
UNCHECKABLE_HOSTS = {"www.linkedin.com", "linkedin.com"}


def is_local(url, base_url):
    return url.startswith(base_url)


@pytest.fixture
def home(page, base_url):
    page.goto(base_url + "/")
    return page


def test_title_and_description(home):
    assert home.title() == "Ashutosh Khatavkar | SDET & QA Automation Engineer"
    description = home.locator('meta[name="description"]').get_attribute("content")
    assert "SDET" in description


def test_no_javascript_or_local_resource_errors(page, base_url):
    problems = []
    page.on("pageerror", lambda error: problems.append(f"JS error: {error}"))
    page.on("requestfailed", lambda request: problems.append(f"failed: {request.url}")
            if is_local(request.url, base_url) else None)
    page.on("response", lambda response: problems.append(f"{response.status}: {response.url}")
            if is_local(response.url, base_url) and response.status >= 400 else None)
    page.goto(base_url + "/", wait_until="networkidle")
    assert problems == []


def test_every_in_page_link_has_a_target(home):
    hrefs = home.eval_on_selector_all('a[href^="#"]', "links => links.map(a => a.getAttribute('href'))")
    assert hrefs, "expected in-page navigation links"
    for href in hrefs:
        assert home.locator(href).count() == 1, f"{href} points to nothing"


def test_local_files_referenced_by_the_page_exist(home, base_url):
    urls = home.eval_on_selector_all(
        "a[href], img[src]",
        "els => els.map(e => e.href || e.src)",
    )
    for url in set(urls):
        if is_local(url, base_url) and "#" not in url:
            response = home.request.get(url)
            assert response.status == 200, f"{url} returned {response.status}"


def test_resume_downloads_as_pdf(home):
    with home.expect_download() as download_info:
        home.get_by_role("link", name="Download Resume").click()
    download = download_info.value
    assert download.suggested_filename.endswith(".pdf")
    with open(download.path(), "rb") as file:
        assert file.read(5) == b"%PDF-"


def test_local_images_actually_render(home, base_url):
    for img in home.locator("img").all():
        src = img.get_attribute("src")
        if src.startswith("http"):
            continue
        img.scroll_into_view_if_needed()
        width = img.evaluate("el => el.complete ? el.naturalWidth : 0")
        assert width > 0, f"{src} did not render"


def test_share_preview_tags_point_to_real_files(home):
    for prop in ["og:title", "og:description", "og:image", "og:url"]:
        assert home.locator(f'meta[property="{prop}"]').get_attribute("content"), f"missing {prop}"
    image_url = home.locator('meta[property="og:image"]').get_attribute("content")
    assert image_url.startswith(LIVE_URL)
    local_path = SITE_ROOT / image_url[len(LIVE_URL):]
    assert local_path.is_file(), f"og:image {local_path.name} is not in the repo"


@pytest.mark.parametrize("width", [375, 768, 1440])
def test_no_horizontal_scroll(page, base_url, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(base_url + "/")
    scroll_width = page.evaluate("document.documentElement.scrollWidth")
    assert scroll_width <= width, f"page is {scroll_width}px wide at a {width}px viewport"


def test_mobile_menu_opens_navigates_and_closes(page, base_url):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(base_url + "/")
    toggle = page.locator(".menu-toggle")
    projects_link = page.locator('.nav-links a[href="#quests"]')

    assert projects_link.is_hidden()
    toggle.click()
    assert projects_link.is_visible()
    assert toggle.get_attribute("aria-expanded") == "true"

    projects_link.click()
    assert projects_link.is_hidden()
    assert toggle.get_attribute("aria-expanded") == "false"


def test_hero_buttons_visible_without_scrolling_on_phone(page, base_url):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(base_url + "/")
    resume_button = page.get_by_role("link", name="Download Resume")
    box = resume_button.bounding_box()
    assert box is not None and box["y"] + box["height"] <= 844


def test_terminal_replay_finishes_with_all_tests_passing(home):
    terminal = home.locator("#terminal-body")
    terminal.get_by_text("41 passed").wait_for(timeout=15000)
    home.locator("#terminal-replay").click()
    terminal.get_by_text("41 passed").wait_for(timeout=15000)


def test_no_serious_accessibility_violations(home):
    # Reveal scroll-animated sections so axe checks them in their final state.
    home.evaluate("document.querySelectorAll('.fade-in').forEach(el => el.classList.add('visible'))")
    home.get_by_text("41 passed").wait_for(timeout=15000)
    results = Axe().run(home)
    serious = []
    for violation in results.response["violations"]:
        if violation["impact"] in ("serious", "critical"):
            targets = [node["target"] for node in violation["nodes"][:3]]
            serious.append(f"{violation['id']}: {violation['help']} {targets}")
    assert serious == [], "\n".join(serious)


@pytest.mark.external
def test_external_links_resolve(home, base_url):
    """Needs internet access. Runs in CI; skip locally with -m 'not external'."""
    urls = home.eval_on_selector_all('a[href^="http"]', "links => links.map(a => a.href)")
    broken = []
    for url in sorted(set(urls)):
        if is_local(url, base_url) or urlparse(url).hostname in UNCHECKABLE_HOSTS:
            continue
        response = home.request.get(url, max_redirects=5, timeout=20000)
        if response.status >= 400:
            broken.append(f"{response.status}: {url}")
    assert broken == []
