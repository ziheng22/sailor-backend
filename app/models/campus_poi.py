from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text

from ..database import Base


class CampusPoi(Base):
    """建筑内 POI / 房间；坐标为 2D 平面导航用，3D 模型由前端 JSON 维护。"""

    __tablename__ = "campus_pois"

    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(String(64), ForeignKey("campus_buildings.building_id"), nullable=False, index=True)
    floor = Column(String(32), nullable=False, default="1")
    name = Column(String(128), nullable=False)
    poi_type = Column(String(32), nullable=False, default="room")
    x = Column(Float, nullable=False, default=0)
    y = Column(Float, nullable=False, default=0)
    meta_json = Column(Text, default="{}")
