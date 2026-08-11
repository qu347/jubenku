from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Material, Project
from app.schemas.common import ApiResponse
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


def project_dict(project: Project, count: int = 0) -> dict:
    return {
        "id": project.id, "name": project.name, "description": project.description,
        "status": project.status, "created_at": project.created_at,
        "updated_at": project.updated_at, "material_count": count,
    }


@router.get("", response_model=ApiResponse[list[ProjectRead]])
def get_projects(db: Session = Depends(get_db)) -> dict:
    rows = db.execute(
        select(Project, func.count(Material.id)).outerjoin(Material).group_by(Project.id).order_by(Project.updated_at.desc())
    ).all()
    return {"success": True, "data": [project_dict(project, count) for project, count in rows], "message": "项目列表获取成功"}


@router.post("", response_model=ApiResponse[ProjectRead], status_code=status.HTTP_201_CREATED)
def post_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> dict:
    project = Project(**payload.model_dump())
    db.add(project)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="项目名称已存在")
    return {"success": True, "data": project_dict(project), "message": "项目创建成功"}


@router.patch("/{project_id}", response_model=ApiResponse[ProjectRead])
def patch_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db)) -> dict:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="项目名称已存在")
    count = db.scalar(select(func.count(Material.id)).where(Material.project_id == project.id)) or 0
    return {"success": True, "data": project_dict(project, count), "message": "项目更新成功"}


@router.delete("/{project_id}", response_model=ApiResponse[dict])
def delete_project(project_id: str, db: Session = Depends(get_db)) -> dict:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    for material in project.materials:
        material.project_id = None
    db.delete(project)
    db.commit()
    return {"success": True, "data": {"id": project_id}, "message": "项目已删除，所属素材已保留"}

