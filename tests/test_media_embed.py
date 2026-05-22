import unittest
from unittest.mock import patch

from app.services import media_embed


class TestNormalizeMediaInput(unittest.TestCase):
    def test_extract_douyin_url_from_share_text(self):
        raw = "2.82 复制打开抖音 https://v.douyin.com/XDQW-j48gCY/ O@X.mQ"
        self.assertEqual(
            media_embed.normalize_media_input(raw),
            "https://v.douyin.com/XDQW-j48gCY/",
        )

    def test_extract_bilibili_short_link(self):
        raw = "快来看 BV1xx https://b23.tv/abc123 吧"
        self.assertEqual(media_embed.normalize_media_input(raw), "https://b23.tv/abc123")

    def test_plain_url_unchanged(self):
        url = "https://www.bilibili.com/video/BV1xx411c7mD"
        self.assertEqual(media_embed.normalize_media_input(url), url)


class TestResolveBilibili(unittest.TestCase):
    def test_direct_bv_page(self):
        url = "https://www.bilibili.com/video/BV1xx411c7mD"
        out = media_embed.resolve_bilibili(url)
        self.assertEqual(out["bvid"], "BV1xx411c7mD")
        self.assertEqual(out["final_url"], url)

    @patch("app.services.media_embed._fetch_url")
    def test_b23_short_link(self, mock_fetch):
        mock_fetch.return_value = (
            "https://www.bilibili.com/video/BV1RboQBCETw/?share",
            "",
        )
        out = media_embed.resolve_bilibili("https://b23.tv/HMjoNjh")
        self.assertEqual(out["bvid"], "BV1RboQBCETw")

    def test_not_bilibili_raises(self):
        with self.assertRaises(ValueError):
            media_embed.resolve_bilibili("https://example.com/")


class TestResolveDouyin(unittest.TestCase):
    def test_not_douyin_raises(self):
        with self.assertRaises(ValueError):
            media_embed.resolve_douyin("https://example.com/")

    @patch("app.services.media_embed.urlopen")
    @patch("app.services.media_embed._fetch_url")
    def test_short_link_resolves_video_id(self, mock_fetch, mock_urlopen):
        mock_fetch.return_value = (
            "https://www.douyin.com/video/7634501234567890123",
            "",
        )
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            b'{"err_no":1}'
        )
        raw = "分享 https://v.douyin.com/ABC123/ 结束"
        out = media_embed.resolve_douyin(raw)
        self.assertEqual(out["video_id"], "7634501234567890123")
        self.assertIn("open.douyin.com/player/video", out["iframe_html"])

    def test_douyin_iframe_contains_video_id(self):
        html = media_embed.douyin_iframe_html("1234567890")
        self.assertIn("vid=1234567890", html)
        self.assertIn("open.douyin.com", html)


class TestMediaRouterHandlers(unittest.TestCase):
    def test_resolve_douyin_bad_input_returns_400(self):
        from fastapi import HTTPException

        from app.routers.media import resolve_douyin

        with self.assertRaises(HTTPException) as ctx:
            resolve_douyin(url="not-a-link")
        self.assertEqual(ctx.exception.status_code, 400)

    @patch("app.services.media_embed.resolve_bilibili")
    def test_resolve_bilibili_success(self, mock_resolve):
        from app.routers.media import resolve_bilibili

        mock_resolve.return_value = {"bvid": "BV1test", "final_url": "https://b23.tv/x"}
        out = resolve_bilibili(url="https://b23.tv/x")
        self.assertEqual(out["bvid"], "BV1test")


if __name__ == "__main__":
    unittest.main()
