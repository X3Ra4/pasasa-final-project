import json
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.urls import reverse

from maps.services.news import normalize_steam_news_item, resolve_news_language, translate_with_google


class NewsServiceTests(SimpleTestCase):
    def test_resolve_news_language_defaults_and_fallbacks(self):
        self.assertEqual(resolve_news_language(None), "ru")
        self.assertEqual(resolve_news_language("ru"), "ru")
        self.assertEqual(resolve_news_language("en"), "en")
        self.assertEqual(resolve_news_language("de"), "en")

    def test_normalize_steam_news_item(self):
        item = {
            "gid": "12345",
            "title": "<b>Community Crunch</b>",
            "contents": """
                <img src="https://example.com/image.jpg">
                <p>Hello <strong>survivors</strong>!</p>
                <p>Second paragraph with more text.</p>
            """,
            "url": "https://store.steampowered.com/news/app/2399830/view/12345",
            "date": 1773079200,
        }

        normalized = normalize_steam_news_item(item)

        self.assertEqual(normalized["id"], "steam:12345")
        self.assertEqual(normalized["title"], "Community Crunch")
        self.assertIn("Hello survivors!", normalized["description"])
        self.assertEqual(normalized["url"], item["url"])
        self.assertEqual(normalized["image"], "https://example.com/image.jpg")
        self.assertEqual(normalized["published_at"], "2026-03-09T18:00:00Z")

    def test_normalize_steam_news_item_strips_bbcode_and_invalid_image(self):
        item = {
            "gid": "999",
            "title": "[b]Update[/b]",
            "contents": """
                [color=#66ffff][b]This summer[/b][/color] begins now.
                [url=https://example.com]Read more[/url]
                [img]not-an-image[/img]
            """,
            "url": "https://store.steampowered.com/news/app/2399830/view/999",
            "date": 1773079200,
        }

        normalized = normalize_steam_news_item(item)

        self.assertEqual(normalized["title"], "Update")
        self.assertIn("This summer begins now.", normalized["description"])
        self.assertNotIn("[color", normalized["description"])
        self.assertEqual(normalized["image"], None)

    @patch("maps.services.news.request.urlopen")
    def test_translate_with_google_returns_joined_text(self, urlopen_mock):
        response_mock = MagicMock()
        response_mock.read.return_value = json.dumps(
            [[["Привет, выжившие!", "Hello survivors!", None, None, 1]]]
        ).encode("utf-8")
        urlopen_mock.return_value.__enter__.return_value = response_mock

        translated = translate_with_google("Hello survivors!", target_lang="ru")

        self.assertEqual(translated, "Привет, выжившие!")


class NewsApiTests(SimpleTestCase):
    @patch("maps.views.get_news_payload")
    def test_news_api_returns_payload(self, get_news_payload_mock):
        get_news_payload_mock.return_value = {
            "lang": "ru",
            "source": "steam",
            "items": [
                {
                    "id": "steam:1",
                    "title": "Заголовок",
                    "description": "Описание",
                    "url": "https://example.com/news/1",
                    "image": None,
                    "published_at": "2026-03-09T18:00:00Z",
                }
            ],
        }

        response = self.client.get(reverse("maps:news_api"), {"lang": "ru"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["lang"], "ru")
        self.assertEqual(response.json()["source"], "steam")
        self.assertEqual(len(response.json()["items"]), 1)
        get_news_payload_mock.assert_called_once_with("ru")
