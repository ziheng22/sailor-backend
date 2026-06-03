from pydantic import BaseModel


class CampusBuildingOut(BaseModel):
    id: int
    building_id: str
    name: str
    description: str = ""
    floors_json: str = "[]"
    sort_order: int = 0
    is_active: bool = True

    class Config:
        from_attributes = True


class CampusPoiOut(BaseModel):
    id: int
    building_id: str
    floor: str
    name: str
    poi_type: str
    x: float
    y: float
    meta_json: str = "{}"

    class Config:
        from_attributes = True
