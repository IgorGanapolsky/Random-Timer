from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_public_root_landing_page_exists_and_points_to_download():
    index_path = ROOT / "index.html"
    assert index_path.is_file(), "GitHub Pages serves the repo root, so index.html must exist."

    html = index_path.read_text(encoding="utf-8")
    assert "Start the 7-day challenge" in html
    assert "https://igorganapolsky.github.io/Random-Timer/download" in html


def test_public_root_download_page_exists_and_preserves_query_params():
    download_path = ROOT / "download" / "index.html"
    assert download_path.is_file(), "GitHub Pages needs a real /download route for tracked install flows."

    html = download_path.read_text(encoding="utf-8")
    assert "randomtimer://open" in html
    assert "query.forEach((value, key) => next.searchParams.set(key, value));" in html
    assert "window.location.replace(deepLink)" in html
