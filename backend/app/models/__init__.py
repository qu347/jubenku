from app.models.genre import GenreMetric, GenreModule, ModuleSection
from app.models.material import Material, MaterialRelation, MaterialVersion, material_tags
from app.models.project import Project, ProjectMaterial
from app.models.tag import MaterialTag, Tag
from app.models.upload_platform import UploadPlatform

__all__ = [
    "GenreMetric", "GenreModule", "ModuleSection", "Material", "MaterialRelation",
    "MaterialTag", "MaterialVersion", "Project", "ProjectMaterial", "Tag", "UploadPlatform", "material_tags",
]
