from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Material, Tag, material_tags
from app.schemas.common import ApiResponse
from app.schemas.tag import TagCreate, TagRead

router = APIRouter(prefix="/tags", tags=["tags"])


def tag_dict(tag: Tag, count: int = 0) -> dict:
    return {"id": tag.id, "name": tag.name, "created_at": tag.created_at, "material_count": count}


@router.get("", response_model=ApiResponse[list[TagRead]])
def get_tags(db: Session = Depends(get_db)) -> dict:
    rows = db.execute(
        select(Tag, func.count(material_tags.c.material_id)).outerjoin(material_tags).group_by(Tag.id).order_by(Tag.name)
    ).all()
    return {"success": True, "data": [tag_dict(tag, count) for tag, count in rows], "message": "标签列表获取成功"}


@router.post("", response_model=ApiResponse[TagRead], status_code=status.HTTP_201_CREATED)
def post_tag(payload: TagCreate, db: Session = Depends(get_db)) -> dict:
    tag = Tag(name=payload.name.strip())
    db.add(tag)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="标签已存在")
    return {"success": True, "data": tag_dict(tag), "message": "标签创建成功"}


@router.delete("/{tag_id}", response_model=ApiResponse[dict])
def delete_tag(tag_id: str, db: Session = Depends(get_db)) -> dict:
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    db.delete(tag)
    db.commit()
    return {"success": True, "data": {"id": tag_id}, "message": "标签已删除"}

