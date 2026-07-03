"""Tests for pipeline.cleaner — Phase 2 Y1d."""
from pipeline.cleaner import clean_body, get_embedding_input


class TestCleanBody:
    """Y1d: 6 unit tests for the body cleaner."""

    def test_ap_photo_credit_stripped(self):
        """(i) AP photo credit line is removed entirely."""
        body = "A man walks past a damaged home in Moron, Thursday, June 25, 2026. (AP Photo/Name)"
        result, warned = clean_body(body)
        assert result == "", f"Expected empty, got: {result!r}"
        assert not warned

    def test_reuters_credit_stripped(self):
        """(ii) Reuters credit stripped from line."""
        body = "Oil prices fell sharply on Tuesday. (Reuters/Jane Doe)"
        result, warned = clean_body(body)
        assert "(Reuters" not in result
        assert "Oil prices fell sharply on Tuesday." in result
        assert not warned

    def test_location_tag_stripped(self):
        """(iii) Location tag 'WASHINGTON (AP) —' stripped from line start."""
        body = (
            "WASHINGTON (AP) — AI giant Anthropic said Friday it has taken "
            "its latest artificial intelligence models offline."
        )
        result, warned = clean_body(body)
        assert "WASHINGTON" not in result
        assert "AI giant Anthropic said Friday" in result
        assert not warned

    def test_left_not_stripped_from_prose(self):
        """(iv) 'Left, shakes hands...' is NOT stripped — it's real prose."""
        body = (
            "Anthropic co-founder and President Daniela Amodei, left, "
            "shakes hands with Snowflake CEO Sridhar Ramaswamy during "
            "the keynote presentation at Snowflake Summit 26."
        )
        result, warned = clean_body(body)
        assert "left," in result
        assert "shakes hands" in result
        assert not warned

    def test_produced_by_mid_sentence_kept(self):
        """(v) Legitimate sentence with 'Produced by' left alone (mid-line)."""
        body = (
            "The film was produced by Warner Bros and distributed globally. "
            "It won several awards."
        )
        result, warned = clean_body(body)
        # "Produced by" mid-sentence (not at line end, not Producer credit) → kept
        assert "produced by warner" in result.lower()
        assert not warned

    def test_no_boilerplate_passes_through(self):
        """(vi) Article with no boilerplate passes through unchanged."""
        body = (
            "The Supreme Court ruled 6-3 on Thursday to uphold a key "
            "provision of the Voting Rights Act. The decision affirms "
            "lower court rulings and represents a victory for civil "
            "rights advocates who had warned of voter suppression."
        )
        result, warned = clean_body(body)
        # Should be substantially the same (whitespace may differ)
        assert "Supreme Court ruled" in result
        assert "Voting Rights Act" in result
        assert "civil rights" in result
        assert not warned


class TestGetEmbeddingInput:
    """Y2: embedding input construction with cleaner."""

    def test_uses_1000_char_window(self):
        """Body window is 1000 chars after cleaning."""
        title = "Breaking News"
        body = "A" * 2000
        result = get_embedding_input(title, body, max_body_chars=1000)
        # Title + space + 1000 chars of body
        assert len(result) <= len(title) + 1 + 1000
        assert result.startswith("Breaking News AAAA")

    def test_strips_photo_captions_from_input(self):
        """Photo captions are removed before the 1000-char window."""
        title = "Earthquake Hits Venezuela"
        body = (
            "A man walks past a damaged building. (AP Photo/Name)\n"
            "Rescue workers search for survivors. (AP Photo/Other)\n"
            "CARACAS, Venezuela (AP) — The earthquake struck at 3am local "
            "time, causing widespread damage across the capital. Officials "
            "report at least 164 dead and hundreds more injured. Rescue "
            "teams are working through the rubble to find survivors. "
            "The 7.1-magnitude quake was followed by a 6.3 aftershock "
            "that further destabilized already weakened structures. "
            "Hospitals are overwhelmed with casualties and the government "
            "has declared a state of emergency across three provinces."
        )
        result = get_embedding_input(title, body, max_body_chars=1000)
        assert "(AP Photo" not in result
        assert "The earthquake struck at 3am" in result
        assert "164 dead" in result

    def test_empty_body_handled(self):
        """Empty body returns just the title."""
        result = get_embedding_input("Title Only", "", max_body_chars=1000)
        assert result == "Title Only"
