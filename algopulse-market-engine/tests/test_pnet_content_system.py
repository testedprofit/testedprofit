from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = (ROOT / "docs/PNET_CONTENT_SYSTEM.md").read_text(encoding="utf-8")
WEBSITE_COPY = (ROOT / "docs/PNET_WEBSITE_COPY.md").read_text(encoding="utf-8")
VISUALS = (ROOT / "docs/PNET_VISUAL_ASSETS.md").read_text(encoding="utf-8")


def test_pnet_content_calendar_covers_30_days_and_guardrails():
    assert "## 30-Day Content Calendar" in CONTENT
    for day in range(1, 31):
        assert f"| {day} |" in CONTENT

    assert "real-world operating evidence" in CONTENT.lower()
    assert "verified receipts and methodology" in CONTENT
    assert "Do not use buy/sell, moon, ROI, yield, guaranteed income" in CONTENT
    assert "Rob approve" in CONTENT or "Rob approves" in CONTENT


def test_pnet_content_system_includes_five_threads_and_blog_templates():
    for index in range(1, 6):
        assert f"### Thread {index}:" in CONTENT

    assert "### Blog 1:" in CONTENT
    assert "### Blog 2:" in CONTENT
    assert "### Blog 3:" in CONTENT
    assert "Credits are not token rewards" in CONTENT
    assert "Past receipts do not imply future income" in CONTENT


def test_pnet_website_copy_keeps_tokenomics_and_contribution_conservative():
    assert "PNET powers transparent contribution and market-intelligence workflows" in WEBSITE_COPY
    assert "Algorand ASA ID: `3169177585`" in WEBSITE_COPY
    assert "price targets, return projections, guaranteed income language, or exchange-listing claims" in WEBSITE_COPY
    assert "manual review" in WEBSITE_COPY
    assert "not token rewards, yield, revenue share, or binding governance power" in WEBSITE_COPY
    assert "Nothing here is financial advice" in WEBSITE_COPY


def test_pnet_visual_assets_define_mermaid_diagrams_and_redaction_rules():
    assert VISUALS.count("```mermaid") >= 4
    assert "Contribution Protocol Flow" in VISUALS
    assert "Utility Boundary" in VISUALS
    assert "Content Evidence Loop" in VISUALS
    assert "Tokenomics Content Gate" in VISUALS
    assert "No secrets" in VISUALS
    assert "No fresh executable route data" in VISUALS
