from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs/COMMUNITY_GROWTH_SYSTEM.md").read_text(encoding="utf-8")


def test_community_growth_doc_defines_referral_leaderboard_reputation_boundaries():
    assert "Referral System" in DOC
    assert "Contributor Leaderboard" in DOC
    assert "Reputation System" in DOC
    assert "Onboarding Flow" in DOC
    assert "record_referral" in DOC
    assert "record_reputation_event" in DOC

    assert "automatic PNET payouts" in DOC
    assert "referral yield" in DOC
    assert "fake/self-referral farming" in DOC
    assert "They do not mean verified income, guaranteed earnings, or profitability" in DOC
    assert "Reputation does not grant" in DOC
    assert "binding governance" in DOC
