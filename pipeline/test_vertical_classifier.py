"""Tests for pipeline.vertical_classifier — embedding-based vertical classification."""
import pytest
from pipeline.vertical_classifier import (
    VERTICAL_PROTOTYPES,
    classify_text,
    classify_cluster,
    get_vertical_list,
)


class TestGetVerticalList:
    def test_returns_all_three_verticals(self):
        verticals = get_vertical_list()
        assert "geopolitics" in verticals
        assert "economics" in verticals
        assert "technology" in verticals
        assert len(verticals) == 3


class TestClassifyText:
    def test_empty_text_returns_geopolitics(self):
        assert classify_text("") == "geopolitics"
        assert classify_text("   ") == "geopolitics"

    def test_geopolitics_article(self):
        text = (
            "The United States conducted retaliatory airstrikes against Iranian "
            "military positions following an attack on American forces."
        )
        assert classify_text(text) == "geopolitics"

    def test_economics_article(self):
        text = (
            "The Federal Reserve raised interest rates by 0.25 percentage points "
            "citing persistent inflation and strong labor market data."
        )
        assert classify_text(text) == "economics"

    def test_technology_article(self):
        text = (
            "An artificial intelligence startup raised 500 million dollars in "
            "venture capital funding to develop next-generation language models."
        )
        assert classify_text(text) == "technology"

    def test_geopolitics_clearly_wins_over_economics(self):
        """Military conflict should score higher on geopolitics than economics."""
        text = (
            "Military forces crossed the border at dawn, triggering an international "
            "crisis. The UN Security Council convened an emergency session."
        )
        assert classify_text(text) == "geopolitics"

    def test_economics_clearly_wins_over_technology(self):
        """Central bank policy should score higher on economics."""
        text = (
            "The central bank cut interest rates to stimulate economic growth "
            "as inflation fell below the two percent target."
        )
        assert classify_text(text) == "economics"


class TestClassifyCluster:
    def test_empty_list_returns_geopolitics(self):
        assert classify_cluster([]) == "geopolitics"

    def test_majority_vote(self):
        texts = [
            "Military conflict escalates in the region.",
            "Diplomatic talks resume between nations.",
            "Stock market reaches all-time high.",  # minority — economics
            "Peace negotiations enter final phase.",
            "UN passes new sanctions resolution.",
        ]
        assert classify_cluster(texts) == "geopolitics"

    def test_split_vote_goes_to_first_majority(self):
        texts = [
            "Interest rates rise as inflation persists.",
            "GDP growth exceeds expectations.",
            "New AI model breaks performance records.",
            "Central bank signals more rate hikes ahead.",
        ]
        assert classify_cluster(texts) == "economics"

    def test_single_article(self):
        texts = ["Federal Reserve raises interest rates amid inflation concerns."]
        result = classify_cluster(texts)
        assert result in get_vertical_list()


class TestPrototypes:
    def test_all_verticals_have_prototypes(self):
        for v in get_vertical_list():
            assert v in VERTICAL_PROTOTYPES
            assert len(VERTICAL_PROTOTYPES[v]) > 50  # richer than keywords

    def test_prototypes_are_distinct(self):
        """Prototypes should not share significant keyword overlap."""
        geo = set(VERTICAL_PROTOTYPES["geopolitics"].lower().split())
        econ = set(VERTICAL_PROTOTYPES["economics"].lower().split())
        tech = set(VERTICAL_PROTOTYPES["technology"].lower().split())

        # Each pair should have < 30% word overlap
        geo_econ = len(geo & econ) / min(len(geo), len(econ))
        geo_tech = len(geo & tech) / min(len(geo), len(tech))
        econ_tech = len(econ & tech) / min(len(econ), len(tech))

        # ponytail: some overlap is fine (e.g. "policy" in both geo+econ)
        assert geo_econ < 0.25
        assert geo_tech < 0.15
        assert econ_tech < 0.15
