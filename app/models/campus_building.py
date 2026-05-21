from sqlalchemy import Boolean, Column, Integer, String, Text

from ..database import Base


class CampusBuilding(Base):
    """校园建筑业务数据；与前端 3D 场景 JSON 通过 building_id 关联。"""

    __tablename__ = "campus_buildings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, default="")
    floors_json = Column(Text, default="[]")
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
