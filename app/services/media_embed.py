import json
import re
from urllib.error import URLError
from urllib.request import Request, urlopen

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

_BVID = re.compile(r"(BV[a-zA-Z0-9]+)", re.I)
_DOUYIN_VIDEO_ID = re.compile(
    r"/video/(\d+)|modal_id=(\d+)|aweme_id[\"']?\s*[:=]\s*[\"']?(\d+)",
)
_MEDIA_URL = re.compile(
    r"https?://(?:v\.douyin\.com|www\.douyin\.com|b23\.tv|www\.bilibili\.com|"
    r"youtu\.be|(?:www\.)?youtube\.com|vimeo\.com)[^\s\"'<>]+",
    re.I,
)


def normalize_media_input(raw: str) -> str:
    """从抖音/B 站分享口令中提取首个 http 链接。"""
    text = (raw or "").strip()
    match = _MEDIA_URL.search(text)
    if match:
        return match.group(0).rstrip(".,;；，。！？)")
    return text

DOUYIN_IFRAME_STYLE = (
    "aspect-ratio:9/16;width:100%;max-width:420px;max-height:80vh;"
    "border:0;border-radius:8px;display:block;margin:12px auto"
)


def _fetch_url(url: str) -> tuple[str, str]:
    req = Request(url.strip(), headers={"User-Agent": UA})
    with urlopen(req, timeout=15) as resp:
        return resp.geturl(), resp.read().decode("utf-8", errors="ignore")


def _first_group(match: re.Match[str] | None) -> str | None:
    if not match:
        return None
    return next((g for g in match.groups() if g), None)


def douyin_iframe_html(video_id: str) -> str:
    src = f"https://open.douyin.com/player/video?vid={video_id}&autoplay=0"
    return (
        f'<iframe src="{src}" allowfullscreen referrerpolicy="unsafe-url" '
        f'style="{DOUYIN_IFRAME_STYLE}" title="抖音视频"></iframe>'
    )


def extract_douyin_video_id(url: str, body: str = "") -> str | None:
    direct = _DOUYIN_VIDEO_ID.search(url)
    if direct:
        return _first_group(direct)
    if body:
        from_body = _DOUYIN_VIDEO_ID.search(body)
        return _first_group(from_body)
    return None


def resolve_bilibili(url: str) -> dict:
    url = normalize_media_input(url)
    direct = _BVID.search(url)
    if direct:
        return {"bvid": direct.group(1), "final_url": url}

    if "b23.tv" not in url and "bilibili.com" not in url:
        raise ValueError("不是 B 站链接")

    final, _ = _fetch_url(url)
    match = _BVID.search(final)
    if not match:
        raise LookupError("跳转后未找到 BV 号")
    return {"bvid": match.group(1), "final_url": final}


def resolve_douyin(url: str) -> dict:
    url = normalize_media_input(url)
    if "douyin.com" not in url and "iesdouyin.com" not in url:
        raise ValueError("不是抖音链接，请粘贴分享文案或 v.douyin.com 链接")

    video_id = extract_douyin_video_id(url)
    final_url = url

    if not video_id or "v.douyin.com" in url:
        try:
            final_url, body = _fetch_url(url)
        except URLError as exc:
            raise ConnectionError(f"无法打开链接: {exc.reason}") from exc
        video_id = extract_douyin_video_id(final_url, body) or video_id

    if not video_id:
        raise LookupError("未找到视频 ID，请用浏览器打开分享链接后复制完整视频页地址")

    iframe_html = douyin_iframe_html(video_id)
    try:
        api = (
            "https://open.douyin.com/api/douyin/v1/video/get_iframe_by_video"
            f"?video_id={video_id}"
        )
        with urlopen(Request(api, headers={"User-Agent": UA}), timeout=12) as resp:
            payload = json.loads(resp.read())
        if payload.get("err_no") == 0:
            code = (payload.get("data") or {}).get("iframe_code") or ""
            if "open.douyin.com/player/video" in code:
                iframe_html = douyin_iframe_html(video_id)
    except (URLError, json.JSONDecodeError, KeyError):
        pass

    return {"video_id": video_id, "final_url": final_url, "iframe_html": iframe_html}
