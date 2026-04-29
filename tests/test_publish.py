import os
from unittest.mock import MagicMock, patch

import pytest

from publish import (
    escape_markdown_v2,
    fetch_last_episode,
    is_published,
    normalize_template,
    publish_to_telegram,
)

ITUNES_NS = 'http://www.itunes.com/dtds/podcast-1.0.dtd'

SAMPLE_RSS = b"""<?xml version="1.0"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <item>
      <title>Episodio 42</title>
      <link>https://example.com/ep42</link>
      <itunes:keywords>python, coding, devops</itunes:keywords>
    </item>
  </channel>
</rss>"""

SAMPLE_RSS_NO_KEYWORDS = b"""<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Episodio senza tag</title>
      <link>https://example.com/ep1</link>
    </item>
  </channel>
</rss>"""

SAMPLE_RSS_NO_LINK = b"""<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Episodio senza link</title>
      <enclosure url="https://cdn.example.com/ep42.mp3?updated=12345" type="audio/mpeg" length="1000"/>
    </item>
  </channel>
</rss>"""


class TestEscapeMarkdownV2:
    def test_escapes_special_chars(self):
        assert escape_markdown_v2("Hello_World") == r"Hello\_World"
        assert escape_markdown_v2("Test.dot") == r"Test\.dot"
        assert escape_markdown_v2("[link]") == r"\[link\]"

    def test_plain_text_unchanged(self):
        assert escape_markdown_v2("Hello World") == "Hello World"

    def test_multiple_specials(self):
        result = escape_markdown_v2("a_b*c")
        assert result == r"a\_b\*c"

    def test_empty_string(self):
        assert escape_markdown_v2("") == ""


class TestNormalizeTemplate:
    def test_converts_literal_crlf(self):
        assert normalize_template("a\\r\\nb") == "a\nb"

    def test_converts_literal_lf(self):
        assert normalize_template("a\\nb") == "a\nb"

    def test_real_newlines_unchanged(self):
        assert normalize_template("a\nb") == "a\nb"

    def test_multiple_sequences(self):
        assert normalize_template("a\\r\\nb\\r\\nc") == "a\nb\nc"

    def test_empty_string(self):
        assert normalize_template("") == ""


class TestIsPublished:
    def test_returns_true_when_link_matches(self):
        assert is_published("https://example.com/ep42", "https://example.com/ep42") is True

    def test_returns_false_when_link_differs(self):
        assert is_published("https://example.com/ep42", "https://example.com/ep41") is False

    def test_returns_false_when_last_url_empty(self):
        assert is_published("https://example.com/ep42", "") is False


class TestFetchLastEpisode:
    def test_parses_title_link_hashtags(self):
        mock_resp = MagicMock()
        mock_resp.content = SAMPLE_RSS
        with patch("publish.requests.get", return_value=mock_resp):
            episode = fetch_last_episode("https://feed.example.com/rss")
        assert episode["title"] == "Episodio 42"
        assert episode["link"] == "https://example.com/ep42"
        assert "#python" in episode["hashtags"]
        assert "#coding" in episode["hashtags"]
        assert "#devops" in episode["hashtags"]

    def test_no_keywords_returns_empty_hashtags(self):
        mock_resp = MagicMock()
        mock_resp.content = SAMPLE_RSS_NO_KEYWORDS
        with patch("publish.requests.get", return_value=mock_resp):
            episode = fetch_last_episode("https://feed.example.com/rss")
        assert episode["hashtags"] == ""

    def test_fallback_to_enclosure_when_no_link(self):
        mock_resp = MagicMock()
        mock_resp.content = SAMPLE_RSS_NO_LINK
        with patch("publish.requests.get", return_value=mock_resp):
            episode = fetch_last_episode("https://feed.example.com/rss")
        assert episode["link"] == "https://cdn.example.com/ep42.mp3"

    def test_raises_on_empty_feed(self):
        empty_rss = b"""<?xml version="1.0"?><rss><channel></channel></rss>"""
        mock_resp = MagicMock()
        mock_resp.content = empty_rss
        with patch("publish.requests.get", return_value=mock_resp):
            with pytest.raises(Exception, match="Nessun episodio"):
                fetch_last_episode("https://feed.example.com/rss")

    def test_raises_on_http_error(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("404")
        with patch("publish.requests.get", return_value=mock_resp):
            with pytest.raises(Exception):
                fetch_last_episode("https://feed.example.com/rss")


class TestPublishToTelegram:
    def test_sends_correct_request(self):
        episode = {"title": "Test Ep", "link": "https://ex.com/ep-1", "hashtags": "#test"}
        template = "Nuovo episodio: {title}\n{link}\n{hashtags}"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True}
        with patch("publish.requests.post", return_value=mock_resp) as mock_post:
            publish_to_telegram(episode, "API_KEY", "-100123", template)
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert "API_KEY" in call_kwargs[0][0]
        payload = call_kwargs[1]["json"]
        assert payload["chat_id"] == "-100123"
        assert "Test Ep" in payload["text"]
        assert "https://ex.com/ep-1" in payload["text"]
        assert payload["link_preview_options"] == {"url": "https://ex.com/ep-1"}

    def test_link_not_escaped_in_output(self):
        episode = {"title": "Ep", "link": "https://www.spreaker.com/ep-12-test--1", "hashtags": ""}
        template = "{title}\n{link}"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True}
        with patch("publish.requests.post", return_value=mock_resp) as mock_post:
            publish_to_telegram(episode, "KEY", "-100", template)
        text = mock_post.call_args[1]["json"]["text"]
        assert "https://www.spreaker.com/ep-12-test--1" in text

    def test_raises_on_api_error(self):
        episode = {"title": "Test", "link": "https://ex.com/ep", "hashtags": ""}
        template = "{title} {link} {hashtags}"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": False, "description": "Unauthorized"}
        with patch("publish.requests.post", return_value=mock_resp):
            with pytest.raises(Exception, match="Errore Telegram API"):
                publish_to_telegram(episode, "BAD_KEY", "-100123", template)
