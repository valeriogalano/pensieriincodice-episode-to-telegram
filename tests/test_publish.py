import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from publish import (
    escape_markdown_v2,
    fetch_last_episode,
    is_published,
    load_podcasts_config,
    load_published_urls,
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


class TestLoadPublishedUrls:
    def test_returns_dict_from_env(self):
        data = {"pod1": "https://example.com/ep1"}
        with patch.dict(os.environ, {"LAST_PUBLISHED_URLS": json.dumps(data)}):
            result = load_published_urls()
        assert result == data

    def test_returns_empty_dict_when_env_missing(self):
        env = {k: v for k, v in os.environ.items() if k != "LAST_PUBLISHED_URLS"}
        with patch.dict(os.environ, env, clear=True):
            result = load_published_urls()
        assert result == {}

    def test_returns_empty_dict_on_invalid_json(self):
        with patch.dict(os.environ, {"LAST_PUBLISHED_URLS": "not-json"}):
            result = load_published_urls()
        assert result == {}


class TestIsPublished:
    def test_returns_true_when_link_matches(self):
        urls = {"pod1": "https://example.com/ep42"}
        assert is_published("https://example.com/ep42", "pod1", urls) is True

    def test_returns_false_when_link_differs(self):
        urls = {"pod1": "https://example.com/ep41"}
        assert is_published("https://example.com/ep42", "pod1", urls) is False

    def test_returns_false_when_podcast_missing(self):
        assert is_published("https://example.com/ep42", "pod1", {}) is False


class TestLoadPodcastsConfig:
    def test_loads_valid_json(self, tmp_path):
        config = [{"id": "p1", "name": "Podcast 1", "feed_url": "https://example.com/feed"}]
        config_file = tmp_path / "podcasts.json"
        config_file.write_text(json.dumps(config))
        result = load_podcasts_config(str(config_file))
        assert result == config

    def test_raises_when_file_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_podcasts_config(str(tmp_path / "missing.json"))


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
        episode = {"title": "Test Ep", "link": "https://ex.com/ep", "hashtags": "#test"}
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
        assert "Test Ep" in payload["text"] or r"Test Ep" in payload["text"]

    def test_raises_on_api_error(self):
        episode = {"title": "Test", "link": "https://ex.com/ep", "hashtags": ""}
        template = "{title} {link} {hashtags}"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": False, "description": "Unauthorized"}
        with patch("publish.requests.post", return_value=mock_resp):
            with pytest.raises(Exception, match="Errore Telegram API"):
                publish_to_telegram(episode, "BAD_KEY", "-100123", template)
