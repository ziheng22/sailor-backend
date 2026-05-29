
from fastapi import APIRouter

router = APIRouter(prefix="/api/campus", tags=["campus"])

@router.get("", summary="校园漫游状态")
def campus_status():
    return {
        "status": "pending",
        "message": "校园漫游数据接口预留，待同伴模块完成后对接",
        "version": 0,
    }

@router.get("/buildings", summary="建筑列表（占位）", description="同伴对接后改为从数据库或配置文件读取。")
def campus_buildings():
    return {"buildings": [], "meta": {"source": "placeholder"}}
