from urllib.error import URLError

from fastapi import APIRouter, HTTPException, Query

from ..services import media_embed

router = APIRouter(prefix="/api/media", tags=["media"])


@router.get("/resolve-bilibili", summary="解析 B 站链接（含 b23.tv 短链）")
def resolve_bilibili(url: str = Query(..., description="B 站页链接或 b23.tv 短链")):
    try:
        return media_embed.resolve_bilibili(url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (URLError, ConnectionError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/resolve-douyin", summary="解析抖音链接（含 v.douyin.com 短链）")
def resolve_douyin(url: str = Query(..., description="抖音分享链接或视频页地址")):
    try:
        return media_embed.resolve_douyin(url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (URLError, ConnectionError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
