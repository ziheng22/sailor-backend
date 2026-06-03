
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import AuthUser, require_admin
from ..database import get_db
from ..models.project import Project
from ..schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from ..services.slug_assign import ensure_unique_slug

router = APIRouter(prefix="/api/projects", tags=["projects"])
admin = APIRouter(prefix="/api/admin/projects", tags=["admin-projects"], dependencies=[Depends(require_admin)])

@router.get("", response_model=list[ProjectOut], summary="项目列表", description="仅返回 is_displayed=true 的项目。")
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).filter(Project.is_displayed.is_(True)).order_by(Project.sort_order, Project.id).all()

@router.get("/by-slug/{slug}", response_model=ProjectOut, summary="按 slug 获取项目")
def get_project_by_slug(slug: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.slug == slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project

@router.get("/{project_id}", response_model=ProjectOut, summary="按 ID 获取项目")
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project

@admin.get("", response_model=list[ProjectOut], summary="项目列表（管理员）")
def admin_list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.sort_order, Project.id).all()

@admin.post("", response_model=ProjectOut, status_code=201, summary="创建项目")
def create_project(data: ProjectCreate, user: AuthUser = Depends(require_admin), db: Session = Depends(get_db)):
    payload = data.model_dump()
    payload["updated_by"] = user.display_name
    base_slug = payload.pop("slug", None) or payload["name"]
    payload["slug"] = ensure_unique_slug(db, Project, base_slug)
    project = Project(**payload)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@admin.put("/{project_id}", response_model=ProjectOut, summary="更新项目")
def update_project(
    project_id: int,
    data: ProjectUpdate,
    user: AuthUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    project.updated_by = user.display_name
    db.commit()
    db.refresh(project)
    return project

@admin.delete("/{project_id}", status_code=204, summary="删除项目")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(project)
    db.commit()
