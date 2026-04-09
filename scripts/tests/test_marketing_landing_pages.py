from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_product_landing_page_exists_and_points_to_download():
    index_path = ROOT / "marketing" / "product-pages" / "index.html"
    assert index_path.is_file(), "Product landing HTML lives under marketing/product-pages/ (root stays tooling-only)."

    html = index_path.read_text(encoding="utf-8")
    assert "Start the 7-day challenge" in html
    assert "https://igorganapolsky.github.io/Random-Timer/download" in html


def test_deployed_download_page_exists_and_preserves_query_params():
    download_path = ROOT / "marketing" / "site" / "download" / "index.html"
    assert download_path.is_file(), "GitHub Pages artifact is marketing/site; /download must exist there."

    html = download_path.read_text(encoding="utf-8")
    assert "randomtimer://open" in html
    assert "query.forEach((value, key) => next.searchParams.set(key, value));" in html
    assert "window.location.replace(deepLink)" in html
