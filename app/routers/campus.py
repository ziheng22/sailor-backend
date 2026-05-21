from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.campus_building import CampusBuilding
from ..models.campus_poi import CampusPoi
from ..schemas.campus import CampusBuildingOut, CampusPoiOut

router = APIRouter(prefix="/api/campus", tags=["campus"])


@router.get("", summary="校园漫游状态")
def campus_status(db: Session = Depends(get_db)):
    building_count = db.query(CampusBuilding).filter(CampusBuilding.is_active.is_(True)).count()
    return {
        "status": "ready" if building_count else "pending",
        "message": "业务数据由 API 提供；3D 场景配置由前端 JSON 维护，通过 buildingId 关联。",
        "version": 1,
        "building_count": building_count,
    }


@router.get("/buildings", response_model=list[CampusBuildingOut], summary="建筑列表")
def campus_buildings(db: Session = Depends(get_db)):
    return (
        db.query(CampusBuilding)
        .filter(CampusBuilding.is_active.is_(True))
        .order_by(CampusBuilding.sort_order, CampusBuilding.id)
        .all()
    )


@router.get("/buildings/{building_id}/pois", response_model=list[CampusPoiOut], summary="建筑 POI")
def campus_pois(building_id: str, db: Session = Depends(get_db)):
    return (
        db.query(CampusPoi)
        .filter(CampusPoi.building_id == building_id)
        .order_by(CampusPoi.floor, CampusPoi.id)
        .all()
    )
